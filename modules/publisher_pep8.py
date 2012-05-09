#! /usr/bin/env python
# Copyright (C) 2012 OpenStack, LLC.
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

# Jenkins Job module for pep8 publishers
# No additional YAML needed

import xml.etree.ElementTree as XML

class publisher_pep8(object):
    def __init__(self, data):
        self.data = data

    def _add_entry(self, xml_parent, name):
        entry = XML.SubElement(xml_parent, 'entry')
        XML.SubElement(entry, 'string').text = name
        tconfig = XML.SubElement(entry, 'hudson.plugins.violations.TypeConfig')
        XML.SubElement(tconfig, 'type').text = name
        XML.SubElement(tconfig, 'min').text = '10'
        XML.SubElement(tconfig, 'max').text = '999'
        XML.SubElement(tconfig, 'unstable').text = '999'
        XML.SubElement(tconfig, 'usePattern').text = 'false'
        XML.SubElement(tconfig, 'pattern')

    def gen_xml(self, xml_parent):
        publishers = XML.SubElement(xml_parent, 'publishers')
        violations = XML.SubElement(publishers, 'hudson.plugins.violations.ViolationsPublisher')
        config = XML.SubElement(violations, 'config')
        suppressions = XML.SubElement(config, 'suppressions', {'class':'tree-set'})
        XML.SubElement(suppressions, 'no-comparator')
        configs = XML.SubElement(config, 'typeConfigs')
        XML.SubElement(configs, 'no-comparator')

        self._add_entry(configs, 'checkstyle')
        self._add_entry(configs, 'codenarc')
        self._add_entry(configs, 'cpd')
        self._add_entry(configs, 'cpplint')
        self._add_entry(configs, 'csslint')
        self._add_entry(configs, 'findbugs')
        self._add_entry(configs, 'fxcop')
        self._add_entry(configs, 'gendarme')
        self._add_entry(configs, 'jcreport')
        self._add_entry(configs, 'jslint')

        entry = XML.SubElement(configs, 'entry')
        XML.SubElement(entry, 'string').text = 'pep8'
        tconfig = XML.SubElement(entry, 'hudson.plugins.violations.TypeConfig')
        XML.SubElement(tconfig, 'type').text = 'pep8'
        XML.SubElement(tconfig, 'min').text = '0'
        XML.SubElement(tconfig, 'max').text = '1'
        XML.SubElement(tconfig, 'unstable').text = '1'
        XML.SubElement(tconfig, 'usePattern').text = 'false'
        XML.SubElement(tconfig, 'pattern').text = '**/pep8.txt'

        self._add_entry(configs, 'pmd')
        self._add_entry(configs, 'pylint')
        self._add_entry(configs, 'simian')
        self._add_entry(configs, 'stylecop')

        XML.SubElement(config, 'limit').text = '100'
        XML.SubElement(config, 'sourcePathPattern')
        XML.SubElement(config, 'fauxProjectPath')
        XML.SubElement(config, 'encoding').text = 'default'
