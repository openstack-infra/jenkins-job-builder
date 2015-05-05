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
import sys
import xml
from xml.dom import minidom
import xml.etree.ElementTree as XML


# Python 2.6's minidom toprettyxml produces broken output by adding extraneous
# whitespace around data. This patches the broken implementation with one taken
# from Python > 2.7.3
def writexml(self, writer, indent="", addindent="", newl=""):
    # indent = current indentation
    # addindent = indentation to add to higher levels
    # newl = newline string
    writer.write(indent + "<" + self.tagName)

    attrs = self._get_attributes()
    a_names = attrs.keys()
    a_names.sort()

    for a_name in a_names:
        writer.write(" %s=\"" % a_name)
        minidom._write_data(writer, attrs[a_name].value)
        writer.write("\"")
    if self.childNodes:
        writer.write(">")
        if (len(self.childNodes) == 1 and
                self.childNodes[0].nodeType == minidom.Node.TEXT_NODE):
            self.childNodes[0].writexml(writer, '', '', '')
        else:
            writer.write(newl)
            for node in self.childNodes:
                node.writexml(writer, indent + addindent, addindent, newl)
            writer.write(indent)
        writer.write("</%s>%s" % (self.tagName, newl))
    else:
        writer.write("/>%s" % (newl))

# PyXML xml.__name__ is _xmlplus. Check that if we don't have the default
# system version of the minidom, then patch the writexml method
if sys.version_info[:3] < (2, 7, 3) or xml.__name__ != 'xml':
    minidom.Element.writexml = writexml


class XmlJob(object):
    def __init__(self, xml, name):
        self.xml = xml
        self.name = name

    def md5(self):
        return hashlib.md5(self.output()).hexdigest()

    def output(self):
        out = minidom.parseString(XML.tostring(self.xml, encoding='UTF-8'))
        return out.toprettyxml(indent='  ', encoding='utf-8')
