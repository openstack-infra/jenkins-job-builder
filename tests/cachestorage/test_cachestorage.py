#
#  - Copyright (c) 2014 Hewlett-Packard Development Company, L.P.
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

import jenkins_jobs
from tests import base
from tests.base import mock


class TestCaseJobCache(base.BaseTestCase):

    @mock.patch('jenkins_jobs.builder.JobCache.get_cache_dir',
                lambda x: '/bad/file')
    def test_save_on_exit(self):
        """
        Test that the cache is saved on normal object deletion
        """

        with mock.patch('jenkins_jobs.builder.JobCache.save') as save_mock:
            with mock.patch('os.path.isfile', return_value=False):
                with mock.patch('jenkins_jobs.builder.JobCache._lock'):
                    jenkins_jobs.builder.JobCache("dummy")
            save_mock.assert_called_with()

    @mock.patch('jenkins_jobs.builder.JobCache.get_cache_dir',
                lambda x: '/bad/file')
    def test_cache_file(self):
        """
        Test providing a cachefile.
        """
        test_file = os.path.abspath(__file__)
        with mock.patch('os.path.join', return_value=test_file):
            with mock.patch('yaml.load'):
                with mock.patch('jenkins_jobs.builder.JobCache._lock'):
                    jenkins_jobs.builder.JobCache("dummy").data = None
