#!/usr/bin/env python
# Copyright (C) 2015 OpenStack, LLC.
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

# Manage Jenkins XML config file output.

import hashlib
import pkg_resources
from xml.dom import minidom
import xml.etree.ElementTree as XML

from jenkins_jobs import errors

__all__ = [
    "XmlJobGenerator",
    "XmlJob"
]


def remove_ignorable_whitespace(node):
    """Remove insignificant whitespace from XML nodes

    It should only remove whitespace in between elements and sub elements.
    This should be safe for Jenkins due to how it's XML serialization works
    but may not be valid for other XML documents. So use this method with
    caution outside of this specific library.
    """
    # strip tail whitespace if it's not significant
    if node.tail and node.tail.strip() == "":
        node.tail = None

    for child in node:
        # only strip whitespace from the text node if there are subelement
        # nodes as this means we are removing leading whitespace before such
        # sub elements. Otherwise risk removing whitespace from an element
        # that only contains whitespace
        if node.text and node.text.strip() == "":
            node.text = None
        remove_ignorable_whitespace(child)


class XmlJob(object):
    def __init__(self, xml, name):
        self.xml = xml
        self.name = name

    def md5(self):
        return hashlib.md5(self.output()).hexdigest()

    def output(self):
        out = minidom.parseString(XML.tostring(self.xml, encoding='UTF-8'))
        return out.toprettyxml(indent='  ', encoding='utf-8')


class XmlJobGenerator(object):
    """ This class is responsible for generating Jenkins Configuration XML from
    a compatible intermediate representation of Jenkins Jobs.
    """

    def __init__(self, registry):
        self.registry = registry

    def generateXML(self, jobdict_list):
        xml_jobs = []
        for job in jobdict_list:
            xml_jobs.append(self._getXMLForJob(job))
        return xml_jobs

    def _getXMLForJob(self, data):
        kind = data.get('project-type', 'freestyle')

        for ep in pkg_resources.iter_entry_points(
                group='jenkins_jobs.projects', name=kind):
            Mod = ep.load()
            mod = Mod(self.registry)
            xml = mod.root_xml(data)
            self._gen_xml(xml, data)
            job = XmlJob(xml, data['name'])
            return job

        raise errors.JenkinsJobsException("Unrecognized project type: '%s'"
                                          % kind)

    def _gen_xml(self, xml, data):
        for module in self.registry.modules:
            if hasattr(module, 'gen_xml'):
                module.gen_xml(xml, data)


class XmlViewGenerator(object):
    """ This class is responsible for generating Jenkins Configuration XML from
    a compatible intermediate representation of Jenkins Views.
    """

    def __init__(self, registry):
        self.registry = registry

    def generateXML(self, viewdict_list):
        xml_views = []
        for view in viewdict_list:
            xml_views.append(self._getXMLForView(view))
        return xml_views

    def _getXMLForView(self, data):
        kind = data.get('view-type', 'list')

        for ep in pkg_resources.iter_entry_points(
                group='jenkins_jobs.views', name=kind):
            Mod = ep.load()
            mod = Mod(self.registry)
            xml = mod.root_xml(data)
            self._gen_xml(xml, data)
            view = XmlJob(xml, data['name'])
            return view

    def _gen_xml(self, xml, data):
        for module in self.registry.modules:
            if hasattr(module, 'gen_xml'):
                module.gen_xml(xml, data)
