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
from six.moves import configparser
from six.moves import StringIO
import testtools
from testtools.content import text_content
from yaml import safe_dump

from jenkins_jobs.cmd import DEFAULT_CONF
import jenkins_jobs.local_yaml as yaml
from jenkins_jobs.modules import project_externaljob
from jenkins_jobs.modules import project_flow
from jenkins_jobs.modules import project_matrix
from jenkins_jobs.modules import project_maven
from jenkins_jobs.modules import project_multijob
from jenkins_jobs.parser import YamlParser
from jenkins_jobs.xml_config import XmlJob

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


class LoggingFixture(object):

    def setUp(self):

        super(LoggingFixture, self).setUp()
        self.useFixture(fixtures.FakeLogger(level=logging.DEBUG))


class BaseTestCase(LoggingFixture):
    scenarios = []
    fixtures_path = None

    # TestCase settings:
    maxDiff = None      # always dump text difference
    longMessage = True  # keep normal error message when providing our

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
        config = configparser.ConfigParser()
        config.readfp(StringIO(DEFAULT_CONF))
        if self.conf_filename is not None:
            with io.open(self.conf_filename, 'r', encoding='utf-8') as cf:
                config.readfp(cf)
        return config

    def test_yaml_snippet(self):
        if not self.in_filename:
            return

        config = self._get_config()

        expected_xml = self._read_utf8_content()
        yaml_content = self._read_yaml_content(self.in_filename)

        plugins_info = None
        if self.plugins_info_filename is not None:
            plugins_info = self._read_yaml_content(self.plugins_info_filename)
            self.addDetail("plugins-info-filename",
                           text_content(self.plugins_info_filename))
            self.addDetail("plugins-info",
                           text_content(str(plugins_info)))

        parser = YamlParser(config, plugins_info)

        pub = self.klass(parser.registry)

        project = None
        if ('project-type' in yaml_content):
            if (yaml_content['project-type'] == "maven"):
                project = project_maven.Maven(parser.registry)
            elif (yaml_content['project-type'] == "matrix"):
                project = project_matrix.Matrix(parser.registry)
            elif (yaml_content['project-type'] == "flow"):
                project = project_flow.Flow(parser.registry)
            elif (yaml_content['project-type'] == "multijob"):
                project = project_multijob.MultiJob(parser.registry)
            elif (yaml_content['project-type'] == "externaljob"):
                project = project_externaljob.ExternalJob(parser.registry)

        if project:
            xml_project = project.root_xml(yaml_content)
        else:
            xml_project = XML.Element('project')

        # Generate the XML tree directly with modules/general
        pub.gen_xml(parser, xml_project, yaml_content)

        # Prettify generated XML
        pretty_xml = XmlJob(xml_project, 'fixturejob').output().decode('utf-8')

        self.assertThat(
            pretty_xml,
            testtools.matchers.DocTestMatches(expected_xml,
                                              doctest.ELLIPSIS |
                                              doctest.REPORT_NDIFF)
        )


class SingleJobTestCase(BaseTestCase):
    def test_yaml_snippet(self):
        config = self._get_config()

        expected_xml = self._read_utf8_content()

        parser = YamlParser(config)
        parser.parse(self.in_filename)

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
                                              doctest.REPORT_NDIFF)
        )


class JsonTestCase(BaseTestCase):

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


class YamlTestCase(BaseTestCase):

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
