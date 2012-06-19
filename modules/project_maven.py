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
    mod = Maven()
    registry.registerModule(mod)


class Maven(object):
    sequence = 0

    def root_xml(self, data):
        if 'maven' not in data:
            return None
        xml_parent = XML.Element('maven2-moduleset')
        root_module = XML.SubElement(xml_parent, 'root_module')
        XML.SubElement(root_module, 'groupId').text = data['maven']['root_module']['group_id']
        XML.SubElement(root_module, 'artifactId').text = data['maven']['root_module']['artifact_id']
        XML.SubElement(xml_parent, 'goals').text = data['maven']['goals']

        XML.SubElement(xml_parent, 'aggregatorStyleBuild').text = 'true'
        XML.SubElement(xml_parent, 'incrementalBuild').text = 'false'
        XML.SubElement(xml_parent, 'perModuleEmail').text = 'true'
        XML.SubElement(xml_parent, 'ignoreUpstremChanges').text = 'true'
        XML.SubElement(xml_parent, 'archivingDisabled').text = 'false'
        XML.SubElement(xml_parent, 'resolveDependencies').text = 'false'
        XML.SubElement(xml_parent, 'processPlugins').text = 'false'
        XML.SubElement(xml_parent, 'mavenValidationLevel').text = '-1'
        XML.SubElement(xml_parent, 'runHeadless').text = 'false'
        XML.SubElement(xml_parent, 'settingConfigId')
        XML.SubElement(xml_parent, 'globalSettingConfigId')

        run_post_steps = XML.SubElement(xml_parent, 'runPostStepsIfResult')
        XML.SubElement(run_post_steps, 'name').text = 'FAILURE'
        XML.SubElement(run_post_steps, 'ordinal').text = '2'
        XML.SubElement(run_post_steps, 'color').text = 'red'

        return xml_parent
