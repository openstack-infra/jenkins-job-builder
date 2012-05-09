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

class properties(object):
    def __init__(self, data):
        self.data = data

    def gen_xml(self, xml_parent):
        main = self.data['main']
        properties = XML.SubElement(xml_parent, 'properties')
        github = XML.SubElement(properties, 'com.coravy.hudson.plugins.github.GithubProjectProperty')
        github_url = XML.SubElement(github, 'projectUrl')
        github_url.text = "https://github.com/{site}/{project}".format(site=main['site'], project=main['project'])
        throttle = XML.SubElement(properties, 'hudson.plugins.throttleconcurrents.ThrottleJobProperty')
        XML.SubElement(throttle, 'maxConcurrentPerNode').text = '0'
        XML.SubElement(throttle, 'maxConcurrentTotal').text = '0'
        #XML.SubElement(throttle, 'categories')
        XML.SubElement(throttle, 'throttleEnabled').text = 'false'
        XML.SubElement(throttle, 'throttleOption').text = 'project'
        XML.SubElement(throttle, 'configVersion').text = '1'
        env = XML.SubElement(properties, 'EnvInjectJobProperty')
        einfo = XML.SubElement(env, 'info')
        eiproperties = XML.SubElement(einfo, 'propertiesContent')
        eiproperties.text = 'PROJECT={project}'.format(project=main['project'])
        XML.SubElement(einfo, 'loadFilesFromMaster').text = 'false'
        XML.SubElement(env, 'on').text = 'true'
        XML.SubElement(env, 'keepJenkinsSystemVariables').text = 'true'
        XML.SubElement(env, 'keepBuildVariables').text = 'true'
        XML.SubElement(env, 'contributors')
        if main.has_key('authenticatedBuild') and main['authenticatedBuild'] == 'true':
            security = XML.SubElement(properties, 'hudson.security.AuthorizationMatrixProperty')
            XML.SubElement(security, 'permission').text = 'hudson.model.Item.Build:authenticated'
