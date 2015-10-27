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
which accepts any number of scm definitions. It is also possible to pass
``[]`` to the ``scm`` attribute. This is useful when a set of configs has a
global default ``scm`` and you want to a particular job to override that
default with no SCM.

**Component**: scm
  :Macro: scm
  :Entry Point: jenkins_jobs.scm

The scm module allows referencing multiple repositories in a Jenkins job.
Note: Adding more than one scm definition requires the Jenkins
:jenkins-wiki:`Multiple SCMs plugin <Multiple+SCMs+Plugin>`.

Example of multiple repositories in a single job:
    .. literalinclude:: /../../tests/macros/fixtures/scm/multi-scms001.yaml

Example of an empty ``scm``:
    .. literalinclude:: /../../tests/scm/fixtures/empty.yaml
"""

import logging
import xml.etree.ElementTree as XML

from jenkins_jobs.errors import InvalidAttributeError
from jenkins_jobs.errors import JenkinsJobsException
from jenkins_jobs.errors import MissingAttributeError
import jenkins_jobs.modules.base
from jenkins_jobs.modules.helpers import convert_mapping_to_xml


def git(parser, xml_parent, data):
    """yaml: git
    Specifies the git SCM repository for this job.
    Requires the Jenkins :jenkins-wiki:`Git Plugin <Git+Plugin>`.

    :arg str url: URL of the git repository
    :arg str credentials-id: ID of credential to use to connect, which is the
        last field (a 32-digit hexadecimal code) of the path of URL visible
        after you clicked the credential under Jenkins Global credentials.
        (optional)
    :arg str refspec: refspec to fetch (default
        '+refs/heads/\*:refs/remotes/remoteName/\*')
    :arg str name: name to fetch (default 'origin')
    :arg list(str) remotes: list of remotes to set up (optional, only needed if
        multiple remotes need to be set up)

        :Remote:
            * **url** (`string`) - url of remote repo
            * **refspec** (`string`) - refspec to fetch (optional)
            * **credentials-id** - ID of credential to use to connect, which
              is the last field of the path of URL (a 32-digit hexadecimal
              code) visible after you clicked credential under Jenkins Global
              credentials. (optional)
    :arg list(str) branches: list of branch specifiers to build (default '**')
    :arg list(str) excluded-users: list of users to ignore revisions from
        when polling for changes. (if polling is enabled, optional)
    :arg list(str) included-regions: list of file/folders to include (optional)
    :arg list(str) excluded-regions: list of file/folders to exclude (optional)
    :arg str local-branch: Checkout/merge to local branch (optional)
    :arg dict merge:
        :merge:
            * **remote** (`string`) - name of repo that contains branch to
              merge to (default 'origin')
            * **branch** (`string`) - name of the branch to merge to
            * **strategy** (`string`) - merge strategy. Can be one of
              'default', 'resolve', 'recursive', 'octopus', 'ours',
              'subtree'. (default 'default')
            * **fast-forward-mode** (`string`) - merge fast-forward mode.
              Can be one of 'FF', 'FF_ONLY' or 'NO_FF'. (default 'FF')
    :arg str basedir: location relative to the workspace root to clone to
        (default workspace)
    :arg bool skip-tag: Skip tagging (default false)
    :arg bool shallow-clone: Perform shallow clone (default false)
    :arg bool prune: Prune remote branches (default false)
    :arg bool clean: Clean after checkout (default false)

        .. deprecated:: 1.1.1. Please use clean extension format.

    :arg bool fastpoll: Use fast remote polling (default false)
    :arg bool disable-submodules: Disable submodules (default false)

        .. deprecated:: 1.1.1. Please use submodule extension.

    :arg bool recursive-submodules: Recursively update submodules (default
      false)

        .. deprecated:: 1.1.1. Please use submodule extension.

    :arg bool use-author: Use author rather than committer in Jenkin's build
        changeset (default false)
    :arg str git-tool: The name of the Git installation to use (default
        'Default')
    :arg str reference-repo: Path of the reference repo to use during clone
        (optional)
    :arg str scm-name: The unique scm name for this Git SCM (optional)
    :arg bool ignore-notify: Ignore notifyCommit URL accesses (default false)
    :arg str browser: what repository browser to use.

        :browsers supported:
            * **auto** - (default)
            * **assemblaweb** - https://www.assembla.com/home
            * **bitbucketweb** - https://bitbucket.org/
            * **cgit** - https://git.zx2c4.com/cgit/about/
            * **fisheye** - https://www.atlassian.com/software/fisheye
            * **gitblit** - http://gitblit.com/
            * **githubweb** - https://github.com/
            * **gitiles** - https://code.google.com/p/gitiles/
            * **gitlab** - https://about.gitlab.com/
            * **gitlist** - http://gitlist.org/
            * **gitoriousweb** - https://gitorious.org/
            * **gitweb** - https://git-scm.com/docs/gitweb
            * **kiln** - https://www.fogcreek.com/kiln/
            * **microsoft\-tfs\-2013** - |tfs_2013|
            * **phabricator** - http://phabricator.org/
            * **redmineweb** - http://www.redmine.org/
            * **rhodecode** - https://rhodecode.com/
            * **stash** - https://www.atlassian.com/software/bitbucket/server
            * **viewgit** - http://viewgit.fealdia.org/
    :arg str browser-url: url for the repository browser (required if browser
        is not 'auto', no default)
    :arg str browser-version: version of the repository browser (GitLab only,
        default '0.0')
    :arg str project-name: project name in Gitblit and ViewGit repobrowser
        (optional)
    :arg str repo-name: repository name in phabricator repobrowser (optional)
    :arg str choosing-strategy: Jenkins class for selecting what to build.
        Can be one of `default`, `inverse`, or `gerrit` (default 'default')
    :arg str git-config-name: Configure name for Git clone (optional)
    :arg str git-config-email: Configure email for Git clone (optional)

    :extensions:

        * **changelog-against** (`dict`)
            * **remote** (`string`) - name of repo that contains branch to
              create changelog against (default 'origin')
            * **branch** (`string`) - name of the branch to create changelog
              against (default 'master')
        * **clean** (`dict`)
            * **after** (`bool`) - Clean the workspace after checkout
            * **before** (`bool`) - Clean the workspace before checkout
        * **ignore-commits-with-messages** (`list(str)`) - Revisions committed
          with messages matching these patterns will be ignored. (optional)
        * **force-polling-using-workspace** (`bool`) - Force polling using
          workspace (default false)
        * **sparse-checkout** (`dict`)
            * **paths** (`list`) - List of paths to sparse checkout. (optional)
        * **submodule** (`dict`)
            * **disable** (`bool`) - By disabling support for submodules you
              can still keep using basic git plugin functionality and just have
              Jenkins to ignore submodules completely as if they didn't exist.
            * **recursive** (`bool`) - Retrieve all submodules recursively
              (uses '--recursive' option which requires git>=1.6.5)
            * **tracking** (`bool`) - Retrieve the tip of the configured
              branch in .gitmodules (Uses '\-\-remote' option which requires
              git>=1.8.2)
            * **reference-repo** (`str`) - Path of the reference repo to use
              during clone (optional)
            * **timeout** (`int`) - Specify a timeout (in minutes) for
              submodules operations (default: 10).
        * **timeout** (`str`) - Timeout for git commands in minutes (optional)
        * **wipe-workspace** (`bool`) - Wipe out workspace before build
            (default true)


    Example:

    .. literalinclude:: /../../tests/scm/fixtures/git001.yaml

    .. |tfs_2013| replace::
        https://www.visualstudio.com/en-us/products/tfs-overview-vs.aspx

    """
    logger = logging.getLogger("%s:git" % __name__)

    # XXX somebody should write the docs for those with option name =
    # None so we have a sensible name/key for it.
    mapping = [
        # option, xml name, default value (text), attributes (hard coded)
        ("disable-submodules", 'disableSubmodules', False),
        ("recursive-submodules", 'recursiveSubmodules', False),
        (None, 'doGenerateSubmoduleConfigurations', False),
        ("use-author", 'authorOrCommitter', False),
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
        ("ignore-notify", "ignoreNotifyCommit", False),
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
    if 'remotes' not in data:
        data['remotes'] = [{data.get('name', 'origin'): data.copy()}]
    for remoteData in data['remotes']:
        huser = XML.SubElement(user, 'hudson.plugins.git.UserRemoteConfig')
        remoteName = next(iter(remoteData.keys()))
        XML.SubElement(huser, 'name').text = remoteName
        remoteParams = next(iter(remoteData.values()))
        if 'refspec' in remoteParams:
            refspec = remoteParams['refspec']
        else:
            refspec = '+refs/heads/*:refs/remotes/' + remoteName + '/*'
        XML.SubElement(huser, 'refspec').text = refspec
        if 'url' in remoteParams:
            remoteURL = remoteParams['url']
        else:
            raise JenkinsJobsException('Must specify a url for git remote \"' +
                                       remoteName + '"')
        XML.SubElement(huser, 'url').text = remoteURL
        if 'credentials-id' in remoteParams:
            credentialsId = remoteParams['credentials-id']
            XML.SubElement(huser, 'credentialsId').text = credentialsId
    xml_branches = XML.SubElement(scm, 'branches')
    branches = data.get('branches', ['**'])
    for branch in branches:
        bspec = XML.SubElement(xml_branches, 'hudson.plugins.git.BranchSpec')
        XML.SubElement(bspec, 'name').text = branch
    excluded_users = '\n'.join(data.get('excluded-users', []))
    XML.SubElement(scm, 'excludedUsers').text = excluded_users
    if 'merge' in data:
        merge = data['merge']
        merge_strategies = ['default', 'resolve', 'recursive', 'octopus',
                            'ours', 'subtree']
        fast_forward_modes = ['FF', 'FF_ONLY', 'NO_FF']
        name = merge.get('remote', 'origin')
        branch = merge['branch']
        urc = XML.SubElement(scm, 'userMergeOptions')
        XML.SubElement(urc, 'mergeRemote').text = name
        XML.SubElement(urc, 'mergeTarget').text = branch
        strategy = merge.get('strategy', 'default')
        if strategy not in merge_strategies:
            raise InvalidAttributeError('strategy', strategy, merge_strategies)
        XML.SubElement(urc, 'mergeStrategy').text = strategy
        fast_forward_mode = merge.get('fast-forward-mode', 'FF')
        if fast_forward_mode not in fast_forward_modes:
            raise InvalidAttributeError('fast-forward-mode', fast_forward_mode,
                                        fast_forward_modes)
        XML.SubElement(urc, 'fastForwardMode').text = fast_forward_mode

    try:
        choosing_strategy = choosing_strategies[data.get('choosing-strategy',
                                                         'default')]
    except KeyError:
        raise ValueError('Invalid choosing-strategy %r' %
                         data.get('choosing-strategy'))
    XML.SubElement(scm, 'buildChooser', {'class': choosing_strategy})

    for elem in mapping:
        (optname, xmlname, val) = elem[:3]

        # Throw warning for deprecated settings and skip if the 'submodule' key
        # is available.
        submodule_cfgs = ['disable-submodules', 'recursive-submodules']
        if optname in submodule_cfgs:
            if optname in data:
                logger.warn("'{0}' is deprecated, please convert to use the "
                            "'submodule' section instead as support for this "
                            "top level option will be removed in a future "
                            "release.".format(optname))
            if 'submodule' in data:
                continue

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

    exts_node = XML.SubElement(scm, 'extensions')
    impl_prefix = 'hudson.plugins.git.extensions.impl.'
    if 'included-regions' in data or 'excluded-regions' in data:
        ext_name = XML.SubElement(exts_node,
                                  'hudson.plugins.git.extensions.impl.'
                                  'PathRestriction')
        if 'included-regions' in data:
            include_string = '\n'.join(data['included-regions'])
            XML.SubElement(ext_name, 'includedRegions').text = include_string
        if 'excluded-regions' in data:
            exclude_string = '\n'.join(data['excluded-regions'])
            XML.SubElement(ext_name, 'excludedRegions').text = exclude_string
    if 'changelog-against' in data:
        ext_name = impl_prefix + 'ChangelogToBranch'
        ext = XML.SubElement(exts_node, ext_name)
        opts = XML.SubElement(ext, 'options')
        change_remote = data['changelog-against'].get('remote', 'origin')
        change_branch = data['changelog-against'].get('branch', 'master')
        XML.SubElement(opts, 'compareRemote').text = change_remote
        XML.SubElement(opts, 'compareTarget').text = change_branch
    if 'clean' in data:
        # Keep support for old format 'clean' configuration by checking
        # if 'clean' is boolean. Else we're using the new extensions style.
        if isinstance(data['clean'], bool):
            clean_after = data['clean']
            clean_before = False
            logger.warn("'clean: bool' configuration format is deprecated, "
                        "please use the extension style format to configure "
                        "this option.")
        else:
            clean_after = data['clean'].get('after', False)
            clean_before = data['clean'].get('before', False)
        if clean_after:
            ext_name = impl_prefix + 'CleanCheckout'
            ext = XML.SubElement(exts_node, ext_name)
        if clean_before:
            ext_name = impl_prefix + 'CleanBeforeCheckout'
            ext = XML.SubElement(exts_node, ext_name)
    if 'ignore-commits-with-messages' in data:
        for msg in data['ignore-commits-with-messages']:
            ext_name = impl_prefix + 'MessageExclusion'
            ext = XML.SubElement(exts_node, ext_name)
            XML.SubElement(ext, 'excludedMessage').text = msg
    if 'sparse-checkout' in data:
        ext_name = impl_prefix + 'SparseCheckoutPaths'
        ext = XML.SubElement(exts_node, ext_name)
        sparse_co = XML.SubElement(ext, 'sparseCheckoutPaths')
        sparse_paths = data['sparse-checkout'].get('paths')
        if sparse_paths is not None:
            path_tagname = impl_prefix + 'SparseCheckoutPath'
            for path in sparse_paths:
                path_tag = XML.SubElement(sparse_co, path_tagname)
                XML.SubElement(path_tag, 'path').text = path
    if 'submodule' in data:
        ext_name = impl_prefix + 'SubmoduleOption'
        ext = XML.SubElement(exts_node, ext_name)
        XML.SubElement(ext, 'disableSubmodules').text = str(
            data['submodule'].get('disable', False)).lower()
        XML.SubElement(ext, 'recursiveSubmodules').text = str(
            data['submodule'].get('recursive', False)).lower()
        XML.SubElement(ext, 'trackingSubmodules').text = str(
            data['submodule'].get('tracking', False)).lower()
        XML.SubElement(ext, 'reference').text = str(
            data['submodule'].get('reference-repo', ''))
        XML.SubElement(ext, 'timeout').text = str(
            data['submodule'].get('timeout', 10))
    if 'timeout' in data:
        co = XML.SubElement(exts_node, impl_prefix + 'CheckoutOption')
        XML.SubElement(co, 'timeout').text = str(data['timeout'])
        clo = XML.SubElement(exts_node, impl_prefix + 'CloneOption')
        XML.SubElement(clo, 'timeout').text = str(data['timeout'])
    polling_using_workspace = str(data.get('force-polling-using-workspace',
                                           False)).lower()
    if polling_using_workspace == 'true':
        ext_name = impl_prefix + 'DisableRemotePoll'
        ext = XML.SubElement(exts_node, ext_name)
    # By default we wipe the workspace
    wipe_workspace = str(data.get('wipe-workspace', True)).lower()
    if wipe_workspace == 'true':
        ext_name = impl_prefix + 'WipeWorkspace'
        ext = XML.SubElement(exts_node, ext_name)

    browser = data.get('browser', 'auto')
    browserdict = {'auto': 'auto',
                   'assemblaweb': 'AssemblaWeb',
                   'bitbucketweb': 'BitbucketWeb',
                   'cgit': 'CGit',
                   'fisheye': 'FisheyeGitRepositoryBrowser',
                   'gitblit': 'GitBlitRepositoryBrowser',
                   'githubweb': 'GithubWeb',
                   'gitiles': 'Gitiles',
                   'gitlab': 'GitLab',
                   'gitlist': 'GitList',
                   'gitoriousweb': 'GitoriousWeb',
                   'gitweb': 'GitWeb',
                   'kiln': 'KilnGit',
                   'microsoft-tfs-2013': 'TFS2013GitRepositoryBrowser',
                   'phabricator': 'Phabricator',
                   'redmineweb': 'RedmineWeb',
                   'rhodecode': 'RhodeCode',
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
        if browser == 'phabricator':
            XML.SubElement(bc, 'repo').text = str(
                data.get('repo-name', ''))


def cvs(parser, xml_parent, data):
    """yaml: cvs
    Specifies the CVS SCM repository for this job.
    Requires the Jenkins :jenkins-wiki:`CVS Plugin <CVS+Plugin>`.

    :arg list repos: List of CVS repositories. (required)

        :Repos:
            * **root** (`str`) -- The CVS connection string Jenkins uses to
              connect to the server. The format is :protocol:user@host:path
              (required)
            * **locations** (`list`) -- List of locations. (required)

                :Locations:
                    * **type** (`str`) -- Type of location.

                        :supported values:
                            * **HEAD** - (default)
                            * **BRANCH**
                            * **TAG**
                    * **name** (`str`) -- Name of location. Only valid in case
                      of 'BRANCH' or 'TAG' location type. (default '')
                    * **use-head** (`bool`) -- Use Head if not found. Only
                      valid in case of 'BRANCH' or 'TAG' location type.
                      (default false)
                    * **modules** (`list`) -- List of modules. (required)

                        :Modules:
                            * **remote** -- The name of the module in the
                              repository at CVSROOT. (required)
                            * **local-name** --  The name to be applied to
                              this module in the local workspace. If blank,
                              the remote module name will be used.
                              (default '')
            * **excluded-regions** (`list str`) -- Patterns for excluding
              regions. (optional)
            * **compression-level** (`int`) -- Compression level. Must be a
              number between -1 and 9 inclusive. Choose -1 for System Default.
              (default -1)
    :arg bool use-update: If true, Jenkins will use 'cvs update' whenever
      possible for builds. This makes a build faster. But this also causes the
      artifacts from the previous build to remain in the file system when a
      new build starts, making it not a true clean build. (default true)
    :arg bool prune-empty: Remove empty directories after checkout using the
      CVS '-P' option. (default true)
    :arg bool skip-changelog: Prevent the changelog being generated after
      checkout has completed. (default false)
    :arg bool show-all-output: Instructs CVS to show all logging output. CVS
      normally runs in quiet mode but this option disables that.
      (default false)
    :arg bool clean-checkout: Perform clean checkout on failed update.
      (default false)
    :arg bool clean-copy: Force clean copy for locally modified files.
      (default false)

    Example

    .. literalinclude:: /../../tests/scm/fixtures/cvs001.yaml
       :language: yaml
    .. literalinclude:: /../../tests/scm/fixtures/cvs002.yaml
       :language: yaml
    """
    prefix = 'hudson.scm.'
    valid_loc_types = {'HEAD': 'Head', 'TAG': 'Tag', 'BRANCH': 'Branch'}
    cvs = XML.SubElement(xml_parent, 'scm', {'class': prefix + 'CVSSCM'})
    repos = data.get('repos')
    if not repos:
        raise JenkinsJobsException("'repos' empty or missing")
    repos_tag = XML.SubElement(cvs, 'repositories')
    for repo in repos:
        repo_tag = XML.SubElement(repos_tag, prefix + 'CvsRepository')
        try:
            XML.SubElement(repo_tag, 'cvsRoot').text = repo['root']
        except KeyError:
            raise MissingAttributeError('root')
        items_tag = XML.SubElement(repo_tag, 'repositoryItems')
        locations = repo.get('locations')
        if not locations:
            raise JenkinsJobsException("'locations' empty or missing")
        for location in locations:
            item_tag = XML.SubElement(items_tag, prefix + 'CvsRepositoryItem')
            loc_type = location.get('type', 'HEAD')
            if loc_type not in valid_loc_types:
                raise InvalidAttributeError('type', loc_type, valid_loc_types)
            loc_class = ('{0}CvsRepositoryLocation${1}Repository'
                         'Location').format(prefix, valid_loc_types[loc_type])
            loc_tag = XML.SubElement(item_tag, 'location',
                                     {'class': loc_class})
            XML.SubElement(loc_tag, 'locationType').text = loc_type
            if loc_type == 'TAG' or loc_type == 'BRANCH':
                XML.SubElement(loc_tag, 'locationName').text = location.get(
                    'name', '')
                XML.SubElement(loc_tag, 'useHeadIfNotFound').text = str(
                    location.get('use-head', False)).lower()
            modules = location.get('modules')
            if not modules:
                raise JenkinsJobsException("'modules' empty or missing")
            modules_tag = XML.SubElement(item_tag, 'modules')
            for module in modules:
                module_tag = XML.SubElement(modules_tag, prefix + 'CvsModule')
                try:
                    XML.SubElement(module_tag, 'remoteName'
                                   ).text = module['remote']
                except KeyError:
                    raise MissingAttributeError('remote')
                XML.SubElement(module_tag, 'localName').text = module.get(
                    'local-name', '')
        excluded = repo.get('excluded-regions', [])
        excluded_tag = XML.SubElement(repo_tag, 'excludedRegions')
        for pattern in excluded:
            pattern_tag = XML.SubElement(excluded_tag,
                                         prefix + 'ExcludedRegion')
            XML.SubElement(pattern_tag, 'pattern').text = pattern
        compression_level = repo.get('compression-level', '-1')
        if int(compression_level) not in range(-1, 10):
            raise InvalidAttributeError('compression-level',
                                        compression_level, range(-1, 10))
        XML.SubElement(repo_tag, 'compressionLevel').text = compression_level
    mapping = [('use-update', 'canUseUpdate', True),
               ('prune-empty', 'pruneEmptyDirectories', True),
               ('skip-changelog', 'skipChangeLog', False),
               ('show-all-output', 'disableCvsQuiet', False),
               ('clean-checkout', 'cleanOnFailedUpdate', False),
               ('clean-copy', 'forceCleanCopy', False)]
    for elem in mapping:
        opt, xml_tag, val = elem[:]
        XML.SubElement(cvs, xml_tag).text = str(
            data.get(opt, val)).lower()


def repo(parser, xml_parent, data):
    """yaml: repo
    Specifies the repo SCM repository for this job.
    Requires the Jenkins :jenkins-wiki:`Repo Plugin <Repo+Plugin>`.

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
    :arg int depth: Specify the depth in history to sync from the source. The
        default is to sync all of the history. Use 1 to just sync the most
        recent commit (default 0)
    :arg bool current-branch: Fetch only the current branch from the server
        (default true)
    :arg bool reset-first: Remove any commits that are not on the repositories
        by running the following command before anything else (default false):
        ``repo forall -c "git reset --hard"``
    :arg bool quiet: Make repo more quiet
        (default true)
    :arg bool force-sync: Continue sync even if a project fails to sync
        (default false)
    :arg bool no-tags: Don't fetch tags (default false)
    :arg bool trace: Trace git command execution into the build logs. (default
        false)
    :arg bool show-all-changes: When this is checked --first-parent is no
        longer passed to git log when determining changesets (default false)
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
        ("depth", 'depth', 0),
        ("current-branch", 'currentBranch', True),
        ("reset-first", 'resetFirst', False),
        ("quiet", 'quiet', True),
        ("force-sync", 'forceSync', False),
        ("no-tags", 'noTags', False),
        ("trace", 'trace', False),
        ("show-all-changes", 'showAllChanges', False),
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


def store(parser, xml_parent, data):
    """yaml: store
    Specifies the Visualworks Smalltalk Store repository for this job.
    Requires the Jenkins :jenkins-wiki:`Visualworks Smalltalk Store Plugin
    <Visualworks+Smalltalk+Store+Plugin>`.

    :arg str script: name of the Store script to run
    :arg str repository: name of the Store repository
    :arg str version-regex: regular expression that specifies which pundle
        versions should be considered (optional)
    :arg str minimum-blessing: minimum blessing level to consider (optional)
    :arg str parcel-builder-file: name of the file to generate as input to
        a later parcel building step (optional - if not specified, then no
        parcel builder file will be generated)
    :arg list pundles:

        :(package or bundle): (`dict`): A package or bundle to check

    Example:

    .. literalinclude:: /../../tests/scm/fixtures/store001.yaml
    """
    namespace = 'org.jenkinsci.plugins.visualworks_store'
    scm = XML.SubElement(xml_parent, 'scm',
                         {'class': '{0}.StoreSCM'.format(namespace)})
    if 'script' in data:
        XML.SubElement(scm, 'scriptName').text = data['script']
    else:
        raise JenkinsJobsException("Must specify a script name")
    if 'repository' in data:
        XML.SubElement(scm, 'repositoryName').text = data['repository']
    else:
        raise JenkinsJobsException("Must specify a repository name")
    pundle_specs = data.get('pundles', [])
    if not pundle_specs:
        raise JenkinsJobsException("At least one pundle must be specified")
    valid_pundle_types = ['package', 'bundle']
    pundles = XML.SubElement(scm, 'pundles')
    for pundle_spec in pundle_specs:
        pundle = XML.SubElement(pundles, '{0}.PundleSpec'.format(namespace))
        pundle_type = next(iter(pundle_spec))
        pundle_name = pundle_spec[pundle_type]
        if pundle_type not in valid_pundle_types:
            raise JenkinsJobsException(
                'pundle type must be must be one of: '
                + ', '.join(valid_pundle_types))
        else:
            XML.SubElement(pundle, 'name').text = pundle_name
            XML.SubElement(pundle, 'pundleType').text = pundle_type.upper()
    if 'version-regex' in data:
        XML.SubElement(scm, 'versionRegex').text = data['version-regex']
    if 'minimum-blessing' in data:
        XML.SubElement(scm, 'minimumBlessingLevel').text = \
            data['minimum-blessing']
    if 'parcel-builder-file' in data:
        XML.SubElement(scm, 'generateParcelBuilderInputFile').text = 'true'
        XML.SubElement(scm, 'parcelBuilderInputFilename').text = \
            data['parcel-builder-file']
    else:
        XML.SubElement(scm, 'generateParcelBuilderInputFile').text = 'false'


def svn(parser, xml_parent, data):
    """yaml: svn
    Specifies the svn SCM repository for this job.

    :arg str url: URL of the svn repository
    :arg str basedir: location relative to the workspace root to checkout to
        (default '.')
    :arg str credentials-id: optional argument to specify the ID of credentials
        to use
    :arg str repo-depth: Repository depth. Can be one of 'infinity', 'empty',
        'files', 'immediates' or 'unknown'. (default 'infinity')
    :arg bool ignore-externals: Ignore Externals. (default false)
    :arg str workspaceupdater: optional argument to specify
    :arg str workspaceupdater: optional argument to specify how to update the
        workspace (default wipeworkspace)

        :supported values:
             * **wipeworkspace** - deletes the workspace before checking out
             * **revertupdate** - do an svn revert then an svn update
             * **emulateclean** - delete unversioned/ignored files then update
             * **update** - do an svn update as much as possible

    :arg list(str) excluded-users: list of users to ignore revisions from
        when polling for changes (if polling is enabled; parameter is optional)
    :arg list(str) included-regions: list of file/folders to include
        (optional)
    :arg list(str) excluded-regions: list of file/folders to exclude (optional)
    :arg list(str) excluded-commit-messages: list of commit messages to exclude
        (optional)
    :arg str exclusion-revprop-name: revision svn-property to ignore (optional)
    :arg bool ignore-property-changes-on-directories: ignore svn-property only
        changes of directories (default false)
    :arg bool filter-changelog: If set Jenkins will apply the same inclusion
        and exclusion patterns for displaying changelog entries as it does for
        polling for changes (default false)
    :arg list repos: list of repositories to checkout (optional)
    :arg str viewvc-url: URL of the svn web interface (optional)

        :Repo:
            * **url** (`str`) -- URL for the repository
            * **basedir** (`str`) -- Location relative to the workspace root
              to checkout to (default '.')
            * **credentials-id** - optional ID of credentials to use
            * **repo-depth** - Repository depth. Can be one of 'infinity',
              'empty', 'files', 'immediates' or 'unknown'. (default 'infinity')
            * **ignore-externals** - Ignore Externals. (default false)

    Multiple repos example:

    .. literalinclude:: /../../tests/scm/fixtures/svn-multiple-repos-001.yaml

    Advanced commit filtering example:

    .. literalinclude:: /../../tests/scm/fixtures/svn-regions-001.yaml
    """
    scm = XML.SubElement(xml_parent, 'scm', {'class':
                         'hudson.scm.SubversionSCM'})
    if 'viewvc-url' in data:
        browser = XML.SubElement(
            scm, 'browser', {'class': 'hudson.scm.browsers.ViewSVN'})
        XML.SubElement(browser, 'url').text = data['viewvc-url']
    locations = XML.SubElement(scm, 'locations')

    def populate_repo_xml(parent, data):
        module = XML.SubElement(parent,
                                'hudson.scm.SubversionSCM_-ModuleLocation')
        XML.SubElement(module, 'remote').text = data['url']
        XML.SubElement(module, 'local').text = data.get('basedir', '.')
        if 'credentials-id' in data:
            XML.SubElement(module, 'credentialsId').text = data[
                'credentials-id']
        repo_depths = ['infinity', 'empty', 'files', 'immediates', 'unknown']
        repo_depth = data.get('repo-depth', 'infinity')
        if repo_depth not in repo_depths:
            raise InvalidAttributeError('repo_depth', repo_depth, repo_depths)
        XML.SubElement(module, 'depthOption').text = repo_depth
        XML.SubElement(module, 'ignoreExternalsOption').text = str(
            data.get('ignore-externals', False)).lower()

    if 'repos' in data:
        repos = data['repos']
        for repo in repos:
            populate_repo_xml(locations, repo)
    elif 'url' in data:
        populate_repo_xml(locations, data)
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

    mapping = [
        # option, xml name, default value
        ("excluded-regions", 'excludedRegions', []),
        ("included-regions", 'includedRegions', []),
        ("excluded-users", 'excludedUsers', []),
        ("exclusion-revprop-name", 'excludedRevprop', ''),
        ("excluded-commit-messages", 'excludedCommitMessages', []),
        ("ignore-property-changes-on-directories", 'ignoreDirPropChanges',
            False),
        ("filter-changelog", 'filterChangelog', False),
    ]

    for optname, xmlname, defvalue in mapping:
        if isinstance(defvalue, list):
            val = '\n'.join(data.get(optname, defvalue))
        else:
            val = data.get(optname, defvalue)
        # Skip adding xml entry if default is empty and no value given
        if not val and (defvalue in ['', []]):
            continue

        xe = XML.SubElement(scm, xmlname)
        if isinstance(defvalue, bool):
            xe.text = str(val).lower()
        else:
            xe.text = str(val)


def tfs(parser, xml_parent, data):
    """yaml: tfs
    Specifies the Team Foundation Server repository for this job.
    Requires the Jenkins :jenkins-wiki:`Team Foundation Server Plugin
    <Team+Foundation+Server+Plugin>`.

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
        domain\\\\user or user\@domain (optional).
        **NOTE**: You must enter in at least two slashes for the
        domain\\\\user format in JJB YAML. It will be rendered normally.
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


    Examples:

    .. literalinclude:: /../../tests/scm/fixtures/tfs-001.yaml

    .. literalinclude:: /../../tests/scm/fixtures/tfs-002.yaml

    """

    tfs = XML.SubElement(xml_parent, 'scm',
                         {'class': 'hudson.plugins.tfs.'
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
        web = XML.SubElement(tfs, 'repositoryBrowser',
                             {'class': 'hudson.plugins.tfs.browsers.'
                                       'TeamSystemWebAccessBrowser'})
        XML.SubElement(web, 'url').text = str(store[0].get('web-url', None))
    elif 'web-access' in data and store is None:
        XML.SubElement(tfs, 'repositoryBrowser', {'class': 'hudson.'
                                                  'plugins.tfs.browsers.'
                                                  'TeamSystemWebAccess'
                                                  'Browser'})


def workspace(parser, xml_parent, data):
    """yaml: workspace
    Specifies the cloned workspace for this job to use as a SCM source.
    Requires the Jenkins :jenkins-wiki:`Clone Workspace SCM Plugin
    <Clone+Workspace+SCM+Plugin>`.

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


def hg(self, xml_parent, data):
    """yaml: hg
    Specifies the mercurial SCM repository for this job.
    Requires the Jenkins :jenkins-wiki:`Mercurial Plugin <Mercurial+Plugin>`.

    :arg str url: URL of the hg repository
    :arg str credentials-id: ID of credentials to use to connect (optional)
    :arg str revision-type: revision type to use (default 'branch')
    :arg str revision: the branch or tag name you would like to track
        (default 'default')
    :arg list(str) modules: reduce unnecessary builds by specifying a list of
        "modules" within the repository. A module is a directory name within
        the repository that this project lives in. (default '')
    :arg bool clean: wipe any local modifications or untracked files in the
        repository checkout (default false)
    :arg str subdir: check out the Mercurial repository into this
        subdirectory of the job's workspace (optional)
    :arg bool disable-changelog: do not calculate the Mercurial changelog
        for each build (default false)
    :arg str browser: what repository browser to use

        :browsers supported:
            * **auto** - (default)
            * **bitbucketweb** - https://bitbucket.org/
            * **fisheye** - https://www.atlassian.com/software/fisheye
            * **googlecode** - https://code.google.com/
            * **hgweb** - https://www.selenic.com/hg/help/hgweb
            * **kilnhg** - https://www.fogcreek.com/kiln/
            * **rhodecode** - https://rhodecode.com/ (versions >= 1.2)
            * **rhodecode-pre-1.2.0** - https://rhodecode.com/ (versions < 1.2)

    :arg str browser-url: url for the repository browser
        (required if browser is set)


    Example:

    .. literalinclude:: ../../tests/scm/fixtures/hg02.yaml
    """
    scm = XML.SubElement(xml_parent, 'scm', {'class':
                         'hudson.plugins.mercurial.MercurialSCM'})
    if 'url' in data:
        XML.SubElement(scm, 'source').text = data['url']
    else:
        raise JenkinsJobsException("A top level url must exist")

    if 'credentials-id' in data:
        XML.SubElement(scm, 'credentialsId').text = data['credentials-id']

    revision_type_dict = {
        'branch': 'BRANCH',
        'tag': 'TAG',
    }
    try:
        revision_type = revision_type_dict[data.get('revision-type', 'branch')]
    except KeyError:
        raise JenkinsJobsException('Invalid revision-type %r' %
                                   data.get('revision-type'))
    XML.SubElement(scm, 'revisionType').text = revision_type

    XML.SubElement(scm, 'revision').text = data.get('revision', 'default')

    if 'subdir' in data:
        XML.SubElement(scm, 'subdir').text = data['subdir']

    xc = XML.SubElement(scm, 'clean')
    xc.text = str(data.get('clean', False)).lower()

    modules = data.get('modules', '')
    if isinstance(modules, list):
        modules = " ".join(modules)
    XML.SubElement(scm, 'modules').text = modules

    xd = XML.SubElement(scm, 'disableChangeLog')
    xd.text = str(data.get('disable-changelog', False)).lower()

    browser = data.get('browser', 'auto')
    browserdict = {
        'auto': '',
        'bitbucket': 'BitBucket',
        'fisheye': 'FishEye',
        'googlecode': 'GoogleCode',
        'hgweb': 'HgWeb',
        'kilnhg': 'KilnHG',
        'rhodecode': 'RhodeCode',
        'rhodecode-pre-1.2.0': 'RhodeCodeLegacy'
    }

    if browser not in browserdict:
        raise JenkinsJobsException("Browser entered is not valid must be one "
                                   "of: %s" % ", ".join(browserdict.keys()))
    if browser != 'auto':
        bc = XML.SubElement(scm, 'browser',
                            {'class': 'hudson.plugins.mercurial.browser.' +
                                      browserdict[browser]})
        if 'browser-url' in data:
            XML.SubElement(bc, 'url').text = data['browser-url']
        else:
            raise JenkinsJobsException("A browser-url must be specified along "
                                       "with browser.")


def openshift_img_streams(parser, xml_parent, data):
    """yaml: openshift-img-streams
    Rather than a Build step extension plugin, this is an extension of the
    Jenkins SCM plugin, where this baked-in polling mechanism provided by
    Jenkins is leveraged by exposing some of the common semantics between
    OpenShift ImageStreams (which are abstractions of Docker repositories)
    and SCMs - versions / commit IDs of related artifacts
    (images vs. programmatics files)
    Requires the Jenkins :jenkins-wiki:`OpenShift
    Pipeline Plugin <OpenShift+Pipeline+Plugin>`._

    :arg str image-stream-name: The name of the ImageStream is what shows up
        in the NAME column if you dump all the ImageStream's with the
        `oc get is` command invocation. (default: nodejs-010-centos7)
    :arg str tag: The specific image tag within the ImageStream to monitor.
        (default: latest)
    :arg str api-url: This would be the value you specify if you leverage the
        --server option on the OpenShift `oc` command.
        (default: \https://openshift.default.svc.cluster.local\)
    :arg str namespace: The value here should be whatever was the output
        form `oc project` when you created the BuildConfig you want to run
        a Build on. (default: test)
    :arg str auth-token: The value here is what you supply with the --token
        option when invoking the OpenShift `oc` command. (optional)
    :arg str verbose: This flag is the toggle for
        turning on or off detailed logging in this plug-in. (optional)

    Full Example:

    .. literalinclude::
        ../../tests/scm/fixtures/openshift-img-streams001.yaml
       :language: yaml

    Minimal Example:

    .. literalinclude::
        ../../tests/scm/fixtures/openshift-img-streams002.yaml
       :language: yaml
    """
    scm = XML.SubElement(xml_parent,
                         'scm', {'class':
                                 'com.openshift.jenkins.plugins.pipeline.'
                                 'OpenShiftImageStreams'})
    mapping = [
        # option, xml name, default value
        ("image-stream-name", 'imageStreamName', 'nodejs-010-centos7'),
        ("tag", 'tag', 'latest'),
        ("api-url", 'apiURL', 'https://openshift.default.svc.cluster.local'),
        ("namespace", 'namespace', 'test'),
        ("auth-token", 'authToken', ''),
        ("verbose", 'verbose', ''),
    ]

    convert_mapping_to_xml(scm, data, mapping)


def bzr(parser, xml_parent, data):
    """yaml: bzr
    Specifies the bzr SCM repository for this job.
    Requires the Jenkins :jenkins-wiki:`Bazaar Plugin <Bazaar+Plugin>`.

    :arg str url: URL of the bzr branch
    :arg bool clean-tree: Clean up the workspace (using bzr) before pulling
        the branch (default: false)
    :arg bool lightweight-checkout: Use a lightweight checkout instead of a
        full branch (default: false)
    :arg str browser: The repository browser to use.

        :browsers supported:
            * **auto** - (default)
            * **loggerhead** - as used by Launchpad
            * **opengrok** - https://opengrok.github.io/OpenGrok/

    :arg str browser-url:
        URL for the repository browser (required if browser is set).

    :arg str opengrok-root-module:
        Root module for OpenGrok (required if browser is opengrok).

    Example:

    .. literalinclude:: /../../tests/scm/fixtures/bzr001.yaml
    """
    if 'url' not in data:
        raise JenkinsJobsException('Must specify a url for bzr scm')
    mapping = [
        # option, xml name, default value (text), attributes (hard coded)
        ('url', 'source', ''),
        ('clean-tree', 'cleantree', False),
        ('lightweight-checkout', 'checkout', False),
    ]
    scm_element = XML.SubElement(
        xml_parent, 'scm', {'class': 'hudson.plugins.bazaar.BazaarSCM'})
    convert_mapping_to_xml(scm_element, data, mapping)

    browser_name_to_class = {
        'loggerhead': 'Loggerhead',
        'opengrok': 'OpenGrok',
    }
    browser = data.get('browser', 'auto')
    if browser == 'auto':
        return
    if browser not in browser_name_to_class:
        raise InvalidAttributeError('browser', browser,
                                    browser_name_to_class.keys())
    browser_element = XML.SubElement(
        scm_element,
        'browser',
        {'class': 'hudson.plugins.bazaar.browsers.{0}'.format(
            browser_name_to_class[browser])})
    XML.SubElement(browser_element, 'url').text = data['browser-url']
    if browser == 'opengrok':
        XML.SubElement(browser_element, 'rootModule').text = (
            data['opengrok-root-module'])


def url(parser, xml_parent, data):
    """yaml: url

    Watch for changes in, and download an artifact from a particular url.
    Requires the Jenkins :jenkins-wiki:`URL SCM <URL+SCM>`.

    :arg list url-list: List of URLs to watch. (required)
    :arg bool clear-workspace: If set to true, clear the workspace before
        downloading the artifact(s) specified in url-list. (default false)

    Examples:

    .. literalinclude:: ../../tests/scm/fixtures/url001.yaml
       :language: yaml
    .. literalinclude:: ../../tests/scm/fixtures/url002.yaml
       :language: yaml
    """

    scm = XML.SubElement(xml_parent, 'scm', {'class':
                         'hudson.plugins.URLSCM.URLSCM'})
    urls = XML.SubElement(scm, 'urls')
    try:
        for data_url in data['url-list']:
            url_tuple = XML.SubElement(
                urls, 'hudson.plugins.URLSCM.URLSCM_-URLTuple')
            XML.SubElement(url_tuple, 'urlString').text = data_url
    except KeyError as e:
        raise MissingAttributeError(e.args[0])
    XML.SubElement(scm, 'clearWorkspace').text = str(
        data.get('clear-workspace', False)).lower()


class SCM(jenkins_jobs.modules.base.Base):
    sequence = 30

    component_type = 'scm'
    component_list_type = 'scm'

    def gen_xml(self, parser, xml_parent, data):
        scms_parent = XML.Element('scms')
        for scm in data.get('scm', []):
            self.registry.dispatch('scm', parser, scms_parent, scm)
        scms_count = len(scms_parent)
        if scms_count == 0:
            XML.SubElement(xml_parent, 'scm', {'class': 'hudson.scm.NullSCM'})
        elif scms_count == 1:
            xml_parent.append(scms_parent[0])
        else:
            class_name = 'org.jenkinsci.plugins.multiplescms.MultiSCM'
            xml_attribs = {'class': class_name}
            xml_parent = XML.SubElement(xml_parent, 'scm', xml_attribs)
            xml_parent.append(scms_parent)
