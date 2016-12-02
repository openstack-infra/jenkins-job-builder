# vim: set fileencoding=utf-8 :
#
#  - Copyright 2014 Guido Günther <agx@sigxcpu.org>
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

from jenkins_jobs.config import JJBConfig
import jenkins_jobs.builder
from tests import base
from tests.base import mock


@mock.patch('jenkins_jobs.builder.JobCache', mock.MagicMock)
class TestCaseTestJenkinsManager(base.BaseTestCase):
    def setUp(self):
        super(TestCaseTestJenkinsManager, self).setUp()
        self.jjb_config = JJBConfig()
        self.jjb_config.validate()

    def test_plugins_list(self):
        self.jjb_config.builder['plugins_info'] = ['plugin1', 'plugin2']
        self.builder = jenkins_jobs.builder.JenkinsManager(self.jjb_config)
        self.assertEqual(self.builder.plugins_list, ['plugin1', 'plugin2'])

    @mock.patch.object(jenkins_jobs.builder.jenkins.Jenkins,
                       'get_plugins_info', return_value=['p1', 'p2'])
    def test_plugins_list_from_jenkins(self, jenkins_mock):
        # Trigger fetching the plugins from jenkins when accessing the property
        self.jjb_config.builder['plugins_info'] = None
        self.builder = jenkins_jobs.builder.JenkinsManager(self.jjb_config)
        self.assertEqual(self.builder.plugins_list, ['p1', 'p2'])

    def test_delete_managed(self):
        self.jjb_config.builder['plugins_info'] = []
        self.builder = jenkins_jobs.builder.JenkinsManager(self.jjb_config)

        with mock.patch.multiple('jenkins_jobs.builder.JenkinsManager',
                                 get_jobs=mock.DEFAULT,
                                 is_managed=mock.DEFAULT,
                                 delete_job=mock.DEFAULT) as patches:
            patches['get_jobs'].return_value = [{'name': 'job1'},
                                                {'name': 'job2'}]
            patches['is_managed'].side_effect = [True, True]

            self.builder.delete_old_managed()
            self.assertEquals(patches['delete_job'].call_count, 2)
