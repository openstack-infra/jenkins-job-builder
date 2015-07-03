
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

import os

from jenkins_jobs import cmd
from jenkins_jobs import builder
from tests.base import mock
from tests.cmd.test_cmd import CmdTestsBase


@mock.patch('jenkins_jobs.builder.Jenkins.get_plugins_info', mock.MagicMock)
class UpdateTests(CmdTestsBase):

    @mock.patch('jenkins_jobs.cmd.Builder.update_job')
    def test_update_jobs(self, update_job_mock):
        """
        Test update_job is called
        """
        # don't care about the value returned here
        update_job_mock.return_value = ([], 0)

        path = os.path.join(self.fixtures_path, 'cmd-002.yaml')
        args = self.parser.parse_args(['update', path])

        cmd.execute(args, self.config)
        update_job_mock.assert_called_with([path], [])

    @mock.patch('jenkins_jobs.builder.Jenkins.is_job', return_value=True)
    @mock.patch('jenkins_jobs.builder.Jenkins.get_jobs')
    @mock.patch('jenkins_jobs.builder.Builder.delete_job')
    @mock.patch('jenkins_jobs.cmd.Builder')
    def test_update_jobs_and_delete_old(self, builder_mock, delete_job_mock,
                                        get_jobs_mock, is_job_mock):
        """
        Test update behaviour with --delete-old option

        Test update of jobs with the --delete-old option enabled, where only
        some jobs result in has_changed() to limit the number of times
        update_job is called, and have the get_jobs() method return additional
        jobs not in the input yaml to test that the code in cmd will call
        delete_job() after update_job() when '--delete-old' is set but only
        for the extra jobs.
        """
        # set up some test data
        jobs = ['old_job001', 'old_job002']
        extra_jobs = [{'name': name} for name in jobs]

        builder_obj = builder.Builder('http://jenkins.example.com',
                                      'doesnot', 'matter',
                                      plugins_list={})

        # get the instance created by mock and redirect some of the method
        # mocks to call real methods on a the above test object.
        b_inst = builder_mock.return_value
        b_inst.plugins_list = builder_obj.plugins_list
        b_inst.update_job.side_effect = builder_obj.update_job
        b_inst.delete_old_managed.side_effect = builder_obj.delete_old_managed

        def _get_jobs():
            return builder_obj.parser.jobs + extra_jobs
        get_jobs_mock.side_effect = _get_jobs

        # override cache to ensure Jenkins.update_job called a limited number
        # of times
        self.cache_mock.return_value.has_changed.side_effect = (
            [True] * 2 + [False] * 2)

        path = os.path.join(self.fixtures_path, 'cmd-002.yaml')
        args = self.parser.parse_args(['update', '--delete-old', path])

        with mock.patch('jenkins_jobs.builder.Jenkins.update_job') as update:
            with mock.patch('jenkins_jobs.builder.Jenkins.is_managed',
                            return_value=True):
                cmd.execute(args, self.config)
            self.assertEquals(2, update.call_count,
                              "Expected Jenkins.update_job to be called '%d' "
                              "times, got '%d' calls instead.\n"
                              "Called with: %s" % (2, update.call_count,
                                                   update.mock_calls))

        calls = [mock.call(name) for name in jobs]
        self.assertEquals(2, delete_job_mock.call_count,
                          "Expected Jenkins.delete_job to be called '%d' "
                          "times got '%d' calls instead.\n"
                          "Called with: %s" % (2, delete_job_mock.call_count,
                                               delete_job_mock.mock_calls))
        delete_job_mock.assert_has_calls(calls, any_order=True)
