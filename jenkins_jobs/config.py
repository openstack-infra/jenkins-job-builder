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

from collections import defaultdict
import io
import logging
import os

from six.moves import configparser, StringIO
from six import PY2

from jenkins_jobs import builder
from jenkins_jobs.errors import JJBConfigException
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
retain_anchors=False

# other named sections could be used in addition to the implicit [jenkins]
# if you have multiple jenkins servers.
[jenkins]
url=http://localhost:8080/
query_plugins_info=False
"""

CONFIG_REQUIRED_MESSAGE = ("A valid configuration file is required. "
                           "No configuration file passed.")
DEPRECATED_PLUGIN_CONFIG_SECTION_MESSAGE = (
    "Defining plugin configuration using a [{plugin}] section in your config"
    " file is deprecated. The recommended way to define plugins now is by"
    " using a [plugin \"{plugin}\"] section"
)
_NOTSET = object()


class JJBConfig(object):

    def __init__(self, config_filename=None,
                 config_file_required=False,
                 config_section='jenkins'):

        """
        The JJBConfig class is intended to encapsulate and resolve priority
        between all sources of configuration for the JJB library. This allows
        the various sources of configuration to provide a consistent accessor
        interface regardless of where they are used.

        It also allows users of JJB-as-an-API to create minimally valid
        configuration and easily make minor modifications to default values
        without strictly adhering to the confusing setup (see the _setup
        method, the behavior of which largely lived in the cmd.execute method
        previously) necessary for the jenkins-jobs command line tool.

        :arg str config_filename: Name of configuration file on which to base
            this config object.
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

        global_conf = '/etc/jenkins_jobs/jenkins_jobs.ini'
        user_conf = os.path.join(os.path.expanduser('~'), '.config',
                                 'jenkins_jobs', 'jenkins_jobs.ini')
        local_conf = os.path.join(os.path.dirname(__file__),
                                  'jenkins_jobs.ini')
        conf = None
        if config_filename is not None:
            conf = config_filename
        else:
            if os.path.isfile(local_conf):
                conf = local_conf
            elif os.path.isfile(user_conf):
                conf = user_conf
            else:
                conf = global_conf

        if config_file_required and conf is None:
            raise JJBConfigException(CONFIG_REQUIRED_MESSAGE)

        config_fp = None
        if conf is not None:
            try:
                config_fp = self._read_config_file(conf)
            except JJBConfigException:
                if config_file_required:
                    raise JJBConfigException(CONFIG_REQUIRED_MESSAGE)
                else:
                    logger.warning("Config file, {0}, not found. Using "
                                   "default config values.".format(conf))

        if config_fp is not None:
            if PY2:
                config_parser.readfp(config_fp)
            else:
                config_parser.read_file(config_fp)

        self.config_parser = config_parser

        self._section = config_section
        self.print_job_urls = False

        self.jenkins = defaultdict(None)
        self.builder = defaultdict(None)
        self.yamlparser = defaultdict(None)

        self._setup()
        self._handle_deprecated_hipchat_config()

    def _init_defaults(self):
        """ Initialize default configuration values using DEFAULT_CONF
        """
        config = configparser.ConfigParser()
        # Load default config always
        if PY2:
            config.readfp(StringIO(DEFAULT_CONF))
        else:
            config.read_file(StringIO(DEFAULT_CONF))
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
            raise JJBConfigException(
                "A valid configuration file is required. "
                "\n{0} is not valid.".format(config_filename))

        return config_fp

    def _handle_deprecated_hipchat_config(self):
        config = self.config_parser

        if config.has_section('hipchat'):
            if config.has_section('plugin "hipchat"'):
                logger.warning(
                    "Both [hipchat] and [plugin \"hipchat\"] sections "
                    "defined, legacy [hipchat] section will be ignored."
                )
            else:
                logger.warning(
                    "[hipchat] section is deprecated and should be moved to a "
                    "[plugins \"hipchat\"] section instead as the [hipchat] "
                    "section will be ignored in the future."
                )
                config.add_section('plugin "hipchat"')
                for option in config.options("hipchat"):
                    config.set('plugin "hipchat"', option,
                               config.get("hipchat", option))

                config.remove_section("hipchat")

        # remove need to reference jenkins section when using hipchat plugin
        # moving to backports configparser would allow use of extended
        # interpolation to remove the need for plugins to need information
        # directly from the jenkins section within code and allow variables
        # in the config file to refer instead.
        if (config.has_section('plugin "hipchat"') and
                not config.has_option('plugin "hipchat"', 'url')):
            config.set('plugin "hipchat"', "url", config.get('jenkins', 'url'))

    def _setup(self):
        config = self.config_parser

        logger.debug("Config: {0}".format(config))

        # check the ignore_cache setting
        ignore_cache = False
        if config.has_option(self._section, 'ignore_cache'):
            logger.warning("ignore_cache option should be moved to the "
                           "[job_builder] section in the config file, the "
                           "one specified in the [jenkins] section will be "
                           "ignored in the future")
            ignore_cache = config.getboolean(self._section, 'ignore_cache')
        elif config.has_option('job_builder', 'ignore_cache'):
            ignore_cache = config.getboolean('job_builder', 'ignore_cache')
        self.builder['ignore_cache'] = ignore_cache

        # check the flush_cache setting
        flush_cache = False
        if config.has_option('job_builder', 'flush_cache'):
            flush_cache = config.getboolean('job_builder', 'flush_cache')
        self.builder['flush_cache'] = flush_cache

        # check the print_job_urls setting
        if config.has_option('job_builder', 'print_job_urls'):
            self.print_job_urls = config.getboolean('job_builder',
                                                    'print_job_urls')

        # Jenkins supports access as an anonymous user, which can be used to
        # ensure read-only behaviour when querying the version of plugins
        # installed for test mode to generate XML output matching what will be
        # uploaded. To enable must pass 'None' as the value for user and
        # password to python-jenkins
        #
        # catching 'TypeError' is a workaround for python 2.6 interpolation
        # error
        # https://bugs.launchpad.net/openstack-ci/+bug/1259631

        try:
            user = config.get(self._section, 'user')
        except (TypeError, configparser.NoOptionError):
            user = None
        self.jenkins['user'] = user

        try:
            password = config.get(self._section, 'password')
        except (TypeError, configparser.NoOptionError):
            password = None
        self.jenkins['password'] = password

        # None -- no timeout, blocking mode; same as setblocking(True)
        # 0.0 -- non-blocking mode; same as setblocking(False) <--- default
        # > 0 -- timeout mode; operations time out after timeout seconds
        # < 0 -- illegal; raises an exception
        # to retain the default must use
        # "timeout=jenkins_jobs.builder._DEFAULT_TIMEOUT" or not set timeout at
        # all.
        try:
            timeout = config.getfloat(self._section, 'timeout')
        except (ValueError):
            raise JenkinsJobsException("Jenkins timeout config is invalid")
        except (TypeError, configparser.NoOptionError):
            timeout = builder._DEFAULT_TIMEOUT
        self.jenkins['timeout'] = timeout

        plugins_info = None
        if (config.has_option(self._section, 'query_plugins_info') and
           not config.getboolean(self._section, "query_plugins_info")):
                logger.debug("Skipping plugin info retrieval")
                plugins_info = []
        self.builder['plugins_info'] = plugins_info

        self.recursive = config.getboolean('job_builder', 'recursive')
        self.excludes = config.get('job_builder', 'exclude').split(os.pathsep)

        # The way we want to do things moving forward:
        self.jenkins['url'] = config.get(self._section, 'url')
        self.builder['print_job_urls'] = self.print_job_urls

        # keep descriptions ? (used by yamlparser)
        keep_desc = False
        if (config and config.has_section('job_builder') and
                config.has_option('job_builder', 'keep_descriptions')):
            keep_desc = config.getboolean('job_builder',
                                          'keep_descriptions')
        self.yamlparser['keep_descriptions'] = keep_desc

        # figure out the include path (used by yamlparser)
        path = ["."]
        if (config and config.has_section('job_builder') and
                config.has_option('job_builder', 'include_path')):
            path = config.get('job_builder',
                              'include_path').split(':')
        self.yamlparser['include_path'] = path

        # allow duplicates?
        allow_duplicates = False
        if config and config.has_option('job_builder', 'allow_duplicates'):
            allow_duplicates = config.getboolean('job_builder',
                                                 'allow_duplicates')
        self.yamlparser['allow_duplicates'] = allow_duplicates

        # allow empty variables?
        self.yamlparser['allow_empty_variables'] = (
            config and config.has_section('job_builder') and
            config.has_option('job_builder', 'allow_empty_variables') and
            config.getboolean('job_builder', 'allow_empty_variables'))

        # retain anchors across files?
        retain_anchors = False
        if config and config.has_option('job_builder', 'retain_anchors'):
            retain_anchors = config.getboolean('job_builder',
                                               'retain_anchors')
        self.yamlparser['retain_anchors'] = retain_anchors

        update = None
        if (config and config.has_section('job_builder') and
                config.has_option('job_builder', 'update')):
            update = config.get('job_builder', 'update')
        self.builder['update'] = update

    def validate(self):
        # Inform the user as to what is likely to happen, as they may specify
        # a real jenkins instance in test mode to get the plugin info to check
        # the XML generated.
        if self.jenkins['user'] is None and self.jenkins['password'] is None:
            logger.info("Will use anonymous access to Jenkins if needed.")
        elif ((self.jenkins['user'] is not None and
               self.jenkins['password'] is None) or
              (self.jenkins['user'] is None and
               self.jenkins['password'] is not None)):
            raise JenkinsJobsException(
                "Cannot authenticate to Jenkins with only one of User and "
                "Password provided, please check your configuration."
            )

        if (self.builder['plugins_info'] is not None and
                not isinstance(self.builder['plugins_info'], list)):
            raise JenkinsJobsException("plugins_info must contain a list!")

    def get_module_config(self, section, key, default=None):
        """ Given a section name and a key value, return the value assigned to
        the key in the JJB .ini file if it exists, otherwise emit a warning
        indicating that the value is not set. Default value returned if no
        value is set in the file will be a blank string.
        """
        result = default
        try:
            result = self.config_parser.get(
                section, key
            )
        except (configparser.NoSectionError, configparser.NoOptionError,
                JenkinsJobsException) as e:
            # use of default ignores missing sections/options
            if result is None:
                logger.warning(
                    "You didn't set a %s neither in the yaml job definition "
                    "nor in the %s section, blank default value will be "
                    "applied:\n%s", key, section, e)
        return result

    def get_plugin_config(self, plugin, key, default=None):
        value = self.get_module_config('plugin "{}"'.format(plugin), key,
                                       default)

        # Backwards compatibility for users who have not switched to the new
        # plugin configuration format in their config. This code should be
        # removed in future versions of JJB after 2.0.
        if value is default:
            old_value = self.get_module_config(plugin, key, _NOTSET)
            # only log warning if detected a plugin config setting.
            if old_value is not _NOTSET:
                value = old_value
                logger.warning(
                    DEPRECATED_PLUGIN_CONFIG_SECTION_MESSAGE.format(
                        plugin=plugin))
        return value
