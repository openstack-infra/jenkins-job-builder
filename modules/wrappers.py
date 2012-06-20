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

def register(registry):
    mod = Wrappers()
    registry.registerModule(mod)


class Wrappers(object):
    sequence = 80

    def gen_xml(self, xml_parent, data):
        wrappers = XML.SubElement(xml_parent, 'buildWrappers')

        if 'timeout' in data['main']:
            self._timeout(wrappers, data)
        if 'ansicolor' in data['main']:
            self._ansicolor(wrappers, data)
        if 'timestamps' in data['main']:
            self._timestamps(wrappers, data)

    def _timeout(self, xml_parent, data):
        twrapper = XML.SubElement(xml_parent, 'hudson.plugins.build__timeout.BuildTimeoutWrapper')
        tminutes = XML.SubElement(twrapper, 'timeoutMinutes')
        tminutes.text = str(data['main']['timeout'])
        failbuild = XML.SubElement(twrapper, 'failBuild')
        fail = data['main'].get('timeout_fail', False)
        if fail:
            failbuild.text = 'true'
        else:
            failbuild.text = 'false'

    def _timestamps(self, xml_parent, data):
        XML.SubElement(xml_parent, 'hudson.plugins.timestamper.TimestamperBuildWrapper')

    def _ansicolor(self, xml_parent, data):
        XML.SubElement(xml_parent, 'hudson.plugins.ansicolor.AnsiColorBuildWrapper')
