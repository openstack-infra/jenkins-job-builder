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
import time

from jenkins_jobs.builder import Builder
from jenkins_jobs.parser import YamlParser
import jenkins_jobs.cli.subcommand.base as base


logger = logging.getLogger(__name__)


class TestSubCommand(base.BaseSubCommand):
    def parse_args(self, subparser):
        test = subparser.add_parser('test')

        self.parse_option_recursive_exclude(test)

        test.add_argument(
            'path',
            help='''colon-separated list of paths to YAML files or
            directories''',
            nargs='?',
            default=sys.stdin)
        test.add_argument(
            '-p',
            dest='plugins_info_path',
            default=None,
            help='path to plugin info YAML file')
        test.add_argument(
            '-o',
            dest='output_dir',
            default=sys.stdout,
            help='path to output XML')
        test.add_argument(
            'name',
            help='name(s) of job(s)', nargs='*')

    def execute(self, options, jjb_config):
        builder = Builder(jjb_config)

        logger.info("Updating jobs in {0} ({1})".format(
            options.path, options.name))
        orig = time.time()

        # Generate XML
        parser = YamlParser(jjb_config, builder.plugins_list)
        parser.load_files(options.path)
        parser.expandYaml(options.name)
        parser.generateXML()

        jobs = parser.jobs
        step = time.time()
        logging.debug('%d XML files generated in %ss',
                      len(jobs), str(step - orig))

        builder.update_jobs(parser.xml_jobs, output=options.output_dir,
                            n_workers=1)
