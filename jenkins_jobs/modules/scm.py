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
which accepts any number of scm definitions.

Note: Adding more than one scm definition requires the Jenkins `Multiple
SCMs plugin.
<https://wiki.jenkins-ci.org/display/JENKINS/Multiple+SCMs+Plugin>`_

**Component**: scm
  :Macro: scm
  :Entry Point: jenkins_jobs.scm

"""


import xml.etree.ElementTree as XML
import jenkins_jobs.modules.base
from jenkins_jobs.errors import JenkinsJobsException


def git(self, xml_parent, data):
    """yaml: git
    Specifies the git SCM repository for this job.
    Requires the Jenkins `Git Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/Git+Plugin>`_

    :arg str url: URL of the git repository
    :arg str credentials-id: ID of credentials to use to connect (optional)
    :arg str refspec: refspec to fetch
    :arg str name: name to fetch
    :arg list(str) branches: list of branch specifiers to build
    :arg list(str) excluded-users: list of users to ignore revisions from
      when polling for changes. (if polling is enabled)
    :arg list(str) included-regions: list of file/folders to include
    :arg list(str) excluded-regions: list of file/folders to exclude
    :arg str local-branch: Checkout/merge to local branch
    :arg dict merge:
        :merge:
            * **remote** (`string`) - name of repo that contains branch to
                merge to (default 'origin')
            * **branch** (`string`) - name of the branch to merge to
    :arg str basedir: location relative to the workspace root to clone to
             (default: workspace)
    :arg bool skip-tag: Skip tagging
    :arg bool shallow-clone: Perform shallow clone
    :arg bool prune: Prune remote branches
    :arg bool clean: Clean after checkout
    :arg bool fastpoll: Use fast remote polling
    :arg bool disable-submodules: Disable submodules
    :arg bool recursive-submodules: Recursively update submodules
    :arg bool use-author: Use author rather than committer in Jenkin's build
      changeset
    :arg str git-tool: The name of the Git installation to use
    :arg str reference-repo: Path of the reference repo to use during clone
    :arg str scm-name: The unique scm name for this Git SCM
    :arg bool wipe-workspace: Wipe out workspace before build
    :arg str browser: what repository browser to use (default '(Auto)')
    :arg str browser-url: url for the repository browser
    :arg str browser-version: version of the repository browser (GitLab)
    :arg str project-name: project name in Gitblit and ViewGit repobrowser
    :arg str choosing-strategy: Jenkins class for selecting what to build
    :arg str git-config-name: Configure name for Git clone
    :arg str git-config-email: Configure email for Git clone

    :browser values:
        :auto:
        :bitbucketweb:
        :cgit:
        :fisheye:
        :gitblit:
        :githubweb:
        :gitlab:
        :gitoriousweb:
        :gitweb:
        :redmineweb:
        :stash:
        :viewgit:

    :choosing-strategy values:
        :default:
        :inverse:
        :gerrit:

    Example:

    .. literalinclude:: /../../tests/scm/fixtures/git001.yaml
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
        ("git-tool", 'gitTool', "Default"),
        (None, 'submoduleCfg', '', {'class': 'list'}),
        ('basedir', 'relativeTargetDir', ''),
        ('reference-repo', 'reference', ''),
        ("git-config-name", 'gitConfigName', ''),
        ("git-config-email", 'gitConfigEmail', ''),
        ('skip-tag', 'skipTag', False),
        ('scm-name', 'scmName', ''),
        ("shallow-clone", "useShallowClone", False),
    ]

    choosing_strategies = {
        'default': 'hudson.plugins.git.util.DefaultBuildChooser',
        'gerrit': ('com.sonyericsson.hudson.plugins.'
                   'gerrit.trigger.hudsontrigger.GerritTriggerBuildChooser'),
        'inverse': 'hudson.plugins.git.util.InverseBuildChooser',
    }

    scm = XML.SubElement(xml_parent,
                         'scm', {'class': 'hudson.plugins.git.GitSCM'})
    XML.SubElement(scm, 'configVersion').text = '2'
    user = XML.SubElement(scm, 'userRemoteConfigs')
    huser = XML.SubElement(user, 'hudson.plugins.git.UserRemoteConfig')
    XML.SubElement(huser, 'name').text = data.get('name', 'origin')
    if 'refspec' in data:
        refspec = data['refspec']
    else:
        refspec = '+refs/heads/*:refs/remotes/origin/*'
    XML.SubElement(huser, 'refspec').text = refspec
    XML.SubElement(huser, 'url').text = data['url']
    if 'credentials-id' in data:
        XML.SubElement(huser, 'credentialsId').text = data['credentials-id']
    xml_branches = XML.SubElement(scm, 'branches')
    branches = data.get('branches', ['**'])
    for branch in branches:
        bspec = XML.SubElement(xml_branches, 'hudson.plugins.git.BranchSpec')
        XML.SubElement(bspec, 'name').text = branch
    excluded_users = '\n'.join(data.get('excluded-users', []))
    XML.SubElement(scm, 'excludedUsers').text = excluded_users
    if 'included-regions' in data:
        include_string = '\n'.join(data['included-regions'])
        XML.SubElement(scm, 'includedRegions').text = include_string
    if 'excluded-regions' in data:
        exclude_string = '\n'.join(data['excluded-regions'])
        XML.SubElement(scm, 'excludedRegions').text = exclude_string
    if 'merge' in data:
        merge = data['merge']
        name = merge.get('remote', 'origin')
        branch = merge['branch']
        urc = XML.SubElement(scm, 'userMergeOptions')
        XML.SubElement(urc, 'mergeRemote').text = name
        XML.SubElement(urc, 'mergeTarget').text = branch

    try:
        choosing_strategy = choosing_strategies[data.get('choosing-strategy',
                                                         'default')]
    except KeyError:
        raise ValueError('Invalid choosing-strategy %r' %
                         data.get('choosing-strategy'))
    XML.SubElement(scm, 'buildChooser', {'class': choosing_strategy})

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

    if 'local-branch' in data:
        XML.SubElement(scm, 'localBranch').text = data['local-branch']

    browser = data.get('browser', 'auto')
    browserdict = {'auto': 'auto',
                   'bitbucketweb': 'BitbucketWeb',
                   'cgit': 'CGit',
                   'fisheye': 'FisheyeGitRepositoryBrowser',
                   'gitblit': 'GitBlitRepositoryBrowser',
                   'githubweb': 'GithubWeb',
                   'gitlab': 'GitLab',
                   'gitoriousweb': 'GitoriousWeb',
                   'gitweb': 'GitWeb',
                   'redmineweb': 'RedmineWeb',
                   'stash': 'Stash',
                   'viewgit': 'ViewGitWeb'}
    if browser not in browserdict:
        valid = sorted(browserdict.keys())
        raise JenkinsJobsException("Browser entered is not valid must be one "
                                   "of: %s or %s." % (", ".join(valid[:-1]),
                                                      valid[-1]))
    if browser != 'auto':
        bc = XML.SubElement(scm, 'browser', {'class':
                            'hudson.plugins.git.browser.' +
                            browserdict[browser]})
        XML.SubElement(bc, 'url').text = data['browser-url']
        if browser in ['gitblit', 'viewgit']:
            XML.SubElement(bc, 'projectName').text = str(
                data.get('project-name', ''))
        if browser == 'gitlab':
            XML.SubElement(bc, 'version').text = str(
                data.get('browser-version', '0.0'))


def repo(self, xml_parent, data):
    """yaml: repo
    Specifies the repo SCM repository for this job.
    Requires the Jenkins `Repo Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/Repo+Plugin>`_

    :arg str manifest-url: URL of the repo manifest
    :arg str manifest-branch: The branch of the manifest to use (optional)
    :arg str manifest-file: Initial manifest file to use when initialising
             (optional)
    :arg str manifest-group: Only retrieve those projects in the manifest
             tagged with the provided group name (optional)
    :arg str destination-dir: Location relative to the workspace root to clone
             under (optional)
    :arg str repo-url: custom url to retrieve the repo application (optional)
    :arg str mirror-dir: Path to mirror directory to reference when
             initialising (optional)
    :arg int jobs: Number of projects to fetch simultaneously (default 0)
    :arg bool current-branch: Fetch only the current branch from the server
              (default true)
    :arg bool quiet: Make repo more quiet
              (default true)
    :arg str local-manifest: Contents of .repo/local_manifest.xml, written
             prior to calling sync (optional)

    Example:

    .. literalinclude:: /../../tests/scm/fixtures/repo001.yaml
    """

    scm = XML.SubElement(xml_parent,
                         'scm', {'class': 'hudson.plugins.repo.RepoScm'})

    if 'manifest-url' in data:
        XML.SubElement(scm, 'manifestRepositoryUrl').text = \
            data['manifest-url']
    else:
        raise JenkinsJobsException("Must specify a manifest url")

    mapping = [
        # option, xml name, default value
        ("manifest-branch", 'manifestBranch', ''),
        ("manifest-file", 'manifestFile', ''),
        ("manifest-group", 'manifestGroup', ''),
        ("destination-dir", 'destinationDir', ''),
        ("repo-url", 'repoUrl', ''),
        ("mirror-dir", 'mirrorDir', ''),
        ("jobs", 'jobs', 0),
        ("current-branch", 'currentBranch', True),
        ("quiet", 'quiet', True),
        ("local-manifest", 'localManifest', ''),
    ]

    for elem in mapping:
        (optname, xmlname, val) = elem
        val = data.get(optname, val)
        # Skip adding xml entry if default is empty string and no value given
        if not val and elem[2] is '':
            continue
        xe = XML.SubElement(scm, xmlname)
        if type(elem[2]) == bool:
            xe.text = str(val).lower()
        else:
            xe.text = str(val)


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
        raise JenkinsJobsException("A top level url or repos list must exist")
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


def tfs(self, xml_parent, data):
    """yaml: tfs
    Specifies the Team Foundation Server repository for this job.
    Requires the Jenkins `Team Foundation Server Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/
    Team+Foundation+Server+Plugin>`_

    **NOTE**: TFS Password must be entered manually on the project if a
    user name is specified. The password will be overwritten with an empty
    value every time the job is rebuilt with Jenkins Job Builder.

    :arg str server-url: The name or URL of the team foundation server.
        If the server has been registered on the machine then it is only
        necessary to enter the name.
    :arg str project-path: The name of the project as it is registered on the
        server.
    :arg str login: The user name that is registered on the server. The user
        name must contain the name and the domain name. Entered as
        domain\\\user or user\@domain (optional).
        **NOTE**: You must enter in at least two slashes for the
        domain\\\user format in JJB YAML. It will be rendered normally.
    :arg str use-update: If true, Hudson will not delete the workspace at end
        of each build. This causes the artifacts from the previous build to
        remain when a new build starts. (default true)
    :arg str local-path: The folder where all files will be retrieved into.
        The folder name is a relative path, under the workspace of the current
        job. (default .)
    :arg str workspace: The name of the workspace under which the source
        should be retrieved. This workspace is created at the start of a
        download, and deleted at the end. You can normally omit the property
        unless you want to name a workspace to avoid conflicts on the server
        (i.e. when you have multiple projects on one server talking to a
        Team Foundation Server). (default Hudson-${JOB_NAME}-${NODE_NAME})

        The TFS plugin supports the following macros that are replaced in the
        workspace name:

        * ${JOB_NAME} - The name of the job.
        * ${USER_NAME} - The user name that the Hudson server or slave is
            running as.
        * ${NODE_NAME} - The name of the node/slave that the plugin currently
            is executed on. Note that this is not the hostname, this value is
            the Hudson configured name of the slave/node.
        * ${ENV} - The environment variable that is set on the master or slave.


    :arg dict web-access: Adds links in "changes" views within Jenkins to an
        external system for browsing the details of those changes. The "Auto"
        selection attempts to infer the repository browser from other jobs,
        if supported by the SCM and a job with matching SCM details can be
        found. (optional, default Auto).

        :web-access value:
            * **web-url** -- Enter the URL to the TSWA server. The plugin will
              strip the last path (if any) of the URL when building URLs for
              change set pages and other pages. (optional, default
              uses server-url)


    Examples::

      scm:
        - tfs:
           server-url: "tfs.company.com"
           project-path: "$/myproject"
           login: "mydomain\\\jane"
           use-update: false
           local-path: "../foo/"
           workspace: "Hudson-${JOB_NAME}"
           web-access:
               - web-url: "http://TFSMachine:8080"

      scm:
        - tfs:
           server-url: "tfs.company.com"
           project-path: "$/myproject"
           login: "jane@mydomain"
           use-update: false
           local-path: "../foo/"
           workspace: "Hudson-${JOB_NAME}"
           web-access:

      scm:
        - tfs:
           server-url: "tfs.company.com"
           project-path: "$/myproject"
           login: "mydomain\\\jane"
           use-update: false
           local-path: "../foo/"
           workspace: "Hudson-${JOB_NAME}"

    """

    tfs = XML.SubElement(xml_parent, 'scm', {'class': 'hudson.plugins.tfs.'
                                             'TeamFoundationServerScm'})
    XML.SubElement(tfs, 'serverUrl').text = str(
        data.get('server-url', ''))
    XML.SubElement(tfs, 'projectPath').text = str(
        data.get('project-path', ''))
    XML.SubElement(tfs, 'localPath').text = str(
        data.get('local-path', '.'))
    XML.SubElement(tfs, 'workspaceName').text = str(
        data.get('workspace', 'Hudson-${JOB_NAME}-${NODE_NAME}'))
    # TODO: In the future, with would be nice to have a place that can pull
    # passwords into JJB without having to commit them in plaintext. This
    # could also integrate nicely with global configuration options.
    XML.SubElement(tfs, 'userPassword')
    XML.SubElement(tfs, 'userName').text = str(
        data.get('login', ''))
    XML.SubElement(tfs, 'useUpdate').text = str(
        data.get('use-update', True))
    store = data.get('web-access', None)
    if 'web-access' in data and isinstance(store, list):
        web = XML.SubElement(tfs, 'repositoryBrowser', {'class': 'hudson.'
                                  'plugins.tfs.browsers.'
                                  'TeamSystemWebAccessBrowser'})
        XML.SubElement(web, 'url').text = str(store[0].get('web-url', None))
    elif 'web-access' in data and store is None:
        XML.SubElement(tfs, 'repositoryBrowser', {'class': 'hudson.'
                                                  'plugins.tfs.browsers.'
                                                  'TeamSystemWebAccess'
                                                  'Browser'})


def workspace(self, xml_parent, data):
    """yaml: workspace
    Specifies the cloned workspace for this job to use as a SCM source.
    Requires the Jenkins `Clone Workspace SCM Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/Clone+Workspace+SCM+Plugin>`_

    The job the workspace is cloned from must be configured with an
    clone-workspace publisher

    :arg str parent-job: The name of the parent job to clone the
        workspace from.
    :arg str criteria: Set the criteria to determine what build of the parent
        project to use. Can be one of 'Any', 'Not Failed' or 'Successful'.
        (default: Any)


    Example:

    .. literalinclude:: /../../tests/scm/fixtures/workspace001.yaml
    """

    workspace = XML.SubElement(xml_parent, 'scm', {'class': 'hudson.plugins.'
                               'cloneworkspace.CloneWorkspaceSCM'})
    XML.SubElement(workspace, 'parentJobName').text = str(
        data.get('parent-job', ''))

    criteria_list = ['Any', 'Not Failed', 'Successful']

    criteria = data.get('criteria', 'Any').title()

    if 'criteria' in data and criteria not in criteria_list:
        raise JenkinsJobsException(
            'clone-workspace criteria must be one of: '
            + ', '.join(criteria_list))
    else:
        XML.SubElement(workspace, 'criteria').text = criteria


class SCM(jenkins_jobs.modules.base.Base):
    sequence = 30

    component_type = 'scm'
    component_list_type = 'scm'

    def gen_xml(self, parser, xml_parent, data):
        scms = data.get('scm', [])
        if scms:
            if len(scms) > 1:
                class_name = 'org.jenkinsci.plugins.multiplescms.MultiSCM'
                xml_attribs = {'class': class_name}
                xml_parent = XML.SubElement(xml_parent, 'scm', xml_attribs)
                xml_parent = XML.SubElement(xml_parent, 'scms')
            for scm in data.get('scm', []):
                self.registry.dispatch('scm', parser, xml_parent, scm)
        else:
            XML.SubElement(xml_parent, 'scm', {'class': 'hudson.scm.NullSCM'})
