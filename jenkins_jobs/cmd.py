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

import logging
import sys

from six.moves import input

from jenkins_jobs.builder import Builder
from jenkins_jobs.errors import JenkinsJobsException


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

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

[__future__]
param_order_from_yaml=False
"""


def confirm(question):
    answer = input('%s (Y/N): ' % question).upper().strip()
    if not answer == 'Y':
        sys.exit('Aborted')


def execute(jjb_config):
    config = jjb_config.config_parser
    options = jjb_config.arguments

    builder = Builder(config.get('jenkins', 'url'),
                      jjb_config.user,
                      jjb_config.password,
                      jjb_config.config_parser,
                      jenkins_timeout=jjb_config.timeout,
                      ignore_cache=jjb_config.ignore_cache,
                      flush_cache=options.flush_cache,
                      plugins_list=jjb_config.plugins_info)

    if options.command == 'delete':
        for job in options.name:
            builder.delete_job(job, options.path)
    elif options.command == 'delete-all':
        confirm('Sure you want to delete *ALL* jobs from Jenkins server?\n'
                '(including those not managed by Jenkins Job Builder)')
        logger.info("Deleting all jobs")
        builder.delete_all_jobs()
    elif options.command == 'update':
        if options.n_workers < 0:
            raise JenkinsJobsException(
                'Number of workers must be equal or greater than 0')

        logger.info("Updating jobs in {0} ({1})".format(
            options.path, options.names))
        jobs, num_updated_jobs = builder.update_jobs(
            options.path, options.names,
            n_workers=options.n_workers)
        logger.info("Number of jobs updated: %d", num_updated_jobs)
        if options.delete_old:
            num_deleted_jobs = builder.delete_old_managed()
            logger.info("Number of jobs deleted: %d", num_deleted_jobs)
    elif options.command == 'test':
        builder.update_jobs(options.path, options.name,
                            output=options.output_dir,
                            n_workers=1)
