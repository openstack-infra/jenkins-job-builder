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

from jenkins_jobs import utils
from jenkins_jobs.builder import JenkinsManager
import jenkins_jobs.cli.subcommand.base as base


logger = logging.getLogger(__name__)


class DeleteAllSubCommand(base.BaseSubCommand):

    def parse_args(self, subparser):
        delete_all = subparser.add_parser(
            'delete-all',
            help="delete *ALL* jobs from Jenkins server, including "
            "those not managed by Jenkins Job Builder.")

        self.parse_option_recursive_exclude(delete_all)

    def execute(self, options, jjb_config):
        builder = JenkinsManager(jjb_config)

        if not utils.confirm(
                'Sure you want to delete *ALL* jobs from Jenkins '
                'server?\n(including those not managed by Jenkins '
                'Job Builder)'):
            sys.exit('Aborted')

        logger.info("Deleting all jobs")
        builder.delete_all_jobs()
