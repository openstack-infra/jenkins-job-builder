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

import codecs
import logging
import os
import re
import doctest
import json
import operator
import testtools
import xml.etree.ElementTree as XML
from six.moves import configparser
import jenkins_jobs.local_yaml as yaml
from jenkins_jobs.builder import XmlJob, YamlParser, ModuleRegistry
from jenkins_jobs.modules import (project_flow,
                                  project_matrix,
                                  project_maven,
                                  project_multijob)


def get_scenarios(fixtures_path, in_ext='yaml', out_ext='xml'):
    """Returns a list of scenarios, each scenario being described
    by two parameters (yaml and xml filenames by default).
        - content of the fixture output file (aka expected)
    """
    scenarios = []
    files = os.listdir(fixtures_path)
    input_files = [f for f in files if re.match(r'.*\.{0}$'.format(in_ext), f)]

    for input_filename in input_files:
        output_candidate = re.sub(r'\.{0}$'.format(in_ext),
                                  '.{0}'.format(out_ext), input_filename)
        # Make sure the input file has a output counterpart
        if output_candidate not in files:
            raise Exception(
                "No {0} file named '{1}' to match {2} file '{3}'"
                .format(out_ext.upper(), output_candidate,
                        in_ext.upper(), input_filename))

        conf_candidate = re.sub(r'\.yaml$', '.conf', input_filename)
        # If present, add the configuration file
        if conf_candidate not in files:
            conf_candidate = None

        scenarios.append((input_filename, {
            'in_filename': input_filename,
            'out_filename': output_candidate,
            'conf_filename': conf_candidate,
        }))

    return scenarios


class BaseTestCase(object):
    scenarios = []
    fixtures_path = None

    # TestCase settings:
    maxDiff = None      # always dump text difference
    longMessage = True  # keep normal error message when providing our

    logging.basicConfig()

    def _read_utf8_content(self):
        # Read XML content, assuming it is unicode encoded
        xml_filepath = os.path.join(self.fixtures_path, self.out_filename)
        xml_content = u"%s" % codecs.open(xml_filepath, 'r', 'utf-8').read()
        return xml_content

    def _read_yaml_content(self):
        yaml_filepath = os.path.join(self.fixtures_path, self.in_filename)
        with open(yaml_filepath, 'r') as yaml_file:
            yaml_content = yaml.load(yaml_file)
        return yaml_content

    def test_yaml_snippet(self):
        if not self.out_filename or not self.in_filename:
            return

        expected_xml = self._read_utf8_content()
        yaml_content = self._read_yaml_content()
        project = None
        if ('project-type' in yaml_content):
            if (yaml_content['project-type'] == "maven"):
                project = project_maven.Maven(None)
            elif (yaml_content['project-type'] == "matrix"):
                project = project_matrix.Matrix(None)
            elif (yaml_content['project-type'] == "flow"):
                project = project_flow.Flow(None)
            elif (yaml_content['project-type'] == "multijob"):
                project = project_multijob.MultiJob(None)

        if project:
            xml_project = project.root_xml(yaml_content)
        else:
            xml_project = XML.Element('project')
        parser = YamlParser()
        pub = self.klass(ModuleRegistry({}))

        # Generate the XML tree directly with modules/general
        pub.gen_xml(parser, xml_project, yaml_content)

        # Prettify generated XML
        pretty_xml = XmlJob(xml_project, 'fixturejob').output().decode('utf-8')

        self.assertThat(
            pretty_xml,
            testtools.matchers.DocTestMatches(expected_xml,
                                              doctest.ELLIPSIS |
                                              doctest.NORMALIZE_WHITESPACE |
                                              doctest.REPORT_NDIFF)
        )


class SingleJobTestCase(BaseTestCase):
    def test_yaml_snippet(self):
        expected_xml = self._read_utf8_content()

        yaml_filepath = os.path.join(self.fixtures_path, self.in_filename)

        if self.conf_filename:
            config = configparser.ConfigParser()
            conf_filepath = os.path.join(self.fixtures_path,
                                         self.conf_filename)
            config.readfp(open(conf_filepath))
        else:
            config = None
        parser = YamlParser(config)
        parser.parse(yaml_filepath)

        # Generate the XML tree
        parser.expandYaml()
        parser.generateXML()

        parser.xml_jobs.sort(key=operator.attrgetter('name'))

        # Prettify generated XML
        pretty_xml = u"\n".join(job.output().decode('utf-8')
                                for job in parser.xml_jobs)

        self.assertThat(
            pretty_xml,
            testtools.matchers.DocTestMatches(expected_xml,
                                              doctest.ELLIPSIS |
                                              doctest.NORMALIZE_WHITESPACE |
                                              doctest.REPORT_NDIFF)
        )


class JsonTestCase(BaseTestCase):

    def test_yaml_snippet(self):
        expected_json = self._read_utf8_content()
        yaml_content = self._read_yaml_content()

        pretty_json = json.dumps(yaml_content, indent=4,
                                 separators=(',', ': '))

        self.assertThat(
            pretty_json,
            testtools.matchers.DocTestMatches(expected_json,
                                              doctest.ELLIPSIS |
                                              doctest.NORMALIZE_WHITESPACE |
                                              doctest.REPORT_NDIFF)
        )
