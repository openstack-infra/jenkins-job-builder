# Joint copyright:
#  - Copyright 2014 Hewlett-Packard Development Company, L.P.
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

from testtools import TestCase, ExpectedException
from testscenarios.testcase import TestWithScenarios

from jenkins_jobs.errors import JenkinsJobsException
from tests.base import SingleJobTestCase
from tests.base import get_scenarios
from tests.base import mock


class TestCaseModuleDuplicates(TestWithScenarios, TestCase,
                               SingleJobTestCase):
    fixtures_path = os.path.join(os.path.dirname(__file__), 'fixtures')
    scenarios = get_scenarios(fixtures_path)

    @mock.patch('jenkins_jobs.builder.logger', autospec=True)
    def test_yaml_snippet(self, mock_logger):

        if os.path.basename(self.in_filename).startswith("exception_"):
            with ExpectedException(JenkinsJobsException, "^Duplicate .*"):
                super(TestCaseModuleDuplicates, self).test_yaml_snippet()
        else:
            super(TestCaseModuleDuplicates, self).test_yaml_snippet()
