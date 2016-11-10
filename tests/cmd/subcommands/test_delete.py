# Joint copyright:
#  - Copyright 2015 Hewlett-Packard Development Company, L.P.
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

# The goal of these tests is to check that given a particular set of flags to
# Jenkins Job Builder's command line tools it will result in a particular set
# of actions by the JJB library, usually through interaction with the
# python-jenkins library.

import os

from tests.base import mock
from tests.cmd.test_cmd import CmdTestsBase


@mock.patch('jenkins_jobs.builder.JenkinsManager.get_plugins_info',
            mock.MagicMock)
class DeleteTests(CmdTestsBase):

    @mock.patch('jenkins_jobs.cli.subcommand.update.'
                'JenkinsManager.delete_jobs')
    @mock.patch('jenkins_jobs.cli.subcommand.update.'
                'JenkinsManager.delete_views')
    def test_delete_single_job(self, delete_job_mock, delete_view_mock):
        """
        Test handling the deletion of a single Jenkins job.
        """

        args = ['--conf', self.default_config_file, 'delete', 'test_job']
        self.execute_jenkins_jobs_with_args(args)

    @mock.patch('jenkins_jobs.cli.subcommand.update.'
                'JenkinsManager.delete_jobs')
    @mock.patch('jenkins_jobs.cli.subcommand.update.'
                'JenkinsManager.delete_views')
    def test_delete_multiple_jobs(self, delete_job_mock, delete_view_mock):
        """
        Test handling the deletion of multiple Jenkins jobs.
        """

        args = ['--conf', self.default_config_file,
                'delete', 'test_job1', 'test_job2']
        self.execute_jenkins_jobs_with_args(args)

    @mock.patch('jenkins_jobs.builder.JenkinsManager.delete_job')
    def test_delete_using_glob_params(self, delete_job_mock):
        """
        Test handling the deletion of multiple Jenkins jobs using the glob
        parameters feature.
        """

        args = ['--conf', self.default_config_file,
                'delete', '--path',
                os.path.join(self.fixtures_path,
                             'cmd-002.yaml'),
                '*bar*']
        self.execute_jenkins_jobs_with_args(args)
        calls = [mock.call('bar001'), mock.call('bar002')]
        delete_job_mock.assert_has_calls(calls, any_order=True)
        self.assertEqual(delete_job_mock.call_count, len(calls),
                         "Jenkins.delete_job() was called '%s' times when "
                         "expected '%s'" % (delete_job_mock.call_count,
                                            len(calls)))
