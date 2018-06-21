# Copyright 2016 Hewlett Packard Enterprise
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

from jenkins_jobs import errors
from jenkins_jobs import parser
from jenkins_jobs import registry
from jenkins_jobs import xml_config

from tests import base


class TestXmlJobGeneratorExceptions(base.BaseTestCase):
    fixtures_path = os.path.join(os.path.dirname(__file__), 'exceptions')

    def test_invalid_project(self):
        self.conf_filename = None
        config = self._get_config()

        yp = parser.YamlParser(config)
        yp.parse(os.path.join(self.fixtures_path,
                              "invalid_project.yaml"))

        reg = registry.ModuleRegistry(config)
        job_data, _ = yp.expandYaml(reg)

        # Generate the XML tree
        xml_generator = xml_config.XmlJobGenerator(reg)
        e = self.assertRaises(errors.JenkinsJobsException,
                              xml_generator.generateXML, job_data)
        self.assertIn("Unrecognized project-type:", str(e))

    def test_invalid_view(self):
        self.conf_filename = None
        config = self._get_config()

        yp = parser.YamlParser(config)
        yp.parse(os.path.join(self.fixtures_path, "invalid_view.yaml"))

        reg = registry.ModuleRegistry(config)
        _, view_data = yp.expandYaml(reg)

        # Generate the XML tree
        xml_generator = xml_config.XmlViewGenerator(reg)
        e = self.assertRaises(errors.JenkinsJobsException,
                              xml_generator.generateXML, view_data)
        self.assertIn("Unrecognized view-type:", str(e))

    def test_incorrect_template_params(self):
        self.conf_filename = None
        config = self._get_config()

        yp = parser.YamlParser(config)
        yp.parse(os.path.join(self.fixtures_path,
                              "failure_formatting_component.yaml"))

        reg = registry.ModuleRegistry(config)
        reg.set_parser_data(yp.data)
        job_data_list, view_data_list = yp.expandYaml(reg)

        xml_generator = xml_config.XmlJobGenerator(reg)
        self.assertRaises(Exception, xml_generator.generateXML, job_data_list)
        self.assertIn("Failure formatting component", self.logger.output)
        self.assertIn("Problem formatting with args", self.logger.output)
