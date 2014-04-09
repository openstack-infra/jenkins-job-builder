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
import ConfigParser
import logging
import os
import sys


def confirm(question):
    answer = raw_input('%s (Y/N): ' % question).upper().strip()
    if not answer == 'Y':
        sys.exit('Aborted')


def main():
    import jenkins_jobs.builder
    import jenkins_jobs.errors
    parser = argparse.ArgumentParser()
    subparser = parser.add_subparsers(help='update, test or delete job',
                                      dest='command')
    parser_update = subparser.add_parser('update')
    parser_update.add_argument('path', help='path to YAML file or directory')
    parser_update.add_argument('names', help='name(s) of job(s)', nargs='*')
    parser_update.add_argument('--delete-old', help='delete obsolete jobs',
                               action='store_true',
                               dest='delete_old', default=False,)
    parser_test = subparser.add_parser('test')
    parser_test.add_argument('path', help='path to YAML file or directory')
    parser_test.add_argument('-o', dest='output_dir', required=True,
                             help='path to output XML')
    parser_test.add_argument('name', help='name(s) of job(s)', nargs='*')
    parser_delete = subparser.add_parser('delete')
    parser_delete.add_argument('name', help='name of job', nargs='+')
    parser_delete.add_argument('-p', '--path', default=None,
                               help='path to YAML file or directory')
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
    options = parser.parse_args()

    options.log_level = getattr(logging, options.log_level.upper(),
                                logging.INFO)
    logging.basicConfig(level=options.log_level)
    logger = logging.getLogger()

    conf = '/etc/jenkins_jobs/jenkins_jobs.ini'
    if options.conf:
        conf = options.conf
    else:
        # Fallback to script directory
        localconf = os.path.join(os.path.dirname(__file__),
                                 'jenkins_jobs.ini')
        if os.path.isfile(localconf):
            conf = localconf

    config = ConfigParser.ConfigParser()
    if os.path.isfile(conf):
        logger.debug("Reading config from {0}".format(conf))
        conffp = open(conf, 'r')
        config.readfp(conffp)
    elif options.command == 'test':
        ## to avoid the 'no section' and 'no option' errors when testing
        config.add_section("jenkins")
        config.set("jenkins", "url", "http://localhost:8080")
        config.set("jenkins", "user", None)
        config.set("jenkins", "password", None)
        config.set("jenkins", "ignore_cache", False)
        logger.debug("Not reading config for test output generation")
    else:
        raise jenkins_jobs.errors.JenkinsJobsException(
            "A valid configuration file is required when not run as a test"
            "\n{0} is not a valid .ini file".format(conf))

    logger.debug("Config: {0}".format(config))

    # check the ignore_cache setting: first from command line,
    # if not present check from ini file
    ignore_cache = False
    if options.ignore_cache:
        ignore_cache = options.ignore_cache
    elif config.has_option('jenkins', 'ignore_cache'):
        ignore_cache = config.get('jenkins', 'ignore_cache')

    # workaround for python 2.6 interpolation error
    # https://bugs.launchpad.net/openstack-ci/+bug/1259631
    try:
        user = config.get('jenkins', 'user')
    except (TypeError, ConfigParser.NoOptionError):
        user = None
    try:
        password = config.get('jenkins', 'password')
    except (TypeError, ConfigParser.NoOptionError):
        password = None

    builder = jenkins_jobs.builder.Builder(config.get('jenkins', 'url'),
                                           user,
                                           password,
                                           config,
                                           ignore_cache=ignore_cache,
                                           flush_cache=options.flush_cache)

    if options.command == 'delete':
        for job in options.name:
            logger.info("Deleting jobs in [{0}]".format(job))
            builder.delete_job(job, options.path)
    elif options.command == 'delete-all':
        confirm('Sure you want to delete *ALL* jobs from Jenkins server?\n'
                '(including those not managed by Jenkins Job Builder)')
        logger.info("Deleting all jobs")
        builder.delete_all_jobs()
    elif options.command == 'update':
        logger.info("Updating jobs in {0} ({1})".format(
            options.path, options.names))
        jobs = builder.update_job(options.path, options.names)
        if options.delete_old:
            builder.delete_old_managed(keep=[x.name for x in jobs])
    elif options.command == 'test':
        builder.update_job(options.path, options.name,
                           output_dir=options.output_dir)

if __name__ == '__main__':
    sys.path.insert(0, '.')
    main()
