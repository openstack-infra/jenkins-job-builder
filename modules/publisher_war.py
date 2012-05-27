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

# Jenkins Job module for war publishers
# To use you add the following into your YAML:
# publish:
#   site: 'nova.openstack.org'
#   warfile: 'gerrit-war/target/gerrit*.war'
#   target_path: 'tarballs/ci/'

import xml.etree.ElementTree as XML

class publisher_war(object):
    def __init__(self, data):
        self.data = data

    def gen_xml(self, xml_parent):
        site = self.data['publisher']['site']
        publishers = XML.SubElement(xml_parent, 'publishers')
        archiver = XML.SubElement(publishers, 'hudson.tasks.ArtifactArchiver')
        XML.SubElement(archiver, 'artifacts').text = self.data['publisher']['warfile']
        XML.SubElement(archiver, 'latestOnly').text = 'false'
        scp = XML.SubElement(publishers, 'be.certipost.hudson.plugin.SCPRepositoryPublisher')
        XML.SubElement(scp, 'siteName').text = site
        entries = XML.SubElement(scp, 'entries')
        entry = XML.SubElement(entries, 'be.certipost.hudson.plugin.Entry')
        XML.SubElement(entry, 'filePath').text = self.data['publisher']['target_path']
        XML.SubElement(entry, 'sourceFile').text = self.data['publisher']['warfile']
        XML.SubElement(entry, 'keepHierarchy').text = 'false'
