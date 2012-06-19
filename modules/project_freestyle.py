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

# Jenkins Job module for maven projects
# To use you add the following into your YAML:
# maven:
#   root_module:
#     group_id: com.google.gerrit
#     artifact_id: gerrit-parent
#   goals: 'test'

import xml.etree.ElementTree as XML


def register(registry):
    mod = Freestyle()
    registry.registerModule(mod)


class Freestyle(object):
    sequence = 0

    def root_xml(self, data):
        if 'maven' in data:
            return None
        xml_parent = XML.Element('project')
        return xml_parent
