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
import testtools
import unittest
import xml.etree.ElementTree as XML
import yaml

from jenkins_jobs.builder import XmlJob, YamlParser, ModuleRegistry
from jenkins_jobs.modules import publishers

FIXTURES_PATH = os.path.join(
    os.path.dirname(__file__), 'fixtures')


def load_tests(loader, tests, pattern):
    return unittest.TestSuite(
        build_test_case(xml, yamldef, files)
        for xml, yamldef, files in get_fixtures()
    )


def get_fixtures():
    """Returns a list of tuples containing, in order:
        - content of the fixture .xml file (aka expected)
        - content of the fixture .yaml file
        - list of the filenames
    """
    fixtures = []
    files = os.listdir(FIXTURES_PATH)
    yaml_files = [f for f in files if re.match(r'.*\.yaml$', f)]

    for yaml_filename in yaml_files:
        xml_candidate = re.sub(r'\.yaml$', '.xml', yaml_filename)
        # Make sure the yaml file has a xml counterpart
        if xml_candidate not in files:
            raise Exception(
                "No XML file named '%s' to match " +
                "YAML file '%s'" % (xml_candidate, yaml_filename))

        # Read XML content, assuming it is unicode encoded
        xml_filename = os.path.join(FIXTURES_PATH, xml_candidate)
        xml_content = u"%s" % open(xml_filename, 'r').read()

        yaml_file = file(os.path.join(FIXTURES_PATH, yaml_filename), 'r')
        yaml_content = yaml.load(yaml_file)

        fixtures.append((
            xml_content,
            yaml_content,
            [xml_filename, yaml_filename],
        ))

    return fixtures


# The class is wrapped in a def to prevent it from being discovered by
# python-discover, it would try to load the class passing unexpected parameters
# which breaks everything.
def build_test_case(expected_xml, yaml, files):
    class TestCaseModulePublisher(testtools.TestCase):

        # testtools.TestCase settings:
        maxDiff = None      # always dump text difference
        longMessage = True  # keep normal error message when providing our

        def __init__(self, expected_xml, yaml, files):
            testtools.TestCase.__init__(self, 'test_yaml_snippet')
            self.xml = expected_xml
            self.yaml = yaml
            self.files = files

        def test_yaml_snippet(self):
            xml_project = XML.Element('project')  # root element
            parser = YamlParser()
            pub = publishers.Publishers(ModuleRegistry({}))

            # Generate the XML tree directly with modules/publishers/*
            pub.gen_xml(parser, xml_project, self.yaml)

            # Prettify generated XML
            pretty_xml = XmlJob(xml_project, 'fixturejob').output()

            self.assertMultiLineEqual(
                self.xml, pretty_xml,
                'Test inputs: %s' % ', '.join(self.files)
            )
    return TestCaseModulePublisher(expected_xml, yaml, files)

if __name__ == "__main__":
    unittest.main()
