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


class XmlGenerator(object):
    """A super-class to capture common XML generation logic.

    Sub-classes should define three attribute: ``entry_point_group``,
    ``kind_attribute`` and ``kind_default``.  The value of ``kind_attribute``
    in the given data dictionary (or ``kind_default`` if it isn't present)
    will be used to filter the entry points in ``entry_point_group``; the
    module so found will be used to generate the XML object.
    """

    def __init__(self, registry):
        self.registry = registry

    def generateXML(self, data_list):
        xml_objs = []
        for data in data_list:
            xml_objs.append(self._getXMLForData(data))
        return xml_objs

    def _getXMLForData(self, data):
        kind = data.get(self.kind_attribute, self.kind_default)

        for ep in pkg_resources.iter_entry_points(
                group=self.entry_point_group, name=kind):
            Mod = ep.load()
            mod = Mod(self.registry)
            xml = mod.root_xml(data)
            if "view-type" not in data:
                self._gen_xml(xml, data)
            obj = XmlJob(xml, data['name'])
            return obj

        names = [
            ep.name for ep in pkg_resources.iter_entry_points(
                group=self.entry_point_group)]
        raise errors.JenkinsJobsException(
            'Unrecognized {}: {} (supported types are: {})'.format(
                self.kind_attribute, kind, ', '.join(names)))

    def _gen_xml(self, xml, data):
        for module in self.registry.modules:
            if hasattr(module, 'gen_xml'):
                module.gen_xml(xml, data)


class XmlJobGenerator(XmlGenerator):
    """ This class is responsible for generating Jenkins Configuration XML from
    a compatible intermediate representation of Jenkins Jobs.
    """
    entry_point_group = 'jenkins_jobs.projects'
    kind_attribute = 'project-type'
    kind_default = 'freestyle'


class XmlViewGenerator(XmlGenerator):
    """ This class is responsible for generating Jenkins Configuration XML from
    a compatible intermediate representation of Jenkins Views.
    """
    entry_point_group = 'jenkins_jobs.views'
    kind_attribute = 'view-type'
    kind_default = 'list'
