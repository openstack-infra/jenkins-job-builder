# Copyright 2012 Hewlett-Packard Development Company, L.P.
# Copyright 2012 Varnish Software AS
# Copyright 2013-2014 Antoine "hashar" Musso
# Copyright 2013-2014 Wikimedia Foundation Inc.
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
Publishers define actions that the Jenkins job should perform after
the build is complete.

**Component**: publishers
  :Macro: publisher
  :Entry Point: jenkins_jobs.publishers
"""


import xml.etree.ElementTree as XML
import jenkins_jobs.modules.base
from jenkins_jobs.modules import hudson_model
from jenkins_jobs.errors import JenkinsJobsException
import logging
import sys
import random


def archive(parser, xml_parent, data):
    """yaml: archive
    Archive build artifacts

    :arg str artifacts: path specifier for artifacts to archive
    :arg str excludes: path specifier for artifacts to exclude
    :arg bool latest-only: only keep the artifacts from the latest
      successful build
    :arg bool allow-empty:  pass the build if no artifacts are
      found (default false)

    Example:

    .. literalinclude::  /../../tests/publishers/fixtures/archive001.yaml

    """
    logger = logging.getLogger("%s:archive" % __name__)
    archiver = XML.SubElement(xml_parent, 'hudson.tasks.ArtifactArchiver')
    artifacts = XML.SubElement(archiver, 'artifacts')
    artifacts.text = data['artifacts']
    if 'excludes' in data:
        excludes = XML.SubElement(archiver, 'excludes')
        excludes.text = data['excludes']
    latest = XML.SubElement(archiver, 'latestOnly')
    # backward compatibility
    latest_only = data.get('latest_only', False)
    if 'latest_only' in data:
        logger.warn('latest_only is deprecated please use latest-only')
    if 'latest-only' in data:
        latest_only = data['latest-only']
    if latest_only:
        latest.text = 'true'
    else:
        latest.text = 'false'

    if 'allow-empty' in data:
        empty = XML.SubElement(archiver, 'allowEmptyArchive')
        # Default behavior is to fail the build.
        empty.text = str(data.get('allow-empty', False)).lower()


def blame_upstream(parser, xml_parent, data):
    """yaml: blame-upstream
    Notify upstream commiters when build fails
    Requires the Jenkins `Blame upstream commiters Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/
    Blame+Upstream+Committers+Plugin>`_

    Example:

    .. literalinclude::  /../../tests/publishers/fixtures/blame001.yaml

    """

    XML.SubElement(xml_parent,
                   'hudson.plugins.blame__upstream__commiters.'
                   'BlameUpstreamCommitersPublisher')


def campfire(parser, xml_parent, data):
    """yaml: campfire
    Send build notifications to Campfire rooms.
    Requires the Jenkins `Campfire Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/Campfire+Plugin>`_

    Campfire notifications global default values must be configured for
    the Jenkins instance. Default values will be used if no specific
    values are specified for each job, so all config params are optional.

    :arg str subdomain: override the default campfire subdomain
    :arg str token: override the default API token
    :arg bool ssl: override the default 'use SSL'
    :arg str room: override the default room name

    Example:

    .. literalinclude::  /../../tests/publishers/fixtures/campfire001.yaml

    """

    root = XML.SubElement(xml_parent,
                          'hudson.plugins.campfire.'
                          'CampfireNotifier')

    campfire = XML.SubElement(root, 'campfire')

    if ('subdomain' in data and data['subdomain']):
        subdomain = XML.SubElement(campfire, 'subdomain')
        subdomain.text = data['subdomain']
    if ('token' in data and data['token']):
        token = XML.SubElement(campfire, 'token')
        token.text = data['token']
    if ('ssl' in data):
        ssl = XML.SubElement(campfire, 'ssl')
        ssl.text = str(data['ssl']).lower()

    if ('room' in data and data['room']):
        room = XML.SubElement(root, 'room')
        name = XML.SubElement(room, 'name')
        name.text = data['room']

        XML.SubElement(room, 'campfire reference="../../campfire"')


def emotional_jenkins(parser, xml_parent, data):
    """yaml: emotional-jenkins
    Emotional Jenkins.
    Requires the Jenkins `Emotional Jenkins Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/Emotional+Jenkins+Plugin>`_

    Example:

    .. literalinclude:: /../../tests/publishers/fixtures/emotional-jenkins.yaml
    """
    XML.SubElement(xml_parent,
                   'org.jenkinsci.plugins.emotional__jenkins.'
                   'EmotionalJenkinsPublisher')


def trigger_parameterized_builds(parser, xml_parent, data):
    """yaml: trigger-parameterized-builds
    Trigger parameterized builds of other jobs.
    Requires the Jenkins `Parameterized Trigger Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/
    Parameterized+Trigger+Plugin>`_

    :arg str project: name of the job to trigger
    :arg str predefined-parameters: parameters to pass to the other
      job (optional)
    :arg bool current-parameters: Whether to include the parameters passed
      to the current build to the triggered job (optional)
    :arg bool svn-revision: Pass svn revision to the triggered job (optional)
    :arg bool git-revision: Pass git revision to the other job (optional)
    :arg str condition: when to trigger the other job (default 'ALWAYS')
    :arg str property-file: Use properties from file (optional)
    :arg bool fail-on-missing: Blocks the triggering of the downstream jobs
      if any of the files are not found in the workspace (default 'False')
    :arg str restrict-matrix-project: Filter that restricts the subset
        of the combinations that the downstream project will run (optional)

    Example::

      publishers:
        - trigger-parameterized-builds:
            - project: other_job, foo, bar
              predefined-parameters: foo=bar
            - project: other_job1, other_job2
              predefined-parameters: BUILD_NUM=${BUILD_NUMBER}
              property-file: version.prop
              fail-on-missing: true
            - project: yet_another_job
              predefined-parameters: foo=bar
              git-revision: true
              restrict-matrix-project: label=="x86"

    """
    tbuilder = XML.SubElement(xml_parent,
                              'hudson.plugins.parameterizedtrigger.'
                              'BuildTrigger')
    configs = XML.SubElement(tbuilder, 'configs')
    for project_def in data:
        tconfig = XML.SubElement(configs,
                                 'hudson.plugins.parameterizedtrigger.'
                                 'BuildTriggerConfig')
        tconfigs = XML.SubElement(tconfig, 'configs')
        if ('predefined-parameters' in project_def
            or 'git-revision' in project_def
            or 'property-file' in project_def
            or 'current-parameters' in project_def
            or 'svn-revision' in project_def
            or 'restrict-matrix-project' in project_def):

            if 'predefined-parameters' in project_def:
                params = XML.SubElement(tconfigs,
                                        'hudson.plugins.parameterizedtrigger.'
                                        'PredefinedBuildParameters')
                properties = XML.SubElement(params, 'properties')
                properties.text = project_def['predefined-parameters']

            if 'git-revision' in project_def and project_def['git-revision']:
                params = XML.SubElement(tconfigs,
                                        'hudson.plugins.git.'
                                        'GitRevisionBuildParameters')
                properties = XML.SubElement(params, 'combineQueuedCommits')
                properties.text = 'false'
            if 'property-file' in project_def and project_def['property-file']:
                params = XML.SubElement(tconfigs,
                                        'hudson.plugins.parameterizedtrigger.'
                                        'FileBuildParameters')
                properties = XML.SubElement(params, 'propertiesFile')
                properties.text = project_def['property-file']
                failOnMissing = XML.SubElement(params, 'failTriggerOnMissing')
                failOnMissing.text = str(project_def.get('fail-on-missing',
                                                         False)).lower()
            if ('current-parameters' in project_def
                and project_def['current-parameters']):
                XML.SubElement(tconfigs,
                               'hudson.plugins.parameterizedtrigger.'
                               'CurrentBuildParameters')
            if 'svn-revision' in project_def and project_def['svn-revision']:
                XML.SubElement(tconfigs,
                               'hudson.plugins.parameterizedtrigger.'
                               'SubversionRevisionBuildParameters')
            if ('restrict-matrix-project' in project_def
                and project_def['restrict-matrix-project']):
                subset = XML.SubElement(tconfigs,
                                        'hudson.plugins.parameterizedtrigger.'
                                        'matrix.MatrixSubsetBuildParameters')
                XML.SubElement(subset, 'filter').text = \
                    project_def['restrict-matrix-project']
        else:
            tconfigs.set('class', 'java.util.Collections$EmptyList')
        projects = XML.SubElement(tconfig, 'projects')
        projects.text = project_def['project']
        condition = XML.SubElement(tconfig, 'condition')
        condition.text = project_def.get('condition', 'ALWAYS')
        trigger_with_no_params = XML.SubElement(tconfig,
                                                'triggerWithNoParameters')
        trigger_with_no_params.text = 'false'


def trigger(parser, xml_parent, data):
    """yaml: trigger
    Trigger non-parametrised builds of other jobs.

    :arg str project: name of the job to trigger
    :arg str threshold: when to trigger the other job (default 'SUCCESS'),
      alternatives: SUCCESS, UNSTABLE, FAILURE

    Example:

    .. literalinclude:: /../../tests/publishers/fixtures/trigger_success.yaml
    """
    tconfig = XML.SubElement(xml_parent, 'hudson.tasks.BuildTrigger')
    childProjects = XML.SubElement(tconfig, 'childProjects')
    childProjects.text = data['project']
    tthreshold = XML.SubElement(tconfig, 'threshold')

    threshold = data.get('threshold', 'SUCCESS')
    supported_thresholds = ['SUCCESS', 'UNSTABLE', 'FAILURE']
    if threshold not in supported_thresholds:
        raise JenkinsJobsException("threshold must be one of %s" %
                                   ", ".join(supported_thresholds))
    tname = XML.SubElement(tthreshold, 'name')
    tname.text = hudson_model.THRESHOLDS[threshold]['name']
    tordinal = XML.SubElement(tthreshold, 'ordinal')
    tordinal.text = hudson_model.THRESHOLDS[threshold]['ordinal']
    tcolor = XML.SubElement(tthreshold, 'color')
    tcolor.text = hudson_model.THRESHOLDS[threshold]['color']


def clone_workspace(parser, xml_parent, data):
    """yaml: clone-workspace
    Archive the workspace from builds of one project and reuse them as the SCM
    source for another project.
    Requires the Jenkins `Clone Workspace SCM Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/Clone+Workspace+SCM+Plugin>`_

    :arg str workspace-glob: Files to include in cloned workspace
    :arg str workspace-exclude-glob: Files to exclude from cloned workspace
    :arg str criteria: Criteria for build to be archived.  Can be 'any',
        'not failed', or 'successful'. (default: any )
    :arg str archive-method: Choose the method to use for archiving the
        workspace.  Can be 'tar' or 'zip'.  (default: tar)
    :arg bool override-default-excludes: Override default ant excludes.
        (default: false)

    Minimal example:

    .. literalinclude::
      /../../tests/publishers/fixtures/clone-workspace001.yaml

    Full example:

    .. literalinclude::
      /../../tests/publishers/fixtures/clone-workspace002.yaml

    """

    cloneworkspace = XML.SubElement(
        xml_parent,
        'hudson.plugins.cloneworkspace.CloneWorkspacePublisher',
        {'plugin': 'clone-workspace-scm'})

    XML.SubElement(
        cloneworkspace,
        'workspaceGlob').text = data.get('workspace-glob', None)

    if 'workspace-exclude-glob' in data:
        XML.SubElement(
            cloneworkspace,
            'workspaceExcludeGlob').text = data['workspace-exclude-glob']

    criteria_list = ['Any', 'Not Failed', 'Successful']

    criteria = data.get('criteria', 'Any').title()

    if 'criteria' in data and criteria not in criteria_list:
        raise JenkinsJobsException(
            'clone-workspace criteria must be one of: '
            + ', '.join(criteria_list))
    else:
        XML.SubElement(cloneworkspace, 'criteria').text = criteria

    archive_list = ['TAR', 'ZIP']

    archive_method = data.get('archive-method', 'TAR').upper()

    if 'archive-method' in data and archive_method not in archive_list:
        raise JenkinsJobsException(
            'clone-workspace archive-method must be one of: '
            + ', '.join(archive_list))
    else:
        XML.SubElement(cloneworkspace, 'archiveMethod').text = archive_method

    override_default_excludes_str = str(
        data.get('override-default-excludes', False)).lower()
    override_default_excludes_elem = XML.SubElement(
        cloneworkspace, 'overrideDefaultExcludes')
    override_default_excludes_elem.text = override_default_excludes_str


def cloverphp(parser, xml_parent, data):
    """yaml: cloverphp
    Capture code coverage reports from PHPUnit
    Requires the Jenkins `Clover PHP Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/Clover+PHP+Plugin>`_

    Your job definition should pass to PHPUnit the --coverage-clover option
    pointing to a file in the workspace (ex: clover-coverage.xml). The filename
    has to be filled in the `xml-location` field.

    :arg str xml-location: Path to the coverage XML file generated by PHPUnit
      using --coverage-clover. Relative to workspace. (required)
    :arg dict html: When existent, whether the plugin should generate a HTML
      report.  Note that PHPUnit already provide a HTML report via its
      --cover-html option which can be set in your builder (optional):

        * **dir** (str): Directory where HTML report will be generated relative
                         to workspace. (required in `html` dict).
        * **archive** (bool): Whether to archive HTML reports (default True).

    :arg list metric-targets: List of metric targets to reach, must be one of
      **healthy**, **unhealthy** and **failing**. Each metric target can takes
      two parameters:

        * **method**  Target for method coverage
        * **statement** Target for statements coverage

      Whenever a metric target is not filled in, the Jenkins plugin can fill in
      defaults for you (as of v0.3.3 of the plugin the healthy target will have
      method: 70 and statement: 80 if both are left empty). Jenkins Job Builder
      will mimic that feature to ensure clean configuration diff.

    Minimal example:

      .. literalinclude:: /../../tests/publishers/fixtures/cloverphp001.yaml

    Full example:

      .. literalinclude:: /../../tests/publishers/fixtures/cloverphp002.yaml

    """
    cloverphp = XML.SubElement(
        xml_parent,
        'org.jenkinsci.plugins.cloverphp.CloverPHPPublisher')

    # The plugin requires clover XML file to parse
    if 'xml-location' not in data:
        raise JenkinsJobsException('xml-location must be set')

    # Whether HTML publishing has been checked
    html_publish = False
    # By default, disableArchiving = false. Note that we use
    # reversed logic.
    html_archive = True

    if 'html' in data:
        html_publish = True
        html_dir = data['html'].get('dir', None)
        html_archive = data['html'].get('archive', html_archive)
        if html_dir is None:
            # No point in going further, the plugin would not work
            raise JenkinsJobsException('htmldir is required in a html block')

    XML.SubElement(cloverphp, 'publishHtmlReport').text = \
        str(html_publish).lower()
    if html_publish:
        XML.SubElement(cloverphp, 'reportDir').text = html_dir
    XML.SubElement(cloverphp, 'xmlLocation').text = data.get('xml-location')
    XML.SubElement(cloverphp, 'disableArchiving').text = \
        str(not html_archive).lower()

    # Handle targets

    # Plugin v0.3.3 will fill defaults for us whenever healthy targets are both
    # blanks.
    default_metrics = {
        'healthy': {'method': 70, 'statement': 80}
    }
    allowed_metrics = ['healthy', 'unhealthy', 'failing']

    metrics = data.get('metric-targets', [])
    # list of dicts to dict
    metrics = dict(kv for m in metrics for kv in m.iteritems())

    # Populate defaults whenever nothing has been filled by user.
    for default in default_metrics.keys():
        if metrics.get(default, None) is None:
            metrics[default] = default_metrics[default]

    # The plugin would at least define empty targets so make sure
    # we output them all in the XML regardless of what the user
    # has or has not entered.
    for target in allowed_metrics:
        cur_target = XML.SubElement(cloverphp, target + 'Target')

        for t_type in ['method', 'statement']:
            val = metrics.get(target, {}).get(t_type)
            if val is None or type(val) != int:
                continue
            if val < 0 or val > 100:
                raise JenkinsJobsException(
                    "Publisher cloverphp metric target %s:%s = %s "
                    "is not in valid range 0-100." % (target, t_type, val))
            XML.SubElement(cur_target, t_type + 'Coverage').text = str(val)


def coverage(parser, xml_parent, data):
    """yaml: coverage
    WARNING: The coverage function is deprecated. Instead, use the
    cobertura function to generate a cobertura coverage report.
    Requires the Jenkins `Cobertura Coverage Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/Cobertura+Plugin>`_

    Example::

      publishers:
        - coverage
    """
    logger = logging.getLogger(__name__)
    logger.warn("Coverage function is deprecated. Switch to cobertura.")

    cobertura = XML.SubElement(xml_parent,
                               'hudson.plugins.cobertura.CoberturaPublisher')
    XML.SubElement(cobertura, 'coberturaReportFile').text = '**/coverage.xml'
    XML.SubElement(cobertura, 'onlyStable').text = 'false'
    healthy = XML.SubElement(cobertura, 'healthyTarget')
    targets = XML.SubElement(healthy, 'targets', {
        'class': 'enum-map',
        'enum-type': 'hudson.plugins.cobertura.targets.CoverageMetric'})
    entry = XML.SubElement(targets, 'entry')
    XML.SubElement(entry, 'hudson.plugins.cobertura.targets.CoverageMetric'
                   ).text = 'CONDITIONAL'
    XML.SubElement(entry, 'int').text = '70'
    entry = XML.SubElement(targets, 'entry')
    XML.SubElement(entry, 'hudson.plugins.cobertura.targets.CoverageMetric'
                   ).text = 'LINE'
    XML.SubElement(entry, 'int').text = '80'
    entry = XML.SubElement(targets, 'entry')
    XML.SubElement(entry, 'hudson.plugins.cobertura.targets.CoverageMetric'
                   ).text = 'METHOD'
    XML.SubElement(entry, 'int').text = '80'
    unhealthy = XML.SubElement(cobertura, 'unhealthyTarget')
    targets = XML.SubElement(unhealthy, 'targets', {
        'class': 'enum-map',
        'enum-type': 'hudson.plugins.cobertura.targets.CoverageMetric'})
    entry = XML.SubElement(targets, 'entry')
    XML.SubElement(entry, 'hudson.plugins.cobertura.targets.CoverageMetric'
                   ).text = 'CONDITIONAL'
    XML.SubElement(entry, 'int').text = '0'
    entry = XML.SubElement(targets, 'entry')
    XML.SubElement(entry, 'hudson.plugins.cobertura.targets.CoverageMetric'
                   ).text = 'LINE'
    XML.SubElement(entry, 'int').text = '0'
    entry = XML.SubElement(targets, 'entry')
    XML.SubElement(entry, 'hudson.plugins.cobertura.targets.CoverageMetric'
                   ).text = 'METHOD'
    XML.SubElement(entry, 'int').text = '0'
    failing = XML.SubElement(cobertura, 'failingTarget')
    targets = XML.SubElement(failing, 'targets', {
        'class': 'enum-map',
        'enum-type': 'hudson.plugins.cobertura.targets.CoverageMetric'})
    entry = XML.SubElement(targets, 'entry')
    XML.SubElement(entry, 'hudson.plugins.cobertura.targets.CoverageMetric'
                   ).text = 'CONDITIONAL'
    XML.SubElement(entry, 'int').text = '0'
    entry = XML.SubElement(targets, 'entry')
    XML.SubElement(entry, 'hudson.plugins.cobertura.targets.CoverageMetric'
                   ).text = 'LINE'
    XML.SubElement(entry, 'int').text = '0'
    entry = XML.SubElement(targets, 'entry')
    XML.SubElement(entry, 'hudson.plugins.cobertura.targets.CoverageMetric'
                   ).text = 'METHOD'
    XML.SubElement(entry, 'int').text = '0'
    XML.SubElement(cobertura, 'sourceEncoding').text = 'ASCII'


def cobertura(parser, xml_parent, data):
    """yaml: cobertura
    Generate a cobertura coverage report.
    Requires the Jenkins `Cobertura Coverage Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/Cobertura+Plugin>`_

    :arg str report-file: This is a file name pattern that can be used
                          to locate the cobertura xml report files (optional)
    :arg bool only-stable: Include only stable builds (default false)
    :arg bool fail-no-reports: fail builds if no coverage reports are found
                               (default false)
    :arg bool fail-unhealthy: Unhealthy projects will be failed
                              (default false)
    :arg bool fail-unstable: Unstable projects will be failed (default false)
    :arg bool health-auto-update: Auto update threshold for health on
                                  successful build (default false)
    :arg bool stability-auto-update: Auto update threshold for stability on
                                     successful build (default false)
    :arg bool zoom-coverage-chart: Zoom the coverage chart and crop area below
                                   the minimum and above the maximum coverage
                                   of the past reports (default false)
    :arg str source-encoding: Override the source encoding (default ASCII)
    :arg dict targets:

           :targets: (packages, files, classes, method, line, conditional)

                * **healthy** (`int`): Healthy threshold (default 0)
                * **unhealthy** (`int`): Unhealthy threshold (default 0)
                * **failing** (`int`): Failing threshold (default 0)

    Example::

      publishers:
        - cobertura:
             report-file: "/reports/cobertura/coverage.xml"
             only-stable: "true"
             fail-no-reports: "true"
             fail-unhealthy: "true"
             fail-unstable: "true"
             health-auto-update: "true"
             stability-auto-update: "true"
             zoom-coverage-chart: "true"
             source-encoding: "Big5"
             targets:
                  - files:
                      healthy: 10
                      unhealthy: 20
                      failing: 30
                  - method:
                      healthy: 50
                      unhealthy: 40
                      failing: 30


    """
    cobertura = XML.SubElement(xml_parent,
                               'hudson.plugins.cobertura.CoberturaPublisher')
    XML.SubElement(cobertura, 'coberturaReportFile').text = data.get(
        'report-file', '**/coverage.xml')
    XML.SubElement(cobertura, 'onlyStable').text = str(
        data.get('only-stable', False)).lower()
    XML.SubElement(cobertura, 'failUnhealthy').text = str(
        data.get('fail-unhealthy', False)).lower()
    XML.SubElement(cobertura, 'failUnstable').text = str(
        data.get('fail-unstable', False)).lower()
    XML.SubElement(cobertura, 'autoUpdateHealth').text = str(
        data.get('health-auto-update', False)).lower()
    XML.SubElement(cobertura, 'autoUpdateStability').text = str(
        data.get('stability-auto-update', False)).lower()
    XML.SubElement(cobertura, 'zoomCoverageChart').text = str(
        data.get('zoom-coverage-chart', False)).lower()
    XML.SubElement(cobertura, 'failNoReports').text = str(
        data.get('fail-no-reports', False)).lower()
    healthy = XML.SubElement(cobertura, 'healthyTarget')
    targets = XML.SubElement(healthy, 'targets', {
        'class': 'enum-map',
        'enum-type': 'hudson.plugins.cobertura.targets.CoverageMetric'})
    for item in data['targets']:
        item_name = item.keys()[0]
        item_values = item.get(item_name, 0)
        entry = XML.SubElement(targets, 'entry')
        XML.SubElement(entry,
                       'hudson.plugins.cobertura.targets.'
                       'CoverageMetric').text = str(item_name).upper()
        XML.SubElement(entry, 'int').text = str(item_values.get('healthy', 0))
    unhealthy = XML.SubElement(cobertura, 'unhealthyTarget')
    targets = XML.SubElement(unhealthy, 'targets', {
        'class': 'enum-map',
        'enum-type': 'hudson.plugins.cobertura.targets.CoverageMetric'})
    for item in data['targets']:
        item_name = item.keys()[0]
        item_values = item.get(item_name, 0)
        entry = XML.SubElement(targets, 'entry')
        XML.SubElement(entry, 'hudson.plugins.cobertura.targets.'
                              'CoverageMetric').text = str(item_name).upper()
        XML.SubElement(entry, 'int').text = str(item_values.get('unhealthy',
                                                                0))
    failing = XML.SubElement(cobertura, 'failingTarget')
    targets = XML.SubElement(failing, 'targets', {
        'class': 'enum-map',
        'enum-type': 'hudson.plugins.cobertura.targets.CoverageMetric'})
    for item in data['targets']:
        item_name = item.keys()[0]
        item_values = item.get(item_name, 0)
        entry = XML.SubElement(targets, 'entry')
        XML.SubElement(entry, 'hudson.plugins.cobertura.targets.'
                              'CoverageMetric').text = str(item_name).upper()
        XML.SubElement(entry, 'int').text = str(item_values.get('failing', 0))
    XML.SubElement(cobertura, 'sourceEncoding').text = data.get(
        'source-encoding', 'ASCII')


def jacoco(parser, xml_parent, data):
    """yaml: jacoco
    Generate a JaCoCo coverage report.
    Requires the Jenkins `JaCoCo Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/JaCoCo+Plugin>`_

    :arg str exec-pattern: This is a file name pattern that can be used to
                          locate the jacoco report files (default
                          ``**/**.exec``)
    :arg str class-pattern: This is a file name pattern that can be used
                          to locate class files (default ``**/classes``)
    :arg str source-pattern: This is a file name pattern that can be used
                          to locate source files (default ``**/src/main/java``)
    :arg bool update-build-status: Update the build according to the results
                          (default False)
    :arg str inclusion-pattern: This is a file name pattern that can be used
                          to include certain class files (optional)
    :arg str exclusion-pattern: This is a file name pattern that can be used
                          to exclude certain class files (optional)
    :arg dict targets:

           :targets: (instruction, branch, complexity, line, method, class)

                * **healthy** (`int`): Healthy threshold (default 0)
                * **unhealthy** (`int`): Unhealthy threshold (default 0)

    Example::

      publishers:
        - jacoco:
            exec-pattern: "**/**.exec"
            class-pattern: "**/classes"
            source-pattern: "**/src/main/java"
            status-update: true
            targets:
              - branch:
                  healthy: 10
                  unhealthy: 20
              - method:
                  healthy: 50
                  unhealthy: 40

    """

    jacoco = XML.SubElement(xml_parent,
                            'hudson.plugins.jacoco.JacocoPublisher')
    XML.SubElement(jacoco, 'execPattern').text = data.get(
        'exec-pattern', '**/**.exec')
    XML.SubElement(jacoco, 'classPattern').text = data.get(
        'class-pattern', '**/classes')
    XML.SubElement(jacoco, 'sourcePattern').text = data.get(
        'source-pattern', '**/src/main/java')
    XML.SubElement(jacoco, 'changeBuildStatus').text = data.get(
        'update-build-status', False)
    XML.SubElement(jacoco, 'inclusionPattern').text = data.get(
        'inclusion-pattern', '')
    XML.SubElement(jacoco, 'exclusionPattern').text = data.get(
        'exclusion-pattern', '')

    itemsList = ['instruction',
                 'branch',
                 'complexity',
                 'line',
                 'method',
                 'class']

    for item in data['targets']:
        item_name = item.keys()[0]
        if item_name not in itemsList:
            raise JenkinsJobsException("item entered is not valid must be "
                                       "one of: %s" % ",".join(itemsList))
        item_values = item.get(item_name, 0)

        XML.SubElement(jacoco,
                       'maximum' +
                       item_name.capitalize() +
                       'Coverage').text = str(item_values.get('healthy', 0))
        XML.SubElement(jacoco,
                       'minimum' +
                       item_name.capitalize() +
                       'Coverage').text = str(item_values.get('unhealthy', 0))


def ftp(parser, xml_parent, data):
    """yaml: ftp
    Upload files via FTP.
    Requires the Jenkins `Publish over FTP Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/Publish+Over+FTP+Plugin>`_

    :arg str site: name of the ftp site
    :arg str target: destination directory
    :arg bool target-is-date-format: whether target is a date format. If true,
      raw text should be quoted (defaults to False)
    :arg bool clean-remote: should the remote directory be deleted before
      transferring files (defaults to False)
    :arg str source: source path specifier
    :arg str excludes: excluded file pattern (optional)
    :arg str remove-prefix: prefix to remove from uploaded file paths
      (optional)
    :arg bool fail-on-error: fail the build if an error occurs (defaults to
      False).

    Example::

      publishers:
        - ftp:
            site: 'ftp.example.com'
            target: 'dest/dir'
            source: 'base/source/dir/**'
            remove-prefix: 'base/source/dir'
            excludes: '**/*.excludedfiletype'
    """
    console_prefix = 'FTP: '
    plugin_tag = 'jenkins.plugins.publish__over__ftp.BapFtpPublisherPlugin'
    publisher_tag = 'jenkins.plugins.publish__over__ftp.BapFtpPublisher'
    transfer_tag = 'jenkins.plugins.publish__over__ftp.BapFtpTransfer'
    plugin_reference_tag = 'jenkins.plugins.publish_over_ftp.'    \
        'BapFtpPublisherPlugin'
    (_, transfer_node) = base_publish_over(xml_parent,
                                           data,
                                           console_prefix,
                                           plugin_tag,
                                           publisher_tag,
                                           transfer_tag,
                                           plugin_reference_tag)
    XML.SubElement(transfer_node, 'asciiMode').text = 'false'


def junit(parser, xml_parent, data):
    """yaml: junit
    Publish JUnit test results.

    :arg str results: results filename
    :arg bool keep-long-stdio: Retain long standard output/error in test
      results (default true).
    :arg bool test-stability: Add historical information about test
        results stability (default false).
        Requires the Jenkins `Test stability Plugin
        <https://wiki.jenkins-ci.org/display/JENKINS/Test+stability+plugin>`_.

    Minimal example using defaults:

    .. literalinclude::  /../../tests/publishers/fixtures/junit001.yaml

    Full example:

    .. literalinclude::  /../../tests/publishers/fixtures/junit002.yaml

    """
    junitresult = XML.SubElement(xml_parent,
                                 'hudson.tasks.junit.JUnitResultArchiver')
    XML.SubElement(junitresult, 'testResults').text = data['results']
    XML.SubElement(junitresult, 'keepLongStdio').text = str(
        data.get('keep-long-stdio', True)).lower()
    datapublisher = XML.SubElement(junitresult, 'testDataPublishers')
    if str(data.get('test-stability', False)).lower() == 'true':
        XML.SubElement(datapublisher,
                       'de.esailors.jenkins.teststability'
                       '.StabilityTestDataPublisher')


def xunit(parser, xml_parent, data):
    """yaml: xunit
    Publish tests results.  Requires the Jenkins `xUnit Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/xUnit+Plugin>`_

    :arg str thresholdmode: whether thresholds represents an absolute \
    number of tests or a percentage. Either 'number' or 'percent', will \
    default to 'number' if omitted.

    :arg dict thresholds: list containing the thresholds for both \
    'failed' and 'skipped' tests. Each entry should in turn have a \
    list of "threshold name: values". The threshold names are \
    'unstable', 'unstablenew', 'failure', 'failurenew'. Omitting a \
    value will resort on xUnit default value (should be 0).

    :arg dict types: per framework configuration. The key should be \
    one of the internal types we support:\
    'aunit', 'boosttest', 'checktype', 'cpptest', 'cppunit', 'fpcunit', \
    'junit', 'mstest', 'nunit', 'phpunit', 'tusar', 'unittest', 'valgrind'. \
    The 'custom' type is not supported.

    Each framework type can be configured using the following parameters:

    :arg str pattern: An Ant pattern to look for Junit result files, \
    relative to the workspace root.

    :arg bool requireupdate: fail the build whenever fresh tests \
    results have not been found (default: true).

    :arg bool deleteoutput: delete temporary JUnit files (default: true)

    :arg bool stoponerror: Fail the build whenever an error occur during \
    a result file processing (default: true).


    Example::

        publishers:
            - xunit:
                thresholdmode: 'percent'
                thresholds:
                  - failed:
                        unstable: 0
                        unstablenew: 0
                        failure: 0
                        failurenew: 0
                  - skipped:
                        unstable: 0
                        unstablenew: 0
                        failure: 0
                        failurenew: 0
                types:
                  - phpunit:
                      pattern: junit.log
                  - cppUnit:
                      pattern: cppunit.log

    """
    logger = logging.getLogger(__name__)
    xunit = XML.SubElement(xml_parent, 'xunit')

    # Map our internal types to the XML element names used by Jenkins plugin
    types_to_plugin_types = {
        'aunit': 'AUnitJunitHudsonTestType',
        'boosttest': 'BoostTestJunitHudsonTestType',
        'checktype': 'CheckType',
        'cpptest': 'CppTestJunitHudsonTestType',
        'cppunit': 'CppUnitJunitHudsonTestType',
        'fpcunit': 'FPCUnitJunitHudsonTestType',
        'junit': 'JUnitType',
        'mstest': 'MSTestJunitHudsonTestType',
        'nunit': 'NUnitJunitHudsonTestType',
        'phpunit': 'PHPUnitJunitHudsonTestType',
        'tusar': 'TUSARJunitHudsonTestType',
        'unittest': 'UnitTestJunitHudsonTestType',
        'valgrind': 'ValgrindJunitHudsonTestType',
        # FIXME should implement the 'custom' type
    }
    implemented_types = types_to_plugin_types.keys()  # shortcut

    # Unit framework we are going to generate xml for
    supported_types = []

    for configured_type in data['types']:
        type_name = configured_type.keys()[0]
        if type_name not in implemented_types:
            logger.warn("Requested xUnit type '%s' is not yet supported" %
                        type_name)
        else:
            # Append for generation
            supported_types.append(configured_type)

    # Generate XML for each of the supported framework types
    xmltypes = XML.SubElement(xunit, 'types')
    for supported_type in supported_types:
        framework_name = supported_type.keys()[0]
        xmlframework = XML.SubElement(xmltypes,
                                      types_to_plugin_types[framework_name])

        XML.SubElement(xmlframework, 'pattern').text = \
            supported_type[framework_name].get('pattern', '')
        XML.SubElement(xmlframework, 'failIfNotNew').text = \
            str(supported_type[framework_name].get(
                'requireupdate', True)).lower()
        XML.SubElement(xmlframework, 'deleteOutputFiles').text = \
            str(supported_type[framework_name].get(
                'deleteoutput', True)).lower()
        XML.SubElement(xmlframework, 'stopProcessingIfError').text = \
            str(supported_type[framework_name].get(
                'stoponerror', True)).lower()

    xmlthresholds = XML.SubElement(xunit, 'thresholds')
    if 'thresholds' in data:
        for t in data['thresholds']:
            if not ('failed' in t or 'skipped' in t):
                logger.warn(
                    "Unrecognized threshold, should be 'failed' or 'skipped'")
                continue
            elname = "org.jenkinsci.plugins.xunit.threshold.%sThreshold" \
                % t.keys()[0].title()
            el = XML.SubElement(xmlthresholds, elname)
            for threshold_name, threshold_value in t.values()[0].items():
                # Normalize and craft the element name for this threshold
                elname = "%sThreshold" % threshold_name.lower().replace(
                    'new', 'New')
                XML.SubElement(el, elname).text = threshold_value

    # Whether to use percent of exact number of tests.
    # Thresholdmode is either:
    # - 1 : absolute (number of tests), default.
    # - 2 : relative (percentage of tests)
    thresholdmode = '1'
    if 'percent' == data.get('thresholdmode', 'number'):
        thresholdmode = '2'
    XML.SubElement(xunit, 'thresholdMode').text = \
        thresholdmode


def _violations_add_entry(xml_parent, name, data):
    vmin = data.get('min', 10)
    vmax = data.get('max', 999)
    vunstable = data.get('unstable', 999)
    pattern = data.get('pattern', None)

    entry = XML.SubElement(xml_parent, 'entry')
    XML.SubElement(entry, 'string').text = name
    tconfig = XML.SubElement(entry, 'hudson.plugins.violations.TypeConfig')
    XML.SubElement(tconfig, 'type').text = name
    XML.SubElement(tconfig, 'min').text = str(vmin)
    XML.SubElement(tconfig, 'max').text = str(vmax)
    XML.SubElement(tconfig, 'unstable').text = str(vunstable)
    XML.SubElement(tconfig, 'usePattern').text = 'false'
    if pattern:
        XML.SubElement(tconfig, 'pattern').text = pattern
    else:
        XML.SubElement(tconfig, 'pattern')


def violations(parser, xml_parent, data):
    """yaml: violations
    Publish code style violations.
    Requires the Jenkins `Violations Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/Violations>`_

    The violations component accepts any number of dictionaries keyed
    by the name of the violations system.  The dictionary has the
    following values:

    :arg int min: sunny threshold
    :arg int max: stormy threshold
    :arg int unstable: unstable threshold
    :arg str pattern: report filename pattern

    Any system without a dictionary provided will use default values.

    Valid systems are:

      checkstyle, codenarc, cpd, cpplint, csslint, findbugs, fxcop,
      gendarme, jcreport, jslint, pep8, pmd, pylint, simian, stylecop

    Example::

      publishers:
        - violations:
            pep8:
              min: 0
              max: 1
              unstable: 1
              pattern: '**/pep8.txt'
    """
    violations = XML.SubElement(xml_parent,
                                'hudson.plugins.violations.'
                                'ViolationsPublisher')
    config = XML.SubElement(violations, 'config')
    suppressions = XML.SubElement(config, 'suppressions',
                                  {'class': 'tree-set'})
    XML.SubElement(suppressions, 'no-comparator')
    configs = XML.SubElement(config, 'typeConfigs')
    XML.SubElement(configs, 'no-comparator')

    for name in [
        'checkstyle',
        'codenarc',
        'cpd',
        'cpplint',
        'csslint',
        'findbugs',
        'fxcop',
        'gendarme',
        'jcreport',
        'jslint',
        'pep8',
        'pmd',
        'pylint',
        'simian',
        'stylecop']:
        _violations_add_entry(configs, name, data.get(name, {}))

    XML.SubElement(config, 'limit').text = '100'
    XML.SubElement(config, 'sourcePathPattern')
    XML.SubElement(config, 'fauxProjectPath')
    XML.SubElement(config, 'encoding').text = 'default'


def checkstyle(parser, xml_parent, data):
    """yaml: checkstyle
    Publish trend reports with Checkstyle.
    Requires the Jenkins `Checkstyle Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/Checkstyle+Plugin>`_

    The checkstyle component accepts a dictionary with the
    following values:

    :arg str pattern: report filename pattern
    :arg bool canRunOnFailed: also runs for failed builds
     (instead of just stable or unstable builds)
    :arg bool shouldDetectModules:
    :arg int healthy: sunny threshold
    :arg int unHealthy: stormy threshold
    :arg str healthThreshold: threshold priority for health status
     (high: only high, normal: high and normal, low: all)
    :arg dict thresholds:
        :thresholds:
            * **unstable** (`dict`)
                :unstable: * **totalAll** (`int`)
                           * **totalHigh** (`int`)
                           * **totalNormal** (`int`)
                           * **totalLow** (`int`)
            * **failed** (`dict`)
                :failed: * **totalAll** (`int`)
                         * **totalHigh** (`int`)
                         * **totalNormal** (`int`)
                         * **totalLow** (`int`)
    :arg str defaultEncoding: encoding for parsing or showing files
     (empty will use platform default)

    Example:

    .. literalinclude::  /../../tests/publishers/fixtures/checkstyle001.yaml

    Full example:

    .. literalinclude::  /../../tests/publishers/fixtures/checkstyle002.yaml

    """
    checkstyle = XML.SubElement(xml_parent,
                                'hudson.plugins.checkstyle.'
                                'CheckStylePublisher')

    XML.SubElement(checkstyle, 'healthy').text = str(
        data.get('healthy', ''))
    XML.SubElement(checkstyle, 'unHealthy').text = str(
        data.get('unHealthy', ''))
    XML.SubElement(checkstyle, 'thresholdLimit').text = \
        data.get('healthThreshold', 'low')

    XML.SubElement(checkstyle, 'pluginName').text = '[CHECKSTYLE] '

    XML.SubElement(checkstyle, 'defaultEncoding').text = \
        data.get('defaultEncoding', '')

    XML.SubElement(checkstyle, 'canRunOnFailed').text = str(
        data.get('canRunOnFailed', False)).lower()

    XML.SubElement(checkstyle, 'useStableBuildAsReference').text = 'false'

    XML.SubElement(checkstyle, 'useDeltaValues').text = 'false'

    dthresholds = data.get('thresholds', {})
    dunstable = dthresholds.get('unstable', {})
    dfailed = dthresholds.get('failed', {})
    thresholds = XML.SubElement(checkstyle, 'thresholds')

    XML.SubElement(thresholds, 'unstableTotalAll').text = str(
        dunstable.get('totalAll', ''))
    XML.SubElement(thresholds, 'unstableTotalHigh').text = str(
        dunstable.get('totalHigh', ''))
    XML.SubElement(thresholds, 'unstableTotalNormal').text = str(
        dunstable.get('totalNormal', ''))
    XML.SubElement(thresholds, 'unstableTotalLow').text = str(
        dunstable.get('totalLow', ''))

    XML.SubElement(thresholds, 'failedTotalAll').text = str(
        dfailed.get('totalAll', ''))
    XML.SubElement(thresholds, 'failedTotalHigh').text = str(
        dfailed.get('totalHigh', ''))
    XML.SubElement(thresholds, 'failedTotalNormal').text = str(
        dfailed.get('totalNormal', ''))
    XML.SubElement(thresholds, 'failedTotalLow').text = str(
        dfailed.get('totalLow', ''))

    XML.SubElement(checkstyle, 'shouldDetectModules').text = \
        str(data.get('shouldDetectModules', False)).lower()

    XML.SubElement(checkstyle, 'dontComputeNew').text = 'true'

    XML.SubElement(checkstyle, 'doNotResolveRelativePaths').text = 'false'

    XML.SubElement(checkstyle, 'pattern').text = data.get('pattern', '')


def scp(parser, xml_parent, data):
    """yaml: scp
    Upload files via SCP
    Requires the Jenkins `SCP Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/SCP+plugin>`_

    :arg str site: name of the scp site
    :arg str target: destination directory
    :arg str source: source path specifier
    :arg bool keep-hierarchy: keep the file hierarchy when uploading
      (default false)
    :arg bool copy-after-failure: copy files even if the job fails
      (default false)
    :arg bool copy-console: copy the console log (default false); if
      specified, omit 'target'

    Example:

    .. literalinclude:: /../../tests/publishers/fixtures/scp001.yaml
    """
    site = data['site']
    scp = XML.SubElement(xml_parent,
                         'be.certipost.hudson.plugin.SCPRepositoryPublisher')
    XML.SubElement(scp, 'siteName').text = site
    entries = XML.SubElement(scp, 'entries')
    for entry in data['files']:
        entry_e = XML.SubElement(entries, 'be.certipost.hudson.plugin.Entry')
        XML.SubElement(entry_e, 'filePath').text = entry['target']
        XML.SubElement(entry_e, 'sourceFile').text = entry.get('source', '')
        if entry.get('keep-hierarchy', False):
            XML.SubElement(entry_e, 'keepHierarchy').text = 'true'
        else:
            XML.SubElement(entry_e, 'keepHierarchy').text = 'false'
        if entry.get('copy-console', False):
            XML.SubElement(entry_e, 'copyConsoleLog').text = 'true'
        else:
            XML.SubElement(entry_e, 'copyConsoleLog').text = 'false'
        if entry.get('copy-after-failure', False):
            XML.SubElement(entry_e, 'copyAfterFailure').text = 'true'
        else:
            XML.SubElement(entry_e, 'copyAfterFailure').text = 'false'


def ssh(parser, xml_parent, data):
    """yaml: ssh
    Upload files via SCP.
    Requires the Jenkins `Publish over SSH Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/Publish+Over+SSH+Plugin>`_

    :arg str site: name of the ssh site
    :arg str target: destination directory
    :arg bool target-is-date-format: whether target is a date format. If true,
      raw text should be quoted (defaults to False)
    :arg bool clean-remote: should the remote directory be deleted before
      transferring files (defaults to False)
    :arg str source: source path specifier
    :arg str command: a command to execute on the remote server (optional)
    :arg int timeout: timeout in milliseconds for the Exec command (optional)
    :arg bool use-pty: run the exec command in pseudo TTY (defaults to False)
    :arg str excludes: excluded file pattern (optional)
    :arg str remove-prefix: prefix to remove from uploaded file paths
      (optional)
    :arg bool fail-on-error: fail the build if an error occurs (defaults to
      False).

    Example::

      publishers:
        - ssh:
            site: 'server.example.com'
            target: 'dest/dir'
            source: 'base/source/dir/**'
            remove-prefix: 'base/source/dir'
            excludes: '**/*.excludedfiletype'
            use-pty: true
            command: 'rm -r jenkins_$BUILD_NUMBER'
            timeout: 1800000
    """
    console_prefix = 'SSH: '
    plugin_tag = 'jenkins.plugins.publish__over__ssh.BapSshPublisherPlugin'
    publisher_tag = 'jenkins.plugins.publish__over__ssh.BapSshPublisher'
    transfer_tag = 'jenkins.plugins.publish__over__ssh.BapSshTransfer'
    plugin_reference_tag = 'jenkins.plugins.publish_over_ssh.'    \
        'BapSshPublisherPlugin'
    base_publish_over(xml_parent,
                      data,
                      console_prefix,
                      plugin_tag,
                      publisher_tag,
                      transfer_tag,
                      plugin_reference_tag)


def pipeline(parser, xml_parent, data):
    """yaml: pipeline
    Specify a downstream project in a pipeline.
    Requires the Jenkins `Build Pipeline Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/Build+Pipeline+Plugin>`_

    :arg str project: the name of the downstream project
    :arg str predefined-parameters: parameters to pass to the other
      job (optional)
    :arg bool current-parameters: Whether to include the parameters passed
      to the current build to the triggered job (optional)

    Example:

    .. literalinclude:: /../../tests/publishers/fixtures/pipeline002.yaml


    You can build pipeline jobs that are re-usable in different pipelines by
    using a :ref:`job-template` to define the pipeline jobs,
    and variable substitution to specify the name of
    the downstream job in the pipeline.
    Job-specific substitutions are useful here (see :ref:`project`).

    See 'samples/pipeline.yaml' for an example pipeline implementation.
    """
    if 'project' in data and data['project'] != '':
        pippub = XML.SubElement(xml_parent,
                                'au.com.centrumsystems.hudson.plugin.'
                                'buildpipeline.trigger.BuildPipelineTrigger')

        configs = XML.SubElement(pippub, 'configs')

        if 'predefined-parameters' in data:
            params = XML.SubElement(configs,
                                    'hudson.plugins.parameterizedtrigger.'
                                    'PredefinedBuildParameters')
            properties = XML.SubElement(params, 'properties')
            properties.text = data['predefined-parameters']

        if ('current-parameters' in data
            and data['current-parameters']):
            XML.SubElement(configs,
                           'hudson.plugins.parameterizedtrigger.'
                           'CurrentBuildParameters')

        XML.SubElement(pippub, 'downstreamProjectNames').text = data['project']


def email(parser, xml_parent, data):
    """yaml: email
    Email notifications on build failure.

    :arg str recipients: Recipient email addresses
    :arg bool notify-every-unstable-build: Send an email for every
      unstable build (default true)
    :arg bool send-to-individuals: Send an email to the individual
      who broke the build (default false)

    Example::

      publishers:
        - email:
            recipients: breakage@example.com
    """

    # TODO: raise exception if this is applied to a maven job
    mailer = XML.SubElement(xml_parent,
                            'hudson.tasks.Mailer')
    XML.SubElement(mailer, 'recipients').text = data['recipients']

    # Note the logic reversal (included here to match the GUI
    if data.get('notify-every-unstable-build', True):
        XML.SubElement(mailer, 'dontNotifyEveryUnstableBuild').text = 'false'
    else:
        XML.SubElement(mailer, 'dontNotifyEveryUnstableBuild').text = 'true'
    XML.SubElement(mailer, 'sendToIndividuals').text = str(
        data.get('send-to-individuals', False)).lower()


def claim_build(parser, xml_parent, data):
    """yaml: claim-build
    Claim build failures
    Requires the Jenkins `Claim Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/Claim+plugin>`_

    Example::

      publishers:
        - claim-build
    """

    XML.SubElement(xml_parent, 'hudson.plugins.claim.ClaimPublisher')


def base_email_ext(parser, xml_parent, data, ttype):
    trigger = XML.SubElement(xml_parent,
                             'hudson.plugins.emailext.plugins.trigger.'
                             + ttype)
    email = XML.SubElement(trigger, 'email')
    XML.SubElement(email, 'recipientList').text = ''
    XML.SubElement(email, 'subject').text = '$PROJECT_DEFAULT_SUBJECT'
    XML.SubElement(email, 'body').text = '$PROJECT_DEFAULT_CONTENT'
    if 'send-to' in data:
        XML.SubElement(email, 'sendToDevelopers').text = \
            str('developers' in data['send-to']).lower()
        XML.SubElement(email, 'sendToRequester').text = \
            str('requester' in data['send-to']).lower()
        XML.SubElement(email, 'includeCulprits').text = \
            str('culprits' in data['send-to']).lower()
        XML.SubElement(email, 'sendToRecipientList').text = \
            str('recipients' in data['send-to']).lower()
    else:
        XML.SubElement(email, 'sendToRequester').text = 'false'
        XML.SubElement(email, 'sendToDevelopers').text = 'false'
        XML.SubElement(email, 'includeCulprits').text = 'false'
        XML.SubElement(email, 'sendToRecipientList').text = 'true'


def email_ext(parser, xml_parent, data):
    """yaml: email-ext
    Extend Jenkin's built in email notification
    Requires the Jenkins `Email-ext Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/Email-ext+plugin>`_

    :arg str recipients: Comma separated list of emails
    :arg str reply-to: Comma separated list of emails that should be in
        the Reply-To header for this project (default is $DEFAULT_RECIPIENTS)
    :arg str content-type: The content type of the emails sent. If not set, the
        Jenkins plugin uses the value set on the main configuration page.
        Possible values: 'html', 'text' or 'default' (default 'default')
    :arg str subject: Subject for the email, can include variables like
        ${BUILD_NUMBER} or even groovy or javascript code
    :arg str body: Content for the body of the email, can include variables
        like ${BUILD_NUMBER}, but the real magic is using groovy or
        javascript to hook into the Jenkins API itself
    :arg bool attach-build-log: Include build log in the email (default false)
    :arg str attachments: pattern of files to include as attachment (optional)
    :arg bool always: Send an email for every result (default false)
    :arg bool unstable: Send an email for an unstable result (default false)
    :arg bool first-failure: Send an email for just the first failure
        (default false)
    :arg bool not-built: Send an email if not built (default false)
    :arg bool aborted: Send an email if the build is aborted (default false)
    :arg bool regression: Send an email if there is a regression
        (default false)
    :arg bool failure: Send an email if the build fails (default true)
    :arg bool improvement: Send an email if the build improves (default false)
    :arg bool still-failing: Send an email if the build is still failing
        (default false)
    :arg bool success: Send an email for a successful build (default false)
    :arg bool fixed: Send an email if the build is fixed (default false)
    :arg bool still-unstable: Send an email if the build is still unstable
        (default false)
    :arg bool pre-build: Send an email before the build (default false)
    :arg str matrix-trigger: If using matrix projects, when to trigger

        :matrix-trigger values:
            * **both**
            * **only-parent**
            * **only-configurations**
    :arg list send-to: list of recipients from the predefined groups

        :send-to values:
            * **developers** (disabled by default)
            * **requester** (disabled by default)
            * **culprits** (disabled by default)
            * **recipients** (enabled by default)

    Example:

    .. literalinclude:: /../../tests/publishers/fixtures/email-ext001.yaml
    """

    emailext = XML.SubElement(xml_parent,
                              'hudson.plugins.emailext.ExtendedEmailPublisher')
    if 'recipients' in data:
        XML.SubElement(emailext, 'recipientList').text = data['recipients']
    else:
        XML.SubElement(emailext, 'recipientList').text = '$DEFAULT_RECIPIENTS'
    ctrigger = XML.SubElement(emailext, 'configuredTriggers')
    if data.get('always', False):
        base_email_ext(parser, ctrigger, data, 'AlwaysTrigger')
    if data.get('unstable', False):
        base_email_ext(parser, ctrigger, data, 'UnstableTrigger')
    if data.get('first-failure', False):
        base_email_ext(parser, ctrigger, data, 'FirstFailureTrigger')
    if data.get('not-built', False):
        base_email_ext(parser, ctrigger, data, 'NotBuiltTrigger')
    if data.get('aborted', False):
        base_email_ext(parser, ctrigger, data, 'AbortedTrigger')
    if data.get('regression', False):
        base_email_ext(parser, ctrigger, data, 'RegressionTrigger')
    if data.get('failure', True):
        base_email_ext(parser, ctrigger, data, 'FailureTrigger')
    if data.get('improvement', False):
        base_email_ext(parser, ctrigger, data, 'ImprovementTrigger')
    if data.get('still-failing', False):
        base_email_ext(parser, ctrigger, data, 'StillFailingTrigger')
    if data.get('success', False):
        base_email_ext(parser, ctrigger, data, 'SuccessTrigger')
    if data.get('fixed', False):
        base_email_ext(parser, ctrigger, data, 'FixedTrigger')
    if data.get('still-unstable', False):
        base_email_ext(parser, ctrigger, data, 'StillUnstableTrigger')
    if data.get('pre-build', False):
        base_email_ext(parser, ctrigger, data, 'PreBuildTrigger')

    content_type_mime = {
        'text': 'text/plain',
        'html': 'text/html',
        'default': 'default',
    }
    ctype = data.get('content-type', 'default')
    if ctype not in content_type_mime:
        raise JenkinsJobsException('email-ext content type must be one of: %s'
                                   % ', '.join(content_type_mime.keys()))
    XML.SubElement(emailext, 'contentType').text = content_type_mime[ctype]

    XML.SubElement(emailext, 'defaultSubject').text = data.get(
        'subject', '$DEFAULT_SUBJECT')
    XML.SubElement(emailext, 'defaultContent').text = data.get(
        'body', '$DEFAULT_CONTENT')
    XML.SubElement(emailext, 'attachmentsPattern').text = data.get(
        'attachments', '')
    XML.SubElement(emailext, 'presendScript').text = ''
    XML.SubElement(emailext, 'attachBuildLog').text = \
        str(data.get('attach-build-log', False)).lower()
    XML.SubElement(emailext, 'replyTo').text = data.get('reply-to',
                                                        '$DEFAULT_RECIPIENTS')
    matrix_dict = {'both': 'BOTH',
                   'only-configurations': 'ONLY_CONFIGURATIONS',
                   'only-parent': 'ONLY_PARENT'}
    matrix_trigger = data.get('matrix-trigger', None)
    ## If none defined, then do not create entry
    if matrix_trigger is not None:
        if matrix_trigger not in matrix_dict:
            raise JenkinsJobsException("matrix-trigger entered is not valid, "
                                       "must be one of: %s" %
                                       ", ".join(matrix_dict.keys()))
        XML.SubElement(emailext, 'matrixTriggerMode').text = \
            matrix_dict.get(matrix_trigger)


def fingerprint(parser, xml_parent, data):
    """yaml: fingerprint
    Fingerprint files to track them across builds

    :arg str files: files to fingerprint, follows the @includes of Ant fileset
        (default is blank)
    :arg bool record-artifacts: fingerprint all archived artifacts
        (default false)

    Example::

      publishers:
        - fingerprint:
            files: builddir/test*.xml
            record-artifacts: false
    """
    finger = XML.SubElement(xml_parent, 'hudson.tasks.Fingerprinter')
    XML.SubElement(finger, 'targets').text = data.get('files', '')
    XML.SubElement(finger, 'recordBuildArtifacts').text = str(data.get(
        'record-artifacts', False)).lower()


def aggregate_tests(parser, xml_parent, data):
    """yaml: aggregate-tests
    Aggregate downstream test results

    :arg bool include-failed-builds: whether to include failed builds

    Example::

      publishers:
        - aggregate-tests:
            include-failed-builds: true
    """
    agg = XML.SubElement(xml_parent,
                         'hudson.tasks.test.AggregatedTestResultPublisher')
    XML.SubElement(agg, 'includeFailedBuilds').text = str(data.get(
        'include-failed-builds', False)).lower()


def cppcheck(parser, xml_parent, data):
    """yaml: cppcheck
    Cppcheck result publisher
    Requires the Jenkins `Cppcheck Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/Cppcheck+Plugin>`_

    :arg str pattern: file pattern for cppcheck xml report

    for more optional parameters see the example

    Example::

      publishers:
        - cppcheck:
            pattern: "**/cppcheck.xml"
            # the rest is optional
            # build status (new) error count thresholds
            thresholds:
              unstable: 5
              new-unstable: 5
              failure: 7
              new-failure: 3
              # severities which count towards the threshold, default all true
              severity:
                error: true
                warning: true
                information: false
            graph:
              xysize: [500, 200]
              # which errors to display, default only sum
              display:
                sum: false
                error: true
    """
    cppextbase = XML.SubElement(xml_parent,
                                'org.jenkinsci.plugins.cppcheck.'
                                'CppcheckPublisher')
    cppext = XML.SubElement(cppextbase, 'cppcheckConfig')
    XML.SubElement(cppext, 'pattern').text = data['pattern']
    XML.SubElement(cppext, 'ignoreBlankFiles').text = \
        str(data.get('ignoreblankfiles', False)).lower()

    csev = XML.SubElement(cppext, 'configSeverityEvaluation')
    thrsh = data.get('thresholds', {})
    XML.SubElement(csev, 'threshold').text = str(thrsh.get('unstable', ''))
    XML.SubElement(csev, 'newThreshold').text = \
        str(thrsh.get('new-unstable', ''))
    XML.SubElement(csev, 'failureThreshold').text = \
        str(thrsh.get('failure', ''))
    XML.SubElement(csev, 'newFailureThreshold').text = \
        str(thrsh.get('new-failure', ''))
    XML.SubElement(csev, 'healthy').text = str(thrsh.get('healthy', ''))
    XML.SubElement(csev, 'unHealthy').text = str(thrsh.get('unhealthy', ''))

    sev = thrsh.get('severity', {})
    XML.SubElement(csev, 'severityError').text = \
        str(sev.get('error', True)).lower()
    XML.SubElement(csev, 'severityWarning').text = \
        str(sev.get('warning', True)).lower()
    XML.SubElement(csev, 'severityStyle').text = \
        str(sev.get('style', True)).lower()
    XML.SubElement(csev, 'severityPerformance').text = \
        str(sev.get('performance', True)).lower()
    XML.SubElement(csev, 'severityInformation').text = \
        str(sev.get('information', True)).lower()

    graph = data.get('graph', {})
    cgraph = XML.SubElement(cppext, 'configGraph')
    x, y = graph.get('xysize', [500, 200])
    XML.SubElement(cgraph, 'xSize').text = str(x)
    XML.SubElement(cgraph, 'ySize').text = str(y)
    gdisplay = graph.get('display', {})
    XML.SubElement(cgraph, 'displayAllErrors').text = \
        str(gdisplay.get('sum', True)).lower()
    XML.SubElement(cgraph, 'displayErrorSeverity').text = \
        str(gdisplay.get('error', False)).lower()
    XML.SubElement(cgraph, 'displayWarningSeverity').text = \
        str(gdisplay.get('warning', False)).lower()
    XML.SubElement(cgraph, 'displayStyleSeverity').text = \
        str(gdisplay.get('style', False)).lower()
    XML.SubElement(cgraph, 'displayPerformanceSeverity').text = \
        str(gdisplay.get('performance', False)).lower()
    XML.SubElement(cgraph, 'displayInformationSeverity').text = \
        str(gdisplay.get('information', False)).lower()


def logparser(parser, xml_parent, data):
    """yaml: logparser
    Requires the Jenkins `Log Parser Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/Log+Parser+Plugin>`_

    :arg str parse-rules: full path to parse rules
    :arg bool unstable-on-warning: mark build unstable on warning
    :arg bool fail-on-error: mark build failed on error

    Example::

      publishers:
        - logparser:
            parse-rules: "/path/to/parserules"
            unstable-on-warning: true
            fail-on-error: true
    """

    clog = XML.SubElement(xml_parent,
                          'hudson.plugins.logparser.LogParserPublisher')
    XML.SubElement(clog, 'unstableOnWarning').text = \
        str(data.get('unstable-on-warning', False)).lower()
    XML.SubElement(clog, 'failBuildOnError').text = \
        str(data.get('fail-on-error', False)).lower()
    # v1.08: this must be the full path, the name of the rules is not enough
    XML.SubElement(clog, 'parsingRulesPath').text = data.get('parse-rules', '')


def copy_to_master(parser, xml_parent, data):
    """yaml: copy-to-master
    Copy files to master from slave
    Requires the Jenkins `Copy To Slave Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/Copy+To+Slave+Plugin>`_

    :arg list includes: list of file patterns to copy
    :arg list excludes: list of file patterns to exclude
    :arg string destination: absolute path into which the files will be copied.
                             If left blank they will be copied into the
                             workspace of the current job

    Example::

      publishers:
        - copy-to-master:
            includes:
              - file1
              - file2*.txt
            excludes:
              - file2bad.txt
    """
    p = 'com.michelin.cio.hudson.plugins.copytoslave.CopyToMasterNotifier'
    cm = XML.SubElement(xml_parent, p)

    XML.SubElement(cm, 'includes').text = ','.join(data.get('includes', ['']))
    XML.SubElement(cm, 'excludes').text = ','.join(data.get('excludes', ['']))

    XML.SubElement(cm, 'destinationFolder').text = \
        data.get('destination', '')

    if data.get('destination', ''):
        XML.SubElement(cm, 'overrideDestinationFolder').text = 'true'


def jira(parser, xml_parent, data):
    """yaml: jira
    Update relevant JIRA issues
    Requires the Jenkins `JIRA Plugin
    <https://wiki.jenkins-ci.org/display/JENKINS/JIRA+Plugin>`_

    Example::

      publishers:
        - jira
    """
    XML.SubElement(xml_parent, 'hudson.plugins.jira.JiraIssueUpdater')


def groovy_postbuild(parser, xml_parent, data):
    """yaml: groovy-postbuild
    Execute a groovy script.
    Requires the Jenkins `Groovy Postbuild Plugin
    <https://wiki.jenkins-ci.org/display/JENKINS/Groovy+Postbuild+Plugin>`_

    :Parameter: the groovy script to execute

    Example::

      publishers:
        - groovy-postbuild: "manager.buildFailure()"

    """
    root_tag = 'org.jvnet.hudson.plugins.groovypostbuild.'\
        'GroovyPostbuildRecorder'
    groovy = XML.SubElement(xml_parent, root_tag)
    XML.SubElement(groovy, 'groovyScript').text = data


def base_publish_over(xml_parent, data, console_prefix,
                      plugin_tag, publisher_tag,
                      transferset_tag, reference_plugin_tag):
    outer = XML.SubElement(xml_parent, plugin_tag)
    XML.SubElement(outer, 'consolePrefix').text = console_prefix
    delegate = XML.SubElement(outer, 'delegate')
    publishers = XML.SubElement(delegate, 'publishers')
    inner = XML.SubElement(publishers, publisher_tag)
    XML.SubElement(inner, 'configName').text = data['site']
    XML.SubElement(inner, 'verbose').text = 'true'

    transfers = XML.SubElement(inner, 'transfers')
    transfersset = XML.SubElement(transfers, transferset_tag)
    XML.SubElement(transfersset, 'remoteDirectory').text = data['target']
    XML.SubElement(transfersset, 'sourceFiles').text = data['source']
    if 'command' in data:
        XML.SubElement(transfersset, 'execCommand').text = data['command']
    if 'timeout' in data:
        XML.SubElement(transfersset, 'execTimeout').text = str(data['timeout'])
    if 'use-pty' in data:
        XML.SubElement(transfersset, 'usePty').text = \
            str(data.get('use-pty', False)).lower()
    XML.SubElement(transfersset, 'excludes').text = data.get('excludes', '')
    XML.SubElement(transfersset, 'removePrefix').text = \
        data.get('remove-prefix', '')
    XML.SubElement(transfersset, 'remoteDirectorySDF').text = \
        str(data.get('target-is-date-format', False)).lower()
    XML.SubElement(transfersset, 'flatten').text = 'false'
    XML.SubElement(transfersset, 'cleanRemote').text = \
        str(data.get('clean-remote', False)).lower()

    XML.SubElement(inner, 'useWorkspaceInPromotion').text = 'false'
    XML.SubElement(inner, 'usePromotionTimestamp').text = 'false'
    XML.SubElement(delegate, 'continueOnError').text = 'false'
    XML.SubElement(delegate, 'failOnError').text = \
        str(data.get('fail-on-error', False)).lower()
    XML.SubElement(delegate, 'alwaysPublishFromMaster').text = 'false'
    XML.SubElement(delegate, 'hostConfigurationAccess',
                   {'class': reference_plugin_tag,
                    'reference': '../..'})
    return (outer, transfersset)


def cifs(parser, xml_parent, data):
    """yaml: cifs
    Upload files via CIFS.
    Requires the Jenkins `Publish over CIFS Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/Publish+Over+CIFS+Plugin>`_

    :arg str site: name of the cifs site/share
    :arg str target: destination directory
    :arg bool target-is-date-format: whether target is a date format. If true,
      raw text should be quoted (defaults to False)
    :arg bool clean-remote: should the remote directory be deleted before
      transferring files (defaults to False)
    :arg str source: source path specifier
    :arg str excludes: excluded file pattern (optional)
    :arg str remove-prefix: prefix to remove from uploaded file paths
      (optional)
    :arg bool fail-on-error: fail the build if an error occurs (defaults to
      False).

    Example::

      publishers:
        - cifs:
            site: 'cifs.share'
            target: 'dest/dir'
            source: 'base/source/dir/**'
            remove-prefix: 'base/source/dir'
            excludes: '**/*.excludedfiletype'
    """
    console_prefix = 'CIFS: '
    plugin_tag = 'jenkins.plugins.publish__over__cifs.CifsPublisherPlugin'
    publisher_tag = 'jenkins.plugins.publish__over__cifs.CifsPublisher'
    transfer_tag = 'jenkins.plugins.publish__over__cifs.CifsTransfer'
    plugin_reference_tag = 'jenkins.plugins.publish_over_cifs.'    \
        'CifsPublisherPlugin'
    base_publish_over(xml_parent,
                      data,
                      console_prefix,
                      plugin_tag,
                      publisher_tag,
                      transfer_tag,
                      plugin_reference_tag)


def cigame(parser, xml_parent, data):
    """yaml: cigame
    This plugin introduces a game where users get points
    for improving the builds.
    Requires the Jenkins `The Continuous Integration Game plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/
    The+Continuous+Integration+Game+plugin>`_

    Example:

    .. literalinclude:: /../../tests/publishers/fixtures/cigame.yaml
    """
    XML.SubElement(xml_parent, 'hudson.plugins.cigame.GamePublisher')


def sonar(parser, xml_parent, data):
    """yaml: sonar
    Sonar plugin support.
    Requires the Jenkins `Sonar Plugin.
    <http://docs.codehaus.org/pages/viewpage.action?pageId=116359341>`_

    :arg str jdk: JDK to use (inherited from the job if omitted). (optional)
    :arg str branch: branch onto which the analysis will be posted (optional)
    :arg str language: source code language (optional)
    :arg str maven-opts: options given to maven (optional)
    :arg str additional-properties: sonar analysis parameters (optional)
    :arg dict skip-global-triggers:
        :Triggers: * **skip-when-scm-change** (`bool`): skip analysis when
                     build triggered by scm
                   * **skip-when-upstream-build** (`bool`): skip analysis when
                     build triggered by an upstream build
                   * **skip-when-envvar-defined** (`str`): skip analysis when
                     the specified environment variable is set to true

    This publisher supports the post-build action exposed by the Jenkins
    Sonar Plugin, which is triggering a Sonar Analysis with Maven.

    Example::

      publishers:
        - sonar:
            jdk: MyJdk
            branch: myBranch
            language: java
            maven-opts: -DskipTests
            additional-properties: -DsonarHostURL=http://example.com/
            skip-global-triggers:
                skip-when-scm-change: true
                skip-when-upstream-build: true
                skip-when-envvar-defined: SKIP_SONAR
    """
    sonar = XML.SubElement(xml_parent, 'hudson.plugins.sonar.SonarPublisher')
    if 'jdk' in data:
        XML.SubElement(sonar, 'jdk').text = data['jdk']
    XML.SubElement(sonar, 'branch').text = data.get('branch', '')
    XML.SubElement(sonar, 'language').text = data.get('language', '')
    XML.SubElement(sonar, 'mavenOpts').text = data.get('maven-opts', '')
    XML.SubElement(sonar, 'jobAdditionalProperties').text = \
        data.get('additional-properties', '')
    if 'skip-global-triggers' in data:
        data_triggers = data['skip-global-triggers']
        triggers = XML.SubElement(sonar, 'triggers')
        XML.SubElement(triggers, 'skipScmCause').text =   \
            str(data_triggers.get('skip-when-scm-change', False)).lower()
        XML.SubElement(triggers, 'skipUpstreamCause').text =  \
            str(data_triggers.get('skip-when-upstream-build', False)).lower()
        XML.SubElement(triggers, 'envVar').text =  \
            data_triggers.get('skip-when-envvar-defined', '')


def performance(parser, xml_parent, data):
    """yaml: performance
    Publish performance test results from jmeter and junit.
    Requires the Jenkins `Performance Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/Performance+Plugin>`_

    :arg int failed-threshold: Specify the error percentage threshold that
                               set the build failed. A negative value means
                               don't use this threshold (default 0)
    :arg int unstable-threshold: Specify the error percentage threshold that
                                 set the build unstable. A negative value means
                                 don't use this threshold (default 0)
    :arg dict report:

       :(jmeter or junit): (`dict` or `str`): Specify a custom report file
         (optional; jmeter default \**/*.jtl, junit default **/TEST-\*.xml)

    Examples::

      publishers:
        - performance:
            failed-threshold: 85
            unstable-threshold: -1
            report:
               - jmeter: "/special/file.jtl"
               - junit: "/special/file.xml"

      publishers:
        - performance:
            failed-threshold: 85
            unstable-threshold: -1
            report:
               - jmeter
               - junit

      publishers:
        - performance:
            failed-threshold: 85
            unstable-threshold: -1
            report:
               - jmeter: "/special/file.jtl"
               - junit: "/special/file.xml"
               - jmeter
               - junit
    """
    logger = logging.getLogger(__name__)

    perf = XML.SubElement(xml_parent, 'hudson.plugins.performance.'
                                      'PerformancePublisher')
    XML.SubElement(perf, 'errorFailedThreshold').text = str(data.get(
        'failed-threshold', 0))
    XML.SubElement(perf, 'errorUnstableThreshold').text = str(data.get(
        'unstable-threshold', 0))
    parsers = XML.SubElement(perf, 'parsers')
    for item in data['report']:
        if isinstance(item, dict):
            item_name = item.keys()[0]
            item_values = item.get(item_name, None)
            if item_name == 'jmeter':
                jmhold = XML.SubElement(parsers, 'hudson.plugins.performance.'
                                                 'JMeterParser')
                XML.SubElement(jmhold, 'glob').text = str(item_values)
            elif item_name == 'junit':
                juhold = XML.SubElement(parsers, 'hudson.plugins.performance.'
                                                 'JUnitParser')
                XML.SubElement(juhold, 'glob').text = str(item_values)
            else:
                logger.fatal("You have not specified jmeter or junit, or "
                             "you have incorrectly assigned the key value.")
                sys.exit(1)
        elif isinstance(item, str):
            if item == 'jmeter':
                jmhold = XML.SubElement(parsers, 'hudson.plugins.performance.'
                                                 'JMeterParser')
                XML.SubElement(jmhold, 'glob').text = '**/*.jtl'
            elif item == 'junit':
                juhold = XML.SubElement(parsers, 'hudson.plugins.performance.'
                                                 'JUnitParser')
                XML.SubElement(juhold, 'glob').text = '**/TEST-*.xml'
            else:
                logger.fatal("You have not specified jmeter or junit, or "
                             "you have incorrectly assigned the key value.")
                sys.exit(1)


def join_trigger(parser, xml_parent, data):
    """yaml: join-trigger
    Trigger a job after all the immediate downstream jobs have completed

    :arg list projects: list of projects to trigger

    Example::

      publishers:
        - join-trigger:
            projects:
              - project-one
              - project-two
    """
    jointrigger = XML.SubElement(xml_parent, 'join.JoinTrigger')

    # Simple Project List
    joinProjectsText = ','.join(data.get('projects', ['']))
    XML.SubElement(jointrigger, 'joinProjects').text = joinProjectsText


def jabber(parser, xml_parent, data):
    """yaml: jabber
    Integrates Jenkins with the Jabber/XMPP instant messaging protocol
    Requires the Jenkins `Jabber Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/Jabber+Plugin>`_

    :arg bool notify-on-build-start: Whether to send notifications
        to channels when a build starts (default false)
    :arg bool notify-scm-committers: Whether to send notifications
        to the users that are suspected of having broken this build
        (default false)
    :arg bool notify-scm-culprits: Also send notifications to 'culprits'
        from previous unstable/failed builds (default false)
    :arg bool notify-upstream-committers: Whether to send notifications to
        upstream committers if no committers were found for a broken build
        (default false)
    :arg bool notify-scm-fixers: Whether to send notifications to the users
        that have fixed a broken build (default false)
    :arg list group-targets: List of group targets to notify
    :arg list individual-targets: List of individual targets to notify
    :arg dict strategy: When to send notifications (default all)

        :strategy values:
          * **all** -- Always
          * **failure** -- On any failure
          * **failure-fixed** -- On failure and fixes
          * **change** -- Only on state change
    :arg dict message: Channel notification message (default summary-scm)

        :message  values:
          * **summary-scm** -- Summary + SCM changes
          * **summary** -- Just summary
          * **summary-build** -- Summary and build parameters
          * **summary-scm-fail** -- Summary, SCM changes, and failed tests

    Example::

      publishers:
        - jabber:
            notify-on-build-start: true
            group-targets:
              - "foo-room@conference-2-fooserver.foo.com"
            individual-targets:
              - "foo-user@conference-2-fooserver.foo.com"
            strategy: all
            message: summary-scm
    """
    j = XML.SubElement(xml_parent, 'hudson.plugins.jabber.im.transport.'
                       'JabberPublisher')
    t = XML.SubElement(j, 'targets')
    if 'group-targets' in data:
        for group in data['group-targets']:
            gcimt = XML.SubElement(t, 'hudson.plugins.im.'
                                   'GroupChatIMMessageTarget')
            XML.SubElement(gcimt, 'name').text = group
            XML.SubElement(gcimt, 'notificationOnly').text = 'false'
    if 'individual-targets' in data:
        for individual in data['individual-targets']:
            dimt = XML.SubElement(t, 'hudson.plugins.im.'
                                  'DefaultIMMessageTarget')
            XML.SubElement(dimt, 'value').text = individual
    strategy = data.get('strategy', 'all')
    strategydict = {'all': 'ALL',
                    'failure': 'ANY_FAILURE',
                    'failure-fixed': 'FAILURE_AND_FIXED',
                    'change': 'STATECHANGE_ONLY'}
    if strategy not in strategydict:
        raise JenkinsJobsException("Strategy entered is not valid, must be " +
                                   "one of: all, failure, failure-fixed, or "
                                   "change")
    XML.SubElement(j, 'strategy').text = strategydict[strategy]
    XML.SubElement(j, 'notifyOnBuildStart').text = str(
        data.get('notify-on-build-start', False)).lower()
    XML.SubElement(j, 'notifySuspects').text = str(
        data.get('notify-scm-committers', False)).lower()
    XML.SubElement(j, 'notifyCulprits').text = str(
        data.get('notify-scm-culprits', False)).lower()
    XML.SubElement(j, 'notifyFixers').text = str(
        data.get('notify-scm-fixers', False)).lower()
    XML.SubElement(j, 'notifyUpstreamCommitters').text = str(
        data.get('notify-upstream-committers', False)).lower()
    message = data.get('message', 'summary-scm')
    messagedict = {'summary-scm': 'DefaultBuildToChatNotifier',
                   'summary': 'SummaryOnlyBuildToChatNotifier',
                   'summary-build': 'BuildParametersBuildToChatNotifier',
                   'summary-scm-fail': 'PrintFailingTestsBuildToChatNotifier'}
    if message not in messagedict:
        raise JenkinsJobsException("Message entered is not valid, must be one "
                                   "of: summary-scm, summary, summary-build "
                                   "or summary-scm-fail")
    XML.SubElement(j, 'buildToChatNotifier', {
        'class': 'hudson.plugins.im.build_notify.' + messagedict[message]})
    XML.SubElement(j, 'matrixMultiplier').text = 'ONLY_CONFIGURATIONS'


def workspace_cleanup(parser, xml_parent, data):
    """yaml: workspace-cleanup (post-build)

    Requires the Jenkins `Workspace Cleanup Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/Workspace+Cleanup+Plugin>`_

    The pre-build workspace-cleanup is available as a wrapper.

    :arg list include: list of files to be included
    :arg list exclude: list of files to be excluded
    :arg bool dirmatch: Apply pattern to directories too (default: false)
    :arg list clean-if: clean depending on build status

        :clean-if values:
            * **success** (`bool`) (default: true)
            * **unstable** (`bool`) (default: true)
            * **failure** (`bool`) (default: true)
            * **aborted** (`bool`) (default: true)
            * **not-built** (`bool`)  (default: true)
    :arg bool fail-build: Fail the build if the cleanup fails (default: true)
    :arg bool clean-parent: Cleanup matrix parent workspace (default: false)

    Example::

      publishers:
        - workspace-cleanup:
            include:
              - "*.zip"
            clean-if:
              - success: true
              - not-built: false
    """

    p = XML.SubElement(xml_parent,
                       'hudson.plugins.ws__cleanup.WsCleanup')
    p.set("plugin", "ws-cleanup@0.14")
    if "include" in data or "exclude" in data:
        patterns = XML.SubElement(p, 'patterns')

    for inc in data.get("include", []):
        ptrn = XML.SubElement(patterns, 'hudson.plugins.ws__cleanup.Pattern')
        XML.SubElement(ptrn, 'pattern').text = inc
        XML.SubElement(ptrn, 'type').text = "INCLUDE"

    for exc in data.get("exclude", []):
        ptrn = XML.SubElement(patterns, 'hudson.plugins.ws__cleanup.Pattern')
        XML.SubElement(ptrn, 'pattern').text = exc
        XML.SubElement(ptrn, 'type').text = "EXCLUDE"

    XML.SubElement(p, 'deleteDirs').text = \
        str(data.get("dirmatch", False)).lower()
    XML.SubElement(p, 'cleanupMatrixParent').text = \
        str(data.get("clean-parent", False)).lower()

    mask = {'success': 'cleanWhenSuccess', 'unstable': 'cleanWhenUnstable',
            'failure': 'cleanWhenFailure', 'not-built': 'cleanWhenNotBuilt',
            'aborted': 'cleanWhenAborted'}
    clean = data.get('clean-if', [])
    cdict = dict()
    for d in clean:
        cdict.update(d)
    for k, v in mask.iteritems():
        XML.SubElement(p, v).text = str(cdict.pop(k, True)).lower()

    if len(cdict) > 0:
        raise ValueError('clean-if must be one of: %r' % list(mask.keys()))

    if str(data.get("fail-build", False)).lower() == 'false':
        XML.SubElement(p, 'notFailBuild').text = 'true'
    else:
        XML.SubElement(p, 'notFailBuild').text = 'false'


def maven_deploy(parser, xml_parent, data):
    """yaml: maven-deploy
    Deploy artifacts to Maven repository.

    :arg str id: Repository ID
    :arg str url: Repository URL
    :arg bool unique-version: Assign unique versions to snapshots
      (default true)
    :arg bool deploy-unstable: Deploy even if the build is unstable
      (default false)


    Example::

      publishers:
        - maven-deploy:
            id: example
            url: http://repo.example.com/maven2/
            unique-version: true
            deploy-unstable: false
    """

    p = XML.SubElement(xml_parent, 'hudson.maven.RedeployPublisher')
    if 'id' in data:
        XML.SubElement(p, 'id').text = data['id']
    XML.SubElement(p, 'url').text = data['url']
    XML.SubElement(p, 'uniqueVersion').text = str(
        data.get('unique-version', True)).lower()
    XML.SubElement(p, 'evenIfUnstable').text = str(
        data.get('deploy-unstable', False)).lower()


def text_finder(parser, xml_parent, data):
    """yaml: text-finder
    This plugin lets you search keywords in the files you specified and
    additionally check build status

    Requires the Jenkins `Text-finder Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/Text-finder+Plugin>`_

    :arg str regexp: Specify a regular expression
    :arg str fileset: Specify the path to search
    :arg bool also-check-console-output:
              Search the console output (default False)
    :arg bool succeed-if-found:
              Force a build to succeed if a string was found (default False)
    :arg bool unstable-if-found:
              Set build unstable instead of failing the build (default False)


    Example::

        publishers:
            - text-finder:
                regexp: "some string"
                fileset: "file.txt"
                also-check-console-output: true
                succeed-if-found: false
                unstable-if-found: false
    """

    finder = XML.SubElement(xml_parent,
                            'hudson.plugins.textfinder.TextFinderPublisher')
    if ('fileset' in data):
        XML.SubElement(finder, 'fileSet').text = data['fileset']
    XML.SubElement(finder, 'regexp').text = data['regexp']
    check_output = str(data.get('also-check-console-output', False)).lower()
    XML.SubElement(finder, 'alsoCheckConsoleOutput').text = check_output
    succeed_if_found = str(data.get('succeed-if-found', False)).lower()
    XML.SubElement(finder, 'succeedIfFound').text = succeed_if_found
    unstable_if_found = str(data.get('unstable-if-found', False)).lower()
    XML.SubElement(finder, 'unstableIfFound').text = unstable_if_found


def html_publisher(parser, xml_parent, data):
    """yaml: html-publisher
    This plugin publishes HTML reports.

    Requires the Jenkins `HTML Publisher Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/HTML+Publisher+Plugin>`_

    :arg str name: Report name
    :arg str dir: HTML directory to archive
    :arg str files: Specify the pages to display
    :arg bool keep-all: keep HTML reports for each past build (Default False)
    :arg bool allow-missing: Allow missing HTML reports (Default False)


    Example::

        publishers:
            - html-publisher:
                name: "some name"
                dir: "path/"
                files: "index.html"
                keep-all: true
                allow-missing: true
    """

    reporter = XML.SubElement(xml_parent, 'htmlpublisher.HtmlPublisher')
    targets = XML.SubElement(reporter, 'reportTargets')
    ptarget = XML.SubElement(targets, 'htmlpublisher.HtmlPublisherTarget')
    XML.SubElement(ptarget, 'reportName').text = data['name']
    XML.SubElement(ptarget, 'reportDir').text = data['dir']
    XML.SubElement(ptarget, 'reportFiles').text = data['files']
    keep_all = str(data.get('keep-all', False)).lower()
    XML.SubElement(ptarget, 'keepAll').text = keep_all
    allow_missing = str(data.get('allow-missing', False)).lower()
    XML.SubElement(ptarget, 'allowMissing').text = allow_missing
    XML.SubElement(ptarget, 'wrapperName').text = "htmlpublisher-wrapper.html"


def tap(parser, xml_parent, data):
    """yaml: tap
    Adds support to TAP test result files

    Requires the Jenkins `TAP Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/TAP+Plugin>`_

    :arg str results: TAP test result files
    :arg bool fail-if-no-results: Fail if no result (default False)
    :arg bool failed-tests-mark-build-as-failure:
                Mark build as failure if test fails (default False)
    :arg bool output-tap-to-console: Output tap to console (default True)
    :arg bool enable-subtests: Enable subtests (Default True)
    :arg bool discard-old-reports: Discard old reports (Default False)
    :arg bool todo-is-failure: Handle TODO's as failures (Default True)


    Example::

        publishers:
            - tap:
                results: puiparts.tap
                todo-is-failure: false
    """

    tap = XML.SubElement(xml_parent, 'org.tap4j.plugin.TapPublisher')

    XML.SubElement(tap, 'testResults').text = data['results']

    XML.SubElement(tap, 'failIfNoResults').text = str(
        data.get('fail-if-no-results', False)).lower()

    XML.SubElement(tap, 'failedTestsMarkBuildAsFailure').text = str(
        data.get('failed-tests-mark-build-as-failure', False)).lower()

    XML.SubElement(tap, 'outputTapToConsole').text = str(
        data.get('output-tap-to-console', True)).lower()

    XML.SubElement(tap, 'enableSubtests').text = str(
        data.get('enable-subtests', True)).lower()

    XML.SubElement(tap, 'discardOldReports').text = str(
        data.get('discard-old-reports', False)).lower()

    XML.SubElement(tap, 'todoIsFailure').text = str(
        data.get('todo-is-failure', True)).lower()


def post_tasks(parser, xml_parent, data):
    """yaml: post-tasks
    Adds support to post build task plugin

    Requires the Jenkins `Post Build Task plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/Post+build+task>`_

    :arg dict task: Post build task definition
    :arg list task[matches]: list of matches when to run the task
    :arg dict task[matches][*]: match definition
    :arg str task[matches][*][log-text]: text to match against the log
    :arg str task[matches][*][operator]: operator to apply with the next match

        :task[matches][*][operator] values (default 'AND'):
            * **AND**
            * **OR**

    :arg bool task[escalate-status]: Escalate the task status to the job
        (default 'false')
    :arg bool task[run-if-job-successful]: Run only if the job was successful
        (default 'false')
    :arg str task[script]: Shell script to run (default '')

    Example::

        publishers:
            - post-tasks:
                - matches:
                    - log-text: line to match
                      operator: AND
                    - log-text: line to match
                      operator: OR
                    - log-text: line to match
                      operator: AND
                  escalate-status: false
                  run-if-job-successful:false
                  script: |
                    echo "Here goes the task script"
    """

    pb_xml = XML.SubElement(xml_parent,
                            'hudson.plugins.postbuildtask.PostbuildTask')
    tasks_xml = XML.SubElement(pb_xml, 'tasks')
    for task in data:
        task_xml = XML.SubElement(
            tasks_xml,
            'hudson.plugins.postbuildtask.TaskProperties')
        matches_xml = XML.SubElement(task_xml, 'logTexts')
        for match in task.get('matches', []):
            lt_xml = XML.SubElement(
                matches_xml,
                'hudson.plugins.postbuildtask.LogProperties')
            XML.SubElement(lt_xml, 'logText').text = str(
                match.get('log-text', ''))
            XML.SubElement(lt_xml, 'operator').text = str(
                match.get('operator', 'AND')).upper()
        XML.SubElement(task_xml, 'EscalateStatus').text = str(
            task.get('escalate-status', False)).lower()
        XML.SubElement(task_xml, 'RunIfJobSuccessful').text = str(
            task.get('run-if-job-successful', False)).lower()
        XML.SubElement(task_xml, 'script').text = str(
            task.get('script', ''))


def postbuildscript(parser, xml_parent, data):
    """yaml: postbuildscript
    Executes additional builders, script or Groovy after the build is
    complete.

    Requires the Jenkins `Post Build Script plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/PostBuildScript+Plugin>`_

    :arg list generic-script: Paths to Batch/Shell scripts
    :arg list groovy-script: Paths to Groovy scripts
    :arg list groovy: Inline Groovy
    :arg list builders: Any supported builders, see :doc:`builders`.
    :arg bool onsuccess: Scripts and builders are run only if the build succeed
                         (default False)
    :arg bool onfailure: Scripts and builders are run only if the build fail
                         (default True)
    :arg str execute-on: For matrix projects, scripts can be run after each
                         axis is built (`axes`), after all axis of the matrix
                         are built (`matrix`) or after each axis AND the matrix
                         are built (`both`).

    The `onsuccess` and `onfailure` options are confusing. If you want
    the post build to always run regardless of the build status, you
    should set them both to `false`.

    Example:

    .. literalinclude:: /../../tests/publishers/fixtures/\
postbuildscript001.yaml

    You can also execute :doc:`builders </builders>`:

    .. literalinclude:: /../../tests/publishers/fixtures/\
postbuildscript002.yaml

    Run once after the whole matrix (all axes) is built:

    .. literalinclude:: /../../tests/publishers/fixtures/\
postbuildscript003.yaml

    """

    pbs_xml = XML.SubElement(
        xml_parent,
        'org.jenkinsci.plugins.postbuildscript.PostBuildScript')

    # Shell/Groovy in a file
    script_types = {
        'generic': 'GenericScript',
        'groovy': 'GroovyScriptFile',
    }
    for script_type in script_types.keys():
        if script_type + '-script' not in data:
            continue

        scripts_xml = XML.SubElement(pbs_xml, script_type + 'ScriptFileList')
        for shell_scripts in [data.get(script_type + '-script', [])]:
            for shell_script in shell_scripts:
                script_xml = XML.SubElement(
                    scripts_xml,
                    'org.jenkinsci.plugins.postbuildscript.'
                    + script_types[script_type])
                file_path_xml = XML.SubElement(script_xml, 'filePath')
                file_path_xml.text = shell_script

    # Inlined Groovy
    if 'groovy' in data:
        groovy_inline_xml = XML.SubElement(pbs_xml, 'groovyScriptContentList')
        for groovy in data.get('groovy', []):
            groovy_xml = XML.SubElement(
                groovy_inline_xml,
                'org.jenkinsci.plugins.postbuildscript.GroovyScriptContent'
            )
            groovy_content = XML.SubElement(groovy_xml, 'content')
            groovy_content.text = groovy

    # Inject builders
    if 'builders' in data:
        build_steps_xml = XML.SubElement(pbs_xml, 'buildSteps')
        for builder in data.get('builders', []):
            parser.registry.dispatch('builder', parser, build_steps_xml,
                                     builder)

    # When to run the build? Note the plugin let one specify both options
    # although they are antinomic
    success_xml = XML.SubElement(pbs_xml, 'scriptOnlyIfSuccess')
    success_xml.text = str(data.get('onsuccess', True)).lower()
    failure_xml = XML.SubElement(pbs_xml, 'scriptOnlyIfFailure')
    failure_xml.text = str(data.get('onfailure', False)).lower()

    # TODO: we may want to avoid setting "execute-on" on non-matrix jobs,
    # either by skipping this part or by raising an error to let the user know
    # an attempt was made to set execute-on on a non-matrix job. There are
    # currently no easy ways to check for this though.
    if 'execute-on' in data:
        valid_values = ('matrix', 'axes', 'both')
        execute_on = data['execute-on'].lower()
        if execute_on not in valid_values:
            raise JenkinsJobsException(
                'execute-on must be one of %s, got %s' %
                valid_values, execute_on
            )
        execute_on_xml = XML.SubElement(pbs_xml, 'executeOn')
        execute_on_xml.text = execute_on.upper()


def xml_summary(parser, xml_parent, data):
    """yaml: xml-summary
    Adds support for the Summary Display Plugin

    Requires the Jenkins `Summary Display Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/Summary+Display+Plugin>`_

    :arg str files: Files to parse (default '')

    Example::

        publishers:
            - xml-summary:
                files: '*_summary_report.xml'
    """

    summary = XML.SubElement(xml_parent,
                             'hudson.plugins.summary__report.'
                             'ACIPluginPublisher')
    XML.SubElement(summary, 'name').text = data['files']


def robot(parser, xml_parent, data):
    """yaml: robot
    Adds support for the Robot Framework Plugin

    Requires the Jenkins `Robot Framework Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/Robot+Framework+Plugin>`_

    :arg str output-path: Path to directory containing robot xml and html files
        relative to build workspace. (default '')
    :arg str log-file-link: Name of log or report file to be linked on jobs
        front page (default '')
    :arg str report-html: Name of the html file containing robot test report
        (default 'report.html')
    :arg str log-html: Name of the html file containing detailed robot test log
        (default 'log.html')
    :arg str output-xml: Name of the xml file containing robot output
        (default 'output.xml')
    :arg str pass-threshold: Minimum percentage of passed tests to consider
        the build successful (default 0.0)
    :arg str unstable-threshold: Minimum percentage of passed test to
        consider the build as not failed (default 0.0)
    :arg bool only-critical: Take only critical tests into account when
        checking the thresholds (default true)
    :arg list other-files: list other files to archive (default '')

    Example::

        - publishers:
            - robot:
                output-path: reports/robot
                log-file-link: report.html
                report-html: report.html
                log-html: log.html
                output-xml: output.xml
                pass-threshold: 80.0
                unstable-threshold: 60.0
                only-critical: false
                other-files:
                    - extra-file1.html
                    - extra-file2.txt
    """
    parent = XML.SubElement(xml_parent, 'hudson.plugins.robot.RobotPublisher')
    XML.SubElement(parent, 'outputPath').text = data['output-path']
    XML.SubElement(parent, 'logFileLink').text = str(
        data.get('log-file-link', ''))
    XML.SubElement(parent, 'reportFileName').text = str(
        data.get('report-html', 'report.html'))
    XML.SubElement(parent, 'logFileName').text = str(
        data.get('log-html', 'log.html'))
    XML.SubElement(parent, 'outputFileName').text = str(
        data.get('output-xml', 'output.xml'))
    XML.SubElement(parent, 'passThreshold').text = str(
        data.get('pass-threshold', 0.0))
    XML.SubElement(parent, 'unstableThreshold').text = str(
        data.get('unstable-threshold', 0.0))
    XML.SubElement(parent, 'onlyCritical').text = str(
        data.get('only-critical', True)).lower()
    other_files = XML.SubElement(parent, 'otherFiles')
    for other_file in data['other-files']:
        XML.SubElement(other_files, 'string').text = str(other_file)


def warnings(parser, xml_parent, data):
    """yaml: warnings
    Generate trend report for compiler warnings in the console log or
    in log files.  Requires the Jenkins `Warnings Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/Warnings+Plugin>`_

    :arg list console-log-parsers: The parser to use to scan the console
        log (default '')
    :arg dict workspace-file-scanners:

        :workspace-file-scanners:
            * **file-pattern** (`str`) -- Fileset 'includes' setting that
                specifies the files to scan for warnings
            * **scanner** (`str`) -- The parser to use to scan the files
                provided in workspace-file-pattern (default '')
    :arg str files-to-include: Comma separated list of regular
        expressions that specifies the files to include in the report
        (based on their absolute filename). By default all files are
        included
    :arg str files-to-ignore: Comma separated list of regular expressions
        that specifies the files to exclude from the report (based on their
        absolute filename). (default '')
    :arg bool run-always: By default, this plug-in runs only for stable or
        unstable builds, but not for failed builds.  Set to true if the
        plug-in should run even for failed builds.  (default false)
    :arg bool detect-modules: Determines if Ant or Maven modules should be
        detected for all files that contain warnings.  Activating this
        option may increase your build time since the detector scans
        the whole workspace for 'build.xml' or 'pom.xml' files in order
        to assign the correct module names. (default false)
    :arg bool resolve-relative-paths: Determines if relative paths in
        warnings should be resolved using a time expensive operation that
        scans the whole workspace for matching files.  Deactivate this
        option if you encounter performance problems.  (default false)
    :arg int health-threshold-high: The upper threshold for the build
        health.  If left empty then no health report is created.  If
        the actual number of warnings is between the provided
        thresholds then the build health is interpolated (default '')
    :arg int health-threshold-low: The lower threshold for the build
        health.  See health-threshold-high.  (default '')
    :arg dict health-priorities: Determines which warning priorities
        should be considered when evaluating the build health (default
        all-priorities)

        :health-priorities values:
          * **priority-high** -- Only priority high
          * **high-and-normal** -- Priorities high and normal
          * **all-priorities** -- All priorities
    :arg dict total-thresholds: If the number of total warnings is greater
        than one of these thresholds then a build is considered as unstable
        or failed, respectively. (default '')

        :total-thresholds:
            * **unstable** (`dict`)
                :unstable: * **total-all** (`int`)
                           * **total-high** (`int`)
                           * **total-normal** (`int`)
                           * **total-low** (`int`)
            * **failed** (`dict`)
                :failed: * **total-all** (`int`)
                         * **total-high** (`int`)
                         * **total-normal** (`int`)
                         * **total-low** (`int`)
    :arg dict new-thresholds: If the specified number of new warnings exceeds
        one of these thresholds then a build is considered as unstable or
        failed, respectively.  (default '')

        :new-thresholds:
            * **unstable** (`dict`)
                :unstable: * **new-all** (`int`)
                           * **new-high** (`int`)
                           * **new-normal** (`int`)
                           * **new-low** (`int`)
            * **failed** (`dict`)
                :failed: * **new-all** (`int`)
                         * **new-high** (`int`)
                         * **new-normal** (`int`)
                         * **new-high** (`int`)
    :arg bool use-delta-for-new-warnings:  If set then the number of new
        warnings is calculated by subtracting the total number of warnings
        of the current build from the reference build. This may lead to wrong
        results if you have both fixed and new warnings in a build. If not set,
        then the number of new warnings is calculated by an asymmetric set
        difference of the warnings in the current and reference build. This
        will find all new warnings even if the number of total warnings is
        decreasing. However, sometimes false positives will be reported due
        to minor changes in a warning (refactoring of variable of method
        names, etc.) (default false)
    :arg bool only-use-stable-builds-as-reference: The number of new warnings
        will be calculated based on the last stable build, allowing reverts
        of unstable builds where the number of warnings was decreased.
        (default false)
    :arg str default-encoding: Default encoding when parsing or showing files
        Leave empty to use default encoding of platform (default '')

    Example::

      publishers:
        - warnings:
            console-log-parsers:
              - FxCop
              - CodeAnalysis
            workspace-file-scanners:
              - file-pattern: '**/*.out'
                scanner: 'AcuCobol Compiler
              - file-pattern: '**/*.warnings'
                scanner: FxCop
            files-to-include: '[a-zA-Z]\.java,[a-zA-Z]\.cpp'
            files-to-ignore: '[a-zA-Z]\.html,[a-zA-Z]\.js'
            run-always: true
            detect-modules: true
            resolve-relative-paths: true
            health-threshold-high: 50
            health-threshold-low: 25
            health-priorities: high-and-normal
            total-thresholds:
                unstable:
                    total-all: 90
                    total-high: 90
                    total-normal: 40
                    total-low: 30
                failed:
                    total-all: 100
                    total-high: 100
                    total-normal: 50
                    total-low: 40
            new-thresholds:
                unstable:
                    new-all: 100
                    new-high: 50
                    new-normal: 30
                    new-low: 10
                failed:
                    new-all: 100
                    new-high: 60
                    new-normal: 50
                    new-low: 40
            use-delta-for-new-warnings: true
            only-use-stable-builds-as-reference: true
            default-encoding: ISO-8859-9
    """

    warnings = XML.SubElement(xml_parent,
                              'hudson.plugins.warnings.'
                              'WarningsPublisher')
    console = XML.SubElement(warnings, 'consoleParsers')
    for parser in data.get('console-log-parsers', []):
        console_parser = XML.SubElement(console,
                                        'hudson.plugins.warnings.'
                                        'ConsoleParser')
        XML.SubElement(console_parser, 'parserName').text = parser
    workspace = XML.SubElement(warnings, 'parserConfigurations')
    for wfs in data.get('workspace-file-scanners', []):
        workspace_pattern = XML.SubElement(workspace,
                                           'hudson.plugins.warnings.'
                                           'ParserConfiguration')
        XML.SubElement(workspace_pattern, 'pattern').text = \
            wfs['file-pattern']
        XML.SubElement(workspace_pattern, 'parserName').text = \
            wfs['scanner']
    warnings_to_include = data.get('files-to-include', '')
    XML.SubElement(warnings, 'includePattern').text = warnings_to_include
    warnings_to_ignore = data.get('files-to-ignore', '')
    XML.SubElement(warnings, 'excludePattern').text = warnings_to_ignore
    run_always = str(data.get('run-always', False)).lower()
    XML.SubElement(warnings, 'canRunOnFailed').text = run_always
    detect_modules = str(data.get('detect-modules', False)).lower()
    XML.SubElement(warnings, 'shouldDetectModules').text = detect_modules
    #Note the logic reversal (included here to match the GUI)
    XML.SubElement(warnings, 'doNotResolveRelativePaths').text = \
        str(not data.get('resolve-relative-paths', False)).lower()
    health_threshold_high = str(data.get('health-threshold-high', ''))
    XML.SubElement(warnings, 'healthy').text = health_threshold_high
    health_threshold_low = str(data.get('health-threshold-low', ''))
    XML.SubElement(warnings, 'unHealthy').text = health_threshold_low
    prioritiesDict = {'priority-high': 'high',
                      'high-and-normal': 'normal',
                      'all-priorities': 'low'}
    priority = data.get('health-priorities', 'all-priorities')
    if priority not in prioritiesDict:
        raise JenkinsJobsException("Health-Priority entered is not valid must "
                                   "be one of: %s" %
                                   ",".join(prioritiesDict.keys()))
    XML.SubElement(warnings, 'thresholdLimit').text = prioritiesDict[priority]
    td = XML.SubElement(warnings, 'thresholds')
    for base in ["total", "new"]:
        thresholds = data.get("%s-thresholds" % base, {})
        for status in ["unstable", "failed"]:
            bystatus = thresholds.get(status, {})
            for level in ["all", "high", "normal", "low"]:
                val = str(bystatus.get("%s-%s" % (base, level), ''))
                XML.SubElement(td, "%s%s%s" % (status,
                               base.capitalize(), level.capitalize())
                               ).text = val
    if data.get('new-thresholds'):
        XML.SubElement(warnings, 'dontComputeNew').text = 'false'
        delta = data.get('use-delta-for-new-warnings', False)
        XML.SubElement(warnings, 'useDeltaValues').text = str(delta).lower()
        use_stable_builds = data.get('only-use-stable-builds-as-reference',
                                     False)
        XML.SubElement(warnings, 'useStableBuildAsReference').text = str(
            use_stable_builds).lower()
    else:
        XML.SubElement(warnings, 'dontComputeNew').text = 'true'
        XML.SubElement(warnings, 'useStableBuildAsReference').text = 'false'
        XML.SubElement(warnings, 'useDeltaValues').text = 'false'
    encoding = data.get('default-encoding', '')
    XML.SubElement(warnings, 'defaultEncoding').text = encoding


def sloccount(parser, xml_parent, data):
    """yaml: sloccount
    Generates the trend report for SLOCCount

    Requires the Jenkins `SLOCCount Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/SLOCCount+Plugin>`_

    :arg str report-files: Setting that specifies the generated raw
                           SLOCCount report files.
                           Be sure not to include any non-report files into
                           this pattern. The report files must have been
                           generated by sloccount using the
                           "--wide --details" options.
                           (default: '\*\*/sloccount.sc')
    :arg str charset: The character encoding to be used to read the SLOCCount
                      result files. (default: 'UTF-8')

    Example::

      publishers:
        - sloccount:
            report-files: sloccount.sc
            charset: UTF-8

    """
    top = XML.SubElement(xml_parent,
                         'hudson.plugins.sloccount.SloccountPublisher')
    XML.SubElement(top, 'pattern').text = data.get('report-files',
                                                   '**/sloccount.sc')
    XML.SubElement(top, 'encoding').text = data.get('charset', 'UTF-8')


def ircbot(parser, xml_parent, data):
    """yaml: ircbot
    ircbot enables Jenkins to send build notifications via IRC and lets you
    interact with Jenkins via an IRC bot.

    Requires the Jenkins `IRC Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/IRC+Plugin>`_

    :arg string strategy: When to send notifications

        :strategy values:
            * **all** always (default)
            * **any-failure** on any failure_and_fixed
            * **failure-and-fixed** on failure and fixes
            * **new-failure-and-fixed** on new failure and fixes
            * **statechange-only** only on state change
    :arg bool notify-start: Whether to send notifications to channels when a
                           build starts
                           (default: false)
    :arg bool notify-committers: Whether to send notifications to the users
                                that are suspected of having broken this build
                                (default: false)
    :arg bool notify-culprits: Also send notifications to 'culprits' from
                              previous unstable/failed builds
                              (default: false)
    :arg bool notify-upstream: Whether to send notifications to upstream
                              committers if no committers were found for a
                              broken build
                              (default: false)
    :arg bool notify-fixers: Whether to send notifications to the users that
                            have fixed a broken build
                            (default: false)
    :arg string message-type: Channel Notification Message.

        :message-type values:
            * **summary-scm** for summary and SCM changes (default)
            * **summary** for summary only
            * **summary-params** for summary and build parameters
            * **summary-scm-fail** for summary, SCM changes, failures)
    :arg list channels: list channels definitions
                        If empty, it takes channel from Jenkins configuration.
                        (default: empty)
                        WARNING: the IRC plugin requires the channel to be
                        configured in the system wide configuration or the jobs
                        will fail to emit notifications to the channel

        :Channel: * **name** (`str`) Channel name
                  * **password** (`str`) Channel password (optional)
                  * **notify-only** (`bool`) Set to true if you want to
                    disallow bot commands (default: false)
    :arg string matrix-notifier: notify for matrix projects
                                 instant-messaging-plugin injects an additional
                                 field in the configuration form whenever the
                                 project is a multi-configuration project

        :matrix-notifier values:
            * **all**
            * **only-configurations** (default)
            * **only-parent**

    Example:

    .. literalinclude:: /../../tests/publishers/fixtures/ircbot001.yaml
    """
    top = XML.SubElement(xml_parent, 'hudson.plugins.ircbot.IrcPublisher')
    message_dict = {'summary-scm': 'DefaultBuildToChatNotifier',
                    'summary': 'SummaryOnlyBuildToChatNotifier',
                    'summary-params': 'BuildParametersBuildToChatNotifier',
                    'summary-scm-fail': 'PrintFailingTestsBuildToChatNotifier'}
    message = data.get('message-type', 'summary-scm')
    if message not in message_dict:
        raise JenkinsJobsException("message-type entered is not valid, must "
                                   "be one of: %s" %
                                   ", ".join(message_dict.keys()))
    message = "hudson.plugins.im.build_notify." + message_dict.get(message)
    XML.SubElement(top, 'buildToChatNotifier', attrib={'class': message})
    strategy_dict = {'all': 'ALL',
                     'any-failure': 'ANY_FAILURE',
                     'failure-and-fixed': 'FAILURE_AND_FIXED',
                     'new-failure-and-fixed': 'NEW_FAILURE_AND_FIXED',
                     'statechange-only': 'STATECHANGE_ONLY'}
    strategy = data.get('strategy', 'all')
    if strategy not in strategy_dict:
        raise JenkinsJobsException("strategy entered is not valid, must be "
                                   "one of: %s" %
                                   ", ".join(strategy_dict.keys()))
    XML.SubElement(top, 'strategy').text = strategy_dict.get(strategy)
    targets = XML.SubElement(top, 'targets')
    channels = data.get('channels', [])
    for channel in channels:
        sub = XML.SubElement(targets,
                             'hudson.plugins.im.GroupChatIMMessageTarget')
        XML.SubElement(sub, 'name').text = channel.get('name')
        XML.SubElement(sub, 'password').text = channel.get('password')
        XML.SubElement(sub, 'notificationOnly').text = str(
            channel.get('notify-only', False)).lower()
    XML.SubElement(top, 'notifyOnBuildStart').text = str(
        data.get('notify-start', False)).lower()
    XML.SubElement(top, 'notifySuspects').text = str(
        data.get('notify-committers', False)).lower()
    XML.SubElement(top, 'notifyCulprits').text = str(
        data.get('notify-culprits', False)).lower()
    XML.SubElement(top, 'notifyFixers').text = str(
        data.get('notify-fixers', False)).lower()
    XML.SubElement(top, 'notifyUpstreamCommitters').text = str(
        data.get('notify-upstream', False)).lower()
    matrix_dict = {'all': 'ALL',
                   'only-configurations': 'ONLY_CONFIGURATIONS',
                   'only-parent': 'ONLY_PARENT'}
    matrix = data.get('matrix-notifier', 'only-configurations')
    if matrix not in matrix_dict:
        raise JenkinsJobsException("matrix-notifier entered is not valid, "
                                   "must be one of: %s" %
                                   ", ".join(matrix_dict.keys()))
    XML.SubElement(top, 'matrixMultiplier').text = matrix_dict.get(matrix)


def plot(parser, xml_parent, data):
    """yaml: plot
    Plot provides generic plotting (or graphing).

    Requires the Jenkins `Plot Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/Plot+Plugin>`_

    :arg str title: title for the graph
                    (default: '')
    :arg str yaxis: title of Y axis
    :arg str group: name of the group to which the plot belongs
    :arg int num-builds: number of builds to plot across
                         (default: plot all builds)
    :arg str style:  Specifies the graph style of the plot
                     Can be: area, bar, bar3d, line, line3d, stackedArea,
                     stackedbar, stackedbar3d, waterfall
                     (default: 'line')
    :arg bool use-description: When false, the X-axis labels are formed
                               using build numbers and dates, and the
                               corresponding tooltips contain the build
                               descriptions. When enabled, the contents of
                               the labels and tooltips are swapped, with the
                               descriptions used as X-axis labels and the
                               build number and date used for tooltips.
                               (default: False)
    :arg str csv-file-name: Use for choosing the file name in which the data
                            will be persisted. If none specified and random
                            name is generated as done in the Jenkins Plot
                            plugin.
                            (default: random generated .csv filename, same
                            behaviour as the Jenkins Plot plugin)
    :arg list series: list data series definitions

      :Serie: * **file** (`str`) : files to include
              * **inclusion-flag** filtering mode for CSV files. Possible
                values are:

                  * **off** (default)
                  * **include-by-string**
                  * **exclude-by-string**
                  * **include-by-column**
                  * **exclude-by-column**

              * **exclude** (`str`) : exclude pattern for CSV file.
              * **url** (`str`) : for 'csv' and 'xml' file types
                used when you click on a point (default: empty)
              * **display-table** (`bool`) : for 'csv' file type
                if true, original CSV will be shown above plot (default: False)
              * **label** (`str`) : used by 'properties' file type
                Specifies the legend label for this data series.
                (default: empty)
              * **format** (`str`) : Type of file where we get datas.
                Can be: properties, csv, xml
              * **xpath-type** (`str`) : The result type of the expression must
                be supplied due to limitations in the java.xml.xpath parsing.
                The result can be: node, nodeset, boolean, string, or number.
                Strings and numbers will be converted to double. Boolean will
                be converted to 1 for true, and 0 for false. (default: 'node')
              * **xpath** (`str`) : used by 'xml' file type
                Xpath which selects the values that should be plotted.


    Example::

      publishers:
        - plot:
            - title: MyPlot
              yaxis: Y
              group: PlotGroup
              num-builds: ''
              style: line
              use-description: false
              series:
                  - file: graph-me-second.properties
                    label: MyLabel
                    format: properties
                  - file: graph-me-first.csv
                    url: 'http://srv1'
                    inclusion-flag: 'off'
                    display-table: true
                    format: csv
            - title: MyPlot2
              yaxis: Y
              group: PlotGroup
              style: line
              use-description: false
              series:
                  - file: graph-me-third.xml
                    url: 'http://srv2'
                    format: xml
                    xpath-type: 'node'
                    xpath: '/*'

    """
    top = XML.SubElement(xml_parent, 'hudson.plugins.plot.PlotPublisher')
    plots = XML.SubElement(top, 'plots')
    format_dict = {'properties': 'hudson.plugins.plot.PropertiesSeries',
                   'csv': 'hudson.plugins.plot.CSVSeries',
                   'xml': 'hudson.plugins.plot.XMLSeries'}
    xpath_dict = {'nodeset': 'NODESET', 'node': 'NODE', 'string': 'STRING',
                  'boolean': 'BOOLEAN', 'number': 'NUMBER'}
    inclusion_dict = {'off': 'OFF',
                      'include-by-string': 'INCLUDE_BY_STRING',
                      'exclude-by-string': 'EXCLUDE_BY_STRING',
                      'include-by-column': 'INCLUDE_BY_COLUMN',
                      'exclude-by-column': 'EXCLUDE_BY_COLUMN'}
    for plot in data:
        plugin = XML.SubElement(plots, 'hudson.plugins.plot.Plot')
        XML.SubElement(plugin, 'title').text = plot.get('title', '')
        XML.SubElement(plugin, 'yaxis').text = plot['yaxis']
        XML.SubElement(plugin, 'csvFileName').text = \
            plot.get('csv-file-name', '%s.csv' % random.randrange(2 << 32))
        topseries = XML.SubElement(plugin, 'series')
        series = plot['series']
        for serie in series:
            format_data = serie.get('format')
            if format_data not in format_dict:
                raise JenkinsJobsException("format entered is not valid, must "
                                           "be one of: %s" %
                                           " , ".join(format_dict.keys()))
            subserie = XML.SubElement(topseries, format_dict.get(format_data))
            XML.SubElement(subserie, 'file').text = serie.get('file')
            if format_data == 'properties':
                XML.SubElement(subserie, 'label').text = serie.get('label', '')
            if format_data == 'csv':
                inclusion_flag = serie.get('inclusion-flag', 'off')
                if inclusion_flag not in inclusion_dict:
                    raise JenkinsJobsException("Inclusion flag result entered "
                                               "is not valid, must be one of: "
                                               "%s"
                                               % ", ".join(inclusion_dict))
                XML.SubElement(subserie, 'inclusionFlag').text = \
                    inclusion_dict.get(inclusion_flag)
                XML.SubElement(subserie, 'exclusionValues').text = \
                    serie.get('exclude', '')
                XML.SubElement(subserie, 'url').text = serie.get('url', '')
                XML.SubElement(subserie, 'displayTableFlag').text = \
                    str(plot.get('display-table', False)).lower()
            if format_data == 'xml':
                XML.SubElement(subserie, 'url').text = serie.get('url', '')
                XML.SubElement(subserie, 'xpathString').text = \
                    serie.get('xpath')
                xpathtype = serie.get('xpath-type', 'node')
                if xpathtype not in xpath_dict:
                    raise JenkinsJobsException("XPath result entered is not "
                                               "valid, must be one of: %s" %
                                               ", ".join(xpath_dict))
                XML.SubElement(subserie, 'nodeTypeString').text = \
                    xpath_dict.get(xpathtype)
            XML.SubElement(subserie, 'fileType').text = serie.get('format')
        XML.SubElement(plugin, 'group').text = plot['group']
        XML.SubElement(plugin, 'useDescr').text = \
            str(plot.get('use-description', False)).lower()
        XML.SubElement(plugin, 'numBuilds').text = plot.get('num-builds', '')
        style_list = ['area', 'bar', 'bar3d', 'line', 'line3d', 'stackedArea',
                      'stackedbar', 'stackedbar3d', 'waterfall']
        style = plot.get('style', 'line')
        if style not in style_list:
            raise JenkinsJobsException("style entered is not valid, must be "
                                       "one of: %s" % ", ".join(style_list))
        XML.SubElement(plugin, 'style').text = style


def git(parser, xml_parent, data):
    """yaml: git
    This plugin will configure the Jenkins Git plugin to
    push merge results, tags, and/or branches to
    remote repositories after the job completes.

    Requires the Jenkins `Git Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/Git+Plugin>`_

    :arg bool push-merge: push merges back to the origin specified in the
                          pre-build merge options (Default: False)
    :arg bool push-only-if-success: Only push to remotes if the build succeeds
                                    - otherwise, nothing will be pushed.
                                    (Default: True)
    :arg list tags: tags to push at the completion of the build

        :tag: * **remote** (`str`) remote repo name to push to
                (Default: 'origin')
              * **name** (`str`) name of tag to push
              * **message** (`str`) message content of the tag
              * **create-tag** (`bool`) whether or not to create the tag
                after the build, if this is False then the tag needs to
                exist locally (Default: False)
              * **update-tag** (`bool`) whether to overwrite a remote tag
                or not (Default: False)

    :arg list branches: branches to push at the completion of the build

        :branch: * **remote** (`str`) remote repo name to push to
                   (Default: 'origin')
                 * **name** (`str`) name of remote branch to push to

    :arg list notes: notes to push at the completion of the build

        :note: * **remote** (`str`) remote repo name to push to
                 (Default: 'origin')
               * **message** (`str`) content of the note
               * **namespace** (`str`) namespace of the note
                 (Default: master)
               * **replace-note** (`bool`) whether to overwrite a note or not
                 (Default: False)


    Example::

        publishers:
            - git:
                push-merge: true
                push-only-if-success: false
                tags:
                    - tag:
                        remote: tagremotename
                        name: tagname
                        message: "some tag message"
                        create-tag: true
                        update-tag: true
                branches:
                    - branch:
                        remote: branchremotename
                        name: "some/branch"
                notes:
                    - note:
                        remote: remotename
                        message: "some note to push"
                        namespace: commits
                        replace-note: true

    """
    mappings = [('push-merge', 'pushMerge', False),
                ('push-only-if-success', 'pushOnlyIfSuccess', True)]

    tag_mappings = [('remote', 'targetRepoName', 'origin'),
                    ('name', 'tagName', None),
                    ('message', 'tagMessage', ''),
                    ('create-tag', 'createTag', False),
                    ('update-tag', 'updateTag', False)]

    branch_mappings = [('remote', 'targetRepoName', 'origin'),
                       ('name', 'branchName', None)]

    note_mappings = [('remote', 'targetRepoName', 'origin'),
                     ('message', 'noteMsg', None),
                     ('namespace', 'noteNamespace', 'master'),
                     ('replace-note', 'noteReplace', False)]

    def handle_entity_children(entity, entity_xml, child_mapping):
        for prop in child_mapping:
            opt, xmlopt, default_val = prop[:3]
            val = entity.get(opt, default_val)
            if val is None:
                raise JenkinsJobsException('Required option missing: %s' % opt)
            if type(val) == bool:
                val = str(val).lower()
            XML.SubElement(entity_xml, xmlopt).text = val

    top = XML.SubElement(xml_parent, 'hudson.plugins.git.GitPublisher')
    XML.SubElement(top, 'configVersion').text = '2'
    handle_entity_children(data, top, mappings)

    tags = data.get('tags', [])
    if tags:
        xml_tags = XML.SubElement(top, 'tagsToPush')
        for tag in tags:
            xml_tag = XML.SubElement(
                xml_tags,
                'hudson.plugins.git.GitPublisher_-TagToPush')
            handle_entity_children(tag['tag'], xml_tag, tag_mappings)

    branches = data.get('branches', [])
    if branches:
        xml_branches = XML.SubElement(top, 'branchesToPush')
        for branch in branches:
            xml_branch = XML.SubElement(
                xml_branches,
                'hudson.plugins.git.GitPublisher_-BranchToPush')
            handle_entity_children(branch['branch'], xml_branch,
                                   branch_mappings)

    notes = data.get('notes', [])
    if notes:
        xml_notes = XML.SubElement(top, 'notesToPush')
        for note in notes:
            xml_note = XML.SubElement(
                xml_notes,
                'hudson.plugins.git.GitPublisher_-NoteToPush')
            handle_entity_children(note['note'], xml_note, note_mappings)


def github_notifier(parser, xml_parent, data):
    """yaml: github-notifier
    Set build status on Github commit.
    Requires the Jenkins `Github Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/GitHub+Plugin>`_

    Example:

    .. literalinclude:: /../../tests/publishers/fixtures/github-notifier.yaml
    """
    XML.SubElement(xml_parent,
                   'com.cloudbees.jenkins.GitHubCommitNotifier')


def build_publisher(parser, xml_parent, data):
    """yaml: build-publisher
    This plugin allows records from one Jenkins to be published
    on another Jenkins.

    Requires the Jenkins `Build Publisher Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/Build+Publisher+Plugin>`_

    :arg str servers: Specify the servers where to publish


    Example::

        publishers:
            - build-publisher:
                name: servername
                publish-unstable-builds: true
                publish-failed-builds: true
                days-to-keep: -1
                num-to-keep: -1
                artifact-days-to-keep: -1
                artifact-num-to-keep: -1

    """

    reporter = XML.SubElement(
        xml_parent,
        'hudson.plugins.build__publisher.BuildPublisher')

    XML.SubElement(reporter, 'serverName').text = data['name']
    XML.SubElement(reporter, 'publishUnstableBuilds').text = \
        str(data.get('publish-unstable-builds', True)).lower()
    XML.SubElement(reporter, 'publishFailedBuilds').text = \
        str(data.get('publish-failed-builds', True)).lower()

    logrotator = XML.SubElement(reporter, 'logRotator')
    XML.SubElement(logrotator, 'daysToKeep').text = \
        str(data.get('days-to-keep', -1))
    XML.SubElement(logrotator, 'numToKeep').text = \
        str(data.get('num-to-keep', -1))
    XML.SubElement(logrotator, 'artifactDaysToKeep').text = \
        str(data.get('artifact-days-to-keep', -1))
    XML.SubElement(logrotator, 'artifactNumToKeep').text = \
        str(data.get('artifact-num-to-keep', -1))


def stash(parser, xml_parent, data):
    """yaml: stash
    This plugin will configure the Jenkins Stash Notifier plugin to
    notify Atlassian Stash after job completes.

    Requires the Jenkins `StashNotifier Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/StashNotifier+Plugin>`_

    :arg string url: Base url of Stash Server (Default: "")
    :arg string username: Username of Stash Server (Default: "")
    :arg string password: Password of Stash Server (Default: "")
    :arg bool   ignore-ssl: Ignore unverified SSL certificate (Default: False)
    :arg string commit-sha1: Commit SHA1 to notify (Default: "")
    :arg bool   include-build-number: Include build number in key
                (Default: False)

    Example:

    .. literalinclude:: /../../tests/publishers/fixtures/stash001.yaml
    """

    top = XML.SubElement(xml_parent,
                         'org.jenkinsci.plugins.stashNotifier.StashNotifier')

    XML.SubElement(top, 'stashServerBaseUrl').text = data.get('url', '')
    XML.SubElement(top, 'stashUserName').text = data.get('username', '')
    XML.SubElement(top, 'stashUserPassword').text = data.get('password', '')
    XML.SubElement(top, 'ignoreUnverifiedSSLPeer').text = str(
        data.get('ignore-ssl', False)).lower()
    XML.SubElement(top, 'commitSha1').text = data.get('commit-sha1', '')
    XML.SubElement(top, 'includeBuildNumberInKey').text = str(
        data.get('include-build-number', False)).lower()


def description_setter(parser, xml_parent, data):
    """yaml: description-setter
    This plugin sets the description for each build,
    based upon a RegEx test of the build log file.

    Requires the Jenkins `Description Setter Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/Description+Setter+Plugin>`_

    :arg str regexp: A RegEx which is used to scan the build log file
    :arg str regexp-for-failed: A RegEx which is used for failed builds
        (optional)
    :arg str description: The description to set on the build (optional)
    :arg str description-for-failed: The description to set on
        the failed builds (optional)
    :arg bool set-for-matrix: Also set the description on
        a multi-configuration build (Default False)

    Example:

    .. literalinclude::
       /../../tests/publishers/fixtures/description-setter001.yaml

    """

    descriptionsetter = XML.SubElement(
        xml_parent,
        'hudson.plugins.descriptionsetter.DescriptionSetterPublisher')
    XML.SubElement(descriptionsetter, 'regexp').text = data.get('regexp', '')
    XML.SubElement(descriptionsetter, 'regexpForFailed').text = \
        data.get('regexp-for-failed', '')
    if 'description' in data:
        XML.SubElement(descriptionsetter, 'description').text = \
            data['description']
    if 'description-for-failed' in data:
        XML.SubElement(descriptionsetter, 'descriptionForFailed').text = \
            data['description-for-failed']
    for_matrix = str(data.get('set-for-matrix', False)).lower()
    XML.SubElement(descriptionsetter, 'setForMatrix').text = for_matrix


def doxygen(parser, xml_parent, data):
    """yaml: doxygen
    This plugin parses the Doxygen descriptor (Doxyfile) and provides a link to
    the generated Doxygen documentation.

    Requires the Jenkins `Doxygen Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/Doxygen+Plugin>`_

    :arg str doxyfile: The doxyfile path
    :arg bool keepall: Retain doxygen generation for each successful build
        (default: false)
    :arg str folder: Folder where you run doxygen (default: '')

    Example:

    .. literalinclude:: /../../tests/publishers/fixtures/doxygen001.yaml

    """
    p = XML.SubElement(xml_parent, 'hudson.plugins.doxygen.DoxygenArchiver')
    if not data['doxyfile']:
        raise JenkinsJobsException("The path to a doxyfile must be specified.")
    XML.SubElement(p, 'doxyfilePath').text = str(data.get("doxyfile"))
    XML.SubElement(p, 'keepAll').text = str(data.get("keepall", False)).lower()
    XML.SubElement(p, 'folderWhereYouRunDoxygen').text = \
        str(data.get("folder", ""))


def sitemonitor(parser, xml_parent, data):
    """yaml: sitemonitor
    This plugin checks the availability of an url.

    It requires the `sitemonitor plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/SiteMonitor+Plugin>`_

    :arg list sites: List of URLs to check

    Example:

    .. literalinclude:: /../../tests/publishers/fixtures/sitemonitor001.yaml

    """
    mon = XML.SubElement(xml_parent,
                         'hudson.plugins.sitemonitor.SiteMonitorRecorder')
    if data.get('sites'):
        sites = XML.SubElement(mon, 'mSites')
        for siteurl in data.get('sites'):
            site = XML.SubElement(sites,
                                  'hudson.plugins.sitemonitor.model.Site')
            XML.SubElement(site, 'mUrl').text = siteurl['url']


def testng(parser, xml_parent, data):
    """yaml: testng
    This plugin publishes TestNG test reports.

    Requires the Jenkins `TestNG Results Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/testng-plugin>`_

    :arg str pattern: filename pattern to locate the TestNG XML report files
    :arg bool escape-test-description: escapes the description string
      associated with the test method while displaying test method details
      (Default True)
    :arg bool escape-exception-msg: escapes the test method's exception
      messages. (Default True)

    Example:

    .. literalinclude:: /../../tests/publishers/fixtures/testng001.yaml

    """

    reporter = XML.SubElement(xml_parent, 'hudson.plugins.testng.Publisher')
    if not data['pattern']:
        raise JenkinsJobsException("A filename pattern must be specified.")
    XML.SubElement(reporter, 'reportFilenamePattern').text = data['pattern']
    XML.SubElement(reporter, 'escapeTestDescp').text = str(data.get(
        'escape-test-description', True))
    XML.SubElement(reporter, 'escapeExceptionMsg').text = str(data.get(
        'escape-exception-msg', True))


def artifact_deployer(parser, xml_parent, data):
    """yaml: artifact-deployer
    This plugin makes it possible to copy artifacts to remote locations.

    Requires the Jenkins `ArtifactDeployer Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/ArtifactDeployer+Plugin>`_

    :arg list entries:
        :entries:
            * **files** (`str`) - files to deploy
            * **basedir** (`str`) - the dir from files are deployed
            * **excludes** (`str`) - the mask to exclude files
            * **remote** (`str`) - a remote output directory
            * **flatten** (`bool`) - ignore the source directory structure
              (Default: False)
            * **delete-remote** (`bool`) - clean-up remote directory
              before deployment (Default: False)
            * **delete-remote-artifacts** (`bool`) - delete remote artifacts
              when the build is deleted (Default: False)
            * **fail-no-files** (`bool`) - fail build if there are no files
              (Default: False)
            * **groovy-script** (`str`) - execute a Groovy script
              before a build is deleted

    :arg bool deploy-if-fail: Deploy if the build is failed (Default: False)

    Example:

    .. literalinclude:: /../../tests/publishers/fixtures/artifact-dep.yaml

    """

    deployer = XML.SubElement(xml_parent,
                              'org.jenkinsci.plugins.artifactdeployer.'
                              'ArtifactDeployerPublisher')
    if data is None or 'entries' not in data:
        raise Exception('entries field is missing')
    elif data.get('entries', None) is None:
        entries = XML.SubElement(deployer, 'entries', {'class': 'empty-list'})
    else:
        entries = XML.SubElement(deployer, 'entries')
        for entry in data.get('entries'):
            deployer_entry = XML.SubElement(
                entries,
                'org.jenkinsci.plugins.artifactdeployer.ArtifactDeployerEntry')
            XML.SubElement(deployer_entry, 'includes').text = \
                entry.get('files')
            XML.SubElement(deployer_entry, 'basedir').text = \
                entry.get('basedir')
            XML.SubElement(deployer_entry, 'excludes').text = \
                entry.get('excludes')
            XML.SubElement(deployer_entry, 'remote').text = entry.get('remote')
            XML.SubElement(deployer_entry, 'flatten').text = \
                str(entry.get('flatten', False)).lower()
            XML.SubElement(deployer_entry, 'deleteRemote').text = \
                str(entry.get('delete-remote', False)).lower()
            XML.SubElement(deployer_entry, 'deleteRemoteArtifacts').text = \
                str(entry.get('delete-remote-artifacts', False)).lower()
            XML.SubElement(deployer_entry, 'failNoFilesDeploy').text = \
                str(entry.get('fail-no-files', False)).lower()
            XML.SubElement(deployer_entry, 'groovyExpression').text = \
                entry.get('groovy-script')
    deploy_if_fail = str(data.get('deploy-if-fail', False)).lower()
    XML.SubElement(deployer, 'deployEvenBuildFail').text = deploy_if_fail


def ruby_metrics(parser, xml_parent, data):
    """yaml: ruby-metrics
    Rcov plugin parses rcov html report files and
    shows it in Jenkins with a trend graph.

    Requires the Jenkins `Ruby metrics plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/Ruby+metrics+plugin>`_

    :arg str report-dir: Relative path to the coverage report directory
    :arg dict targets:

           :targets: (total-coverage, code-coverage)

                * **healthy** (`int`): Healthy threshold
                * **unhealthy** (`int`): Unhealthy threshold
                * **unstable** (`int`): Unstable threshold

    Example:

    .. literalinclude:: /../../tests/publishers/fixtures/ruby-metrics.yaml

    """

    metrics = XML.SubElement(
        xml_parent,
        'hudson.plugins.rubyMetrics.rcov.RcovPublisher')
    report_dir = data.get('report-dir', '')
    XML.SubElement(metrics, 'reportDir').text = report_dir
    targets = XML.SubElement(metrics, 'targets')
    if 'target' in data:
        for t in data['target']:
            if not ('code-coverage' in t or 'total-coverage' in t):
                raise JenkinsJobsException('Unrecognized target name')
            el = XML.SubElement(
                targets,
                'hudson.plugins.rubyMetrics.rcov.model.MetricTarget')
            if 'total-coverage' in t:
                XML.SubElement(el, 'metric').text = 'TOTAL_COVERAGE'
            else:
                XML.SubElement(el, 'metric').text = 'CODE_COVERAGE'
            for threshold_name, threshold_value in t.values()[0].items():
                elname = threshold_name.lower()
                XML.SubElement(el, elname).text = str(threshold_value)
    else:
        raise JenkinsJobsException('Coverage metric targets must be set')


def fitnesse(parser, xml_parent, data):
    """yaml: fitnesse
    Publish Fitnesse test results

    Requires the Jenkins `Fitnesse plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/Fitnesse+Plugin>`_

    :arg str results: path specifier for results files

    Example:

    .. literalinclude::  /../../tests/publishers/fixtures/fitnesse001.yaml

    """
    fitnesse = XML.SubElement(
        xml_parent,
        'hudson.plugins.fitnesse.FitnesseResultsRecorder')
    results = data.get('results', '')
    XML.SubElement(fitnesse, 'fitnessePathToXmlResultsIn').text = results


class Publishers(jenkins_jobs.modules.base.Base):
    sequence = 70

    component_type = 'publisher'
    component_list_type = 'publishers'

    def gen_xml(self, parser, xml_parent, data):
        publishers = XML.SubElement(xml_parent, 'publishers')

        for action in data.get('publishers', []):
            self.registry.dispatch('publisher', parser, publishers, action)
