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
    :arg str refspec: refspec to fetch
    :arg list(str) branches: list of branch specifiers to build
    :arg bool skip-tag: Skip tagging
    :arg bool prune: Prune remote branches
    :arg bool clean: Clean after checkout
    :arg bool fastpoll: Use fast remote polling
    :arg bool disable-submodules: Disable submodules
    :arg bool recursive-submodules: Recursively update submodules
    :arg bool use-author: Use author rather than committer in Jenkin's build
      changeset
    :arg bool wipe-workspace: Wipe out workspace before build

    Example::

      scm:
        - git:
          url: https://example.com/project.git
          branches:
            - master
            - stable
    """

    # XXX somebody should write the docs for those with option name =
    # None so we have a sensible name/key for it.
    mapping = [
        # option, xml name, default value (text), attributes (hard coded)
        ("disable-submodules", 'disableSubmodules', False),
        ("recursive-submodules", 'recursiveSubmodules', False),
        (None, 'doGenerateSubmoduleConfigurations', False),
        ("use-author", 'authorOrCommitter', False),
        ("clean", 'clean', False),
        ("wipe-workspace", 'wipeOutWorkspace', True),
        ("prune", 'pruneBranches', False),
        ("fastpoll", 'remotePoll', False),
        (None, 'buildChooser', '', {
            'class': 'hudson.plugins.git.util.DefaultBuildChooser'}),
        (None, 'gitTool', "Default"),
        (None, 'submoduleCfg', '', {'class': 'list'}),
        (None, 'relativeTargetDir', ''),
        (None, 'reference', ''),
        (None, 'excludedRegions', ''),
        (None, 'excludedUsers', ''),
        (None, 'gitConfigName', ''),
        (None, 'gitConfigEmail', ''),
        ('skip-tag', 'skipTag', False),
        (None, 'scmName', ''),
        ]

    scm = XML.SubElement(xml_parent,
                         'scm', {'class': 'hudson.plugins.git.GitSCM'})
    XML.SubElement(scm, 'configVersion').text = '2'
    user = XML.SubElement(scm, 'userRemoteConfigs')
    huser = XML.SubElement(user, 'hudson.plugins.git.UserRemoteConfig')
    XML.SubElement(huser, 'name').text = 'origin'
    if 'refspec' in data:
        refspec = data['refspec']
    else:
        refspec = '+refs/heads/*:refs/remotes/origin/*'
    XML.SubElement(huser, 'refspec').text = refspec
    XML.SubElement(huser, 'url').text = data['url']
    xml_branches = XML.SubElement(scm, 'branches')
    branches = data.get('branches', ['**'])
    for branch in branches:
        bspec = XML.SubElement(xml_branches, 'hudson.plugins.git.BranchSpec')
        XML.SubElement(bspec, 'name').text = branch
    for elem in mapping:
        (optname, xmlname, val) = elem[:3]
        attrs = {}
        if len(elem) >= 4:
            attrs = elem[3]
        xe = XML.SubElement(scm, xmlname, attrs)
        if optname and optname in data:
            val = data[optname]
        if type(val) == bool:
            xe.text = str(val).lower()
        else:
            xe.text = val


def svn(self, xml_parent, data):
    """yaml: svn
    Specifies the svn SCM repository for this job.

    :arg str url: URL of the svn repository
    :arg str basedir: location relative to the workspace root to checkout to
      (default '.')
    :arg str workspaceupdater: optional argument to specify
      how to update the workspace (default wipeworkspace)
    :arg list repos: list of repositories to checkout (optional)

      :Repo: * **url** (`str`) -- URL for the repository
             * **basedir** (`str`) -- Location relative to the workspace
                                      root to checkout to (default '.')

    :workspaceupdater values:
             :wipeworkspace: - deletes the workspace before checking out
             :revertupdate:  - do an svn revert then an svn update
             :emulateclean:  - delete unversioned/ignored files then update
             :update:        - do an svn update as much as possible

    Example::

      scm:
        - svn:
           workspaceupdater: update
           repos:
             - url: http://svn.example.com/repo
               basedir: .
             - url: http://svn.example.com/repo2
               basedir: repo2
    """
    scm = XML.SubElement(xml_parent, 'scm', {'class':
              'hudson.scm.SubversionSCM'})
    locations = XML.SubElement(scm, 'locations')
    if 'repos' in data:
        repos = data['repos']
        for repo in repos:
            module = XML.SubElement(locations,
              'hudson.scm.SubversionSCM_-ModuleLocation')
            XML.SubElement(module, 'remote').text = repo['url']
            XML.SubElement(module, 'local').text = repo.get('basedir', '.')
    elif 'url' in data:
        module = XML.SubElement(locations,
           'hudson.scm.SubversionSCM_-ModuleLocation')
        XML.SubElement(module, 'remote').text = data['url']
        XML.SubElement(module, 'local').text = data.get('basedir', '.')
    else:
        raise Exception("A top level url or repos list must exist")
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
