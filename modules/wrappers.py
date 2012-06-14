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

# Jenkins Job module for wrappers

import xml.etree.ElementTree as XML

class wrappers(object):
    def __init__(self, data):
        self.data = data

    def gen_xml(self, xml_parent):
        publishers = XML.SubElement(xml_parent, 'buildWrappers')

        if 'timeout' in self.data['main']:
            self._timeout(publishers)
        if 'timestamps' in self.data['main']:
            self._timestamps(publishers)

    def _timeout(self, xml_parent):
        twrapper = XML.SubElement(xml_parent, 'hudson.plugins.build__timeout.BuildTimeoutWrapper')
        tminutes = XML.SubElement(twrapper, 'timeoutMinutes')
        tminutes.text = str(self.data['main']['timeout'])
        failbuild = XML.SubElement(twrapper, 'failBuild')
        fail = self.data['main'].get('timeout_fail', False)
        if fail:
            failbuild.text = 'true'
        else:
            failbuild.text = 'false'

    def _timestamps(self, xml_parent):
        XML.SubElement(xml_parent, 'hudson.plugins.timestamper.TimestamperBuildWrapper')
