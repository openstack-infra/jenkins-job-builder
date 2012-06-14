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

# Jenkins Job module for coverage publishers
# No additional YAML needed

import xml.etree.ElementTree as XML

class publishers(object):
    def __init__(self, data):
        self.data = data

    def gen_xml(self, xml_parent):
        publishers = XML.SubElement(xml_parent, 'publishers')
        actions = self.data.get('post_build_actions', [])
        for action in actions:
            if isinstance(action, dict):
                for key, value in action.items():
                    getattr(self, '_' + key)(publishers, value)
            else:
                getattr(self, '_' + action)(publishers)

    def _archive(self, xml_parent, data):
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

    def _trigger_parameterized_builds(self, xml_parent, data):
        tbuilder = XML.SubElement(xml_parent, 'hudson.plugins.parameterizedtrigger.BuildTrigger')
        configs = XML.SubElement(tbuilder, 'configs')
        for project_def in data:
            tconfig = XML.SubElement(configs, 'hudson.plugins.parameterizedtrigger.BuildTriggerConfig')
            tconfigs = XML.SubElement(tconfig, 'configs')
            if project_def.has_key('predefined_parameters'):
                params = XML.SubElement(tconfigs,
                                        'hudson.plugins.parameterizedtrigger.PredefinedBuildParameters')
                properties = XML.SubElement(params, 'properties')
                properties.text = project_def['predefined_parameters']
            else:
                tconfigs.set('class', 'java.util.Collections$EmptyList')
            projects = XML.SubElement(tconfig, 'projects')
            projects.text = project_def['project']
            condition = XML.SubElement(tconfig, 'condition')
            condition.text = project_def.get('condition', 'ALWAYS')
            trigger_with_no_params = XML.SubElement(tconfig, 'triggerWithNoParameters')
            trigger_with_no_params.text = 'false'

    def _coverage(self, xml_parent):
        cobertura = XML.SubElement(xml_parent, 'hudson.plugins.cobertura.CoberturaPublisher')
        XML.SubElement(cobertura, 'coberturaReportFile').text = '**/coverage.xml'
        XML.SubElement(cobertura, 'onlyStable').text = 'false'
        healthy = XML.SubElement(cobertura, 'healthyTarget')
        targets = XML.SubElement(healthy, 'targets', {'class':'enum-map','enum-type':'hudson.plugins.cobertura.targets.CoverageMetric'})
        entry = XML.SubElement(targets, 'entry')
        XML.SubElement(entry, 'hudson.plugins.cobertura.targets.CoverageMetric').text = 'CONDITIONAL'
        XML.SubElement(entry, 'int').text = '70'
        entry = XML.SubElement(targets, 'entry')
        XML.SubElement(entry, 'hudson.plugins.cobertura.targets.CoverageMetric').text = 'LINE'
        XML.SubElement(entry, 'int').text = '80'
        entry = XML.SubElement(targets, 'entry')
        XML.SubElement(entry, 'hudson.plugins.cobertura.targets.CoverageMetric').text = 'METHOD'
        XML.SubElement(entry, 'int').text = '80'
        unhealthy = XML.SubElement(cobertura, 'unhealthyTarget')
        targets = XML.SubElement(unhealthy, 'targets', {'class':'enum-map','enum-type':'hudson.plugins.cobertura.targets.CoverageMetric'})
        entry = XML.SubElement(targets, 'entry')
        XML.SubElement(entry, 'hudson.plugins.cobertura.targets.CoverageMetric').text = 'CONDITIONAL'
        XML.SubElement(entry, 'int').text = '0'
        entry = XML.SubElement(targets, 'entry')
        XML.SubElement(entry, 'hudson.plugins.cobertura.targets.CoverageMetric').text = 'LINE'
        XML.SubElement(entry, 'int').text = '0'
        entry = XML.SubElement(targets, 'entry')
        XML.SubElement(entry, 'hudson.plugins.cobertura.targets.CoverageMetric').text = 'METHOD'
        XML.SubElement(entry, 'int').text = '0'
        failing = XML.SubElement(cobertura, 'failingTarget')
        targets = XML.SubElement(failing, 'targets', {'class':'enum-map','enum-type':'hudson.plugins.cobertura.targets.CoverageMetric'})
        entry = XML.SubElement(targets, 'entry')
        XML.SubElement(entry, 'hudson.plugins.cobertura.targets.CoverageMetric').text = 'CONDITIONAL'
        XML.SubElement(entry, 'int').text = '0'
        entry = XML.SubElement(targets, 'entry')
        XML.SubElement(entry, 'hudson.plugins.cobertura.targets.CoverageMetric').text = 'LINE'
        XML.SubElement(entry, 'int').text = '0'
        entry = XML.SubElement(targets, 'entry')
        XML.SubElement(entry, 'hudson.plugins.cobertura.targets.CoverageMetric').text = 'METHOD'
        XML.SubElement(entry, 'int').text = '0'
        XML.SubElement(cobertura, 'sourceEncoding').text = 'ASCII'

    # Jenkins Job module for publishing via ftp
    # publish:
    #   site: 'docs.openstack.org'
    #   remote_dir: 'dest/dir'
    #   source_files: 'base/source/dir/**'
    #   remove_prefix: 'base/source/dir'
    #   excludes: '**/*.exludedfiletype'
    #
    # This will upload everything under $workspace/base/source/dir to
    # docs.openstack.org $ftpdir/dest/dir exluding the excluded file type.

    def _ftp(self, xml_parent, data):
        """
        Example XML:
        <publishers>
          <jenkins.plugins.publish__over__ftp.BapFtpPublisherPlugin>
            <consolePrefix>FTP: </consolePrefix>
            <delegate>
              <publishers>
                <jenkins.plugins.publish__over__ftp.BapFtpPublisher>
                  <configName>docs.openstack.org</configName>
                  <verbose>true</verbose>
                  <transfers>
                    <jenkins.plugins.publish__over__ftp.BapFtpTransfer>
                      <remoteDirectory></remoteDirectory>
                      <sourceFiles>openstack-identity-api/target/docbkx/webhelp/api/openstack-identity-service/2.0/**</sourceFiles>
                      <excludes>**/*.xml,**/null*</excludes>
                      <removePrefix>openstack-identity-api/target/docbkx/webhelp</removePrefix>
                      <remoteDirectorySDF>false</remoteDirectorySDF>
                      <flatten>false</flatten>
                      <cleanRemote>false</cleanRemote>
                      <asciiMode>false</asciiMode>
                    </jenkins.plugins.publish__over__ftp.BapFtpTransfer>
                  </transfers>
                  <useWorkspaceInPromotion>false</useWorkspaceInPromotion>
                  <usePromotionTimestamp>false</usePromotionTimestamp>
                </jenkins.plugins.publish__over__ftp.BapFtpPublisher>
              </publishers>
              <continueOnError>false</continueOnError>
              <failOnError>false</failOnError>
              <alwaysPublishFromMaster>false</alwaysPublishFromMaster>
              <hostConfigurationAccess class="jenkins.plugins.publish_over_ftp.BapFtpPublisherPlugin" reference="../.."/>
            </delegate>
          </jenkins.plugins.publish__over__ftp.BapFtpPublisherPlugin>
        </publishers>
        """
        outer_ftp = XML.SubElement(xml_parent,
                                   'jenkins.plugins.publish__over__ftp.BapFtpPublisherPlugin')
        XML.SubElement(outer_ftp, 'consolePrefix').text = 'FTP: '
        delegate = XML.SubElement(outer_ftp, 'delegate')
        publishers = XML.SubElement(delegate, 'publishers')
        ftp = XML.SubElement(publishers, 'jenkins.plugins.publish__over__ftp.BapFtpPublisher')
        XML.SubElement(ftp, 'configName').text = data['site']
        XML.SubElement(ftp, 'verbose').text = 'true'

        transfers = XML.SubElement(ftp, 'transfers')
        ftp_transfers = XML.SubElement(transfers, 'jenkins.plugins.publish__over__ftp.BapFtpTransfer')
        # TODO: the next four fields are where the magic happens. Fill them in.
        XML.SubElement(ftp_transfers, 'remoteDirectory').text = data['remote_dir']
        XML.SubElement(ftp_transfers, 'sourceFiles').text = data['source_files']
        XML.SubElement(ftp_transfers, 'excludes').text = data['excludes']
        XML.SubElement(ftp_transfers, 'removePrefix').text = data['remove_prefix']
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

    # Jenkins Job module for coverage publishers
    # To use you add the following into your YAML:
    # publisher:
    #   results: 'nosetests.xml'

    def _junit(self, xml_parent, data):
        junitresult = XML.SubElement(xml_parent,
            'hudson.tasks.junit.JUnitResultArchiver')
        XML.SubElement(junitresult, 'testResults').text = data['results']
        XML.SubElement(junitresult, 'keepLongStdio').text = "true"
        XML.SubElement(junitresult, 'testDataPublishers')

    # Jenkins Job module for pep8 publishers
    # No additional YAML needed

    def _pep8_add_entry(self, xml_parent, name):
        entry = XML.SubElement(xml_parent, 'entry')
        XML.SubElement(entry, 'string').text = name
        tconfig = XML.SubElement(entry, 'hudson.plugins.violations.TypeConfig')
        XML.SubElement(tconfig, 'type').text = name
        XML.SubElement(tconfig, 'min').text = '10'
        XML.SubElement(tconfig, 'max').text = '999'
        XML.SubElement(tconfig, 'unstable').text = '999'
        XML.SubElement(tconfig, 'usePattern').text = 'false'
        XML.SubElement(tconfig, 'pattern')

    def _pep8(self, xml_parent):
        violations = XML.SubElement(xml_parent, 'hudson.plugins.violations.ViolationsPublisher')
        config = XML.SubElement(violations, 'config')
        suppressions = XML.SubElement(config, 'suppressions', {'class':'tree-set'})
        XML.SubElement(suppressions, 'no-comparator')
        configs = XML.SubElement(config, 'typeConfigs')
        XML.SubElement(configs, 'no-comparator')

        self._pep8_add_entry(configs, 'checkstyle')
        self._pep8_add_entry(configs, 'codenarc')
        self._pep8_add_entry(configs, 'cpd')
        self._pep8_add_entry(configs, 'cpplint')
        self._pep8_add_entry(configs, 'csslint')
        self._pep8_add_entry(configs, 'findbugs')
        self._pep8_add_entry(configs, 'fxcop')
        self._pep8_add_entry(configs, 'gendarme')
        self._pep8_add_entry(configs, 'jcreport')
        self._pep8_add_entry(configs, 'jslint')

        entry = XML.SubElement(configs, 'entry')
        XML.SubElement(entry, 'string').text = 'pep8'
        tconfig = XML.SubElement(entry, 'hudson.plugins.violations.TypeConfig')
        XML.SubElement(tconfig, 'type').text = 'pep8'
        XML.SubElement(tconfig, 'min').text = '0'
        XML.SubElement(tconfig, 'max').text = '1'
        XML.SubElement(tconfig, 'unstable').text = '1'
        XML.SubElement(tconfig, 'usePattern').text = 'false'
        XML.SubElement(tconfig, 'pattern').text = '**/pep8.txt'

        self._pep8_add_entry(configs, 'pmd')
        self._pep8_add_entry(configs, 'pylint')
        self._pep8_add_entry(configs, 'simian')
        self._pep8_add_entry(configs, 'stylecop')

        XML.SubElement(config, 'limit').text = '100'
        XML.SubElement(config, 'sourcePathPattern')
        XML.SubElement(config, 'fauxProjectPath')
        XML.SubElement(config, 'encoding').text = 'default'

    # Jenkins Job module for PPA publishers
    # No additional YAML needed

    def _ppa(self, xml_parent):
        archiver = XML.SubElement(xml_parent, 'hudson.tasks.ArtifactArchiver')
        XML.SubElement(archiver, 'artifacts').text = 'build/*.dsc,build/*.tar.gz,build/*.changes'
        XML.SubElement(archiver, 'latestOnly').text = 'false'

    # Jenkins Job module for tarball publishers
    # To use you add the following into your YAML:
    # publish:
    #   site: 'glance.openstack.org'

    def _tarball(self, xml_parent, data):
        site = data['site']
        archiver = XML.SubElement(xml_parent, 'hudson.tasks.ArtifactArchiver')
        XML.SubElement(archiver, 'artifacts').text = 'dist/*.tar.gz'
        XML.SubElement(archiver, 'latestOnly').text = 'false'
        scp = XML.SubElement(xml_parent, 'be.certipost.hudson.plugin.SCPRepositoryPublisher')
        XML.SubElement(scp, 'siteName').text = site
        entries = XML.SubElement(scp, 'entries')
        entry = XML.SubElement(entries, 'be.certipost.hudson.plugin.Entry')
        XML.SubElement(entry, 'filePath').text = 'tarballs/{proj}/'.format(proj=self.data['main']['project'])
        XML.SubElement(entry, 'sourceFile').text = 'dist/*.tar.gz'
        XML.SubElement(entry, 'keepHierarchy').text = 'false'

    # Jenkins Job module for war publishers
    # To use you add the following into your YAML:
    # publish:
    #   site: 'nova.openstack.org'
    #   warfile: 'gerrit-war/target/gerrit*.war'
    #   target_path: 'tarballs/ci/'

    def _war(self, xml_parent, data):
        site = data['site']
        archiver = XML.SubElement(xml_parent, 'hudson.tasks.ArtifactArchiver')
        XML.SubElement(archiver, 'artifacts').text = data['warfile']
        XML.SubElement(archiver, 'latestOnly').text = 'false'
        scp = XML.SubElement(xml_parent, 'be.certipost.hudson.plugin.SCPRepositoryPublisher')
        XML.SubElement(scp, 'siteName').text = site
        entries = XML.SubElement(scp, 'entries')
        entry = XML.SubElement(entries, 'be.certipost.hudson.plugin.Entry')
        XML.SubElement(entry, 'filePath').text = data['target_path']
        XML.SubElement(entry, 'sourceFile').text = data['warfile']
        XML.SubElement(entry, 'keepHierarchy').text = 'false'
