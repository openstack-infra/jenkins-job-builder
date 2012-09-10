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


def archive(parser, xml_parent, data):
    """yaml: archive
    Archive build artifacts

    :arg str artifacts: path specifier for artifacts to archive
    :arg str excludes: path specifier for artifacts to exclude
    :arg bool latest_only: only keep the artifacts from the latest
      successful build

    Example::

      publishers:
        - archive:
            artifacts: *.tar.gz
    """
    archiver = XML.SubElement(xml_parent, 'hudson.tasks.ArtifactArchiver')
    artifacts = XML.SubElement(archiver, 'artifacts')
    artifacts.text = data['artifacts']
    if 'excludes' in data:
        excludes = XML.SubElement(archiver, 'excludes')
        excludes.text = data['excludes']
    latest = XML.SubElement(archiver, 'latestOnly')
    latest_only = data.get('latest_only', False)
    if latest_only:
        latest.text = 'true'
    else:
        latest.text = 'false'


def trigger_parameterized_builds(parser, xml_parent, data):
    """yaml: trigger-parameterized-builds
    Trigger parameterized builds of other jobs.

    :arg str project: name of the job to trigger
    :arg str predefined-parameters: parameters to pass to the other
      job (optional)
    :arg str condition: when to trigger the other job (default 'ALWAYS')

    Example::

      publishers:
        - trigger-parameterized-builds:
            project: other_job
    """
    tbuilder = XML.SubElement(xml_parent,
        'hudson.plugins.parameterizedtrigger.BuildTrigger')
    configs = XML.SubElement(tbuilder, 'configs')
    for project_def in data:
        tconfig = XML.SubElement(configs,
            'hudson.plugins.parameterizedtrigger.BuildTriggerConfig')
        tconfigs = XML.SubElement(tconfig, 'configs')
        if 'predefined-parameters' in project_def:
            params = XML.SubElement(tconfigs,
              'hudson.plugins.parameterizedtrigger.PredefinedBuildParameters')
            properties = XML.SubElement(params, 'properties')
            properties.text = project_def['predefined-parameters']
        else:
            tconfigs.set('class', 'java.util.Collections$EmptyList')
        projects = XML.SubElement(tconfig, 'projects')
        projects.text = project_def['project']
        condition = XML.SubElement(tconfig, 'condition')
        condition.text = project_def.get('condition', 'ALWAYS')
        trigger_with_no_params = XML.SubElement(tconfig,
                                                'triggerWithNoParameters')
        trigger_with_no_params.text = 'false'


def coverage(parser, xml_parent, data):
    """yaml: coverage
    Generate a cobertura coverage report.

    Example::

      publishers:
        - coverage
    """
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


def ftp(parser, xml_parent, data):
    """yaml: ftp
    Upload files via FTP.

    :arg str site: name of the ftp site
    :arg str target: destination directory
    :arg str source: source path specifier
    :arg str excludes: excluded file pattern (optional)
    :arg str remove-prefix: prefix to remove from uploaded file paths
      (optional)

    Example::

      publishers:
        - ftp:
            site: 'ftp.example.com'
            target: 'dest/dir'
            source: 'base/source/dir/**'
            remove-prefix: 'base/source/dir'
            excludes: '**/*.excludedfiletype'
    """
    outer_ftp = XML.SubElement(xml_parent,
        'jenkins.plugins.publish__over__ftp.BapFtpPublisherPlugin')
    XML.SubElement(outer_ftp, 'consolePrefix').text = 'FTP: '
    delegate = XML.SubElement(outer_ftp, 'delegate')
    publishers = XML.SubElement(delegate, 'publishers')
    ftp = XML.SubElement(publishers,
                         'jenkins.plugins.publish__over__ftp.BapFtpPublisher')
    XML.SubElement(ftp, 'configName').text = data['site']
    XML.SubElement(ftp, 'verbose').text = 'true'

    transfers = XML.SubElement(ftp, 'transfers')
    ftp_transfers = XML.SubElement(transfers,
        'jenkins.plugins.publish__over__ftp.BapFtpTransfer')
    XML.SubElement(ftp_transfers, 'remoteDirectory').text = data['target']
    XML.SubElement(ftp_transfers, 'sourceFiles').text = data['source']
    XML.SubElement(ftp_transfers, 'excludes').text = data['excludes']
    XML.SubElement(ftp_transfers, 'removePrefix').text = data['remove-prefix']
    XML.SubElement(ftp_transfers, 'remoteDirectorySDF').text = 'false'
    XML.SubElement(ftp_transfers, 'flatten').text = 'false'
    XML.SubElement(ftp_transfers, 'cleanRemote').text = 'false'
    XML.SubElement(ftp_transfers, 'asciiMode').text = 'false'

    XML.SubElement(ftp, 'useWorkspaceInPromotion').text = 'false'
    XML.SubElement(ftp, 'usePromotionTimestamp').text = 'false'
    XML.SubElement(delegate, 'continueOnError').text = 'false'
    XML.SubElement(delegate, 'failOnError').text = 'false'
    XML.SubElement(delegate, 'alwaysPublishFromMaster').text = 'false'
    XML.SubElement(delegate, 'hostConfigurationAccess',
        {'class': 'jenkins.plugins.publish_over_ftp.BapFtpPublisherPlugin',
         'reference': '../..'})


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
                    'hudson.plugins.violations.ViolationsPublisher')
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


# Jenkins Job module for generic scp publishing
# To use you add the following into your YAML:
# publish:
#   site: 'openstack-ci.openstack.org'
#   source: 'doc/build/html/**/*'
#   target_path: 'ci/zuul'
#   keep_heirarchy: 'true'

def scp(parser, xml_parent, data):
    """yaml: scp
    Upload files via SCP

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

def pipeline(parser, xml_parent, data):
    pippub = XML.SubElement(xml_parent, 
           'au.com.centrumsystems.hudson.plugin.buildpipeline.trigger.BuildPipelineTrigger')
    XML.SubElement(pippub, 'downstreamProjectNames').text = data

class Publishers(jenkins_jobs.modules.base.Base):
    sequence = 70

    def gen_xml(self, parser, xml_parent, data):
        publishers = XML.SubElement(xml_parent, 'publishers')

        for action in data.get('publishers', []):
            self._dispatch('publisher', 'publishers',
                           parser, publishers, action)
