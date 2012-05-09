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

# Jenkins Job module for docs publishers
# No additional YAML needed

import xml.etree.ElementTree as XML

class publisher_docs(object):
    def __init__(self, data):
        self.data = data

    def gen_xml(self, xml_parent):
        main = self.data['main']
        publishers = XML.SubElement(xml_parent, 'publishers')
        scp = XML.SubElement(publishers, 'be.certipost.hudson.plugin.SCPRepositoryPublisher')
        XML.SubElement(scp, 'siteName').text = '{proj}.{site}.org'.format(proj=main['project'], site=main['site'])
        entries = XML.SubElement(scp, 'entries')
        entry = XML.SubElement(entries, 'be.certipost.hudson.plugin.Entry')
        XML.SubElement(entry, 'filePath').text = 'docs/{proj}'.format(proj=main['project'])
        XML.SubElement(entry, 'sourceFile').text = 'doc/build/html/**'
        XML.SubElement(entry, 'keepHierarchy').text = 'false'
        entry = XML.SubElement(entries, 'be.certipost.hudson.plugin.Entry')
        XML.SubElement(entry, 'filePath').text = 'docs/{proj}/_static'.format(proj=main['project'])
        XML.SubElement(entry, 'sourceFile').text = 'doc/build/html/_static/**'
        XML.SubElement(entry, 'keepHierarchy').text = 'false'
        entry = XML.SubElement(entries, 'be.certipost.hudson.plugin.Entry')
        XML.SubElement(entry, 'filePath').text = 'docs/{proj}/_sources'.format(proj=main['project'])
        XML.SubElement(entry, 'sourceFile').text = 'doc/build/html/_sources/**'
        XML.SubElement(entry, 'keepHierarchy').text = 'false'

