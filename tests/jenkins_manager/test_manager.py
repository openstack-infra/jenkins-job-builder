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


_plugins_info = {}
_plugins_info['plugin1'] = {'longName': '',
                            'shortName': '',
                            'version': ''}


@mock.patch('jenkins_jobs.builder.JobCache', mock.MagicMock)
class TestCaseTestJenkinsManager(base.BaseTestCase):

    def setUp(self):
        super(TestCaseTestJenkinsManager, self).setUp()
        self.jjb_config = JJBConfig()
        self.jjb_config.validate()

    def test_plugins_list(self):
        self.jjb_config.builder['plugins_info'] = _plugins_info

        self.builder = jenkins_jobs.builder.JenkinsManager(self.jjb_config)
        self.assertEqual(self.builder.plugins_list, _plugins_info)

    @mock.patch.object(jenkins_jobs.builder.jenkins.Jenkins,
                       'get_plugins',
                       return_value=_plugins_info)
    def test_plugins_list_from_jenkins(self, jenkins_mock):
        # Trigger fetching the plugins from jenkins when accessing the property
        self.jjb_config.builder['plugins_info'] = {}
        self.builder = jenkins_jobs.builder.JenkinsManager(self.jjb_config)
        # See https://github.com/formiaczek/multi_key_dict/issues/17
        # self.assertEqual(self.builder.plugins_list, k)
        for key_tuple in self.builder.plugins_list.keys():
            for key in key_tuple:
                self.assertEqual(self.builder.plugins_list[key],
                                 _plugins_info[key])

    def test_delete_managed(self):
        self.jjb_config.builder['plugins_info'] = {}
        self.builder = jenkins_jobs.builder.JenkinsManager(self.jjb_config)

        with mock.patch.multiple('jenkins_jobs.builder.JenkinsManager',
                                 get_jobs=mock.DEFAULT,
                                 is_job=mock.DEFAULT,
                                 is_managed=mock.DEFAULT,
                                 delete_job=mock.DEFAULT) as patches:
            patches['get_jobs'].return_value = [{'fullname': 'job1'},
                                                {'fullname': 'job2'}]
            patches['is_managed'].side_effect = [True, True]
            patches['is_job'].side_effect = [True, True]

            self.builder.delete_old_managed()
            self.assertEqual(patches['delete_job'].call_count, 2)

    def _get_plugins_info_error_test(self, error_string):
        builder = jenkins_jobs.builder.JenkinsManager(self.jjb_config)
        exception = jenkins_jobs.builder.jenkins.JenkinsException(error_string)
        with mock.patch.object(builder.jenkins, 'get_plugins',
                               side_effect=exception):
            plugins_info = builder.get_plugins_info()
        self.assertEqual([_plugins_info['plugin1']], plugins_info)

    def test_get_plugins_info_handles_connectionrefused_errors(self):
        self._get_plugins_info_error_test('Connection refused')

    def test_get_plugins_info_handles_forbidden_errors(self):
        self._get_plugins_info_error_test('Forbidden')
