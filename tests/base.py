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

import doctest
import io
import json
import logging
import operator
import os
import re
import xml.etree.ElementTree as XML

import fixtures
from six.moves import StringIO
import testtools
from testtools.content import text_content
import testscenarios
from yaml import safe_dump

from jenkins_jobs.config import JJBConfig
from jenkins_jobs.errors import InvalidAttributeError
import jenkins_jobs.local_yaml as yaml
from jenkins_jobs.modules import project_externaljob
from jenkins_jobs.modules import project_flow
from jenkins_jobs.modules import project_matrix
from jenkins_jobs.modules import project_maven
from jenkins_jobs.modules import project_multijob
from jenkins_jobs.modules import view_list
from jenkins_jobs.modules import view_pipeline
from jenkins_jobs.parser import YamlParser
from jenkins_jobs.registry import ModuleRegistry
from jenkins_jobs.xml_config import XmlJob
from jenkins_jobs.xml_config import XmlJobGenerator

# This dance deals with the fact that we want unittest.mock if
# we're on Python 3.4 and later, and non-stdlib mock otherwise.
try:
    from unittest import mock
except ImportError:
    import mock  # noqa


def get_scenarios(fixtures_path, in_ext='yaml', out_ext='xml',
                  plugins_info_ext='plugins_info.yaml',
                  filter_func=None):
    """Returns a list of scenarios, each scenario being described
    by two parameters (yaml and xml filenames by default).
        - content of the fixture output file (aka expected)
    """
    scenarios = []
    files = []
    for dirpath, dirs, fs in os.walk(fixtures_path):
        files.extend([os.path.join(dirpath, f) for f in fs])

    input_files = [f for f in files if re.match(r'.*\.{0}$'.format(in_ext), f)]

    for input_filename in input_files:
        if input_filename.endswith(plugins_info_ext):
            continue

        if callable(filter_func) and filter_func(input_filename):
            continue

        output_candidate = re.sub(r'\.{0}$'.format(in_ext),
                                  '.{0}'.format(out_ext), input_filename)
        # assume empty file if no output candidate found
        if output_candidate not in files:
            output_candidate = None

        plugins_info_candidate = re.sub(r'\.{0}$'.format(in_ext),
                                        '.{0}'.format(plugins_info_ext),
                                        input_filename)
        if plugins_info_candidate not in files:
            plugins_info_candidate = None

        conf_candidate = re.sub(r'\.yaml$|\.json$', '.conf', input_filename)
        # If present, add the configuration file
        if conf_candidate not in files:
            conf_candidate = None

        scenarios.append((input_filename, {
            'in_filename': input_filename,
            'out_filename': output_candidate,
            'conf_filename': conf_candidate,
            'plugins_info_filename': plugins_info_candidate,
        }))

    return scenarios


class BaseTestCase(testtools.TestCase):

    # TestCase settings:
    maxDiff = None      # always dump text difference
    longMessage = True  # keep normal error message when providing our

    def setUp(self):

        super(BaseTestCase, self).setUp()
        self.logger = self.useFixture(fixtures.FakeLogger(level=logging.DEBUG))

    def _read_utf8_content(self):
        # if None assume empty file
        if self.out_filename is None:
            return u""

        # Read XML content, assuming it is unicode encoded
        xml_content = u"%s" % io.open(self.out_filename,
                                      'r', encoding='utf-8').read()
        return xml_content

    def _read_yaml_content(self, filename):
        with io.open(filename, 'r', encoding='utf-8') as yaml_file:
            yaml_content = yaml.load(yaml_file)
        return yaml_content

    def _get_config(self):
        jjb_config = JJBConfig(self.conf_filename)
        jjb_config.validate()

        return jjb_config


class BaseScenariosTestCase(testscenarios.TestWithScenarios, BaseTestCase):

    scenarios = []
    fixtures_path = None

    def test_yaml_snippet(self):
        if not self.in_filename:
            return

        jjb_config = self._get_config()

        expected_xml = self._read_utf8_content()
        yaml_content = self._read_yaml_content(self.in_filename)

        plugins_info = None
        if self.plugins_info_filename is not None:
            plugins_info = self._read_yaml_content(self.plugins_info_filename)
            self.addDetail("plugins-info-filename",
                           text_content(self.plugins_info_filename))
            self.addDetail("plugins-info",
                           text_content(str(plugins_info)))

        parser = YamlParser(jjb_config)
        registry = ModuleRegistry(jjb_config, plugins_info)
        registry.set_parser_data(parser.data)

        pub = self.klass(registry)

        project = None
        if ('project-type' in yaml_content):
            if (yaml_content['project-type'] == "maven"):
                project = project_maven.Maven(registry)
            elif (yaml_content['project-type'] == "matrix"):
                project = project_matrix.Matrix(registry)
            elif (yaml_content['project-type'] == "flow"):
                project = project_flow.Flow(registry)
            elif (yaml_content['project-type'] == "multijob"):
                project = project_multijob.MultiJob(registry)
            elif (yaml_content['project-type'] == "externaljob"):
                project = project_externaljob.ExternalJob(registry)

        if 'view-type' in yaml_content:
            if yaml_content['view-type'] == "list":
                project = view_list.List(None)
            elif yaml_content['view-type'] == "pipeline":
                project = view_pipeline.Pipeline(None)
            else:
                raise InvalidAttributeError(
                    'view-type', yaml_content['view-type'])

        if project:
            xml_project = project.root_xml(yaml_content)
        else:
            xml_project = XML.Element('project')

        # Generate the XML tree directly with modules/general
        pub.gen_xml(xml_project, yaml_content)

        # Prettify generated XML
        pretty_xml = XmlJob(xml_project, 'fixturejob').output().decode('utf-8')

        self.assertThat(
            pretty_xml,
            testtools.matchers.DocTestMatches(expected_xml,
                                              doctest.ELLIPSIS |
                                              doctest.REPORT_NDIFF)
        )


class SingleJobTestCase(BaseScenariosTestCase):

    def test_yaml_snippet(self):
        config = self._get_config()

        expected_xml = self._read_utf8_content()

        parser = YamlParser(config)
        parser.parse(self.in_filename)

        registry = ModuleRegistry(config)
        registry.set_parser_data(parser.data)
        job_data_list, view_data_list = parser.expandYaml(registry)

        # Generate the XML tree
        xml_generator = XmlJobGenerator(registry)
        xml_jobs = xml_generator.generateXML(job_data_list)

        xml_jobs.sort(key=operator.attrgetter('name'))

        # Prettify generated XML
        pretty_xml = u"\n".join(job.output().decode('utf-8')
                                for job in xml_jobs)

        self.assertThat(
            pretty_xml,
            testtools.matchers.DocTestMatches(expected_xml,
                                              doctest.ELLIPSIS |
                                              doctest.REPORT_NDIFF)
        )


class JsonTestCase(BaseScenariosTestCase):

    def test_yaml_snippet(self):
        expected_json = self._read_utf8_content()
        yaml_content = self._read_yaml_content(self.in_filename)

        pretty_json = json.dumps(yaml_content, indent=4,
                                 separators=(',', ': '))

        self.assertThat(
            pretty_json,
            testtools.matchers.DocTestMatches(expected_json,
                                              doctest.ELLIPSIS |
                                              doctest.REPORT_NDIFF)
        )


class YamlTestCase(BaseScenariosTestCase):

    def test_yaml_snippet(self):
        expected_yaml = self._read_utf8_content()
        yaml_content = self._read_yaml_content(self.in_filename)

        # using json forces expansion of yaml anchors and aliases in the
        # outputted yaml, otherwise it would simply appear exactly as
        # entered which doesn't show that the net effect of the yaml
        data = StringIO(json.dumps(yaml_content))

        pretty_yaml = safe_dump(json.load(data), default_flow_style=False)

        self.assertThat(
            pretty_yaml,
            testtools.matchers.DocTestMatches(expected_yaml,
                                              doctest.ELLIPSIS |
                                              doctest.REPORT_NDIFF)
        )
