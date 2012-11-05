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


"""
Triggers define what causes a jenkins job to start buliding.

**Component**: triggers
  :Macro: trigger
  :Entry Point: jenkins_jobs.triggers

Example::

  job:
    name: test_job

    triggers:
      - timed: '@daily'
"""


import xml.etree.ElementTree as XML
import jenkins_jobs.modules.base


def gerrit(parser, xml_parent, data):
    """yaml: gerrit
    Trigger on a Gerrit event.
    Requires the Jenkins `Gerrit Trigger Plugin.
    <wiki.jenkins-ci.org/display/JENKINS/Gerrit+Trigger>`_

    :arg bool triggerOnPatchsetUploadedEvent: Trigger on patchset upload
    :arg bool triggerOnChangeMergedEvent: Trigger on change merged
    :arg bool triggerOnCommentAddedEvent: Trigger on comment added
    :arg bool triggerOnRefUpdatedEvent: Trigger on ref-updated
    :arg str triggerApprovalCategory: Approval category for comment added
    :arg int triggerApprovalValue: Approval value for comment added
    :arg bool overrideVotes: Override default vote values
    :arg int gerritBuildSuccessfulVerifiedValue: Successful ''Verified'' value
    :arg int gerritBuildFailedVerifiedValue: Failed ''Verified'' value
    :arg str failureMessage: Message to leave on failure
    :arg list projects: list of projects to match

      :Project: * **projectCompareType** (`str`) --  ''PLAIN'' or ''ANT''
                * **projectPattern** (`str`) -- Project name pattern to match
                * **branchComprareType** (`str`) -- ''PLAIN'' or ''ANT''
                * **branchPattern** ('str') -- Branch name pattern to match

    You may select one or more gerrit events upon which to trigger.
    You must also supply at least one project and branch, optionally
    more.  If you select the comment-added trigger, you should alse
    indicate which approval category and value you want to trigger the
    job.

    Example::

      triggers:
        - gerrit:
            triggerOnCommentAddedEvent: true
            triggerApprovalCategory: 'APRV'
            triggerApprovalValue: 1
            projects:
              - projectCompareType: 'PLAIN'
                projectPattern: 'test-project'
                branchCompareType: 'ANT'
                branchPattern: '**'
    """

    projects = data['projects']
    gtrig = XML.SubElement(xml_parent,
                           'com.sonyericsson.hudson.plugins.gerrit.trigger.'
                           'hudsontrigger.GerritTrigger')
    XML.SubElement(gtrig, 'spec')
    gprojects = XML.SubElement(gtrig, 'gerritProjects')
    for project in projects:
        gproj = XML.SubElement(gprojects,
                               'com.sonyericsson.hudson.plugins.gerrit.'
                               'trigger.hudsontrigger.data.GerritProject')
        XML.SubElement(gproj, 'compareType').text = \
            project['projectCompareType']
        XML.SubElement(gproj, 'pattern').text = project['projectPattern']
        branches = XML.SubElement(gproj, 'branches')
        gbranch = XML.SubElement(branches, 'com.sonyericsson.hudson.plugins.'
                                 'gerrit.trigger.hudsontrigger.data.Branch')
        XML.SubElement(gbranch, 'compareType').text = \
            project['branchCompareType']
        XML.SubElement(gbranch, 'pattern').text = project['branchPattern']
    XML.SubElement(gtrig, 'silentMode').text = 'false'
    XML.SubElement(gtrig, 'escapeQuotes').text = 'true'
    XML.SubElement(gtrig, 'triggerOnPatchsetUploadedEvent').text = \
        data['triggerOnPatchsetUploadedEvent']
    XML.SubElement(gtrig, 'triggerOnChangeMergedEvent').text = \
        data['triggerOnChangeMergedEvent']
    XML.SubElement(gtrig, 'triggerOnCommentAddedEvent').text = \
        data['triggerOnCommentAddedEvent']
    XML.SubElement(gtrig, 'triggerOnRefUpdatedEvent').text = \
        data['triggerOnRefUpdatedEvent']
    if 'overrideVotes' in data and data['overrideVotes'] == 'true':
        XML.SubElement(gtrig, 'gerritBuildSuccessfulVerifiedValue').text = \
            str(data['gerritBuildSuccessfulVerifiedValue'])
        XML.SubElement(gtrig, 'gerritBuildFailedVerifiedValue').text = \
            str(data['gerritBuildFailedVerifiedValue'])
    if data['triggerOnCommentAddedEvent'] == 'true':
        XML.SubElement(gtrig, 'commentAddedTriggerApprovalCategory').text = \
            data['triggerApprovalCategory']
        XML.SubElement(gtrig, 'commentAddedTriggerApprovalValue').text = \
            str(data['triggerApprovalValue'])
    XML.SubElement(gtrig, 'buildStartMessage')
    XML.SubElement(gtrig, 'buildFailureMessage').text = data['failureMessage']
    XML.SubElement(gtrig, 'buildSuccessfulMessage')
    XML.SubElement(gtrig, 'buildUnstableMessage')
    XML.SubElement(gtrig, 'customUrl')


def pollscm(parser, xml_parent, data):
    """yaml: pollscm
    Poll the SCM to determine if there has been a change.

    :Parameter: the polling interval (cron syntax)

    Example::

      triggers:
        - pollscm: "\*/15 * * * \*"
    """

    scmtrig = XML.SubElement(xml_parent, 'hudson.triggers.SCMTrigger')
    XML.SubElement(scmtrig, 'spec').text = data


def timed(parser, xml_parent, data):
    """yaml: timed
    Trigger builds at certain times.

    :Parameter: when to run the job (cron syntax)

    Example::

      triggers:
        - timed: "@midnight"
    """
    scmtrig = XML.SubElement(xml_parent, 'hudson.triggers.TimerTrigger')
    XML.SubElement(scmtrig, 'spec').text = data


class Triggers(jenkins_jobs.modules.base.Base):
    sequence = 50

    def gen_xml(self, parser, xml_parent, data):
        triggers = data.get('triggers', [])
        if not triggers:
            return

        trig_e = XML.SubElement(xml_parent, 'triggers', {'class': 'vector'})
        for trigger in triggers:
            self._dispatch('trigger', 'triggers',
                           parser, trig_e, trigger)
