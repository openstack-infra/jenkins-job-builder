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

# Jenkins Job module for job properties
# No additional YAML needed

import xml.etree.ElementTree as XML
import jenkins_jobs.modules.base


def github(parser, xml_parent, data):
    github = XML.SubElement(xml_parent,
               'com.coravy.hudson.plugins.github.GithubProjectProperty')
    github_url = XML.SubElement(github, 'projectUrl')
    github_url.text = data['url']


def throttle(parser, xml_parent, data):
    throttle = XML.SubElement(xml_parent,
                 'hudson.plugins.throttleconcurrents.ThrottleJobProperty')
    XML.SubElement(throttle, 'maxConcurrentPerNode').text = str(
        data.get('max-per-node', '0'))
    XML.SubElement(throttle, 'maxConcurrentTotal').text = str(
        data.get('max-total', '0'))
    # TODO: What's "categories"?
    #XML.SubElement(throttle, 'categories')
    if data.get('enabled', True):
        XML.SubElement(throttle, 'throttleEnabled').text = 'true'
    else:
        XML.SubElement(throttle, 'throttleEnabled').text = 'false'
    XML.SubElement(throttle, 'throttleOption').text = data.get('option')
    XML.SubElement(throttle, 'configVersion').text = '1'

def inject(parser, xml_parent, data):
    inject = XML.SubElement(xml_parent,
                 'EnvInjectJobProperty')
    info = XML.SubElement(inject, 'info')
    XML.SubElement(info, 'propertiesFilePath').text = str(
        data.get('properties-file', ''))
    XML.SubElement(info, 'propertiesContent').text = str(
        data.get('properties-content', ''))
    XML.SubElement(info, 'scriptFilePath').text = str(
        data.get('script-file', ''))
    XML.SubElement(info, 'scriptContent').text = str(
        data.get('script-content', ''))
    XML.SubElement(info, 'groovyScriptContent').text = str(
        data.get('groovy-content', ''))
    XML.SubElement(info, 'loadFilesFromMaster').text = str(
        data.get('load-from-master', 'false')).lower()
    XML.SubElement(inject, 'on').text = str(
        data.get('enabled', 'true')).lower()
    XML.SubElement(inject, 'keepJenkinsSystemVariables').text = str(
        data.get('keep-system-variables', 'true')).lower()
    XML.SubElement(inject, 'keepBuildVariables').text = str(
        data.get('keep-build-variables', 'true')).lower()

def authenticated_build(parser, xml_parent, data):
    # TODO: generalize this
    if data:
        security = XML.SubElement(xml_parent,
                        'hudson.security.AuthorizationMatrixProperty')
        XML.SubElement(security, 'permission').text = \
        'hudson.model.Item.Build:authenticated'


def base_param(parser, xml_parent, data, do_default, ptype):
    pdef = XML.SubElement(xml_parent, ptype)
    XML.SubElement(pdef, 'name').text = data['name']
    XML.SubElement(pdef, 'description').text = data['description']
    if do_default:
        default = data.get('default', None)
        if default:
            XML.SubElement(pdef, 'defaultValue').text = default
        else:
            XML.SubElement(pdef, 'defaultValue')


def string_param(parser, xml_parent, data):
    base_param(parser, xml_parent, data, True,
               'hudson.model.StringParameterDefinition')


def bool_param(parser, xml_parent, data):
    data['default'] = str(data.get('default', 'false')).lower()
    base_param(parser, xml_parent, data, True,
               'hudson.model.BooleanParameterDefinition')


def file_param(parser, xml_parent, data):
    base_param(parser, xml_parent, data, False,
               'hudson.model.FileParameterDefinition')


def text_param(parser, xml_parent, data):
    base_param(parser, xml_parent, data, True,
               'hudson.model.TextParameterDefinition')


def label_param(parser, xml_parent, data):
    base_param(parser, xml_parent, data, True,
      'org.jvnet.jenkins.plugins.nodelabelparameter.LabelParameterDefinition')


def http_endpoint(parser, xml_parent, data):
    endpoint_element = XML.SubElement(xml_parent,
                'com.tikal.hudson.plugins.notification.Endpoint')
    XML.SubElement(endpoint_element, 'protocol').text = 'HTTP'
    XML.SubElement(endpoint_element, 'url').text = data['url']


class Properties(jenkins_jobs.modules.base.Base):
    sequence = 20

    def gen_xml(self, parser, xml_parent, data):
        properties = XML.SubElement(xml_parent, 'properties')

        for prop in data.get('properties', []):
            self._dispatch('property', 'properties',
                           parser, properties, prop)

        parameters = data.get('parameters', [])
        if parameters:
            pdefp = XML.SubElement(properties,
                                   'hudson.model.ParametersDefinitionProperty')
            pdefs = XML.SubElement(pdefp, 'parameterDefinitions')
            for param in parameters:
                self._dispatch('parameter', 'parameters',
                               parser, pdefs, param)

        notifications = data.get('notifications', [])
        if notifications:
            notify_element = XML.SubElement(properties,
            'com.tikal.hudson.plugins.notification.HudsonNotificationProperty')
            endpoints_element = XML.SubElement(notify_element, 'endpoints')

            for endpoint in notifications:
                self._dispatch('notification', 'notifications',
                               parser, endpoints_element, endpoint)
