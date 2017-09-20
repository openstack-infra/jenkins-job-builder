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
from jenkins_jobs.errors import JenkinsJobsException
import jenkins_jobs.cli.subcommand.base as base


logger = logging.getLogger(__name__)


class DeleteAllSubCommand(base.BaseSubCommand):

    def parse_args(self, subparser):
        delete_all = subparser.add_parser(
            'delete-all',
            help="delete *ALL* jobs from Jenkins server, including "
            "those not managed by Jenkins Job Builder.")

        self.parse_option_recursive_exclude(delete_all)

        delete_all.add_argument(
            '-j', '--jobs-only',
            action='store_true', dest='del_jobs',
            default=False,
            help='delete only jobs'
        )
        delete_all.add_argument(
            '-v', '--views-only',
            action='store_true', dest='del_views',
            default=False,
            help='delete only views'
        )

    def execute(self, options, jjb_config):
        builder = JenkinsManager(jjb_config)

        reach = set()
        if options.del_jobs and options.del_views:
            raise JenkinsJobsException(
                '"--views-only" and "--jobs-only" cannot be used together.')
        elif options.del_jobs and not options.del_views:
            reach.add('jobs')
        elif options.del_views and not options.del_jobs:
            reach.add('views')
        else:
            reach.update(('jobs', 'views'))

        if not utils.confirm(
                'Sure you want to delete *ALL* {} from Jenkins '
                'server?\n(including those not managed by Jenkins '
                'Job Builder)'.format(" AND ".join(reach))):
            sys.exit('Aborted')

        if 'jobs' in reach:
            logger.info("Deleting all jobs")
            builder.delete_all_jobs()

        if 'views' in reach:
            logger.info("Deleting all views")
            builder.delete_all_views()
