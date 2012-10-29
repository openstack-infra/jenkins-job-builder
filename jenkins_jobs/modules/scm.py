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
The SCM module allows you to specify the source code location for the
project.  It adds the ``scm`` attribute to the :ref:`Job` definition,
which accepts a single scm definiton.

**Component**: scm
  :Macro: scm
  :Entry Point: jenkins_jobs.scm

Example::

  job:
    name: test_job
    scm:
      -git:
        url: https://example.com/project.git

"""


import xml.etree.ElementTree as XML
import jenkins_jobs.modules.base


def git(self, xml_parent, data):
    """yaml: git
    Specifies the git SCM repository for this job.
    Requires the Jenkins `Git Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/Git+Plugin>`_

    :arg str url: URL of the git repository
    :arg list(str) branches: list of branch specifiers to build

    Example::

      scm:
        -git:
          url: https://example.com/project.git
          branches:
            - master
            - stable
    """
    scm = XML.SubElement(xml_parent,
                         'scm', {'class': 'hudson.plugins.git.GitSCM'})
    XML.SubElement(scm, 'configVersion').text = '2'
    user = XML.SubElement(scm, 'userRemoteConfigs')
    huser = XML.SubElement(user, 'hudson.plugins.git.UserRemoteConfig')
    XML.SubElement(huser, 'name').text = 'origin'
    XML.SubElement(huser, 'refspec').text = \
        '+refs/heads/*:refs/remotes/origin/*'
    XML.SubElement(huser, 'url').text = data['url']
    xml_branches = XML.SubElement(scm, 'branches')
    branches = data.get('branches', ['**'])
    for branch in branches:
        bspec = XML.SubElement(xml_branches, 'hudson.plugins.git.BranchSpec')
        XML.SubElement(bspec, 'name').text = branch
    XML.SubElement(scm, 'disableSubmodules').text = 'false'
    XML.SubElement(scm, 'recursiveSubmodules').text = 'false'
    XML.SubElement(scm, 'doGenerateSubmoduleConfigurations').text = 'false'
    XML.SubElement(scm, 'authorOrCommitter').text = 'false'
    XML.SubElement(scm, 'clean').text = 'false'
    XML.SubElement(scm, 'wipeOutWorkspace').text = 'true'
    XML.SubElement(scm, 'pruneBranches').text = 'false'
    XML.SubElement(scm, 'remotePoll').text = 'false'
    XML.SubElement(scm, 'buildChooser',
                   {'class': 'hudson.plugins.git.util.DefaultBuildChooser'})
    XML.SubElement(scm, 'gitTool').text = 'Default'
    XML.SubElement(scm, 'submoduleCfg', {'class': 'list'})
    XML.SubElement(scm, 'relativeTargetDir')
    XML.SubElement(scm, 'reference')
    XML.SubElement(scm, 'excludedRegions')
    XML.SubElement(scm, 'excludedUsers')
    XML.SubElement(scm, 'gitConfigName')
    XML.SubElement(scm, 'gitConfigEmail')
    XML.SubElement(scm, 'skipTag').text = 'false'
    XML.SubElement(scm, 'scmName')


def svn(self, xml_parent, data):
    """yaml: svn
    Specifies the svn SCM repository for this job.

    :arg str url: URL of the svn repository
    :arg str basedir: location relative to the workspace root to checkout to
    :arg str workspaceupdater: optional argument to specify
         how to update the workspace

    :workspaceupdater values:
             :wipeworkspace: - deletes the workspace before checking out
             :revertupdate:  - do an svn revert then an svn update
             :emulateclean:  - delete unversioned/ignored files then update
             :update:        - do an svn update as much as possible

    Example::

      scm:
        - svn:
           url: http://svn.example.com/repo
           basedir: .
           workspaceupdater: update
    """

    scm = XML.SubElement(xml_parent, 'scm', {'class':
              'hudson.scm.SubversionSCM'})
    locations = XML.SubElement(scm, 'locations')
    module = XML.SubElement(locations,
              'hudson.scm.SubversionSCM_-ModuleLocation')
    XML.SubElement(module, 'remote').text = data['url']
    XML.SubElement(module, 'local').text = data['basedir']
    updater = data.get('workspaceupdater', 'wipeworkspace')
    if updater == 'wipeworkspace':
        updaterclass = 'CheckoutUpdater'
    elif updater == 'revertupdate':
        updaterclass = 'UpdateWithRevertUpdater'
    elif updater == 'emulateclean':
        updaterclass = 'UpdateWithCleanUpdater'
    elif updater == 'update':
        updaterclass = 'UpdateUpdater'
    XML.SubElement(scm, 'workspaceUpdater', {'class':
                'hudson.scm.subversion.' + updaterclass})


class SCM(jenkins_jobs.modules.base.Base):
    sequence = 30

    def gen_xml(self, parser, xml_parent, data):
        scms = data.get('scm', [])
        if scms:
            for scm in data.get('scm', []):
                self._dispatch('scm', 'scm',
                               parser, xml_parent, scm)
        else:
            XML.SubElement(xml_parent, 'scm', {'class': 'hudson.scm.NullSCM'})
