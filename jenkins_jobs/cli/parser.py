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

import argparse
import os

import jenkins_jobs.version

from stevedore import extension


def __version__():
    return "Jenkins Job Builder version: %s" % \
        jenkins_jobs.version.version_info.version_string()


def create_parser():
    """ Create an ArgumentParser object usable by JenkinsJobs.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--conf',
        dest='conf',
        default=os.environ.get('JJB_CONF', None),
        help="configuration file [JJB_CONF]")
    parser.add_argument(
        '-l',
        '--log_level',
        dest='log_level',
        default=os.environ.get('JJB_LOG_LEVEL', 'info'),
        help="log level (default: %(default)s) [JJB_LOG_LEVEL]")
    parser.add_argument(
        '--ignore-cache',
        action='store_true',
        dest='ignore_cache',
        default=None,
        help="ignore the cache and update the jobs anyhow (that will "
        "only flush the specified jobs cache)")
    parser.add_argument(
        '--flush-cache',
        action='store_true',
        dest='flush_cache',
        default=None,
        help="flush all the cache entries before updating")
    parser.add_argument(
        '--version',
        dest='version',
        action='version',
        version=__version__(),
        help="show version")
    parser.add_argument(
        '--allow-empty-variables',
        action='store_true',
        dest='allow_empty_variables',
        default=None,
        help="Don\'t fail if any of the variables inside any string are "
        "not defined, replace with empty string instead.")
    parser.add_argument(
        '--server', '-s',
        dest='section',
        default=os.environ.get('JJB_SECTION', 'jenkins'),
        help="The Jenkins server ini section to use. Defaults to 'jenkins' "
        "[JJB_SECTION]")
    parser.add_argument(
        '--user', '-u',
        default=os.environ.get('JJB_USER', None),
        help="The Jenkins user to use for authentication. This overrides "
        "the user specified in the configuration file. [JJB_USER]")
    parser.add_argument(
        '--password', '-p',
        default=os.environ.get('JJB_PASSWORD', None),
        help="Password or API token to use for authenticating towards Jenkins."
        " This overrides the password specified in the configuration file."
        " [JJB_PASSWORD]")

    subparser = parser.add_subparsers(
        dest='command',
        help="update, test, list or delete job")

    extension_manager = extension.ExtensionManager(
        namespace='jjb.cli.subcommands',
        invoke_on_load=True,
    )

    def parse_subcommand_args(ext, subparser):
        ext.obj.parse_args(subparser)

    extension_manager.map(parse_subcommand_args, subparser)

    return parser
