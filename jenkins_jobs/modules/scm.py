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

# Jenkins Job module for scm
# To use add the folowing into your YAML:
# scm:
#  scm: 'true'
# or
#  scm: 'false'

import xml.etree.ElementTree as XML
import jenkins_jobs.modules.base

def git(self, xml_parent, data):
    scm = XML.SubElement(xml_parent,
                         'scm',{'class':'hudson.plugins.git.GitSCM'})
    XML.SubElement(scm, 'configVersion').text = '2'
    user = XML.SubElement(scm, 'userRemoteConfigs')
    huser = XML.SubElement(user, 'hudson.plugins.git.UserRemoteConfig')
    XML.SubElement(huser, 'name').text = 'origin'
    XML.SubElement(huser, 'refspec').text = \
        '+refs/heads/*:refs/remotes/origin/*'
    XML.SubElement(huser, 'url').text = data['url']
    xml_branches = XML.SubElement(scm, 'branches')
    branches = data.get('branches', ['**'])
    for branch in branches:
        bspec = XML.SubElement(xml_branches, 'hudson.plugins.git.BranchSpec')
        XML.SubElement(bspec, 'name').text = branch
    XML.SubElement(scm, 'disableSubmodules').text = 'false'
    XML.SubElement(scm, 'recursiveSubmodules').text = 'false'
    XML.SubElement(scm, 'doGenerateSubmoduleConfigurations').text = 'false'
    XML.SubElement(scm, 'authorOrCommitter').text = 'false'
    XML.SubElement(scm, 'clean').text = 'false'
    XML.SubElement(scm, 'wipeOutWorkspace').text = 'true'
    XML.SubElement(scm, 'pruneBranches').text = 'false'
    XML.SubElement(scm, 'remotePoll').text = 'false'
    XML.SubElement(scm, 'buildChooser',
                   {'class':'hudson.plugins.git.util.DefaultBuildChooser'})
    XML.SubElement(scm, 'gitTool').text = 'Default'
    XML.SubElement(scm, 'submoduleCfg', {'class':'list'})
    XML.SubElement(scm, 'relativeTargetDir')
    XML.SubElement(scm, 'reference')
    XML.SubElement(scm, 'excludedRegions')
    XML.SubElement(scm, 'excludedUsers')
    XML.SubElement(scm, 'gitConfigName')
    XML.SubElement(scm, 'gitConfigEmail')
    XML.SubElement(scm, 'skipTag').text = 'false'
    XML.SubElement(scm, 'scmName')

class SCM(jenkins_jobs.modules.base.Base):
    sequence = 30

    def gen_xml(self, parser, xml_parent, data):
        scms = data.get('scm', [])
        if scms:
            for scm in data.get('scm', []):
                self._dispatch('scm', 'scm',
                               parser, xml_parent, scm)
        else:
            XML.SubElement(xml_parent, 'scm', {'class':'hudson.scm.NullSCM'})

