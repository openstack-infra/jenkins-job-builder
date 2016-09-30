#
# Copyright (c) 2016 Kien Ha <kienha9922@gmail.com>
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

from testtools.matchers import Equals
import xml.etree.ElementTree as XML
import yaml

from jenkins_jobs.errors import InvalidAttributeError
from jenkins_jobs.errors import MissingAttributeError
from jenkins_jobs.modules.helpers import convert_mapping_to_xml
from tests import base


class TestCaseTestHelpers(base.BaseTestCase):

    def test_convert_mapping_to_xml(self):
        """
        Tests the test_convert_mapping_to_xml_fail_required function
        """

        # Test default values
        default_root = XML.Element('testdefault')
        default_data = yaml.load("string: hello")
        default_mappings = [('default-string', 'defaultString', 'default')]

        convert_mapping_to_xml(
            default_root,
            default_data,
            default_mappings,
            fail_required=True)
        result = default_root.find('defaultString').text
        self.assertThat(result, Equals('default'))

        # Test user input
        user_input_root = XML.Element('testUserInput')
        user_input_data = yaml.load("user-input-string: hello")
        user_input_mappings = [('user-input-string', 'userInputString',
                                'user-input')]

        convert_mapping_to_xml(
            user_input_root,
            user_input_data,
            user_input_mappings,
            fail_required=True)
        result = user_input_root.find('userInputString').text
        self.assertThat(result, Equals('hello'))

        # Test missing required input
        required_root = XML.Element('testrequired')
        required_data = yaml.load("string: hello")
        required_mappings = [('required-string', 'requiredString', None)]

        self.assertRaises(MissingAttributeError,
                          convert_mapping_to_xml,
                          required_root,
                          required_data,
                          required_mappings,
                          fail_required=True)

        # Test invalid user input for list
        user_input_root = XML.Element('testUserInput')
        user_input_data = yaml.load("user-input-string: bye")
        valid_inputs = ['hello']
        user_input_mappings = [('user-input-string', 'userInputString',
                                'user-input', valid_inputs)]

        self.assertRaises(InvalidAttributeError,
                          convert_mapping_to_xml,
                          user_input_root,
                          user_input_data,
                          user_input_mappings)

        # Test invalid user input for dict
        user_input_root = XML.Element('testUserInput')
        user_input_data = yaml.load("user-input-string: later")
        valid_inputs = {'hello': 'world'}
        user_input_mappings = [('user-input-string', 'userInputString',
                                'user-input', valid_inputs)]

        self.assertRaises(InvalidAttributeError,
                          convert_mapping_to_xml,
                          user_input_root,
                          user_input_data,
                          user_input_mappings)

        # Test invalid key for dict
        user_input_root = XML.Element('testUserInput')
        user_input_data = yaml.load("user-input-string: world")
        valid_inputs = {'hello': 'world'}
        user_input_mappings = [('user-input-string', 'userInputString',
                                'user-input', valid_inputs)]

        self.assertRaises(InvalidAttributeError,
                          convert_mapping_to_xml,
                          user_input_root,
                          user_input_data,
                          user_input_mappings)
