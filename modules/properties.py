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

# Jenkins Job module for job properties
# No additional YAML needed

import xml.etree.ElementTree as XML


def register(registry):
    mod = Properties()
    registry.registerModule(mod)


class Properties(object):
    sequence = 20

    def handle_data(self, data):
        self.data = data

    def gen_xml(self, xml_parent, data):
        main = self.data['main']
        properties = XML.SubElement(xml_parent, 'properties')
        if main.get('project'):
            github = XML.SubElement(properties, 'com.coravy.hudson.plugins.github.GithubProjectProperty')
            github_url = XML.SubElement(github, 'projectUrl')
            github_url.text = "https://github.com/{org}/{project}".format(
                org=main['github_org'], project=main['project'])
        throttle = XML.SubElement(properties, 'hudson.plugins.throttleconcurrents.ThrottleJobProperty')
        XML.SubElement(throttle, 'maxConcurrentPerNode').text = '0'
        XML.SubElement(throttle, 'maxConcurrentTotal').text = '0'
        #XML.SubElement(throttle, 'categories')
        XML.SubElement(throttle, 'throttleEnabled').text = 'false'
        XML.SubElement(throttle, 'throttleOption').text = 'project'
        XML.SubElement(throttle, 'configVersion').text = '1'
        if main.has_key('authenticatedBuild') and main['authenticatedBuild'] == 'true':
            security = XML.SubElement(properties, 'hudson.security.AuthorizationMatrixProperty')
            XML.SubElement(security, 'permission').text = 'hudson.model.Item.Build:authenticated'
        self.do_parameters(properties)
        self.do_notifications(properties)

    parameter_types = {
        'string': 'hudson.model.StringParameterDefinition',
        'bool': 'hudson.model.BooleanParameterDefinition',
        'file': 'hudson.model.FileParameterDefinition',
        'text': 'hudson.model.TextParameterDefinition',
        # Others require more work
        }

    def do_parameters(self, xml_parent):
        params = self.data.get('parameters', None)
        if not params:
            return
        pdefp = XML.SubElement(xml_parent, 'hudson.model.ParametersDefinitionProperty')
        pdefs = XML.SubElement(pdefp, 'parameterDefinitions')
        for param in params:
            ptype = self.parameter_types.get(param['type'])
            pdef = XML.SubElement(pdefs, ptype)
            XML.SubElement(pdef, 'name').text = param['name']
            XML.SubElement(pdef, 'description').text = param['description']
            if param['type'] != 'file':
                default = param.get('default', None)
                if default:
                    XML.SubElement(pdef, 'defaultValue').text = default
                else:
                    XML.SubElement(pdef, 'defaultValue')

    def do_notifications(self, xml_parent):
        endpoints = self.data.get('notification_endpoints', None)
        if not endpoints:
            return
        notify_element = XML.SubElement(xml_parent, 'com.tikal.hudson.plugins.notification.HudsonNotificationProperty')
        endpoints_element = XML.SubElement(notify_element, 'endpoints')
        for ep in endpoints:
            endpoint_element = XML.SubElement(endpoints_element, 'com.tikal.hudson.plugins.notification.Endpoint')
            XML.SubElement(endpoint_element, 'protocol').text = ep['protocol']
            XML.SubElement(endpoint_element, 'url').text = ep['URL']
