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

# Jenkins Job module for gerrit triggers
# To use add the following into your YAML:
# trigger:
#  triggerOnPatchsetUploadedEvent: 'false'
#  triggerOnChangeMergedEvent: 'false'
#  triggerOnCommentAddedEvent: 'true'
#  triggerOnRefUpdatedEvent: 'false'
#  triggerApprovalCategory: 'APRV'
#  triggerApprovalValue: 1
#  overrideVotes: 'true'
#  gerritBuildSuccessfulVerifiedValue: 1
#  gerritBuildFailedVerifiedValue: -1
#  failureMessage: 'This change was unable to be automatically merged with the current state of the repository. Please rebase your change and upload a new patchset.'
#   projects:
#     - projectCompareType: 'PLAIN'
#       projectPattern: 'openstack/nova'
#       branchCompareType: 'ANT'
#       branchPattern: '**'
#     - projectCompareType: 'PLAIN'
#       projectPattern: 'openstack/glance'
#       branchCompareType: 'ANT'
#       branchPattern: '**'
#     ...
#
# triggerApprovalCategory and triggerApprovalValue only required if triggerOnCommentAddedEvent: 'true'

import xml.etree.ElementTree as XML

class trigger_gerrit(object):
    def __init__(self, data):
        self.data = data

    def gen_xml(self, xml_parent):
        trigger_data = self.data['trigger']
        projects = trigger_data['projects']
        trigger = XML.SubElement(xml_parent, 'triggers', {'class':'vector'})
        gtrig = XML.SubElement(trigger, 'com.sonyericsson.hudson.plugins.gerrit.trigger.hudsontrigger.GerritTrigger')
        XML.SubElement(gtrig, 'spec')
        gprojects = XML.SubElement(gtrig, 'gerritProjects')
        for project in projects:
            gproj = XML.SubElement(gprojects, 'com.sonyericsson.hudson.plugins.gerrit.trigger.hudsontrigger.data.GerritProject')
            XML.SubElement(gproj, 'compareType').text = project['projectCompareType']
            XML.SubElement(gproj, 'pattern').text = project['projectPattern']
            branches = XML.SubElement(gproj, 'branches')
            gbranch = XML.SubElement(branches, 'com.sonyericsson.hudson.plugins.gerrit.trigger.hudsontrigger.data.Branch')
            XML.SubElement(gbranch, 'compareType').text = project['branchCompareType']
            XML.SubElement(gbranch, 'pattern').text = project['branchPattern']
        XML.SubElement(gtrig, 'silentMode').text = 'false'
        XML.SubElement(gtrig, 'escapeQuotes').text = 'true'
        XML.SubElement(gtrig, 'triggerOnPatchsetUploadedEvent').text = trigger_data['triggerOnPatchsetUploadedEvent']
        XML.SubElement(gtrig, 'triggerOnChangeMergedEvent').text = trigger_data['triggerOnChangeMergedEvent']
        XML.SubElement(gtrig, 'triggerOnCommentAddedEvent').text = trigger_data['triggerOnCommentAddedEvent']
        XML.SubElement(gtrig, 'triggerOnRefUpdatedEvent').text = trigger_data['triggerOnRefUpdatedEvent']
        if trigger_data.has_key('overrideVotes') and trigger_data['overrideVotes'] == 'true':
            XML.SubElement(gtrig, 'gerritBuildSuccessfulVerifiedValue').text = str(trigger_data['gerritBuildSuccessfulVerifiedValue'])
            XML.SubElement(gtrig, 'gerritBuildFailedVerifiedValue').text = str(trigger_data['gerritBuildFailedVerifiedValue'])
        if trigger_data['triggerOnCommentAddedEvent'] == 'true':
            XML.SubElement(gtrig, 'commentAddedTriggerApprovalCategory').text = trigger_data['triggerApprovalCategory']
            XML.SubElement(gtrig, 'commentAddedTriggerApprovalValue').text = str(trigger_data['triggerApprovalValue'])
        XML.SubElement(gtrig, 'buildStartMessage')
        XML.SubElement(gtrig, 'buildFailureMessage').text = trigger_data['failureMessage']
        XML.SubElement(gtrig, 'buildSuccessfulMessage')
        XML.SubElement(gtrig, 'buildUnstableMessage')
        XML.SubElement(gtrig, 'customUrl')
