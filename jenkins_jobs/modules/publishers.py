# Copyright 2012 Hewlett-Packard Development Company, L.P.
# Copyright 2012 Varnish Software AS
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

Example::

  job:
    name: test_job

    publishers:
      - scp:
          site: 'example.com'
          source: 'doc/build/html/**/*'
          target_path: 'project'
"""


import xml.etree.ElementTree as XML
import jenkins_jobs.modules.base
import logging
import sys


def archive(parser, xml_parent, data):
    """yaml: archive
    Archive build artifacts

    :arg str artifacts: path specifier for artifacts to archive
    :arg str excludes: path specifier for artifacts to exclude
    :arg bool latest-only: only keep the artifacts from the latest
      successful build

    Example::

      publishers:
        - archive:
            artifacts: '*.tar.gz'
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

    Example::

      publishers:
        - trigger:
            project: other_job
    """
    thresholds = {
        'SUCCESS': {
            'ordinal': '0',
            'color': 'BLUE'
        },
        'UNSTABLE': {
            'ordinal': '1',
            'color': 'YELLOW'
        },
        'FAILURE': {
            'ordinal': '2',
            'color': 'RED'
        }
    }

    tconfig = XML.SubElement(xml_parent, 'hudson.tasks.BuildTrigger')
    childProjects = XML.SubElement(tconfig, 'childProjects')
    childProjects.text = data['project']
    tthreshold = XML.SubElement(tconfig, 'threshold')

    threshold = data.get('threshold', 'SUCCESS')
    if threshold not in thresholds.keys():
        raise Exception("threshold must be one of " +
                        ", ".join(threshold.keys()))
    tname = XML.SubElement(tthreshold, 'name')
    tname.text = threshold
    tordinal = XML.SubElement(tthreshold, 'ordinal')
    tordinal.text = thresholds[threshold]['ordinal']
    tcolor = XML.SubElement(tthreshold, 'color')
    tcolor.text = thresholds[threshold]['color']


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
      transfering files (defaults to False)
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

    Example::

      publishers:
        - junit:
            results: nosetests.xml
    """
    junitresult = XML.SubElement(xml_parent,
                                 'hudson.tasks.junit.JUnitResultArchiver')
    XML.SubElement(junitresult, 'testResults').text = data['results']
    XML.SubElement(junitresult, 'keepLongStdio').text = "true"
    XML.SubElement(junitresult, 'testDataPublishers')


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
        'boosttest': 'AUnitJunitHudsonTestType',
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
    Requires the `Checkstyle Plugin.
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

    Example::

      publishers:
        - checkstyle:
            pattern: '**/checkstyle-result.xml'
            healthy: 0
            unHealthy: 100
            healthThreshold: 'high'
            thresholds:
                unstable:
                    totalHigh: 10
                failed:
                    totalHigh: 1
    """
    checkstyle = XML.SubElement(xml_parent,
                                'hudson.plugins.checkstyle.'
                                'CheckStylePublisher')

    dval = data.get('healthy', None)
    if dval:
        XML.SubElement(checkstyle, 'healthy').text = str(dval)
    else:
        XML.SubElement(checkstyle, 'healthy')

    dval = data.get('unHealthy', None)
    if dval:
        XML.SubElement(checkstyle, 'unHealthy').text = str(dval)
    else:
        XML.SubElement(checkstyle, 'unHealthy')

    XML.SubElement(checkstyle, 'thresholdLimit').text = \
        data.get('healthThreshold', 'low')

    XML.SubElement(checkstyle, 'pluginName').text = '[CHECKSTYLE] '

    XML.SubElement(checkstyle, 'defaultEncoding').text = \
        data.get('defaultEncoding', '')

    if data.get('canRunOnFailed', False):
        XML.SubElement(checkstyle, 'canRunOnFailed').text = 'true'
    else:
        XML.SubElement(checkstyle, 'canRunOnFailed').text = 'false'

    XML.SubElement(checkstyle, 'useStableBuildAsReference').text = 'false'

    XML.SubElement(checkstyle, 'useDeltaValues').text = 'false'

    dthresholds = data.get('thresholds', {})
    dunstable = dthresholds.get('unstable', {})
    dfailed = dthresholds.get('failed', {})
    thresholds = XML.SubElement(checkstyle, 'thresholds')

    dval = dunstable.get('totalAll', None)
    if dval:
        XML.SubElement(thresholds, 'unstableTotalAll').text = str(dval)
    else:
        XML.SubElement(thresholds, 'unstableTotalAll')

    dval = dunstable.get('totalHigh', None)
    if dval:
        XML.SubElement(thresholds, 'unstableTotalHigh').text = str(dval)
    else:
        XML.SubElement(thresholds, 'unstableTotalHigh')

    dval = dunstable.get('totalNormal', None)
    if dval:
        XML.SubElement(thresholds, 'unstableTotalNormal').text = str(dval)
    else:
        XML.SubElement(thresholds, 'unstableTotalNormal')

    dval = dunstable.get('totalLow', None)
    if dval:
        XML.SubElement(thresholds, 'unstableTotalLow').text = str(dval)
    else:
        XML.SubElement(thresholds, 'unstableTotalLow')

    dval = dfailed.get('totalAll', None)
    if dval:
        XML.SubElement(thresholds, 'failedTotalAll').text = str(dval)
    else:
        XML.SubElement(thresholds, 'failedTotalAll')

    dval = dfailed.get('totalHigh', None)
    if dval:
        XML.SubElement(thresholds, 'failedTotalHigh').text = str(dval)
    else:
        XML.SubElement(thresholds, 'failedTotalHigh')

    dval = dfailed.get('totalNormal', None)
    if dval:
        XML.SubElement(thresholds, 'failedTotalNormal').text = str(dval)
    else:
        XML.SubElement(thresholds, 'failedTotalNormal')

    dval = dfailed.get('totalLow', None)
    if dval:
        XML.SubElement(thresholds, 'failedTotalLow').text = str(dval)
    else:
        XML.SubElement(thresholds, 'failedTotalLow')

    if data.get('shouldDetectModules', False):
        XML.SubElement(checkstyle, 'shouldDetectModules').text = 'true'
    else:
        XML.SubElement(checkstyle, 'shouldDetectModules').text = 'false'

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

    Example::

      publishers:
        - scp:
            site: 'example.com'
            target: 'dest/dir'
            source: 'base/source/dir/**'
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
      transfering files (defaults to False)
    :arg str source: source path specifier
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

    :Parameter: the name of the downstream project

    Example::

      publishers:
        - pipleline: deploy

    You can build pipeline jobs that are re-usable in different pipelines by
    using a :ref:`job-template` to define the pipeline jobs,
    and variable substitution to specify the name of
    the downstream job in the pipeline.
    Job-specific substitutions are useful here (see :ref:`project`).

    See 'samples/pipeline.yaml' for an example pipeline implementation.
    """
    if data != '':
        pippub = XML.SubElement(xml_parent,
                                'au.com.centrumsystems.hudson.plugin.'
                                'buildpipeline.trigger.BuildPipelineTrigger')
        XML.SubElement(pippub, 'downstreamProjectNames').text = data


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
    XML.SubElement(email, 'sendToDevelopers').text = 'false'
    XML.SubElement(email, 'sendToRequester').text = 'false'
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
    :arg str subject: Subject for the email, can include variables like
        ${BUILD_NUMBER} or even groovy or javascript code
    :arg str body: Content for the body of the email, can include variables
        like ${BUILD_NUMBER}, but the real magic is using groovy or
        javascript to hook into the Jenkins API itself
    :arg bool attach-build-log: Include build log in the email (default false)
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

    Example::

      publishers:
        - email-ext:
            recipients: foo@example.com, bar@example.com
            reply-to: foo@example.com
            subject: Subject for Build ${BUILD_NUMBER}
            body: The build has finished
            attach-build-log: false
            unstable: true
            first-failure: true
            not-built: true
            aborted: true
            regression: true
            failure: true
            improvement: true
            still-failing: true
            success: true
            fixed: true
            still-unstable: true
            pre-build: true
    """
    emailext = XML.SubElement(xml_parent,
                              'hudson.plugins.emailext.ExtendedEmailPublisher')
    if 'recipients' in data:
        XML.SubElement(emailext, 'recipientList').text = data['recipients']
    else:
        XML.SubElement(emailext, 'recipientList').text = '$DEFAULT_RECIPIENTS'
    ctrigger = XML.SubElement(emailext, 'configuredTriggers')
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
    XML.SubElement(emailext, 'contentType').text = 'default'
    XML.SubElement(emailext, 'defaultSubject').text = data.get(
        'subject', '$DEFAULT_SUBJECT')
    XML.SubElement(emailext, 'defaultContent').text = data.get(
        'body', '$DEFAULT_CONTENT')
    XML.SubElement(emailext, 'attachmentsPattern').text = ''
    XML.SubElement(emailext, 'presendScript').text = ''
    XML.SubElement(emailext, 'attachBuildLog').text = \
        str(data.get('attach-build-log', False)).lower()
    XML.SubElement(emailext, 'replyTo').text = data.get('reply-to',
                                                        '$DEFAULT_RECIPIENTS')


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
      transfering files (defaults to False)
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
        raise Exception("Strategy entered is not valid, must be one of: " +
                        "all, failure, failure-fixed, or change")
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
        raise Exception("Message entered is not valid, must be one of: " +
                        "summary-scm, summary, summary-build " +
                        "of summary-scm-fail")
    XML.SubElement(j, 'buildToChatNotifier', {
        'class': 'hudson.plugins.im.build_notify.' + messagedict[message]})
    XML.SubElement(j, 'matrixMultiplier').text = 'ONLY_CONFIGURATIONS'


def workspace_cleanup(parser, xml_parent, data):
    """yaml: workspace-cleanup (post-build)

    See `Workspace Cleanup Plugin.
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

    See `Text-finder Plugin.
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

    See `HTML Publisher Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/HTML+Publisher+Plugin>`_

    :arg str name: Report name
    :arg str dir: HTML directory to archive
    :arg str files: Specify the pages to display
    :arg bool keep-all: keep HTML reports for each past build (Default False)


    Example::

        publishers:
            - html-publisher:
                name: "some name"
                dir: "path/"
                files: "index.html"
                keep-all: true
    """

    reporter = XML.SubElement(xml_parent, 'htmlpublisher.HtmlPublisher')
    targets = XML.SubElement(reporter, 'reportTargets')
    ptarget = XML.SubElement(targets, 'htmlpublisher.HtmlPublisherTarget')
    XML.SubElement(ptarget, 'reportName').text = data['name']
    XML.SubElement(ptarget, 'reportDir').text = data['dir']
    XML.SubElement(ptarget, 'reportFiles').text = data['files']
    keep_all = str(data.get('keep-all', False)).lower()
    XML.SubElement(ptarget, 'keepAll').text = keep_all
    XML.SubElement(ptarget, 'wrapperName').text = "htmlpublisher-wrapper.html"


def tap(parser, xml_parent, data):
    """yaml: tap
    Adds support to TAP test result files

    See `TAP Plugin.
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

    See `Post Build Task plugin.
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


def xml_summary(parser, xml_parent, data):
    """yaml: xml-summary
    Adds support for the Summary Display Plugin

    See `Summary Display Plugin.
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

    See `Robot Framework Plugin` plugin:
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
        the build succesful (default 0.0)
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
        raise Exception("Health-Priority entered is not valid must be one " +
                        "of: " + ",".join(prioritiesDict.keys()))
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


class Publishers(jenkins_jobs.modules.base.Base):
    sequence = 70

    component_type = 'publisher'
    component_list_type = 'publishers'

    def gen_xml(self, parser, xml_parent, data):
        publishers = XML.SubElement(xml_parent, 'publishers')

        for action in data.get('publishers', []):
            self.registry.dispatch('publisher', parser, publishers, action)
