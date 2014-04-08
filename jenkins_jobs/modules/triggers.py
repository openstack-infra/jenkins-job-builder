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
Triggers define what causes a Jenkins job to start building.

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
    :arg int gerrit-build-successful-codereview-value: Successful
        ''CodeReview'' value
    :arg int gerrit-build-failed-codereview-value: Failed ''CodeReview'' value
    :arg str failure-message: Message to leave on failure (default '')
    :arg str successful-message: Message to leave on success (default '')
    :arg str unstable-message: Message to leave when unstable (default '')
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

    :arg bool silent:  When silent mode is on there will be no communication
        back to Gerrit, i.e. no build started/failed/successful approve
        messages etc. If other non-silent jobs are triggered by the same
        Gerrit event as this job, the result of this job's build will not be
        counted in the end result of the other jobs. (default false)
    :arg bool escape-quotes: escape quotes in the values of Gerrit change
        parameters (default true)
    :arg bool no-name-and-email: Do not pass compound 'name and email'
        parameters (default false)
    :arg bool dynamic-trigger-enabled: Enable/disable the dynamic trigger
        (default false)
    :arg str dynamic-trigger-url: if you specify this option, the Gerrit
        trigger configuration will be fetched from there on a regular interval
    :arg str custom-url: Custom URL for a message sent to Gerrit. Build
        details URL will be used if empty. (default '')

    You may select one or more Gerrit events upon which to trigger.
    You must also supply at least one project and branch, optionally
    more.  If you select the comment-added trigger, you should also
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
            silent: false
            escape-quotes: false
            no-name-and-email: false
            dynamic-trigger-enabled: true
            dynamic-trigger-url: http://myhost/mytrigger
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
    XML.SubElement(gtrig, 'silentMode').text = str(
        data.get('silent', False)).lower()
    XML.SubElement(gtrig, 'escapeQuotes').text = str(
        data.get('escape-quotes', True)).lower()
    XML.SubElement(gtrig, 'noNameAndEmailParameters').text = str(
        data.get('no-name-and-email', False)).lower()
    XML.SubElement(gtrig, 'dynamicTriggerConfiguration').text = str(
        data.get('dynamic-trigger-enabled', False))
    XML.SubElement(gtrig, 'triggerConfigURL').text = str(
        data.get('dynamic-trigger-url', ''))
    build_gerrit_triggers(gtrig, data)
    override = str(data.get('override-votes', False)).lower()
    if override == 'true':
        for yamlkey, xmlkey in [('gerrit-build-successful-verified-value',
                                 'gerritBuildSuccessfulVerifiedValue'),
                                ('gerrit-build-failed-verified-value',
                                 'gerritBuildFailedVerifiedValue'),
                                ('gerrit-build-successful-codereview-value',
                                 'gerritBuildSuccessfulCodereviewValue'),
                                ('gerrit-build-failed-codereview-value',
                                 'gerritBuildFaiedCodeReviewValue')]:
            if data.get(yamlkey) is not None:
                # str(int(x)) makes input values like '+1' work
                XML.SubElement(gtrig, xmlkey).text = str(
                    int(data.get(yamlkey)))
    XML.SubElement(gtrig, 'buildStartMessage').text = str(
        data.get('start-message', ''))
    XML.SubElement(gtrig, 'buildFailureMessage').text = \
        data.get('failure-message', '')
    XML.SubElement(gtrig, 'buildSuccessfulMessage').text = str(
        data.get('successful-message', ''))
    XML.SubElement(gtrig, 'buildUnstableMessage').text = str(
        data.get('unstable-message', ''))
    XML.SubElement(gtrig, 'customUrl').text = str(data.get('custom-url', ''))


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
    Trigger a job when github repository is pushed to.
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
    Build pull requests in github and report results.
    Requires the Jenkins `GitHub Pull Request Builder Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/
    GitHub+pull+request+builder+plugin>`_

    :arg list admin-list: the users with admin rights (optional)
    :arg list white-list: users whose pull requests build (optional)
    :arg list org-list: orgs whose users should be white listed (optional)
    :arg string cron: cron syntax of when to run (optional)
    :arg string trigger-phrase: when filled, commenting this phrase
        in the pull request will trigger a build (optional)
    :arg bool only-trigger-phrase: only commenting the trigger phrase
        in the pull request will trigger a build (default false)
    :arg bool github-hooks: use github hook (default false)
    :arg bool permit-all: build every pull request automatically
        without asking (default false)
    :arg bool auto-close-on-fail: close failed pull request automatically
        (default false)

    Example:

    .. literalinclude:: /../../tests/triggers/fixtures/github-pull-request.yaml
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
    XML.SubElement(ghprb, 'triggerPhrase').text = \
        data.get('trigger-phrase', '')
    XML.SubElement(ghprb, 'onlyTriggerPhrase').text = str(
        data.get('only-trigger-phrase', False)).lower()
    XML.SubElement(ghprb, 'useGitHubHooks').text = str(
        data.get('github-hooks', False)).lower()
    XML.SubElement(ghprb, 'permitAll').text = str(
        data.get('permit-all', False)).lower()
    XML.SubElement(ghprb, 'autoCloseFailedPullRequests').text = str(
        data.get('auto-close-on-fail', False)).lower()


def build_result(parser, xml_parent, data):
    """yaml: build-result
    Configure jobB to monitor jobA build result. A build is scheduled if there
    is a new build result that matches your criteria (unstable, failure, ...).
    Requires the Jenkins `BuildResultTrigger Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/BuildResultTrigger+Plugin>`_

    :arg list groups: List groups of jobs and results to monitor for
    :arg list jobs: The jobs to monitor (required)
    :arg list results: Build results to monitor for (default success)
    :arg bool combine: Combine all job information.  A build will be
        scheduled only if all conditions are met (default false)
    :arg str cron: The cron syntax with which to poll the jobs for the
        supplied result (default '')

    Example::

      triggers:
        - build-result:
            combine: true
            cron: '* * * * *'
            groups:
              - jobs:
                  - foo
                  - example
                results:
                  - unstable
              - jobs:
                  - foo2
                results:
                  - not-built
                  - aborted
    """
    brt = XML.SubElement(xml_parent, 'org.jenkinsci.plugins.'
                         'buildresulttrigger.BuildResultTrigger')
    XML.SubElement(brt, 'spec').text = data.get('cron', '')
    XML.SubElement(brt, 'combinedJobs').text = str(
        data.get('combine', False)).lower()
    jobs_info = XML.SubElement(brt, 'jobsInfo')
    result_dict = {'success': 'SUCCESS',
                   'unstable': 'UNSTABLE',
                   'failure': 'FAILURE',
                   'not-built': 'NOT_BUILT',
                   'aborted': 'ABORTED'}
    for group in data['groups']:
        brti = XML.SubElement(jobs_info, 'org.jenkinsci.plugins.'
                              'buildresulttrigger.model.'
                              'BuildResultTriggerInfo')
        if not group.get('jobs', []):
            raise jenkins_jobs.errors.\
                JenkinsJobsException('Jobs is missing and a required'
                                     ' element')
        jobs_string = ",".join(group['jobs'])
        XML.SubElement(brti, 'jobNames').text = jobs_string
        checked_results = XML.SubElement(brti, 'checkedResults')
        for result in group.get('results', ['success']):
            if result not in result_dict:
                raise jenkins_jobs.errors.\
                    JenkinsJobsException('Result entered is not valid,'
                                         ' must be one of: '
                                         + ', '.join(result_dict.keys()))
            model_checked = XML.SubElement(checked_results, 'org.jenkinsci.'
                                           'plugins.buildresulttrigger.model.'
                                           'CheckedResult')
            XML.SubElement(model_checked, 'checked').text = result_dict[result]


def script(parser, xml_parent, data):
    """yaml: script
    Triggers the job using shell or batch script.
    Requires the Jenkins `ScriptTrigger Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/ScriptTrigger+Plugin>`_

    :arg str label: Restrict where the polling should run. (default '')
    :arg str script: A shell or batch script. (default '')
    :arg str cron: cron syntax of when to run (default '')
    :arg bool enable-concurrent:  Enables triggering concurrent builds.
                                  (default false)
    :arg int exit-code:  If the exit code of the script execution returns this
                         expected exit code, a build is scheduled. (default 0)

    Example:

    .. literalinclude:: /../../tests/triggers/fixtures/script.yaml
    """
    data = data if data else {}
    st = XML.SubElement(
        xml_parent,
        'org.jenkinsci.plugins.scripttrigger.ScriptTrigger'
    )
    label = data.get('label')

    XML.SubElement(st, 'script').text = str(data.get('script', ''))
    XML.SubElement(st, 'scriptFilePath').text = str(
        data.get('script-file-path', ''))
    XML.SubElement(st, 'spec').text = str(data.get('cron', ''))
    XML.SubElement(st, 'labelRestriction').text = str(bool(label)).lower()
    if label:
        XML.SubElement(st, 'triggerLabel').text = label
    XML.SubElement(st, 'enableConcurrentBuild').text = str(
        data.get('enable-concurrent', False)).lower()
    XML.SubElement(st, 'exitCode').text = str(data.get('exit-code', 0))


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
