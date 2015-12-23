#!/usr/bin/env python
# Copyright (C) 2015 Wayne Warren
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

# Manage JJB Configuration sources, defaults, and access.

import io
import logging
import platform
import os
import yaml

from six.moves import configparser, StringIO

from jenkins_jobs import builder
from jenkins_jobs import utils
from jenkins_jobs.cli.parser import create_parser
from jenkins_jobs.errors import JenkinsJobsException

__all__ = [
    "JJBConfig"
]

logger = logging.getLogger(__name__)

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
"""


class JJBConfigException(JenkinsJobsException):
    pass


class JJBConfig(object):

    def __init__(self, config_filename=None, arguments=None,
                 config_file_required=False):

        """
        The JJBConfig class is intended to encapsulate and resolve priority
        between all sources of configuration for the JJB library. This allows
        the various sources of configuration to provide a consistent accessor
        interface regardless of where they are used.

        It also allows users of JJB-as-an-API to create minimally valid
        configuration and easily make minor modifications to default values
        without strictly adhering to the confusing setup (see the
        do_magical_things method, the behavior of which largely lived in the
        cmd.execute method previously) necessary for the jenkins-jobs command
        line tool.

        :arg str config_filename: Name of configuration file on which to base
            this config object.
        :arg dict arguments: A argparse.Namespace object as produced by the
            jenkins-jobs argument parser.
        :arg bool config_file_required: Allows users of the JJBConfig class to
            decide whether or not it's really necessary for a config file to be
            passed in when creating an instance. This has two effects on the
            behavior of JJBConfig initialization:
            * It determines whether or not we try "local" and "global" config
              files.
            * It determines whether or not failure to read some config file
              will raise an exception or simply print a warning message
              indicating that no config file was found.
        """

        config_parser = self._init_defaults()

        if arguments is None:
            jenkins_jobs_parser = create_parser()
            arguments = jenkins_jobs_parser.parse_args(['test'])

        global_conf = '/etc/jenkins_jobs/jenkins_jobs.ini'
        user_conf = os.path.join(os.path.expanduser('~'), '.config',
                                 'jenkins_jobs', 'jenkins_jobs.ini')
        local_conf = os.path.join(os.path.dirname(__file__),
                                  'jenkins_jobs.ini')
        conf = None
        if config_filename is not None:
            conf = config_filename

        elif hasattr(arguments, 'conf') and arguments.conf is not None:
            conf = arguments.conf

        elif config_file_required:
            if os.path.isfile(local_conf):
                conf = local_conf
            elif os.path.isfile(user_conf):
                conf = user_conf
            else:
                conf = global_conf

        config_fp = None
        if conf is not None:
            try:
                config_fp = self._read_config_file(conf)
            except JJBConfigException as e:
                if config_file_required:
                    raise e
                else:
                    logger.warn("""Config file, {0}, not found. Using default
                    config values.""".format(conf))

        if config_fp is not None:
            config_parser.readfp(config_fp)

        self.config_parser = config_parser
        self.arguments = arguments

    def _init_defaults(self):
        """ Initialize default configuration values using DEFAULT_CONF
        """
        config = configparser.ConfigParser()
        # Load default config always
        config.readfp(StringIO(DEFAULT_CONF))
        return config

    def _read_config_file(self, config_filename):
        """ Given path to configuration file, read it in as a ConfigParser
        object and return that object.
        """
        if os.path.isfile(config_filename):
            self.__config_file = config_filename  # remember file we read from
            logger.debug("Reading config from {0}".format(config_filename))
            config_fp = io.open(config_filename, 'r', encoding='utf-8')
        else:
            raise JJBConfigException("""A valid configuration file is required.
                \n{0} is not valid.""".format(config_filename))

        return config_fp

    def do_magical_things(self):
        config = self.config_parser
        options = self.arguments

        logger.debug("Config: {0}".format(config))

        # check the ignore_cache setting: first from command line,
        # if not present check from ini file
        self.ignore_cache = False
        if options.ignore_cache:
            self.ignore_cache = options.ignore_cache
        elif config.has_option('jenkins', 'ignore_cache'):
            logging.warn('''ignore_cache option should be moved to the
                          [job_builder] section in the config file, the one
                          specified in the [jenkins] section will be ignored in
                          the future''')
            self.ignore_cache = config.getboolean('jenkins', 'ignore_cache')
        elif config.has_option('job_builder', 'ignore_cache'):
            self.ignore_cache = config.getboolean('job_builder',
                                                  'ignore_cache')

        # Jenkins supports access as an anonymous user, which can be used to
        # ensure read-only behaviour when querying the version of plugins
        # installed for test mode to generate XML output matching what will be
        # uploaded. To enable must pass 'None' as the value for user and
        # password to python-jenkins
        #
        # catching 'TypeError' is a workaround for python 2.6 interpolation
        # error
        # https://bugs.launchpad.net/openstack-ci/+bug/1259631
        if options.user:
            self.user = options.user
        else:
            try:
                self.user = config.get('jenkins', 'user')
            except (TypeError, configparser.NoOptionError):
                self.user = None

        if options.password:
            self.password = options.password
        else:
            try:
                self.password = config.get('jenkins', 'password')
            except (TypeError, configparser.NoOptionError):
                self.password = None

        # Inform the user as to what is likely to happen, as they may specify
        # a real jenkins instance in test mode to get the plugin info to check
        # the XML generated.
        if self.user is None and self.password is None:
            logger.info("Will use anonymous access to Jenkins if needed.")
        elif (self.user is not None and self.password is None) or (
                self.user is None and self.password is not None):
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
        self.timeout = builder._DEFAULT_TIMEOUT
        try:
            self.timeout = config.getfloat('jenkins', 'timeout')
        except (ValueError):
            raise JenkinsJobsException("Jenkins timeout config is invalid")
        except (TypeError, configparser.NoOptionError):
            pass

        self.plugins_info = None

        if getattr(options, 'plugins_info_path', None) is not None:
            with io.open(options.plugins_info_path, 'r',
                         encoding='utf-8') as yaml_file:
                self.plugins_info = yaml.load(yaml_file)
            if not isinstance(self.plugins_info, list):
                raise JenkinsJobsException("{0} must contain a Yaml list!"
                                           .format(options.plugins_info_path))
        elif (not options.conf or not
              config.getboolean("jenkins", "query_plugins_info")):
            logger.debug("Skipping plugin info retrieval")
            self.plugins_info = {}

        if options.allow_empty_variables is not None:
            config.set('job_builder',
                       'allow_empty_variables',
                       str(options.allow_empty_variables))

        if getattr(options, 'path', None):
            if hasattr(options.path, 'read'):
                logger.debug("Input file is stdin")
                if options.path.isatty():
                    if platform.system() == 'Windows':
                        key = 'CTRL+Z'
                    else:
                        key = 'CTRL+D'
                    logger.warn("""Reading configuration from STDIN. Press %s
                    to end input.""", key)
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
                        paths.extend(utils.recurse_path(path, excludes))
                    else:
                        paths.append(path)
                options.path = paths

        self.config_parser = config
        self.arguments = options
