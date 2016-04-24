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

from jenkins_jobs import parser
from jenkins_jobs import registry

from tests import base


class TestCaseModuleYamlInclude(base.SingleJobTestCase):
    fixtures_path = os.path.join(os.path.dirname(__file__), 'fixtures')
    scenarios = base.get_scenarios(fixtures_path)


class TestYamlParserExceptions(base.BaseTestCase):
    fixtures_path = os.path.join(os.path.dirname(__file__), 'exceptions')

    def test_incorrect_template_dimensions(self):
        self.conf_filename = None
        config = self._get_config()

        yp = parser.YamlParser(config)
        yp.parse(os.path.join(self.fixtures_path,
                              "incorrect_template_dimensions.yaml"))

        reg = registry.ModuleRegistry(config)

        e = self.assertRaises(Exception, yp.expandYaml, reg)
        self.assertIn("'NoneType' object is not iterable", str(e))
        self.assertIn("- branch: current\n  current: null", self.logger.output)


class TestYamlParserFailureFormattingExceptions(base.BaseScenariosTestCase):
    fixtures_path = os.path.join(os.path.dirname(__file__), 'exceptions')
    scenarios = [
        ('s1', {'name': 'template'}),
        ('s2', {'name': 'params'})
    ]

    def test_yaml_snippet(self):
        self.conf_filename = None
        config = self._get_config()

        yp = parser.YamlParser(config)
        yp.parse(os.path.join(self.fixtures_path,
                              "failure_formatting_{}.yaml".format(self.name)))

        reg = registry.ModuleRegistry(config)

        self.assertRaises(Exception, yp.expandYaml, reg)
        self.assertIn("Failure formatting {}".format(self.name),
                      self.logger.output)
        self.assertIn("Problem formatting with args", self.logger.output)
