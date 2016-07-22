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

import logging
import sys

from jenkins_jobs import cmd
from jenkins_jobs import version
from jenkins_jobs.cli.parser import create_parser
from jenkins_jobs.config import JJBConfig

logging.basicConfig(level=logging.INFO)


def __version__():
    return "Jenkins Job Builder version: %s" % \
        version.version_info.version_string()


class JenkinsJobs(object):
    """ This is the entry point class for the `jenkins-jobs` command line tool.
    While this class can be used programmatically by external users of the JJB
    API, the main goal here is to abstract the `jenkins_jobs` tool in a way
    that prevents test suites from caring overly much about various
    implementation details--for example, tests of subcommands must not have
    access to directly modify configuration objects, instead they must provide
    a fixture in the form of an .ini file that provides the configuration
    necessary for testing.

    External users of the JJB API may be interested in this class as an
    alternative to wrapping `jenkins_jobs` with a subprocess that execs it as a
    system command; instead, python scripts may be written that pass
    `jenkins_jobs` args directly to this class to allow programmatic setting of
    various command line parameters.
    """

    def __init__(self, args=None, **kwargs):
        if args is None:
            args = []
        parser = create_parser()
        options = parser.parse_args(args)

        self.jjb_config = JJBConfig(arguments=options, **kwargs)
        self.jjb_config.do_magical_things()

        if not options.command:
            parser.error("Must specify a 'command' to be performed")

        logger = logging.getLogger()
        if (options.log_level is not None):
            options.log_level = getattr(logging,
                                        options.log_level.upper(),
                                        logger.getEffectiveLevel())
            logger.setLevel(options.log_level)

    def execute(self):
        cmd.execute(self.jjb_config)


def main():
    argv = sys.argv[1:]
    jjb = JenkinsJobs(argv)
    jjb.execute()
