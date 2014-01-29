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
import operator
import testtools
import xml.etree.ElementTree as XML
from ConfigParser import ConfigParser
import yaml
from jenkins_jobs.builder import XmlJob, YamlParser, ModuleRegistry
from jenkins_jobs.modules import (project_flow,
                                  project_matrix,
                                  project_maven,
                                  project_multijob)


def get_scenarios(fixtures_path):
    """Returns a list of scenarios, each scenario being described
    by two parameters (yaml and xml filenames).
        - content of the fixture .xml file (aka expected)
    """
    scenarios = []
    files = os.listdir(fixtures_path)
    yaml_files = [f for f in files if re.match(r'.*\.yaml$', f)]

    for yaml_filename in yaml_files:
        xml_candidate = re.sub(r'\.yaml$', '.xml', yaml_filename)
        # Make sure the yaml file has a xml counterpart
        if xml_candidate not in files:
            raise Exception(
                "No XML file named '%s' to match "
                "YAML file '%s'" % (xml_candidate, yaml_filename))
        conf_candidate = re.sub(r'\.yaml$', '.conf', yaml_filename)
        # If present, add the configuration file
        if conf_candidate not in files:
            conf_candidate = None

        scenarios.append((yaml_filename, {
            'yaml_filename': yaml_filename,
            'xml_filename': xml_candidate,
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

    def __read_content(self):
        # Read XML content, assuming it is unicode encoded
        xml_filepath = os.path.join(self.fixtures_path, self.xml_filename)
        xml_content = u"%s" % codecs.open(xml_filepath, 'r', 'utf-8').read()

        yaml_filepath = os.path.join(self.fixtures_path, self.yaml_filename)
        with file(yaml_filepath, 'r') as yaml_file:
            yaml_content = yaml.load(yaml_file)

        return (yaml_content, xml_content)

    def test_yaml_snippet(self):
        if not self.xml_filename or not self.yaml_filename:
            return

        yaml_content, expected_xml = self.__read_content()
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
        pretty_xml = unicode(XmlJob(xml_project, 'fixturejob').output(),
                             'utf-8')

        self.assertThat(
            pretty_xml,
            testtools.matchers.DocTestMatches(expected_xml,
                                              doctest.ELLIPSIS |
                                              doctest.NORMALIZE_WHITESPACE |
                                              doctest.REPORT_NDIFF)
        )


class SingleJobTestCase(BaseTestCase):
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

        parser.jobs.sort(key=operator.attrgetter('name'))

        # Prettify generated XML
        pretty_xml = "\n".join(job.output() for job in parser.jobs)

        self.assertThat(
            pretty_xml,
            testtools.matchers.DocTestMatches(expected_xml,
                                              doctest.ELLIPSIS |
                                              doctest.NORMALIZE_WHITESPACE |
                                              doctest.REPORT_NDIFF)
        )
