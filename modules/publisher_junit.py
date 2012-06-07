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
# To use you add the following into your YAML:
# publisher:
#   results: 'nosetests.xml'

import xml.etree.ElementTree as XML

class publisher_junit(object):
    def __init__(self, data):
        self.data = data

    def gen_xml(self, xml_parent):
        publishers = XML.SubElement(xml_parent, 'publishers')
        junitresult = XML.SubElement(publishers,
            'hudson.tasks.junit.JUnitResultArchiver')
        XML.SubElement(junitresult, 'testResults').text = self.data['publisher']['results']
        XML.SubElement(junitresult, 'keepLongStdio').text = "true"
        XML.SubElement(junitresult, 'testDataPublishers')
