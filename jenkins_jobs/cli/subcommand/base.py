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

import abc
import six


@six.add_metaclass(abc.ABCMeta)
class BaseSubCommand(object):
    """Base class for Jenkins Job Builder subcommands, intended to allow
    subcommands to be loaded as stevedore extensions by third party users.
    """
    def __init__(self):
        pass

    @abc.abstractmethod
    def parse_args(self, subparsers, recursive_parser):
        """Define subcommand arguments.

        :param subparsers
          A sub parser object. Implementations of this method should
          create a new subcommand parser by calling
            parser = subparsers.add_parser('command-name', ...)
          This will return a new ArgumentParser object; all other arguments to
          this method will be passed to the argparse.ArgumentParser constructor
          for the returned object.
        """

    @abc.abstractmethod
    def execute(self, config):
        """Execute subcommand behavior.

        :param config
          JJBConfig object containing final configuration from config files,
          command line arguments, and environment variables.
        """

    @staticmethod
    def parse_option_recursive_exclude(parser):
        """Add '--recursive'  and '--exclude' arguments to given parser.
        """
        parser.add_argument(
            '-r', '--recursive',
            action='store_true',
            dest='recursive',
            default=False,
            help="look for yaml files recursively")

        parser.add_argument(
            '-x', '--exclude',
            dest='exclude',
            action='append',
            default=[],
            help="paths to exclude when using recursive search, "
            "uses standard globbing.")
