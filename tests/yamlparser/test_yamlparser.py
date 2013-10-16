# Joint copyright:
#  - Copyright 2012,2013 Wikimedia Foundation
#  - Copyright 2012,2013 Antoine "hashar" Musso
#  - Copyright 2013 Arnaud Fabre
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
from ConfigParser import ConfigParser
from testtools import TestCase
from testscenarios.testcase import TestWithScenarios
from tests.base import get_scenarios, BaseTestCase
import doctest
import testtools
from jenkins_jobs.builder import YamlParser


class TestCaseModuleYamlInclude(TestWithScenarios, TestCase, BaseTestCase):
    fixtures_path = os.path.join(os.path.dirname(__file__), 'fixtures')
    scenarios = get_scenarios(fixtures_path)

    def test_yaml_snippet(self):
        if not self.xml_filename or not self.yaml_filename:
            return

        xml_filepath = os.path.join(self.fixtures_path, self.xml_filename)
        expected_xml = u"%s" % open(xml_filepath, 'r').read()

        yaml_filepath = os.path.join(self.fixtures_path, self.yaml_filename)

        if self.conf_filename:
            config = ConfigParser()
            conf_filepath = os.path.join(self.fixtures_path,
                                         self.conf_filename)
            config.readfp(open(conf_filepath))
        else:
            config = None
        parser = YamlParser(config)
        parser.parse(yaml_filepath)

        # Generate the XML tree
        parser.generateXML()

        # Prettify generated XML
        pretty_xml = parser.jobs[0].output()

        self.assertThat(
            pretty_xml,
            testtools.matchers.DocTestMatches(expected_xml,
                                              doctest.ELLIPSIS |
                                              doctest.NORMALIZE_WHITESPACE |
                                              doctest.REPORT_NDIFF)
        )
