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
import jenkins_jobs.modules.base
import jenkins_jobs.modules.helpers as helpers


def git(registry, xml_parent, data):
    r"""yaml: git
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
    :arg bool skip-tag: Skip tagging (default true)

        .. deprecated:: 2.0.0. Please use per-build-tag extension, which has
           the inverse meaning.

    :arg bool clean: Clean after checkout (default false)

        .. deprecated:: 1.1.1. Please use clean extension format.

    :arg bool fastpoll: Use fast remote polling (default false)
    :arg bool disable-submodules: Disable submodules (default false)

        .. deprecated:: 1.1.1. Please use submodule extension.

    :arg bool recursive-submodules: Recursively update submodules (default
      false)

        .. deprecated:: 1.1.1. Please use submodule extension.

    :arg str git-tool: The name of the Git installation to use (default
        'Default')
    :arg str reference-repo: Path of the reference repo to use during clone
        (optional)
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
    :arg str git-config-name: Configure name for Git clone (optional)
    :arg str git-config-email: Configure email for Git clone (optional)

    :extensions:

        * **basedir** (`string`) - Location relative to the workspace root to
            clone to (default workspace)
        * **changelog-against** (`dict`)
            * **remote** (`string`) - name of repo that contains branch to
              create changelog against (default 'origin')
            * **branch** (`string`) - name of the branch to create changelog
              against (default 'master')
        * **choosing-strategy**: (`string`) - Jenkins class for selecting what
            to build. Can be one of `default`,`inverse`, or `gerrit`
            (default 'default')
        * **clean** (`dict`)
            * **after** (`bool`) - Clean the workspace after checkout
            * **before** (`bool`) - Clean the workspace before checkout
        * **excluded-users**: (`list(string)`) - list of users to ignore
            revisions from when polling for changes.
            (if polling is enabled, optional)
        * **included-regions**: (`list(string)`) - list of file/folders to
            include (optional)
        * **excluded-regions**: (`list(string)`) - list of file/folders to
            exclude (optional)
        * **ignore-commits-with-messages** (`list(str)`) - Revisions committed
            with messages matching these patterns will be ignored. (optional)
        * **ignore-notify**: (`bool`) - Ignore notifyCommit URL accesses
            (default false)
        * **force-polling-using-workspace** (`bool`) - Force polling using
            workspace (default false)
        * **local-branch** (`string`) - Checkout/merge to local branch
            (optional)
        * **merge** (`dict`)
            * **remote** (`string`) - name of repo that contains branch to
              merge to (default 'origin')
            * **branch** (`string`) - name of the branch to merge to
            * **strategy** (`string`) - merge strategy. Can be one of
              'default', 'resolve', 'recursive', 'octopus', 'ours',
              'subtree'. (default 'default')
            * **fast-forward-mode** (`string`) - merge fast-forward mode.
              Can be one of 'FF', 'FF_ONLY' or 'NO_FF'. (default 'FF')
        * **per-build-tag** (`bool`) - Create a tag in the workspace for every
            build. (default is inverse of skip-tag if set, otherwise false)
        * **prune** (`bool`) - Prune remote branches (default false)
        * **scm-name** (`string`) - The unique scm name for this Git SCM
            (optional)
        * **shallow-clone** (`bool`) - Perform shallow clone (default false)
        * **depth** (`int`) - Set shallow clone depth (default 1)
        * **do-not-fetch-tags** (`bool`) - Perform a clone without tags
            (default false)
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
            * **parent-credentials** (`bool`) - Use credentials from default
              remote of parent repository (default false).
            * **reference-repo** (`str`) - Path of the reference repo to use
              during clone (optional)
            * **timeout** (`int`) - Specify a timeout (in minutes) for
              submodules operations (default 10).
        * **timeout** (`str`) - Timeout for git commands in minutes (optional)
        * **use-author** (`bool`): Use author rather than committer in Jenkin's
            build changeset (default false)
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
        # XXX is this the same as force-polling-using-workspace?
        ("fastpoll", 'remotePoll', False),
        # XXX does this option still exist?
        ("git-tool", 'gitTool', "Default"),
        (None, 'submoduleCfg', '', {'class': 'list'}),
        ('reference-repo', 'reference', ''),
        ("git-config-name", 'gitConfigName', ''),
        ("git-config-email", 'gitConfigEmail', ''),
    ]

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
            raise JenkinsJobsException(
                'Must specify a url for git remote \"' + remoteName + '"')
        XML.SubElement(huser, 'url').text = remoteURL
        if 'credentials-id' in remoteParams:
            credentialsId = remoteParams['credentials-id']
            XML.SubElement(huser, 'credentialsId').text = credentialsId
    xml_branches = XML.SubElement(scm, 'branches')
    branches = data.get('branches', ['**'])
    for branch in branches:
        bspec = XML.SubElement(xml_branches, 'hudson.plugins.git.BranchSpec')
        XML.SubElement(bspec, 'name').text = branch
    for elem in mapping:
        (optname, xmlname, val) = elem[:3]

        # Throw warning for deprecated settings and skip if the 'submodule' key
        # is available.
        submodule_cfgs = ['disable-submodules', 'recursive-submodules']
        if optname in submodule_cfgs:
            if optname in data:
                logger.warning(
                    "'{0}' is deprecated, please convert to use the "
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

    exts = XML.SubElement(scm, 'extensions')

    # handle all supported git extensions
    git_extensions(exts, data)

    browser = data.get('browser', 'auto')
    browserdict = {
        'auto': 'auto',
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
        'viewgit': 'ViewGitWeb',
    }
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


def git_extensions(xml_parent, data):
    logger = logging.getLogger("%s:git_extensions" % __name__)

    trait = xml_parent.tag == "traits"

    # list of availavble traits here: https://bit.ly/2CNEtqS
    trait_prefix = 'jenkins.plugins.git.traits.'
    impl_prefix = 'hudson.plugins.git.extensions.impl.'

    choosing_strategies = {
        'default': 'hudson.plugins.git.util.DefaultBuildChooser',
        'gerrit': ('com.sonyericsson.hudson.plugins.'
                   'gerrit.trigger.hudsontrigger.GerritTriggerBuildChooser'),
        'inverse': 'hudson.plugins.git.util.InverseBuildChooser',
    }

    if not trait and 'basedir' in data:
        ext = XML.SubElement(xml_parent,
                             impl_prefix + 'RelativeTargetDirectory')
        XML.SubElement(ext, 'relativeTargetDir').text = data['basedir']
    if not trait and 'changelog-against' in data:
        ext_name = impl_prefix + 'ChangelogToBranch'
        ext = XML.SubElement(xml_parent, ext_name)
        opts = XML.SubElement(ext, 'options')
        change_remote = data['changelog-against'].get('remote', 'origin')
        change_branch = data['changelog-against'].get('branch', 'master')
        XML.SubElement(opts, 'compareRemote').text = change_remote
        XML.SubElement(opts, 'compareTarget').text = change_branch
    if not trait and 'choosing-strategy' in data:
        try:
            choosing_strategy = choosing_strategies[
                data.get('choosing-strategy')]
        except KeyError:
            raise ValueError('Invalid choosing-strategy %r' %
                             data.get('choosing-strategy'))
        ext = XML.SubElement(xml_parent, impl_prefix + 'BuildChooserSetting')
        XML.SubElement(ext, 'buildChooser', {'class': choosing_strategy})
    if 'clean' in data:
        # Keep support for old format 'clean' configuration by checking
        # if 'clean' is boolean. Else we're using the new extensions style.
        if isinstance(data['clean'], bool):
            clean_after = data['clean']
            clean_before = False
            logger.warning(
                "'clean: bool' configuration format is deprecated, "
                "please use the extension style format to configure "
                "this option.")
        else:
            clean_after = data['clean'].get('after', False)
            clean_before = data['clean'].get('before', False)
        if clean_after:
            ext_name = impl_prefix + 'CleanCheckout'
            if trait:
                trait_name = 'CleanAfterCheckoutTrait'
                tr = XML.SubElement(xml_parent, trait_prefix + trait_name)
                ext = XML.SubElement(tr, "extension", {"class": ext_name})
            else:
                ext = XML.SubElement(xml_parent, ext_name)
        if clean_before:
            ext_name = impl_prefix + 'CleanBeforeCheckout'
            if trait:
                trait_name = 'CleanBeforeCheckoutTrait'
                tr = XML.SubElement(xml_parent, trait_prefix + trait_name)
                ext = XML.SubElement(tr, "extension", {"class": ext_name})
            else:
                ext = XML.SubElement(xml_parent, ext_name)
    if not trait and 'excluded-users' in data:
        excluded_users = '\n'.join(data['excluded-users'])
        ext = XML.SubElement(xml_parent, impl_prefix + 'UserExclusion')
        XML.SubElement(ext, 'excludedUsers').text = excluded_users
    if not trait and 'included-regions' in data or 'excluded-regions' in data:
        ext = XML.SubElement(xml_parent,
                             'hudson.plugins.git.extensions.impl.'
                             'PathRestriction')
        if 'included-regions' in data:
            include_string = '\n'.join(data['included-regions'])
            XML.SubElement(ext, 'includedRegions').text = include_string
        if 'excluded-regions' in data:
            exclude_string = '\n'.join(data['excluded-regions'])
            XML.SubElement(ext, 'excludedRegions').text = exclude_string
    if not trait and 'ignore-commits-with-messages' in data:
        for msg in data['ignore-commits-with-messages']:
            ext_name = impl_prefix + 'MessageExclusion'
            ext = XML.SubElement(xml_parent, ext_name)
            XML.SubElement(ext, 'excludedMessage').text = msg
    if not trait and 'local-branch' in data:
        ext = XML.SubElement(xml_parent, impl_prefix + 'LocalBranch')
        XML.SubElement(ext, 'localBranch').text = str(data['local-branch'])
    if not trait and 'merge' in data:
        merge = data['merge']
        merge_strategies = ['default', 'resolve', 'recursive', 'octopus',
                            'ours', 'subtree']
        fast_forward_modes = ['FF', 'FF_ONLY', 'NO_FF']
        name = merge.get('remote', 'origin')
        branch = merge['branch']
        ext = XML.SubElement(xml_parent, impl_prefix + 'PreBuildMerge')
        merge_opts = XML.SubElement(ext, 'options')
        XML.SubElement(merge_opts, 'mergeRemote').text = name
        XML.SubElement(merge_opts, 'mergeTarget').text = branch
        strategy = merge.get('strategy', 'default')
        if strategy not in merge_strategies:
            raise InvalidAttributeError('strategy', strategy, merge_strategies)
        XML.SubElement(merge_opts, 'mergeStrategy').text = strategy
        fast_forward_mode = merge.get('fast-forward-mode', 'FF')
        if fast_forward_mode not in fast_forward_modes:
            raise InvalidAttributeError('fast-forward-mode', fast_forward_mode,
                                        fast_forward_modes)
        XML.SubElement(merge_opts, 'fastForwardMode').text = fast_forward_mode
    if not trait and 'scm-name' in data:
        ext = XML.SubElement(xml_parent, impl_prefix + 'ScmName')
        XML.SubElement(ext, 'name').text = str(data['scm-name'])

    clone_options = (
        "shallow-clone",
        "timeout",
        "do-not-fetch-tags"
    )
    if any(key in data for key in clone_options):
        ext_name = impl_prefix + 'CloneOption'

        if trait:
            tr = XML.SubElement(xml_parent, trait_prefix + 'CloneOptionTrait')
            ext = XML.SubElement(tr, "extension", {"class": ext_name})
        else:
            ext = XML.SubElement(xml_parent, ext_name)

        clone_mapping = [
            ('shallow-clone', 'shallow', False),
            ('depth', 'depth', 1),
        ]
        helpers.convert_mapping_to_xml(
            ext, data, clone_mapping, fail_required=True)
        if 'do-not-fetch-tags' in data:
            XML.SubElement(ext, 'noTags').text = str(
                data.get('do-not-fetch-tags', False)).lower()
        if 'timeout' in data:
            XML.SubElement(ext, 'timeout').text = str(data['timeout'])
    if not trait and 'sparse-checkout' in data:
        ext_name = impl_prefix + 'SparseCheckoutPaths'
        ext = XML.SubElement(xml_parent, ext_name)
        sparse_co = XML.SubElement(ext, 'sparseCheckoutPaths')
        sparse_paths = data['sparse-checkout'].get('paths')
        if sparse_paths is not None:
            path_tagname = impl_prefix + 'SparseCheckoutPath'
            for path in sparse_paths:
                path_tag = XML.SubElement(sparse_co, path_tagname)
                XML.SubElement(path_tag, 'path').text = path
    if 'submodule' in data:
        ext_name = impl_prefix + 'SubmoduleOption'
        if trait:
            trait_name = 'SubmoduleOptionTrait'
            tr = XML.SubElement(xml_parent, trait_prefix + trait_name)
            ext = XML.SubElement(tr, "extension", {"class": ext_name})
        else:
            ext = XML.SubElement(xml_parent, ext_name)

        XML.SubElement(ext, 'disableSubmodules').text = str(
            data['submodule'].get('disable', False)).lower()
        XML.SubElement(ext, 'recursiveSubmodules').text = str(
            data['submodule'].get('recursive', False)).lower()
        XML.SubElement(ext, 'trackingSubmodules').text = str(
            data['submodule'].get('tracking', False)).lower()
        XML.SubElement(ext, 'parentCredentials').text = str(
            data['submodule'].get('parent-credentials', False)).lower()
        XML.SubElement(ext, 'reference').text = str(
            data['submodule'].get('reference-repo', ''))
        XML.SubElement(ext, 'timeout').text = str(
            data['submodule'].get('timeout', 10))
    if 'timeout' in data:
        ext_name = impl_prefix + 'CheckoutOption'
        if trait:
            trait_name = 'CheckoutOptionTrait'
            tr = XML.SubElement(xml_parent, trait_prefix + trait_name)
            ext = XML.SubElement(tr, "extension", {"class": ext_name})
        else:
            ext = XML.SubElement(xml_parent, ext_name)
        XML.SubElement(ext, 'timeout').text = str(data['timeout'])

    polling_using_workspace = str(data.get('force-polling-using-workspace',
                                           False)).lower()
    if not trait and polling_using_workspace == 'true':
        ext_name = impl_prefix + 'DisableRemotePoll'
        ext = XML.SubElement(xml_parent, ext_name)
    if not trait and 'per-build-tag' in data or 'skip-tag' in data:
        # We want to support both skip-tag (the old option) and per-build-tag
        # (the new option), with the new one overriding the old one.
        # Unfortunately they have inverse meanings, so we have to be careful.
        # The default value of per-build-tag is False if skip-tag is not set,
        # so we set the default value of skip-tag to True.
        per_build_tag_default = False
        if str(data.get('skip-tag', True)).lower() == 'false':
            per_build_tag_default = True
        if str(data.get('per-build-tag',
                        per_build_tag_default)).lower() == 'true':
            XML.SubElement(xml_parent, impl_prefix + 'PerBuildTag')
    prune = str(data.get('prune', False)).lower()
    if prune == 'true':
        ext_name = impl_prefix + 'PruneStaleBranch'
        if trait:
            trait_name = 'PruneStaleBranchTrait'
            tr = XML.SubElement(xml_parent, trait_prefix + trait_name)
            ext = XML.SubElement(tr, "extension", {"class": ext_name})
        else:
            ext = XML.SubElement(xml_parent, ext_name)
    ignore_notify_commits = str(data.get('ignore-notify', False)).lower()
    if not trait and ignore_notify_commits == 'true':
        XML.SubElement(xml_parent, impl_prefix + 'IgnoreNotifyCommit')
    # By default we wipe the workspace
    wipe_workspace = str(data.get('wipe-workspace', True)).lower()
    if wipe_workspace == 'true':
        ext_name = impl_prefix + 'WipeWorkspace'
        if trait:
            trait_name = 'WipeWorkspaceTrait'
            tr = XML.SubElement(xml_parent, trait_prefix + trait_name)
            ext = XML.SubElement(tr, "extension", {"class": ext_name})
        else:
            ext = XML.SubElement(xml_parent, ext_name)

    use_author = str(data.get('use-author', False)).lower()
    if use_author == 'true':
        ext_name = impl_prefix + 'AuthorInChangelog'
        if trait:
            trait_name = 'AuthorInChangelogTrait'
            tr = XML.SubElement(xml_parent, trait_prefix + trait_name)
            ext = XML.SubElement(tr, "extension", {"class": ext_name})
        else:
            ext = XML.SubElement(xml_parent, ext_name)


def cvs(registry, xml_parent, data):
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
    valid_loc_types = {
        'HEAD': 'Head',
        'TAG': 'Tag',
        'BRANCH': 'Branch'
    }

    cvs = XML.SubElement(xml_parent, 'scm', {'class': prefix + 'CVSSCM'})
    repos = data.get('repos')
    repos_tag = XML.SubElement(cvs, 'repositories')
    for repo in repos:
        repo_tag = XML.SubElement(repos_tag, prefix + 'CvsRepository')
        compression_level = repo.get('compression-level', '-1')
        repo_mapping = [
            ('root', 'cvsRoot', None),
            ('', 'compressionLevel', int(compression_level), range(-1, 10)),
        ]
        helpers.convert_mapping_to_xml(repo_tag,
            repo, repo_mapping, fail_required=True)

        items_tag = XML.SubElement(repo_tag, 'repositoryItems')
        locations = repo.get('locations')
        for location in locations:
            item_tag = XML.SubElement(items_tag, prefix + 'CvsRepositoryItem')
            loc_type = location.get('type', 'HEAD')
            if loc_type not in valid_loc_types:
                raise InvalidAttributeError('type', loc_type, valid_loc_types)
            loc_class = ('{0}CvsRepositoryLocation${1}Repository'
                         'Location').format(prefix, valid_loc_types[loc_type])
            loc_tag = XML.SubElement(item_tag, 'location',
                                     {'class': loc_class})
            mapping = [
                ('type', 'locationType', 'HEAD'),
            ]
            helpers.convert_mapping_to_xml(
                loc_tag, location, mapping, fail_required=True)

            if loc_type != 'HEAD':
                mapping = [
                    ('name', 'locationName', ''),
                    ('use-head', 'useHeadIfNotFound', False),
                ]
                helpers.convert_mapping_to_xml(
                    loc_tag, location, mapping, fail_required=True)

            modules = location.get('modules')
            modules_tag = XML.SubElement(item_tag, 'modules')
            for module in modules:
                module_tag = XML.SubElement(modules_tag, prefix + 'CvsModule')
                mapping = [
                    ('remote', 'remoteName', None),
                    ('local-name', 'localName', ''),
                ]
                helpers.convert_mapping_to_xml(
                    module_tag, module, mapping, fail_required=True)

        excluded = repo.get('excluded-regions', [])
        excluded_tag = XML.SubElement(repo_tag, 'excludedRegions')
        for pattern in excluded:
            pattern_tag = XML.SubElement(excluded_tag,
                                         prefix + 'ExcludedRegion')
            XML.SubElement(pattern_tag, 'pattern').text = pattern

    mappings = [
        ('use-update', 'canUseUpdate', True),
        ('prune-empty', 'pruneEmptyDirectories', True),
        ('skip-changelog', 'skipChangeLog', False),
        ('show-all-output', 'disableCvsQuiet', False),
        ('clean-checkout', 'cleanOnFailedUpdate', False),
        ('clean-copy', 'forceCleanCopy', False),
    ]
    helpers.convert_mapping_to_xml(cvs, data, mappings, fail_required=True)


def repo(registry, xml_parent, data):
    """yaml: repo
    Specifies the repo SCM repository for this job.
    Requires the Jenkins :jenkins-wiki:`Repo Plugin <Repo+Plugin>`.

    :arg str manifest-url: URL of the repo manifest (required)
    :arg str manifest-branch: The branch of the manifest to use (optional)
    :arg str manifest-file: Initial manifest file to use when initialising
        (optional)
    :arg str manifest-group: Only retrieve those projects in the manifest
        tagged with the provided group name (optional)
    :arg list(str) ignore-projects: a list of projects in which changes would
        not be considered to trigger a build when pooling (optional)
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

    mapping = [
        # option, xml name, default value
        ('manifest-url', 'manifestRepositoryUrl', None),
        ('jobs', 'jobs', 0),
        ('depth', 'depth', 0),
        ('current-branch', 'currentBranch', True),
        ('reset-first', 'resetFirst', False),
        ('quiet', 'quiet', True),
        ('force-sync', 'forceSync', False),
        ('no-tags', 'noTags', False),
        ('trace', 'trace', False),
        ('show-all-changes', 'showAllChanges', False),
    ]
    helpers.convert_mapping_to_xml(scm, data, mapping, fail_required=True)

    optional_mapping = [
        # option, xml name, default value
        ('manifest-branch', 'manifestBranch', None),
        ('manifest-file', 'manifestFile', None),
        ('manifest-group', 'manifestGroup', None),
        ('destination-dir', 'destinationDir', None),
        ('repo-url', 'repoUrl', None),
        ('mirror-dir', 'mirrorDir', None),
        ('local-manifest', 'localManifest', None),
    ]
    helpers.convert_mapping_to_xml(
        scm, data, optional_mapping, fail_required=False)

    # ignore-projects does not follow the same pattern of the other parameters,
    # so process it here:
    ip = XML.SubElement(scm, 'ignoreProjects', {'class': 'linked-hash-set'})
    ignored_projects = data.get('ignore-projects', [''])
    for ignored_project in ignored_projects:
        XML.SubElement(ip, 'string').text = str(ignored_project)


def store(registry, xml_parent, data):
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
    mapping = [
        ('script', 'scriptName', None),
        ('repository', 'repositoryName', None),
    ]
    helpers.convert_mapping_to_xml(scm, data, mapping, fail_required=True)

    pundle_specs = data.get('pundles', [])
    if not pundle_specs:
        raise JenkinsJobsException("At least one pundle must be specified")
    valid_pundle_types = ['PACKAGE', 'BUNDLE']
    pundles = XML.SubElement(scm, 'pundles')

    for pundle_spec in pundle_specs:
        pundle = XML.SubElement(pundles, '{0}.PundleSpec'.format(namespace))
        pundle_type = next(iter(pundle_spec))
        pundle_name = pundle_spec[pundle_type]
        mapping = [
            ('', 'name', pundle_name),
            ('', 'pundleType', pundle_type.upper(), valid_pundle_types),
        ]
        helpers.convert_mapping_to_xml(
            pundle, data, mapping, fail_required=True)

    generate_parcel = 'parcel-builder-file' in data
    mapping_optional = [
        ('version-regex', 'versionRegex', None),
        ('minimum-blessing', 'minimumBlessingLevel', None),
        ('', 'generateParcelBuilderInputFile', generate_parcel),
        ('parcel-builder-file', 'parcelBuilderInputFilename', None),
    ]
    helpers.convert_mapping_to_xml(scm,
        data, mapping_optional, fail_required=False)


def svn(registry, xml_parent, data):
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
    :arg list additional-credentials: list of additional credentials (optional)
        :Additional-Credentials:

            * **realm** (`str`) --  realm to use
            * **credentials-id** (`str`) -- optional ID of credentials to use

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
        mapping = [
            ('viewvc-url', 'url', None),
        ]
        helpers.convert_mapping_to_xml(
            browser, data, mapping, fail_required=True)
    locations = XML.SubElement(scm, 'locations')

    def populate_repo_xml(parent, data):
        module = XML.SubElement(parent,
                                'hudson.scm.SubversionSCM_-ModuleLocation')
        mapping = [
            ('url', 'remote', None),
            ('basedir', 'local', '.'),
        ]
        helpers.convert_mapping_to_xml(
            module, data, mapping, fail_required=True)

        repo_depths = ['infinity', 'empty', 'files', 'immediates', 'unknown']
        mapping_optional = [
            ('credentials-id', 'credentialsId', None),
            ('repo-depth', 'depthOption', 'infinity', repo_depths),
            ('ignore-externals', 'ignoreExternalsOption', False),
        ]
        helpers.convert_mapping_to_xml(module, data,
            mapping_optional, fail_required=False)

    if 'repos' in data:
        repos = data['repos']
        for repo in repos:
            populate_repo_xml(locations, repo)
    elif 'url' in data:
        populate_repo_xml(locations, data)
    else:
        raise JenkinsJobsException("A top level url or repos list must exist")

    def populate_additional_credential_xml(parent, data):
        module = XML.SubElement(parent,
                            'hudson.scm.SubversionSCM_-AdditionalCredentials')
        XML.SubElement(module, 'realm').text = data['realm']
        if 'credentials-id' in data:
            XML.SubElement(module, 'credentialsId').text = data[
                'credentials-id']

    if 'additional-credentials' in data:
        additional_credentials = XML.SubElement(scm, 'additionalCredentials')
        additional_credentials_data = data['additional-credentials']

        for additional_credential in additional_credentials_data:
            populate_additional_credential_xml(additional_credentials,
                                               additional_credential)

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


def tfs(registry, xml_parent, data):
    r"""yaml: tfs
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
    mapping = [
        ('server-url', 'serverUrl', ''),
        ('project-path', 'projectPath', ''),
        ('local-path', 'localPath', '.'),
        ('workspace', 'workspaceName', 'Hudson-${JOB_NAME}-${NODE_NAME}'),
        # TODO: In the future, it would be nice to have a place that can pull
        # passwords into JJB without having to commit them in plaintext. This
        # could also integrate nicely with global configuration options.
        ('', 'userPassword', ''),
        ('login', 'userName', ''),
        ('use-update', 'useUpdate', True),
    ]
    helpers.convert_mapping_to_xml(tfs, data, mapping, fail_required=True)

    store = data.get('web-access', None)
    if isinstance(store, list):
        web = XML.SubElement(tfs, 'repositoryBrowser',
                             {'class': 'hudson.plugins.tfs.browsers.'
                                       'TeamSystemWebAccessBrowser'})
        XML.SubElement(web, 'url').text = str(store[0].get('web-url', None))
    elif 'web-access' in data and store is None:
        XML.SubElement(tfs, 'repositoryBrowser', {'class': 'hudson.'
                                                  'plugins.tfs.browsers.'
                                                  'TeamSystemWebAccess'
                                                  'Browser'})


def workspace(registry, xml_parent, data):
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
        (default Any)


    Example:

    .. literalinclude:: /../../tests/scm/fixtures/workspace001.yaml
    """

    workspace = XML.SubElement(xml_parent, 'scm', {'class': 'hudson.plugins.'
                               'cloneworkspace.CloneWorkspaceSCM'})
    criteria_list = ['Any', 'Not Failed', 'Successful']

    criteria = data.get('criteria', 'Any').title()

    mapping = [
        ('parent-job', 'parentJobName', ''),
        ('', 'criteria', criteria, criteria_list),
    ]
    helpers.convert_mapping_to_xml(
        workspace, data, mapping, fail_required=True)


def hg(self, xml_parent, data):
    """yaml: hg
    Specifies the mercurial SCM repository for this job.
    Requires the Jenkins :jenkins-wiki:`Mercurial Plugin <Mercurial+Plugin>`.

    :arg str url: URL of the hg repository (required)
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

    revision_type_dict = {
        'branch': 'BRANCH',
        'tag': 'TAG',
    }
    browser = data.get('browser', 'auto')
    browserdict = {
        'auto': '',
        'bitbucket': 'BitBucket',  # deprecated
        'bitbucketweb': 'BitBucket',
        'fisheye': 'FishEye',
        'googlecode': 'GoogleCode',
        'hgweb': 'HgWeb',
        'kilnhg': 'KilnHG',
        'rhodecode': 'RhodeCode',
        'rhodecode-pre-1.2.0': 'RhodeCodeLegacy'
    }

    scm = XML.SubElement(xml_parent, 'scm', {'class':
                         'hudson.plugins.mercurial.MercurialSCM'})
    mapping = [
        ('url', 'source', None),
    ]
    helpers.convert_mapping_to_xml(scm, data, mapping, fail_required=True)

    mapping_optional = [
        ('credentials-id', 'credentialsId', None),
        ('revision-type', 'revisionType', 'branch', revision_type_dict),
        ('revision', 'revision', 'default'),
        ('subdir', 'subdir', None),
        ('clean', 'clean', False),
    ]
    helpers.convert_mapping_to_xml(
        scm, data, mapping_optional, fail_required=False)

    modules = data.get('modules', '')
    if isinstance(modules, list):
        modules = " ".join(modules)
    XML.SubElement(scm, 'modules').text = modules
    XML.SubElement(scm, 'disableChangeLog').text = str(data.get(
        'disable-changelog', False)).lower()

    if browser != 'auto':
        bc = XML.SubElement(scm, 'browser',
                            {'class': 'hudson.plugins.mercurial.browser.' +
                                      browserdict[browser]})
        mapping = [
            ('browser-url', 'url', None, browserdict[browser]),
        ]
        helpers.convert_mapping_to_xml(bc, data, mapping, fail_required=True)


def openshift_img_streams(registry, xml_parent, data):
    r"""yaml: openshift-img-streams
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
        `oc get is` command invocation. (default nodejs-010-centos7)
    :arg str tag: The specific image tag within the ImageStream to monitor.
        (default latest)
    :arg str api-url: This would be the value you specify if you leverage the
        --server option on the OpenShift `oc` command.
        (default \https://openshift.default.svc.cluster.local\)
    :arg str namespace: The value here should be whatever was the output
        form `oc project` when you created the BuildConfig you want to run
        a Build on. (default test)
    :arg str auth-token: The value here is what you supply with the --token
        option when invoking the OpenShift `oc` command. (default '')
    :arg bool verbose: This flag is the toggle for
        turning on or off detailed logging in this plug-in. (default false)

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
        ("verbose", 'verbose', False),
    ]
    helpers.convert_mapping_to_xml(scm, data, mapping, fail_required=True)


def bzr(registry, xml_parent, data):
    """yaml: bzr
    Specifies the bzr SCM repository for this job.
    Requires the Jenkins :jenkins-wiki:`Bazaar Plugin <Bazaar+Plugin>`.

    :arg str url: URL of the bzr branch (required)
    :arg bool clean-tree: Clean up the workspace (using bzr) before pulling
        the branch (default false)
    :arg bool lightweight-checkout: Use a lightweight checkout instead of a
        full branch (default false)
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
       :language: yaml
    """
    mapping = [
        # option, xml name, default value (text), attributes (hard coded)
        ('url', 'source', None),
        ('clean-tree', 'cleantree', False),
        ('lightweight-checkout', 'checkout', False),
    ]
    scm_element = XML.SubElement(
        xml_parent, 'scm', {'class': 'hudson.plugins.bazaar.BazaarSCM'})
    helpers.convert_mapping_to_xml(
        scm_element, data, mapping, fail_required=True)

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
    mapping = [
        ('browser-url', 'url', None),
    ]
    helpers.convert_mapping_to_xml(
        browser_element, data, mapping, fail_required=True)

    if browser == 'opengrok':
        mapping = [
            ('opengrok-root-module', 'rootModule', None),
        ]
        helpers.convert_mapping_to_xml(browser_element,
            data, mapping, fail_required=True)


def url(registry, xml_parent, data):
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
    for data_url in data['url-list']:
        url_tuple = XML.SubElement(
            urls, 'hudson.plugins.URLSCM.URLSCM_-URLTuple')
        mapping = [
            ('', 'urlString', data_url),
        ]
        helpers.convert_mapping_to_xml(
            url_tuple, data, mapping, fail_required=True)
    mapping = [
        ('clear-workspace', 'clearWorkspace', False),
    ]
    helpers.convert_mapping_to_xml(scm, data, mapping, fail_required=True)


def dimensions(registry, xml_parent, data):
    """yaml: dimensions

    Specifies the Dimensions SCM repository for this job.
    Requires Jenkins :jenkins-wiki:`Dimensions Plugin <Dimensions+Plugin>`.

    :arg str project: Project name of format PRODUCT_ID:PROJECT_NAME (required)
    :arg str permissions: Default Permissions for updated files
        (default: DEFAULT)

        :Permissions:
            * **DEFAULT**
            * **READONLY**
            * **WRITABLE**
    :arg str eol: End of line (default: DEFAULT)

        :End of line:
            * **DEFAULT**
            * **UNIX**
            * **WINDOWS**
            * **UNCHANGED**
    :arg list folders: Folders to monitor (default /)
    :arg list exclude: Paths to exclude from monitor
    :arg str username: Repository username for this job
    :arg str password: Repository password for this job
    :arg str server: Dimensions server for this job
    :arg str database: Dimensions database for this job.
        Format must be database@dsn
    :arg bool update: Use update (default false)
    :arg bool clear-workspace: Clear workspace prior to build (default false)
    :arg bool force-build: Force build even if the repository SCM checkout
        operation fails (default false)
    :arg bool overwrite-modified: Overwrite files in worspace from
        repository files (default false)
    :arg bool expand-vars: Expand substitution variables (default false)
    :arg bool no-metadata: Checkout files with no metadata (default false)
    :arg bool maintain-timestamp: Maintain file timestamp from Dimensions
        (default false)
    :arg bool slave-checkout: Force slave based checkout (default false)
    :arg str timezone: Server timezone
    :arg str web-url: Dimensions Web URL

    Examples:

    .. literalinclude:: /../../tests/scm/fixtures/dimensions-minimal.yaml
       :language: yaml
    .. literalinclude:: /../../tests/scm/fixtures/dimensions-full.yaml
       :language: yaml

    """

    scm = XML.SubElement(
        xml_parent,
        'scm', {'class': 'hudson.plugins.dimensionsscm.DimensionsSCM'})

    # List to check against for valid permission
    perm = ['DEFAULT', 'READONLY', 'WRITABLE']

    # List to check against for valid end of line
    eol = ['DEFAULT', 'UNIX', 'WINDOWS', 'UNCHANGED']

    mapping = [
        # option, xml name, default value (text), attributes (hard coded)
        ('project', 'project', None),
        ('permissions', 'permissions', 'DEFAULT', perm),
        ('eol', 'eol', 'DEFAULT', eol),
        ('update', 'canJobUpdate', False),
        ('clear-workspace', 'canJobDelete', False),
        ('force-build', 'canJobForce', False),
        ('overwrite-modified', 'canJobRevert', False),
        ('expand-vars', 'canJobExpand', False),
        ('no-metadata', 'canJobNoMetadata', False),
        ('maintain-timestamp', 'canJobNoTouch', False),
        ('slave-checkout', 'forceAsSlave', False),
    ]
    helpers.convert_mapping_to_xml(scm, data, mapping, fail_required=True)

    # Folders to monitor. Default '/'
    folders = XML.SubElement(scm, 'folders')
    if 'folders' in data:
        for folder in data['folders']:
            XML.SubElement(folders, 'string').text = folder
    else:
        XML.SubElement(folders, 'string').text = '/'

    # Excluded paths
    exclude = XML.SubElement(scm, 'pathsToExclude')
    if 'exclude' in data:
        for exc in data['exclude']:
            XML.SubElement(exclude, 'string').text = exc

    optional_mapping = [
        # option, xml name, default value (text), attributes (hard coded)
        ('username', 'jobUserName', None),
        ('password', 'jobPasswd', None),
        ('server', 'jobServer', None),
        ('database', 'jobDatabase', None),
        ('timezone', 'jobTimeZone', None),
        ('web-url', 'jobWebUrl', None),
    ]
    helpers.convert_mapping_to_xml(
        scm, data, optional_mapping, fail_required=False)


def accurev(registry, xml_parent, data):
    """yaml: accurev
    Specifies the AccuRev SCM repository for this job.
    Requires the Jenkins :jenkins-wiki:`AccuRev Plugin <AccuRev+Plugin>`.

    :arg str depot: Depot you want to use for the current job (optional)
    :arg str stream: Stream where the build will be generated from (optional)
    :arg str server-name: AccuRev server you are using
        for your builds (required)
    :arg bool ignore-parent-changes: Ignore possibility
        of changes in the parent stream (default false)
    :arg bool clean-reference-tree: Deletes any external files
        in reference tree (default false)
    :arg bool build-from-snapshot: Creates snapshot
        of the target stream, then populates and
        builds from that snapshot (default false)
    :arg bool do-not-pop-content: If checkbox is on, elements
        are not populating vice versa (default false)
    :arg str workspace: Name of existing workspace (optional)
    :arg str reference-tree: Name of the reference tree (optional)
    :arg str directory-offset: Relative directory path from
        the default Jenkins workspace location
        where the files from the stream, workspace,
        or reference tree should be retrieved from. (optional)
    :arg str sub-path: Makes a "best effort" to ensure
        that only the sub-path is populated (optional)
    :arg str filter-poll-scm: Specify directories or
        files you want Jenkins to check before starting a build (optional)
    :arg str snapshot-name-format: Naming conventions
        for the snapshot in this field (optional)

    Example:

    .. literalinclude:: /../../tests/scm/fixtures/accurev001.yaml
    """
    scm = XML.SubElement(xml_parent,
                         'scm', {'class': 'hudson.plugins.accurev.AccurevSCM'})
    mapping = [
        ('depot', 'depot', None),
        ('stream', 'stream', None),
        ('server-name', 'serverName', None),
        ('ignore-parent-changes', 'ignoreStreamParent', False),
        ('clean-reference-tree', 'cleanreftree', False),
        ('build-from-snapshot', 'useSnapshot', False),
        ('do-not-pop-content', 'dontPopContent', False),
    ]
    helpers.convert_mapping_to_xml(scm, data, mapping, fail_required=True)

    additional_mapping = [
        ('workspace', 'workspace', None),
        ('reference-tree', 'reftree', None),
        ('directory-offset', 'directoryOffset', None),
        ('sub-path', 'subPath', None),
        ('filter-poll-scm', 'filterForPollSCM', None),
        ('snapshot-name-format', 'snapshotNameFormat', None),
    ]
    helpers.convert_mapping_to_xml(
        scm, data, additional_mapping, fail_required=False)


class SCM(jenkins_jobs.modules.base.Base):
    sequence = 30

    component_type = 'scm'
    component_list_type = 'scm'

    def gen_xml(self, xml_parent, data):

        # multibranch-pipeline scm implementation is incompatible with SCM
        if data.get('project-type') in ['multibranch', 'multibranch-defaults']:
            logging.debug("SCM Module skipped for multibranch project-type.")
            return

        scms_parent = XML.Element('scms')
        for scm in data.get('scm', []):
            self.registry.dispatch('scm', scms_parent, scm)
        scms_count = len(scms_parent)
        if scms_count == 0:
            XML.SubElement(xml_parent, 'scm', {'class': 'hudson.scm.NullSCM'})
        elif scms_count == 1:
            xml_parent.append(scms_parent[0])
        else:
            class_name = 'org.jenkinsci.plugins.multiplescms.MultiSCM'
            xml_attribs = {'class': class_name}
            xml_parent = XML.SubElement(xml_parent, 'scm', xml_attribs)

            for scms_child in scms_parent:
                try:
                    scms_child.tag = scms_child.attrib['class']
                    del(scms_child.attrib['class'])
                except KeyError:
                    pass

            xml_parent.append(scms_parent)


class PipelineSCM(jenkins_jobs.modules.base.Base):
    sequence = 30

    component_type = 'pipeline-scm'
    component_list_type = 'pipeline-scm'

    def gen_xml(self, xml_parent, data):
        definition_parent = xml_parent.find('definition')
        pipeline_dict = data.get(self.component_type, {})
        scms = pipeline_dict.get('scm')
        if scms:
            scms_count = len(scms)
            if scms_count == 0:
                raise JenkinsJobsException("'scm' missing or empty")
            elif scms_count == 1:
                self.registry.dispatch('scm', definition_parent, scms[0])
                mapping = [
                    ('script-path', 'scriptPath', 'Jenkinsfile'),
                    ('lightweight-checkout', 'lightweight', None,
                     [True, False]),
                ]
                helpers.convert_mapping_to_xml(
                    definition_parent, pipeline_dict, mapping,
                    fail_required=False)
            else:
                raise JenkinsJobsException('Only one SCM can be specified '
                                           'as pipeline-scm')
