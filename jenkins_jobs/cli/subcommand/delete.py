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


from jenkins_jobs.builder import JenkinsManager
from jenkins_jobs.errors import JenkinsJobsException
from jenkins_jobs.parser import YamlParser
from jenkins_jobs.registry import ModuleRegistry
import jenkins_jobs.cli.subcommand.base as base


class DeleteSubCommand(base.BaseSubCommand):

    def parse_args(self, subparser):
        delete = subparser.add_parser('delete')

        self.parse_option_recursive_exclude(delete)

        delete.add_argument(
            'name',
            help='name of job',
            nargs='+')
        delete.add_argument(
            '-p', '--path',
            default=None,
            help="colon-separated list of paths to YAML files "
            "or directories")
        delete.add_argument(
            '-j', '--jobs-only',
            action='store_true', dest='del_jobs',
            default=False,
            help='delete only jobs'
        )
        delete.add_argument(
            '-v', '--views-only',
            action='store_true', dest='del_views',
            default=False,
            help='delete only views'
        )

    def execute(self, options, jjb_config):
        builder = JenkinsManager(jjb_config)

        if options.del_jobs and options.del_views:
            raise JenkinsJobsException(
                '"--views-only" and "--jobs-only" cannot be used together.')

        fn = options.path
        registry = ModuleRegistry(jjb_config, builder.plugins_list)
        parser = YamlParser(jjb_config)

        if fn:
            parser.load_files(fn)
            parser.expandYaml(registry, options.name)
            jobs = [j['name'] for j in parser.jobs]
            views = [v['name'] for v in parser.views]
        else:
            jobs = options.name
            views = options.name

        if options.del_jobs:
            builder.delete_jobs(jobs)
        elif options.del_views:
            builder.delete_views(views)
        else:
            builder.delete_jobs(jobs)
            builder.delete_views(views)
