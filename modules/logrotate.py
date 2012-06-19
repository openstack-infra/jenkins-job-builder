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

# Jenkins Job module for logrotate
# To use add the folowing into your YAML:
# logrotate:
#  daysToKeep: 3
#  numToKeep: 20
#  artifactDaysToKeep: -1
#  artifactNumToKeep: -1

import xml.etree.ElementTree as XML


def register(registry):
    mod = LogRotate()
    registry.registerModule(mod)


class LogRotate(object):
    sequence = 10

    def handle_data(self, data):
        self.data = data

    def gen_xml(self, xml_parent, data):
        if self.data.has_key('logrotate'):
            lr_xml = XML.SubElement(xml_parent, 'logRotator')
            logrotate = self.data['logrotate']
            lr_days = XML.SubElement(lr_xml, 'daysToKeep')
            lr_days.text = str(logrotate['daysToKeep'])
            lr_num = XML.SubElement(lr_xml, 'numToKeep')
            lr_num.text = str(logrotate['numToKeep'])
            lr_adays = XML.SubElement(lr_xml, 'artifactDaysToKeep')
            lr_adays.text = str(logrotate['artifactDaysToKeep'])
            lr_anum = XML.SubElement(lr_xml, 'artifactNumToKeep')
            lr_anum.text = str(logrotate['artifactNumToKeep'])
