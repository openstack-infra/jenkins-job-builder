# Copyright 2012 Hewlett-Packard Development Company, L.P.
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
import jenkins_jobs.modules.base


def timeout(parser, xml_parent, data):
    twrapper = XML.SubElement(xml_parent,
        'hudson.plugins.build__timeout.BuildTimeoutWrapper')
    tminutes = XML.SubElement(twrapper, 'timeoutMinutes')
    tminutes.text = str(data['timeout'])
    failbuild = XML.SubElement(twrapper, 'failBuild')
    fail = data.get('fail', False)
    if fail:
        failbuild.text = 'true'
    else:
        failbuild.text = 'false'


def timestamps(parser, xml_parent, data):
    XML.SubElement(xml_parent,
                   'hudson.plugins.timestamper.TimestamperBuildWrapper')


def ansicolor(parser, xml_parent, data):
    XML.SubElement(xml_parent,
                   'hudson.plugins.ansicolor.AnsiColorBuildWrapper')


class Wrappers(jenkins_jobs.modules.base.Base):
    sequence = 80

    def gen_xml(self, parser, xml_parent, data):
        wrappers = XML.SubElement(xml_parent, 'buildWrappers')

        for wrap in data.get('wrappers', []):
            self._dispatch('wrapper', 'wrappers',
                           parser, wrappers, wrap)
