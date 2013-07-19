#!/usr/bin/env python
#
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
import re
from testscenarios.testcase import TestWithScenarios
import unittest
import xml.etree.ElementTree as XML
import yaml

from jenkins_jobs.builder import XmlJob, YamlParser, ModuleRegistry
from jenkins_jobs.modules import publishers

FIXTURES_PATH = os.path.join(
    os.path.dirname(__file__), 'fixtures')


def get_scenarios():
    """Returns a list of scenarios, each scenario being described
    by two parameters (yaml and xml filenames).
        - content of the fixture .xml file (aka expected)
    """
    scenarios = []
    files = os.listdir(FIXTURES_PATH)
    yaml_files = [f for f in files if re.match(r'.*\.yaml$', f)]

    for yaml_filename in yaml_files:
        xml_candidate = re.sub(r'\.yaml$', '.xml', yaml_filename)
        # Make sure the yaml file has a xml counterpart
        if xml_candidate not in files:
            raise Exception(
                "No XML file named '%s' to match " +
                "YAML file '%s'" % (xml_candidate, yaml_filename))

        scenarios.append((yaml_filename, {
            'yaml_filename': yaml_filename, 'xml_filename': xml_candidate
        }))

    return scenarios


class TestCaseModulePublisher(TestWithScenarios):
    scenarios = get_scenarios()

    # unittest.TestCase settings:
    maxDiff = None      # always dump text difference
    longMessage = True  # keep normal error message when providing our

    def __read_content(self):
        # Read XML content, assuming it is unicode encoded
        xml_filepath = os.path.join(FIXTURES_PATH, self.xml_filename)
        xml_content = u"%s" % open(xml_filepath, 'r').read()

        yaml_filepath = os.path.join(FIXTURES_PATH, self.yaml_filename)
        with file(yaml_filepath, 'r') as yaml_file:
            yaml_content = yaml.load(yaml_file)

        return (yaml_content, xml_content)

    def test_yaml_snippet(self):
        yaml_content, expected_xml = self.__read_content()

        xml_project = XML.Element('project')  # root element
        parser = YamlParser()
        pub = publishers.Publishers(ModuleRegistry({}))

        # Generate the XML tree directly with modules/publishers/*
        pub.gen_xml(parser, xml_project, yaml_content)

        # Prettify generated XML
        pretty_xml = XmlJob(xml_project, 'fixturejob').output()

        self.assertMultiLineEqual(
            expected_xml, pretty_xml,
            'Test inputs: %s, %s' % (self.yaml_filename, self.xml_filename)
        )

if __name__ == "__main__":
    unittest.main()
