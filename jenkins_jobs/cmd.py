#!/usr/bin/env python
# Copyright (C) 2012 OpenStack Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import argparse
import fnmatch
import io
import logging
import os
import platform
import sys
import yaml

from six.moves import configparser
from six.moves import input
from six.moves import StringIO

from jenkins_jobs.builder import Builder
from jenkins_jobs.errors import JenkinsJobsException
import jenkins_jobs.version


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

DEFAULT_CONF = """
[job_builder]
keep_descriptions=False
ignore_cache=False
recursive=False
exclude=.*
allow_duplicates=False
allow_empty_variables=False

[jenkins]
url=http://localhost:8080/
query_plugins_info=True

[hipchat]
authtoken=dummy
send-as=Jenkins

[__future__]
param_order_from_yaml=False
"""


def confirm(question):
    answer = input('%s (Y/N): ' % question).upper().strip()
    if not answer == 'Y':
        sys.exit('Aborted')


def recurse_path(root, excludes=None):
    if excludes is None:
        excludes = []

    basepath = os.path.realpath(root)
    pathlist = [basepath]

    patterns = [e for e in excludes if os.path.sep not in e]
    absolute = [e for e in excludes if os.path.isabs(e)]
    relative = [e for e in excludes if os.path.sep in e and
                not os.path.isabs(e)]
    for root, dirs, files in os.walk(basepath, topdown=True):
        dirs[:] = [
            d for d in dirs
            if not any([fnmatch.fnmatch(d, pattern) for pattern in patterns])
            if not any([fnmatch.fnmatch(os.path.abspath(os.path.join(root, d)),
                                        path)
                        for path in absolute])
            if not any([fnmatch.fnmatch(os.path.relpath(os.path.join(root, d)),
                                        path)
                        for path in relative])
        ]
        pathlist.extend([os.path.join(root, path) for path in dirs])

    return pathlist


def create_parser():

    parser = argparse.ArgumentParser()
    recursive_parser = argparse.ArgumentParser(add_help=False)
    recursive_parser.add_argument('-r', '--recursive', action='store_true',
                                  dest='recursive', default=False,
                                  help='look for yaml files recursively')
    recursive_parser.add_argument('-x', '--exclude', dest='exclude',
                                  action='append', default=[],
                                  help='paths to exclude when using recursive'
                                       ' search, uses standard globbing.')
    subparser = parser.add_subparsers(help='update, test or delete job',
                                      dest='command')

    # subparser: update
    parser_update = subparser.add_parser('update', parents=[recursive_parser])
    parser_update.add_argument('path', help='colon-separated list of paths to'
                                            ' YAML files or directories')
    parser_update.add_argument('names', help='name(s) of job(s)', nargs='*')
    parser_update.add_argument('--delete-old', help='delete obsolete jobs',
                               action='store_true',
                               dest='delete_old', default=False,)
    parser_update.add_argument('--workers', dest='n_workers', type=int,
                               default=1, help='number of workers to use, 0 '
                               'for autodetection and 1 for just one worker.')

    # subparser: test
    parser_test = subparser.add_parser('test', parents=[recursive_parser])
    parser_test.add_argument('path', help='colon-separated list of paths to'
                                          ' YAML files or directories',
                             nargs='?', default=sys.stdin)
    parser_test.add_argument('-p', dest='plugins_info_path', default=None,
                             help='path to plugin info YAML file')
    parser_test.add_argument('-o', dest='output_dir', default=sys.stdout,
                             help='path to output XML')
    parser_test.add_argument('name', help='name(s) of job(s)', nargs='*')

    # subparser: delete
    parser_delete = subparser.add_parser('delete', parents=[recursive_parser])
    parser_delete.add_argument('name', help='name of job', nargs='+')
    parser_delete.add_argument('-p', '--path', default=None,
                               help='colon-separated list of paths to'
                                    ' YAML files or directories')

    # subparser: delete-all
    subparser.add_parser('delete-all',
                         help='delete *ALL* jobs from Jenkins server, '
                         'including those not managed by Jenkins Job '
                         'Builder.')
    parser.add_argument('--conf', dest='conf', help='configuration file')
    parser.add_argument('-l', '--log_level', dest='log_level', default='info',
                        help="log level (default: %(default)s)")
    parser.add_argument(
        '--ignore-cache', action='store_true',
        dest='ignore_cache', default=False,
        help='ignore the cache and update the jobs anyhow (that will only '
             'flush the specified jobs cache)')
    parser.add_argument(
        '--flush-cache', action='store_true', dest='flush_cache',
        default=False, help='flush all the cache entries before updating')
    parser.add_argument('--version', dest='version', action='version',
                        version=version(),
                        help='show version')
    parser.add_argument(
        '--allow-empty-variables', action='store_true',
        dest='allow_empty_variables', default=None,
        help='Don\'t fail if any of the variables inside any string are not '
        'defined, replace with empty string instead')
    parser.add_argument(
        '--user', '-u',
        help='The Jenkins user to use for authentication. This overrides '
        'the user specified in the configuration file')
    parser.add_argument(
        '--password', '-p',
        help='Password or API token to use for authenticating towards '
        'Jenkins. This overrides the password specified in the '
        'configuration file.')

    return parser


def main(argv=None):

    # We default argv to None and assign to sys.argv[1:] below because having
    # an argument default value be a mutable type in Python is a gotcha. See
    # http://bit.ly/1o18Vff
    if argv is None:
        argv = sys.argv[1:]

    parser = create_parser()
    options = parser.parse_args(argv)
    if not options.command:
        parser.error("Must specify a 'command' to be performed")
    if (options.log_level is not None):
        options.log_level = getattr(logging, options.log_level.upper(),
                                    logger.getEffectiveLevel())
        logger.setLevel(options.log_level)

    config = setup_config_settings(options)
    execute(options, config)


def get_config_file(options):
    # Initialize with the global fallback location for the config.
    conf = '/etc/jenkins_jobs/jenkins_jobs.ini'
    if options.conf:
        conf = options.conf
    else:
        # Allow a script directory config to override.
        localconf = os.path.join(os.path.dirname(__file__),
                                 'jenkins_jobs.ini')
        if os.path.isfile(localconf):
            conf = localconf
        # Allow a user directory config to override.
        userconf = os.path.join(os.path.expanduser('~'), '.config',
                                'jenkins_jobs', 'jenkins_jobs.ini')
        if os.path.isfile(userconf):
            conf = userconf
    return conf


def setup_config_settings(options):

    conf = get_config_file(options)
    config = configparser.ConfigParser()
    # Load default config always
    config.readfp(StringIO(DEFAULT_CONF))
    if os.path.isfile(conf):
        options.conf = conf  # remember file we read from
        logger.debug("Reading config from {0}".format(conf))
        conffp = io.open(conf, 'r', encoding='utf-8')
        config.readfp(conffp)
    elif options.command == 'test':
        logger.debug("Not requiring config for test output generation")
    else:
        raise JenkinsJobsException(
            "A valid configuration file is required when not run as a test"
            "\n{0} is not a valid .ini file".format(conf))

    return config


def execute(options, config):
    logger.debug("Config: {0}".format(config))

    # check the ignore_cache setting: first from command line,
    # if not present check from ini file
    ignore_cache = False
    if options.ignore_cache:
        ignore_cache = options.ignore_cache
    elif config.has_option('jenkins', 'ignore_cache'):
        logging.warn('ignore_cache option should be moved to the [job_builder]'
                     ' section in the config file, the one specified in the '
                     '[jenkins] section will be ignored in the future')
        ignore_cache = config.getboolean('jenkins', 'ignore_cache')
    elif config.has_option('job_builder', 'ignore_cache'):
        ignore_cache = config.getboolean('job_builder', 'ignore_cache')

    # Jenkins supports access as an anonymous user, which can be used to
    # ensure read-only behaviour when querying the version of plugins
    # installed for test mode to generate XML output matching what will be
    # uploaded. To enable must pass 'None' as the value for user and password
    # to python-jenkins
    #
    # catching 'TypeError' is a workaround for python 2.6 interpolation error
    # https://bugs.launchpad.net/openstack-ci/+bug/1259631
    if options.user:
        user = options.user
    else:
        try:
            user = config.get('jenkins', 'user')
        except (TypeError, configparser.NoOptionError):
            user = None

    if options.password:
        password = options.password
    else:
        try:
            password = config.get('jenkins', 'password')
        except (TypeError, configparser.NoOptionError):
            password = None

    # Inform the user as to what is likely to happen, as they may specify
    # a real jenkins instance in test mode to get the plugin info to check
    # the XML generated.
    if user is None and password is None:
        logger.info("Will use anonymous access to Jenkins if needed.")
    elif (user is not None and password is None) or (
            user is None and password is not None):
        raise JenkinsJobsException(
            "Cannot authenticate to Jenkins with only one of User and "
            "Password provided, please check your configuration."
        )

    # None -- no timeout, blocking mode; same as setblocking(True)
    # 0.0 -- non-blocking mode; same as setblocking(False) <--- default
    # > 0 -- timeout mode; operations time out after timeout seconds
    # < 0 -- illegal; raises an exception
    # to retain the default must use
    # "timeout=jenkins_jobs.builder._DEFAULT_TIMEOUT" or not set timeout at
    # all.
    timeout = jenkins_jobs.builder._DEFAULT_TIMEOUT
    try:
        timeout = config.getfloat('jenkins', 'timeout')
    except (ValueError):
        raise JenkinsJobsException("Jenkins timeout config is invalid")
    except (TypeError, configparser.NoOptionError):
        pass

    plugins_info = None

    if getattr(options, 'plugins_info_path', None) is not None:
        with io.open(options.plugins_info_path, 'r',
                     encoding='utf-8') as yaml_file:
            plugins_info = yaml.load(yaml_file)
        if not isinstance(plugins_info, list):
            raise JenkinsJobsException("{0} must contain a Yaml list!"
                                       .format(options.plugins_info_path))
    elif (not options.conf or not
          config.getboolean("jenkins", "query_plugins_info")):
        logger.debug("Skipping plugin info retrieval")
        plugins_info = {}

    if options.allow_empty_variables is not None:
        config.set('job_builder',
                   'allow_empty_variables',
                   str(options.allow_empty_variables))

    builder = Builder(config.get('jenkins', 'url'),
                      user,
                      password,
                      config,
                      jenkins_timeout=timeout,
                      ignore_cache=ignore_cache,
                      flush_cache=options.flush_cache,
                      plugins_list=plugins_info)

    if getattr(options, 'path', None):
        if hasattr(options.path, 'read'):
            logger.debug("Input file is stdin")
            if options.path.isatty():
                key = 'CTRL+Z' if platform.system() == 'Windows' else 'CTRL+D'
                logger.warn(
                    "Reading configuration from STDIN. Press %s to end input.",
                    key)
        else:
            # take list of paths
            options.path = options.path.split(os.pathsep)

            do_recurse = (getattr(options, 'recursive', False) or
                          config.getboolean('job_builder', 'recursive'))

            excludes = [e for elist in options.exclude
                        for e in elist.split(os.pathsep)] or \
                config.get('job_builder', 'exclude').split(os.pathsep)
            paths = []
            for path in options.path:
                if do_recurse and os.path.isdir(path):
                    paths.extend(recurse_path(path, excludes))
                else:
                    paths.append(path)
            options.path = paths

    if options.command == 'delete':
        for job in options.name:
            builder.delete_job(job, options.path)
    elif options.command == 'delete-all':
        confirm('Sure you want to delete *ALL* jobs from Jenkins server?\n'
                '(including those not managed by Jenkins Job Builder)')
        logger.info("Deleting all jobs")
        builder.delete_all_jobs()
    elif options.command == 'update':
        if options.n_workers < 0:
            raise JenkinsJobsException(
                'Number of workers must be equal or greater than 0')

        logger.info("Updating jobs in {0} ({1})".format(
            options.path, options.names))
        jobs, num_updated_jobs = builder.update_jobs(
            options.path, options.names,
            n_workers=options.n_workers)
        logger.info("Number of jobs updated: %d", num_updated_jobs)
        if options.delete_old:
            num_deleted_jobs = builder.delete_old_managed()
            logger.info("Number of jobs deleted: %d", num_deleted_jobs)
    elif options.command == 'test':
        builder.update_jobs(options.path, options.name,
                            output=options.output_dir,
                            n_workers=1)


def version():
    return "Jenkins Job Builder version: %s" % \
        jenkins_jobs.version.version_info.version_string()


if __name__ == '__main__':
    sys.path.insert(0, '.')
    main()
