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
import six

from tests.base import mock
from tests.cmd.test_cmd import CmdTestsBase


@mock.patch('jenkins_jobs.builder.JenkinsManager.get_plugins_info',
            mock.MagicMock)
class UpdateTests(CmdTestsBase):

    @mock.patch('jenkins_jobs.builder.jenkins.Jenkins.job_exists')
    @mock.patch('jenkins_jobs.builder.jenkins.Jenkins.get_all_jobs')
    @mock.patch('jenkins_jobs.builder.jenkins.Jenkins.reconfig_job')
    def test_update_jobs(self,
                         jenkins_reconfig_job,
                         jenkins_get_jobs,
                         jenkins_job_exists, ):
        """
        Test update_job is called
        """
        path = os.path.join(self.fixtures_path, 'cmd-002.yaml')
        args = ['--conf', self.default_config_file, 'update', path]

        self.execute_jenkins_jobs_with_args(args)

        jenkins_reconfig_job.assert_has_calls(
            [mock.call(job_name, mock.ANY)
             for job_name in ['bar001', 'bar002', 'baz001', 'bam001']],
            any_order=True
        )

    @mock.patch('jenkins_jobs.builder.JenkinsManager.is_job',
                return_value=True)
    @mock.patch('jenkins_jobs.builder.JenkinsManager.get_jobs')
    @mock.patch('jenkins_jobs.builder.JenkinsManager.get_job_md5')
    @mock.patch('jenkins_jobs.builder.JenkinsManager.update_job')
    def test_update_jobs_decode_job_output(self, update_job_mock,
                                           get_job_md5_mock, get_jobs_mock,
                                           is_job_mock):
        """
        Test that job xml output has been decoded before attempting to update
        """
        # don't care about the value returned here
        update_job_mock.return_value = ([], 0)

        path = os.path.join(self.fixtures_path, 'cmd-002.yaml')
        args = ['--conf', self.default_config_file, 'update', path]

        self.execute_jenkins_jobs_with_args(args)
        self.assertTrue(isinstance(update_job_mock.call_args[0][1],
                                   six.text_type))

    @mock.patch('jenkins_jobs.builder.jenkins.Jenkins.job_exists')
    @mock.patch('jenkins_jobs.builder.jenkins.Jenkins.get_all_jobs')
    @mock.patch('jenkins_jobs.builder.jenkins.Jenkins.reconfig_job')
    @mock.patch('jenkins_jobs.builder.jenkins.Jenkins.delete_job')
    def test_update_jobs_and_delete_old(self,
                                        jenkins_delete_job,
                                        jenkins_reconfig_job,
                                        jenkins_get_all_jobs,
                                        jenkins_job_exists):
        """
        Test update behaviour with --delete-old option

        * mock out a call to jenkins.Jenkins.get_jobs() to return a known list
          of job names.
        * mock out a call to jenkins.Jenkins.reconfig_job() and
          jenkins.Jenkins.delete_job() to detect calls being made to determine
          that JJB does correctly delete the jobs it should delete when passed
          a specific set of inputs.
        * mock out a call to jenkins.Jenkins.job_exists() to always return
          True.
        """
        yaml_jobs = ['bar001', 'bar002', 'baz001', 'bam001']
        extra_jobs = ['old_job001', 'old_job002', 'unmanaged']

        path = os.path.join(self.fixtures_path, 'cmd-002.yaml')
        args = ['--conf', self.default_config_file, 'update', '--delete-old',
                path]

        jenkins_get_all_jobs.return_value = [
            {'fullname': name} for name in yaml_jobs + extra_jobs]

        with mock.patch('jenkins_jobs.builder.JenkinsManager.is_managed',
                        side_effect=(lambda name: name != 'unmanaged')):
            self.execute_jenkins_jobs_with_args(args)

        jenkins_reconfig_job.assert_has_calls(
            [mock.call(job_name, mock.ANY) for job_name in yaml_jobs],
            any_order=True
        )
        calls = [mock.call(name) for name in extra_jobs if name != 'unmanaged']
        jenkins_delete_job.assert_has_calls(calls)
        # to ensure only the calls we expected were made, have to check
        # there were no others, as no API call for assert_has_only_calls
        self.assertEqual(jenkins_delete_job.call_count, len(calls))

    def test_update_timeout_not_set(self):
        """Validate update timeout behavior when timeout not explicitly configured.
        """
        self.skipTest("TODO: Develop actual update timeout test approach.")

    def test_update_timeout_set(self):
        """Validate update timeout behavior when timeout is explicitly configured.
        """
        self.skipTest("TODO: Develop actual update timeout test approach.")
