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
import re


def gerrit_handle_legacy_configuration(data):
    hyphenizer = re.compile("[A-Z]")

    def hyphenize(attr):
        """Convert strings like triggerOn to trigger-on.
        """
        return hyphenizer.sub(lambda x: "-%s" % x.group(0).lower(),
                              attr)

    def convert_dict(d, old_keys):
        for old_key in old_keys:
            if old_key in d:
                d[hyphenize(old_key)] = d[old_key]
                del d[old_key]

    convert_dict(data, [
        'triggerOnPatchsetUploadedEvent',
        'triggerOnChangeAbandonedEvent',
        'triggerOnChangeMergedEvent',
        'triggerOnChangeRestoredEvent',
        'triggerOnCommentAddedEvent',
        'triggerOnDraftPublishedEvent',
        'triggerOnRefUpdatedEvent',
        'triggerApprovalCategory',
        'triggerApprovalValue',
        'overrideVotes',
        'gerritBuildSuccessfulVerifiedValue',
        'gerritBuildFailedVerifiedValue',
        'failureMessage',
        'skipVote',
    ])
    for project in data['projects']:
        convert_dict(project, [
            'projectCompareType',
            'projectPattern',
            'branchCompareType',
            'branchPattern',
        ])


def build_gerrit_triggers(xml_parent, data):
    available_simple_triggers = {
        'trigger-on-change-abandoned-event': 'PluginChangeAbandonedEvent',
        'trigger-on-change-merged-event': 'PluginChangeMergedEvent',
        'trigger-on-change-restored-event': 'PluginChangeRestoredEvent',
        'trigger-on-draft-published-event': 'PluginDraftPublishedEvent',
        'trigger-on-patchset-uploaded-event': 'PluginPatchsetCreatedEvent',
        'trigger-on-ref-updated-event': 'PluginRefUpdatedEvent',
    }
    tag_namespace = 'com.sonyericsson.hudson.plugins.gerrit.trigger.'   \
        'hudsontrigger.events'

    trigger_on_events = XML.SubElement(xml_parent, 'triggerOnEvents')
    for config_key, tag_name in available_simple_triggers.iteritems():
        if data.get(config_key, False):
            XML.SubElement(trigger_on_events,
                           '%s.%s' % (tag_namespace, tag_name))

    if data.get('trigger-on-comment-added-event', False):
        cadded = XML.SubElement(trigger_on_events,
                                '%s.%s' % (tag_namespace,
                                           'PluginCommentAddedEvent'))
        XML.SubElement(cadded, 'verdictCategory').text = \
            data['trigger-approval-category']
        XML.SubElement(cadded, 'commentAddedTriggerApprovalValue').text = \
            str(data['trigger-approval-value'])


def build_gerrit_skip_votes(xml_parent, data):
    outcomes = {'successful': 'onSuccessful',
                'failed': 'onFailed',
                'unstable': 'onUnstable',
                'notbuilt': 'onNotBuilt'}

    skip_vote_node = XML.SubElement(xml_parent, 'skipVote')
    skip_vote = data.get('skip-vote', {})
    for result_kind, tag_name in outcomes.iteritems():
        if skip_vote.get(result_kind, False):
            XML.SubElement(skip_vote_node, tag_name).text = 'true'
        else:
            XML.SubElement(skip_vote_node, tag_name).text = 'false'


def gerrit(parser, xml_parent, data):
    """yaml: gerrit
    Trigger on a Gerrit event.
    Requires the Jenkins `Gerrit Trigger Plugin
    <wiki.jenkins-ci.org/display/JENKINS/Gerrit+Trigger>`_ version >= 2.6.0.

    :arg bool trigger-on-patchset-uploaded-event: Trigger on patchset upload
    :arg bool trigger-on-change-abandoned-event: Trigger on change abandoned.
        Requires Gerrit Trigger Plugin version >= 2.8.0
    :arg bool trigger-on-change-merged-event: Trigger on change merged
    :arg bool trigger-on-change-restored-event: Trigger on change restored.
        Requires Gerrit Trigger Plugin version >= 2.8.0
    :arg bool trigger-on-comment-added-event: Trigger on comment added
    :arg bool trigger-on-draft-published-event: Trigger on draft published
        event
    :arg bool trigger-on-ref-updated-event: Trigger on ref-updated
    :arg str trigger-approval-category: Approval category for comment added
    :arg int trigger-approval-value: Approval value for comment added
    :arg bool override-votes: Override default vote values
    :arg int gerrit-build-successful-verified-value: Successful ''Verified''
        value
    :arg int gerrit-build-failed-verified-value: Failed ''Verified'' value
    :arg str failure-message: Message to leave on failure
    :arg list projects: list of projects to match

      :Project: * **project-compare-type** (`str`) --  ''PLAIN'', ''ANT'' or
                  ''REG_EXP''
                * **project-pattern** (`str`) -- Project name pattern to match
                * **branch-compare-type** (`str`) -- ''PLAIN'', ''ANT'' or
                  ''REG_EXP''
                * **branch-pattern** (`str`) -- Branch name pattern to match
                * **file-paths** (`list`) -- List of file paths to match
                  (optional)

                  :File Path: * **compare-type** (`str`) -- ''PLAIN'', ''ANT''
                                or ''REG_EXP'' (optional, defaults to
                                ''PLAIN'')
                              * **pattern** (`str`) -- File path pattern to
                                match

    :arg dict skip-vote: map of build outcomes for which Jenkins must skip
        vote. Requires Gerrit Trigger Plugin version >= 2.7.0

        :Outcome: * **successful** (`bool`)
                  * **failed** (`bool`)
                  * **unstable** (`bool`)
                  * **notbuilt** (`bool`)

    You may select one or more gerrit events upon which to trigger.
    You must also supply at least one project and branch, optionally
    more.  If you select the comment-added trigger, you should alse
    indicate which approval category and value you want to trigger the
    job.

    Until version 0.4.0 of Jenkins Job Builder, camelCase keys were used to
    configure Gerrit Trigger Plugin, instead of hyphenated-keys.  While still
    supported, camedCase keys are deprecated and should not be used.

    Example::

      triggers:
        - gerrit:
            trigger-on-comment-added-event: true
            trigger-approval-category: 'APRV'
            trigger-approval-value: 1
            projects:
              - project-compare-type: 'PLAIN'
                project-pattern: 'test-project'
                branch-compare-type: 'ANT'
                branch-pattern: '**'
                file-paths:
                    - compare-type: ANT
                      pattern: subdirectory/**
            skip-vote:
                successful: true
                failed: true
                unstable: true
                notbuilt: true
    """

    gerrit_handle_legacy_configuration(data)

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
            project['project-compare-type']
        XML.SubElement(gproj, 'pattern').text = project['project-pattern']
        branches = XML.SubElement(gproj, 'branches')
        gbranch = XML.SubElement(branches, 'com.sonyericsson.hudson.plugins.'
                                 'gerrit.trigger.hudsontrigger.data.Branch')
        XML.SubElement(gbranch, 'compareType').text = \
            project['branch-compare-type']
        XML.SubElement(gbranch, 'pattern').text = project['branch-pattern']
        project_file_paths = project.get('file-paths', [])
        if project_file_paths:
            fps_tag = XML.SubElement(gproj, 'filePaths')
            for file_path in project_file_paths:
                fp_tag = XML.SubElement(fps_tag,
                                        'com.sonyericsson.hudson.plugins.'
                                        'gerrit.trigger.hudsontrigger.data.'
                                        'FilePath')
                XML.SubElement(fp_tag, 'compareType').text = \
                    file_path.get('compare-type', 'PLAIN')
                XML.SubElement(fp_tag, 'pattern').text = file_path['pattern']
    build_gerrit_skip_votes(gtrig, data)
    XML.SubElement(gtrig, 'silentMode').text = 'false'
    XML.SubElement(gtrig, 'escapeQuotes').text = 'true'
    build_gerrit_triggers(gtrig, data)
    if 'override-votes' in data and data['override-votes'] == 'true':
        XML.SubElement(gtrig, 'gerritBuildSuccessfulVerifiedValue').text = \
            str(data['gerrit-build-successful-verified-value'])
        XML.SubElement(gtrig, 'gerritBuildFailedVerifiedValue').text = \
            str(data['gerrit-build-failed-verified-value'])
    XML.SubElement(gtrig, 'buildStartMessage')
    XML.SubElement(gtrig, 'buildFailureMessage').text = data['failure-message']
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


def github(parser, xml_parent, data):
    """yaml: github
    Trigger a job when github repository is pushed to
    Requires the Jenkins `GitHub Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/GitHub+Plugin>`_

    Example::

      triggers:
        - github
    """
    ghtrig = XML.SubElement(xml_parent, 'com.cloudbees.jenkins.'
                            'GitHubPushTrigger')
    XML.SubElement(ghtrig, 'spec').text = ''


def github_pull_request(parser, xml_parent, data):
    """yaml: github-pull-request
    Build pull requests in github and report results
    Requires the Jenkins `GitHub Pull Request Builder Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/
    GitHub+pull+request+builder+plugin>`_

    :arg list admin-list: the users with admin rights (optional)
    :arg string cron: cron syntax of when to run (optional)
    :arg list white-list: users whose pull requests build (optional)
    :arg list org-list: orgs whose users should be white listed (optional)

    Example::

      triggers:
        - github-pull-request:
            admin-list:
              - user1
              - user2
            cron: * * * * *
            white-list:
              - user3
              - user4
            org-list:
              - org1
              - org2
    """
    ghprb = XML.SubElement(xml_parent, 'org.jenkinsci.plugins.ghprb.'
                           'GhprbTrigger')
    XML.SubElement(ghprb, 'spec').text = data.get('cron', '')
    admin_string = "\n".join(data.get('admin-list', []))
    XML.SubElement(ghprb, 'adminlist').text = admin_string
    white_string = "\n".join(data.get('white-list', []))
    XML.SubElement(ghprb, 'whitelist').text = white_string
    org_string = "\n".join(data.get('org-list', []))
    XML.SubElement(ghprb, 'orgslist').text = org_string
    XML.SubElement(ghprb, 'cron').text = data.get('cron', '')


class Triggers(jenkins_jobs.modules.base.Base):
    sequence = 50

    component_type = 'trigger'
    component_list_type = 'triggers'

    def gen_xml(self, parser, xml_parent, data):
        triggers = data.get('triggers', [])
        if not triggers:
            return

        trig_e = XML.SubElement(xml_parent, 'triggers', {'class': 'vector'})
        for trigger in triggers:
            self.registry.dispatch('trigger', parser, trig_e, trigger)
