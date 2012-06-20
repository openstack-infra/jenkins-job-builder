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


def register(registry):
    mod = Triggers(registry)
    registry.registerModule(mod)


class Triggers(object):
    sequence = 50

    def __init__(self, registry):
        self.registry = registry
        for f in dir(self):
            if not f.startswith('_trigger_'):
                continue
            self.registry.registerHandler('trigger', f[len('_trigger_'):],
                                          getattr(self, f))

    def handle_data(self, data):
        self.data = data

    def gen_xml(self, xml_parent, data):
        actions = self.data.get('triggers', [])
        if not actions:
            return
        triggers = XML.SubElement(xml_parent, 'triggers', {'class':'vector'})
        for action in actions:
            if isinstance(action, dict):
                for key, value in action.items():
                    func = self.registry.getHandler('trigger', key)
                    func(triggers, value)
            else:
                func = self.registry.getHandler('trigger', action)
                func(triggers)

    def _trigger_gerrit(self, xml_parent, data):
        projects = data['projects']
        gtrig = XML.SubElement(xml_parent, 'com.sonyericsson.hudson.plugins.gerrit.trigger.hudsontrigger.GerritTrigger')
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
        XML.SubElement(gtrig, 'triggerOnPatchsetUploadedEvent').text = data['triggerOnPatchsetUploadedEvent']
        XML.SubElement(gtrig, 'triggerOnChangeMergedEvent').text = data['triggerOnChangeMergedEvent']
        XML.SubElement(gtrig, 'triggerOnCommentAddedEvent').text = data['triggerOnCommentAddedEvent']
        XML.SubElement(gtrig, 'triggerOnRefUpdatedEvent').text = data['triggerOnRefUpdatedEvent']
        if data.has_key('overrideVotes') and data['overrideVotes'] == 'true':
            XML.SubElement(gtrig, 'gerritBuildSuccessfulVerifiedValue').text = str(data['gerritBuildSuccessfulVerifiedValue'])
            XML.SubElement(gtrig, 'gerritBuildFailedVerifiedValue').text = str(data['gerritBuildFailedVerifiedValue'])
        if data['triggerOnCommentAddedEvent'] == 'true':
            XML.SubElement(gtrig, 'commentAddedTriggerApprovalCategory').text = data['triggerApprovalCategory']
            XML.SubElement(gtrig, 'commentAddedTriggerApprovalValue').text = str(data['triggerApprovalValue'])
        XML.SubElement(gtrig, 'buildStartMessage')
        XML.SubElement(gtrig, 'buildFailureMessage').text = data['failureMessage']
        XML.SubElement(gtrig, 'buildSuccessfulMessage')
        XML.SubElement(gtrig, 'buildUnstableMessage')
        XML.SubElement(gtrig, 'customUrl')

    # Jenkins Job module for scm polling triggers
    # To use add the following into your YAML:
    # trigger:
    #   pollscm: '@midnight'
    # or
    #   pollscm: '*/15 * * * *'

    def _trigger_pollscm(self, xml_parent, data):
        scmtrig = XML.SubElement(xml_parent, 'hudson.triggers.SCMTrigger')
        XML.SubElement(scmtrig, 'spec').text = data

    # Jenkins Job module for timed triggers
    # To use add the following into your YAML:
    # trigger:
    #   timed: '@midnight'
    # or
    #   timed: '*/15 * * * *'

    def _trigger_timed(self, xml_parent, data):
        scmtrig = XML.SubElement(xml_parent, 'hudson.triggers.TimerTrigger')
        XML.SubElement(scmtrig, 'spec').text = data
