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

# Jenkins Job module for coverage publishers
# No additional YAML needed

import xml.etree.ElementTree as XML

class publisher_coverage(object):
    def __init__(self, data):
        self.data = data

    def gen_xml(self, xml_parent):
        publishers = XML.SubElement(xml_parent, 'publishers')
        cobertura = XML.SubElement(publishers, 'hudson.plugins.cobertura.CoberturaPublisher')
        XML.SubElement(cobertura, 'coberturaReportFile').text = '**/coverage.xml'
        XML.SubElement(cobertura, 'onlyStable').text = 'false'
        healthy = XML.SubElement(cobertura, 'healthyTarget')
        targets = XML.SubElement(healthy, 'targets', {'class':'enum-map','enum-type':'hudson.plugins.cobertura.targets.CoverageMetric'})
        entry = XML.SubElement(targets, 'entry')
        XML.SubElement(entry, 'hudson.plugins.cobertura.targets.CoverageMetric').text = 'CONDITIONAL'
        XML.SubElement(entry, 'int').text = '70'
        entry = XML.SubElement(targets, 'entry')
        XML.SubElement(entry, 'hudson.plugins.cobertura.targets.CoverageMetric').text = 'LINE'
        XML.SubElement(entry, 'int').text = '80'
        entry = XML.SubElement(targets, 'entry')
        XML.SubElement(entry, 'hudson.plugins.cobertura.targets.CoverageMetric').text = 'METHOD'
        XML.SubElement(entry, 'int').text = '80'
        unhealthy = XML.SubElement(cobertura, 'unhealthyTarget')
        targets = XML.SubElement(unhealthy, 'targets', {'class':'enum-map','enum-type':'hudson.plugins.cobertura.targets.CoverageMetric'})
        entry = XML.SubElement(targets, 'entry')
        XML.SubElement(entry, 'hudson.plugins.cobertura.targets.CoverageMetric').text = 'CONDITIONAL'
        XML.SubElement(entry, 'int').text = '0'
        entry = XML.SubElement(targets, 'entry')
        XML.SubElement(entry, 'hudson.plugins.cobertura.targets.CoverageMetric').text = 'LINE'
        XML.SubElement(entry, 'int').text = '0'
        entry = XML.SubElement(targets, 'entry')
        XML.SubElement(entry, 'hudson.plugins.cobertura.targets.CoverageMetric').text = 'METHOD'
        XML.SubElement(entry, 'int').text = '0'
        failing = XML.SubElement(cobertura, 'failingTarget')
        targets = XML.SubElement(failing, 'targets', {'class':'enum-map','enum-type':'hudson.plugins.cobertura.targets.CoverageMetric'})
        entry = XML.SubElement(targets, 'entry')
        XML.SubElement(entry, 'hudson.plugins.cobertura.targets.CoverageMetric').text = 'CONDITIONAL'
        XML.SubElement(entry, 'int').text = '0'
        entry = XML.SubElement(targets, 'entry')
        XML.SubElement(entry, 'hudson.plugins.cobertura.targets.CoverageMetric').text = 'LINE'
        XML.SubElement(entry, 'int').text = '0'
        entry = XML.SubElement(targets, 'entry')
        XML.SubElement(entry, 'hudson.plugins.cobertura.targets.CoverageMetric').text = 'METHOD'
        XML.SubElement(entry, 'int').text = '0'
        XML.SubElement(cobertura, 'sourceEncoding').text = 'ASCII'
