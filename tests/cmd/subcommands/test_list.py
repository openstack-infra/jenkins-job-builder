#!/usr/bin/env python
# Copyright (C) 2018 Sorin Sbarnea
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
import io
import os

from testscenarios.testcase import TestWithScenarios

from tests.base import mock
from tests.cmd.test_cmd import CmdTestsBase


@mock.patch('jenkins_jobs.builder.JenkinsManager.get_plugins_info',
            mock.MagicMock)
class ListFromJenkinsTests(TestWithScenarios, CmdTestsBase):

    scenarios = [
        ('single',
            dict(jobs=['job1'], globs=[], found=['job1'])),
        ('multiple',
            dict(jobs=['job1', 'job2'], globs=[], found=['job1', 'job2'])),
        ('multiple_with_glob',
            dict(jobs=['job1', 'job2', 'job3'], globs=["job[1-2]"],
                 found=['job1', 'job2'])),
        ('multiple_with_multi_glob',
            dict(jobs=['job1', 'job2', 'job3', 'job4'],
                 globs=["job1", "job[24]"],
                 found=['job1', 'job2', 'job4'])),
    ]

    @mock.patch('jenkins_jobs.builder.JenkinsManager.get_jobs')
    def test_list(self, get_jobs_mock):

        def _get_jobs():
            return [{'name': name} for name in self.jobs]

        get_jobs_mock.side_effect = _get_jobs
        console_out = io.BytesIO()

        args = ['--conf', self.default_config_file, 'list'] + self.globs

        with mock.patch('sys.stdout', console_out):
            self.execute_jenkins_jobs_with_args(args)

        self.assertEqual(console_out.getvalue().decode('utf-8').rstrip(),
                         ('\n'.join(self.found)))


@mock.patch('jenkins_jobs.builder.JenkinsManager.get_plugins_info',
            mock.MagicMock)
class ListFromYamlTests(TestWithScenarios, CmdTestsBase):

    scenarios = [
        ('all',
            dict(globs=[], found=['bam001', 'bar001', 'bar002', 'baz001'])),
        ('some',
            dict(globs=["*am*", "*002", "bar001"],
                 found=['bam001', 'bar001', 'bar002'])),
    ]

    def test_list(self):
        path = os.path.join(self.fixtures_path, 'cmd-002.yaml')

        console_out = io.BytesIO()
        with mock.patch('sys.stdout', console_out):
            self.execute_jenkins_jobs_with_args(
                ['--conf',
                 self.default_config_file,
                 'list',
                 '-p',
                 path] + self.globs)

        self.assertEqual(console_out.getvalue().decode('utf-8').rstrip(),
                         ('\n'.join(self.found)))
