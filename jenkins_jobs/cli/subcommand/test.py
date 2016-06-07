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

import jenkins_jobs.cli.subcommand.update as update


logger = logging.getLogger(__name__)


class TestSubCommand(update.UpdateSubCommand):

    def parse_args(self, subparser):
        test = subparser.add_parser('test')

        self.parse_option_recursive_exclude(test)

        self.parse_arg_path(test)
        self.parse_arg_names(test)

        test.add_argument(
            '--config-xml',
            action='store_true',
            dest='config_xml',
            default=False,
            help='use alternative output file layout using config.xml files')
        test.add_argument(
            '-p', '--plugin-info',
            dest='plugins_info_path',
            default=None,
            help='path to plugin info YAML file')
        test.add_argument(
            '-o',
            dest='output_dir',
            default=sys.stdout,
            help='path to output XML')

    def execute(self, options, jjb_config):

        builder, xml_jobs, xml_views = self._generate_xmljobs(
            options, jjb_config)

        builder.update_jobs(xml_jobs, output=options.output_dir, n_workers=1,
                            config_xml=options.config_xml)
        builder.update_views(xml_views, output=options.output_dir, n_workers=1,
                             config_xml=options.config_xml)
