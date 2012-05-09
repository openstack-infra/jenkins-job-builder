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

# Jenkins Job module for builders
# To use add the folowing into your YAML:
# builders:
#   - 'gerrit_git_prep'
#   - 'python26'

import xml.etree.ElementTree as XML

class builders(object):
    def __init__(self, data):
        self.data = data

    def gen_xml(self, xml_parent):
        builders = XML.SubElement(xml_parent, 'builders')
        for builder in self.data['builders']:
            getattr(self, '_' + builder)(builders)

    def _add_script(self, xml_parent, script):
        shell = XML.SubElement(xml_parent, 'hudson.tasks.Shell')
        XML.SubElement(shell, 'command').text = script

    def _copy_bundle(self, xml_parent):
        copy = XML.SubElement(xml_parent, 'hudson.plugins.copyartifact.CopyArtifact')
        XML.SubElement(copy, 'projectName').text = '$PROJECT-venv'
        XML.SubElement(copy, 'filter')
        XML.SubElement(copy, 'target')
        XML.SubElement(copy, 'selector', {'class':'hudson.plugins.copyartifact.StatusBuildSelector'})
        self._add_script(xml_parent, '/usr/local/jenkins/slave_scripts/copy-bundle.sh')

    def _coverage(self, xml_parent):
        self._add_script(xml_parent, '/usr/local/jenkins/slave_scripts/run-cover.sh')

    def _docs(self, xml_parent):
        self._add_script(xml_parent, '/usr/local/jenkins/slave_scripts/run-docs.sh')

    def _gerrit_git_prep(self, xml_parent):
        self._add_script(xml_parent, '/usr/local/jenkins/slave_scripts/gerrit-git-prep.sh {site}'.format(site=self.data['main']['site']))

    def _pep8(self, xml_parent):
        self._add_script(xml_parent, 'tox -v -epep8 | tee pep8.txt')

    def _python26(self, xml_parent):
        self._add_script(xml_parent, '/usr/local/jenkins/slave_scripts/run-tox.sh 26')

    def _python27(self, xml_parent):
        self._add_script(xml_parent, '/usr/local/jenkins/slave_scripts/run-tox.sh 27')

    def _tarball(self, xml_parent):
        self._add_script(xml_parent, '/usr/local/jenkins/slave_scripts/create-tarball.sh')

    def _venv(self, xml_parent):
        self._add_script(xml_parent, '/usr/local/jenkins/slave_scripts/build-bundle.sh')

    def _ppa(self, xml_parent):
        self._add_script(xml_parent, 'rm -rf build dist.zip\n\
mkdir build')
        copy = XML.SubElement(xml_parent, 'hudson.plugins.copyartifact.CopyArtifact')
        XML.SubElement(copy, 'projectName').text = '$PROJECT-tarball'
        XML.SubElement(copy, 'filter').text = 'dist/*.tar.gz'
        XML.SubElement(copy, 'target').text = 'build'
        selector = XML.SubElement(copy, 'selector', {'class':'hudson.plugins.copyartifact.StatusBuildSelector'})
        XML.SubElement(selector, 'parameterName').text = 'BUILD_SELECTOR'
        self._add_script(xml_parent, '#!/bin/bash\n\
\n\
#export DO_UPLOAD=&quot;no&quot;\n\
export PROJECT=&quot;<%= project %>&quot;\n\
export GERRIT_REFNAME=$BRANCH\n\
/usr/local/jenkins/slave_scripts/create-ppa-package.sh')
