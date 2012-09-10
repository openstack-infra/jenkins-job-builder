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

# Jenkins Job module for builders
# To use add the folowing into your YAML:
# builders:
#   - 'gerrit_git_prep'
#   - 'python26'

import xml.etree.ElementTree as XML
import jenkins_jobs.modules.base


def shell(parser, xml_parent, data):
    shell = XML.SubElement(xml_parent, 'hudson.tasks.Shell')
    XML.SubElement(shell, 'command').text = data


def trigger_builds(parser, xml_parent, data):
    tbuilder = XML.SubElement(xml_parent,
                   'hudson.plugins.parameterizedtrigger.TriggerBuilder')
    configs = XML.SubElement(tbuilder, 'configs')
    for project_def in data:
        tconfig = XML.SubElement(configs,
            'hudson.plugins.parameterizedtrigger.BlockableBuildTriggerConfig')
        tconfigs = XML.SubElement(tconfig, 'configs')
        if 'predefined-parameters' in project_def:
            params = XML.SubElement(tconfigs,
              'hudson.plugins.parameterizedtrigger.PredefinedBuildParameters')
            properties = XML.SubElement(params, 'properties')
            properties.text = project_def['predefined-parameters']
        if(project_def.get('current-parameters')):
            XML.SubElement(tconfigs, 
                 'hudson.plugins.parameterizedtrigger.CurrentBuildParameters')
        if(len(list(tconfigs)) == 0):
            tconfigs.set('class', 'java.util.Collections$EmptyList')
        projects = XML.SubElement(tconfig, 'projects')
        projects.text = project_def['project']
        condition = XML.SubElement(tconfig, 'condition')
        condition.text = 'ALWAYS'
        trigger_with_no_params = XML.SubElement(tconfig,
                                                'triggerWithNoParameters')
        trigger_with_no_params.text = 'false'
        build_all_nodes_with_label = XML.SubElement(tconfig,
                                                    'buildAllNodesWithLabel')
        build_all_nodes_with_label.text = 'false'

def builders_from(parser, xml_parent, data):
    pbs = XML.SubElement(xml_parent, 
        'hudson.plugins.templateproject.ProxyBuilder')
    XML.SubElement(pbs, 'projectName').text = data

class Builders(jenkins_jobs.modules.base.Base):
    sequence = 60

    def gen_xml(self, parser, xml_parent, data):
        for alias in ['prebuilders', 'builders', 'postbuilders']:
            if alias in data:
                builders = XML.SubElement(xml_parent, alias)
                for builder in data[alias]:
                    self._dispatch('builder', 'builders',
                                   parser, builders, builder)
