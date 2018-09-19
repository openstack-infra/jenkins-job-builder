# -*- coding: utf-8 -*-
# Copyright (C) 2015 Joost van der Griendt <joostvdg@gmail.com>
# Copyright (C) 2018 Sorin Sbarnea <ssbarnea@users.noreply.github.com>
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
The Multibranch Pipeline project module handles creating Jenkins workflow
projects.
You may specify ``multibranch`` in the ``project-type`` attribute of
the :ref:`Job` definition.

Multibranch Pipeline implementantion in JJB is marked as **experimental**
which means that there is no guarantee that its behavior (or configuration)
will not change, even between minor releases.

Plugins required:
    * :jenkins-wiki:`Workflow Plugin <Workflow+Plugin>`.
    * :jenkins-wiki:`Pipeline Multibranch Defaults Plugin
      <Pipeline+Multibranch+Defaults+Plugin>` (optional)
    * :jenkins-wiki:`Basic Branch Build Strategies Plugin
      <Basic+Branch+Build+Strategies+Plugin>` (optional)

:Job Parameters:

    * **scm** (`list`): The SCM definition.

        * **bitbucket** (`dict`): Refer to
          :func:`~bitbucket_scm <bitbucket_scm>` for documentation.

        * **gerrit** (`dict`): Refer to
          :func:`~gerrit_scm <gerrit_scm>` for documentation.

        * **git** (`dict`): Refer to
          :func:`~git_scm <git_scm>` for documentation.

        * **github** (`dict`): Refer to
          :func:`~github_scm <github_scm>` for documentation.

    * **periodic-folder-trigger** (`str`): How often to scan for new branches
      or pull/change requests. Valid values: 1m, 2m, 5m, 10m, 15m, 20m, 25m,
      30m, 1h, 2h, 4h, 8h, 12h, 1d, 2d, 1w, 2w, 4w. (default none)
    * **prune-dead-branches** (`bool`): If dead branches upon check should
      result in their job being dropped. (default true)
    * **number-to-keep** (`int`): How many builds should be kept.
      (default '-1, all')
    * **days-to-keep** (`int`): For how many days should a build be kept.
      (default '-1, forever')
    * **script-path** (`str`): Path to Jenkinsfile, relative to workspace.
      (default 'Jenkinsfile')

Job examples:

.. literalinclude:: /../../tests/multibranch/fixtures/multibranch_defaults.yaml

.. literalinclude:: /../../tests/multibranch/fixtures/multi_scm_full.yaml

"""
import collections
import logging
import xml.etree.ElementTree as XML
import jenkins_jobs.modules.base
import jenkins_jobs.modules.helpers as helpers
import six

from jenkins_jobs.modules.scm import git_extensions
from jenkins_jobs.errors import InvalidAttributeError

logger = logging.getLogger(str(__name__))


class WorkflowMultiBranch(jenkins_jobs.modules.base.Base):
    sequence = 0
    multibranch_path = 'org.jenkinsci.plugins.workflow.multibranch'
    jenkins_class = ''.join([multibranch_path, '.WorkflowMultiBranchProject'])
    jenkins_factory_class = ''.join(
        [multibranch_path, '.WorkflowBranchProjectFactory'])

    def root_xml(self, data):
        xml_parent = XML.Element(self.jenkins_class)
        xml_parent.attrib['plugin'] = 'workflow-multibranch'
        XML.SubElement(xml_parent, 'properties')

        #########
        # Views #
        #########

        views = XML.SubElement(xml_parent, 'views')
        all_view = XML.SubElement(views, 'hudson.model.AllView')
        all_view_mapping = [
            ('', 'name', 'All'),
            ('', 'filterExecutors', False),
            ('', 'filterQueue', False),
        ]
        helpers.convert_mapping_to_xml(
            all_view, {}, all_view_mapping, fail_required=True)

        XML.SubElement(all_view, 'properties', {
            'class': 'hudson.model.View$PropertyList'
        })

        XML.SubElement(all_view, 'owner', {
            'class': self.jenkins_class,
            'reference': '../../..'
        })

        XML.SubElement(xml_parent, 'viewsTabBar', {
            'class': 'hudson.views.DefaultViewsTabBar'
        })

        ################
        # Folder Views #
        ################

        folderViews = XML.SubElement(xml_parent, 'folderViews', {
            'class': 'jenkins.branch.MultiBranchProjectViewHolder',
            'plugin': 'branch-api',
        })

        XML.SubElement(folderViews, 'owner', {
            'class': self.jenkins_class,
            'reference': '../..'
        })

        ##################
        # Health Metrics #
        ##################

        hm = XML.SubElement(xml_parent, 'healthMetrics')
        hm_path = ('com.cloudbees.hudson.plugins.folder.health'
                   '.WorstChildHealthMetric')
        hm_plugin = XML.SubElement(hm, hm_path, {
            'plugin': 'cloudbees-folder',
        })
        XML.SubElement(hm_plugin, 'nonRecursive').text = 'false'

        ########
        # Icon #
        ########

        icon = XML.SubElement(xml_parent, 'icon', {
            'class': 'jenkins.branch.MetadataActionFolderIcon',
            'plugin': 'branch-api',
        })
        XML.SubElement(icon, 'owner', {
            'class': self.jenkins_class,
            'reference': '../..'
        })

        ########################
        # Orphan Item Strategy #
        ########################

        ois_default_strategy = ('com.cloudbees.hudson.plugins.'
            'folder.computed.DefaultOrphanedItemStrategy')
        ois = XML.SubElement(
            xml_parent, 'orphanedItemStrategy', {
                'class': ois_default_strategy,
                'plugin': 'cloudbees-folder',
            }
        )

        ois_mapping = [
            ('prune-dead-branches', 'pruneDeadBranches', True, [True, False]),
            ('days-to-keep', 'daysToKeep', -1),
            ('number-to-keep', 'numToKeep', -1),
        ]
        helpers.convert_mapping_to_xml(ois, data, ois_mapping)

        ###########################
        # Periodic Folder Trigger #
        ###########################

        triggers = XML.SubElement(xml_parent, 'triggers')

        # Valid options for the periodic trigger interval.
        pft_map = collections.OrderedDict([
            ("1m", ("* * * * *", '60000')),
            ("2m", ("*/2 * * * *", '120000')),
            ("5m", ("*/5 * * * *", '300000')),
            ("10m", ("H/6 * * * *", '600000')),
            ("15m", ("H/6 * * * *", '900000')),
            ("20m", ("H/3 * * * *", '1200000')),
            ("25m", ("H/3 * * * *", '1500000')),
            ("30m", ("H/2 * * * *", '1800000')),
            ("1h", ("H * * * *", '3600000')),
            ("2h", ("H * * * *", '7200000')),
            ("4h", ("H * * * *", '14400000')),
            ("8h", ("H * * * *", '28800000')),
            ("12h", ("H H * * *", '43200000')),
            ("1d", ("H H * * *", '86400000')),
            ("2d", ("H H * * *", '172800000')),
            ("1w", ("H H * * *", '604800000')),
            ("2w", ("H H * * *", '1209600000')),
            ("4w", ("H H * * *", '2419200000')),
        ])

        pft_val = data.get('periodic-folder-trigger')
        if pft_val:
            if not pft_map.get(pft_val):
                raise InvalidAttributeError(
                    'periodic-folder-trigger',
                    pft_val,
                    pft_map.keys())

            pft_path = (
                'com.cloudbees.hudson.plugins.folder.computed.'
                'PeriodicFolderTrigger')
            pft = XML.SubElement(triggers, pft_path, {
                'plugin': 'cloudbees-folder'
            })
            XML.SubElement(pft, 'spec').text = pft_map[pft_val][0]
            XML.SubElement(pft, 'interval').text = pft_map[pft_val][1]

        ###########
        # Sources #
        ###########

        sources = XML.SubElement(xml_parent, 'sources', {
            'class': 'jenkins.branch.MultiBranchProject$BranchSourceList',
            'plugin': 'branch-api',
        })
        sources_data = XML.SubElement(sources, 'data')
        XML.SubElement(sources, 'owner', {
            'class': self.jenkins_class,
            'reference': '../..',
        })

        valid_scm = [
            'bitbucket',
            'gerrit',
            'git',
            'github',
        ]
        for scm_data in data.get('scm', None):
            for scm in scm_data:
                bs = XML.SubElement(
                    sources_data, 'jenkins.branch.BranchSource')

                if scm == 'bitbucket':
                    bitbucket_scm(bs, scm_data[scm])

                elif scm == 'gerrit':
                    gerrit_scm(bs, scm_data[scm])

                elif scm == 'git':
                    git_scm(bs, scm_data[scm])

                elif scm == 'github':
                    github_scm(bs, scm_data[scm])

                else:
                    raise InvalidAttributeError('scm', scm_data, valid_scm)

        ###########
        # Factory #
        ###########

        factory = XML.SubElement(xml_parent, 'factory', {
            'class': self.jenkins_factory_class,
        })
        XML.SubElement(factory, 'owner', {
            'class': self.jenkins_class,
            'reference': '../..'
        })
        XML.SubElement(factory, 'scriptPath').text = data.get(
            'script-path', 'Jenkinsfile')

        return xml_parent


class WorkflowMultiBranchDefaults(WorkflowMultiBranch):
    jenkins_class = (
        'org.jenkinsci.plugins.pipeline.multibranch'
        '.defaults.PipelineMultiBranchDefaultsProject')
    jenkins_factory_class = (
        'org.jenkinsci.plugins.pipeline.multibranch'
        '.defaults.PipelineBranchDefaultsProjectFactory')


def bitbucket_scm(xml_parent, data):
    """Configure BitBucket scm

    Requires the :jenkins-wiki:`Bitbucket Branch Source Plugin
    <Bitbucket+Branch+Source+Plugin>`.

    :arg str credentials-id: The credential to use to scan BitBucket.
        (required)
    :arg str repo-owner: Specify the name of the Bitbucket Team or Bitbucket
        User Account. (required)
    :arg str repo: The BitBucket repo. (required)

    :arg bool discover-tags: Discovers tags on the repository.
        (default false)
    :arg str server-url: The address of the bitbucket server. (optional)
    :arg str head-filter-regex: A regular expression for filtering
        discovered source branches. Requires the :jenkins-wiki:`SCM API Plugin
        <SCM+API+Plugin>`.
    :arg str discovery-branch: Discovers branches on the repository.
        Valid options: ex-pr, only-pr, all.
        Value is not specified by default.
    :arg str discover-pr-origin: Discovers pull requests where the origin
        repository is the same as the target repository.
        Valid options: mergeOnly, headOnly, mergeAndHead.
        Value is not specified by default.
    :arg str discover-pr-forks-strategy: Fork strategy. Valid options:
        merge-current, current, both, false. (default 'merge-current')
    :arg str discover-pr-forks-trust: Discovers pull requests where the origin
        repository is a fork of the target repository.
        Valid options: contributors, everyone, permission or nobody.
        (default 'contributors')
    :arg list build-strategies: Provides control over whether to build a branch
        (or branch like things such as change requests and tags) whenever it is
        discovered initially or a change from the previous revision has been
        detected. (optional)
        Refer to :func:`~build_strategies <build_strategies>`.
    :arg bool local-branch: Check out to matching local branch
        If given, checkout the revision to build as HEAD on this branch.
        If selected, then the branch name is computed from the remote branch
        without the origin. In that case, a remote branch origin/master will
        be checked out to a local branch named master, and a remote branch
        origin/develop/new-feature will be checked out to a local branch
        named develop/newfeature.
        Requires the :jenkins-wiki:`Git Plugin <Git+Plugin>`.
    :arg dict checkout-over-ssh: Checkout repo over ssh.

        * **credentials** ('str'): Credentials to use for
            checkout of the repo over ssh.

    :arg dict filter-by-name-wildcard: Enable filter by name with wildcards.
        Requires the :jenkins-wiki:`SCM API Plugin <SCM+API+Plugin>`.

        * **includes** ('str'): Space-separated list
            of name patterns to consider. You may use * as a wildcard;
            for example: `master release*`
        * **excludes** ('str'): Name patterns to
            ignore even if matched by the includes list.
            For example: `release*`

    :extensions:

        * **clean** (`dict`)
            * **after** (`bool`) - Clean the workspace after checkout
            * **before** (`bool`) - Clean the workspace before checkout
        * **prune** (`bool`) - Prune remote branches (default false)
        * **shallow-clone** (`bool`) - Perform shallow clone (default false)
        * **depth** (`int`) - Set shallow clone depth (default 1)
        * **do-not-fetch-tags** (`bool`) - Perform a clone without tags
            (default false)
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


    Minimal Example:

    .. literalinclude::
       /../../tests/multibranch/fixtures/scm_bitbucket_minimal.yaml

    Full Example:

    .. literalinclude::
       /../../tests/multibranch/fixtures/scm_bitbucket_full.yaml
    """
    source = XML.SubElement(xml_parent, 'source', {
        'class': 'com.cloudbees.jenkins.plugins.bitbucket.BitbucketSCMSource',
        'plugin': 'cloudbees-bitbucket-branch-source',
    })
    source_mapping = [
        ('', 'id', '-'.join(['bb', data.get('repo-owner', ''),
            data.get('repo', '')])),
        ('repo-owner', 'repoOwner', None),
        ('repo', 'repository', None),
    ]
    helpers.convert_mapping_to_xml(
        source, data, source_mapping, fail_required=True)

    mapping_optional = [
        ('credentials-id', 'credentialsId', None),
        ('server-url', 'serverUrl', None),
    ]
    helpers.convert_mapping_to_xml(
        source, data, mapping_optional, fail_required=False)

    traits = XML.SubElement(source, 'traits')
    if data.get('discover-tags', False):
        XML.SubElement(traits,
            'com.cloudbees.jenkins.plugins.bitbucket.TagDiscoveryTrait')
    if data.get('head-filter-regex', None):
        rshf = XML.SubElement(traits,
            'jenkins.scm.impl.trait.RegexSCMHeadFilterTrait')
        XML.SubElement(rshf, 'regex').text = data.get('head-filter-regex')

    if data.get('discover-pr-origin', None):
        dpro = XML.SubElement(traits,
            'com.cloudbees.jenkins.plugins.bitbucket'
            '.OriginPullRequestDiscoveryTrait')
        dpro_strategies = {
            'mergeOnly': '1',
            'headOnly': '2',
            'mergeAndHead': '3'
        }
        dpro_mapping = [
            ('discover-pr-origin', 'strategyId', None, dpro_strategies)
        ]
        helpers.convert_mapping_to_xml(
            dpro, data, dpro_mapping, fail_required=True)

    if data.get('discover-pr-forks-strategy'):
        dprf = XML.SubElement(traits,
             'com.cloudbees.jenkins.plugins.bitbucket'
             '.ForkPullRequestDiscoveryTrait')
        dprf_strategy = {
            'merge-current': '1',
            'current': '2',
            'both': '3',
        }
        dprf_mapping = [
            ('discover-pr-forks-strategy', 'strategyId', 'merge-current',
            dprf_strategy)
        ]
        helpers.convert_mapping_to_xml(
            dprf, data, dprf_mapping, fail_required=True)

        trust = data.get('discover-pr-forks-trust', 'contributors')
        trust_map = {
            'contributors': ''.join([
                'com.cloudbees.jenkins.plugins.bitbucket'
                '.ForkPullRequestDiscoveryTrait$TrustContributors']),
            'everyone': ''.join([
                'com.cloudbees.jenkins.plugins.bitbucket'
                '.ForkPullRequestDiscoveryTrait$TrustEveryone']),
            'permission': ''.join([
                'com.cloudbees.jenkins.plugins.bitbucket'
                '.ForkPullRequestDiscoveryTrait$TrustPermission']),
            'nobody': ''.join([
                'com.cloudbees.jenkins.plugins.bitbucket'
                '.ForkPullRequestDiscoveryTrait$TrustNobody']),
        }
        if trust not in trust_map:
            raise InvalidAttributeError('discover-pr-forks-trust',
                                        trust,
                                        trust_map.keys())
        XML.SubElement(dprf, 'trust').attrib['class'] = trust_map[trust]

    if data.get('discover-branch', None):
        dbr = XML.SubElement(traits,
            'com.cloudbees.jenkins.plugins.bitbucket.BranchDiscoveryTrait')
        dbr_strategies = {
            'ex-pr': '1',
            'only-pr': '2',
            'all': '3'
        }
        dbr_mapping = [
            ('discover-branch', 'strategyId', None, dbr_strategies)
        ]
        helpers.convert_mapping_to_xml(
            dbr, data, dbr_mapping, fail_required=True)

    if data.get('build-strategies', None):
        build_strategies(xml_parent, data)

    if data.get('local-branch', False):
        lbr = XML.SubElement(traits,
            'jenkins.plugins.git.traits.LocalBranchTrait', {
                'plugin': 'git',
            }
        )
        lbr_extension = XML.SubElement(lbr,
            'extension', {
                'class': 'hudson.plugins.git.extensions.impl.LocalBranch',
            }
        )
        XML.SubElement(lbr_extension,
            'localBranch').text = "**"

    if data.get('checkout-over-ssh', None):
        cossh = XML.SubElement(traits,
            'com.cloudbees.jenkins.plugins.bitbucket.SSHCheckoutTrait')
        cossh_credentials = [
            ('credentials', 'credentialsId', ''),
        ]
        helpers.convert_mapping_to_xml(
            cossh,
            data.get('checkout-over-ssh'),
            cossh_credentials,
            fail_required=True)

    if data.get('filter-by-name-wildcard', None):
        wscmf_name = XML.SubElement(traits,
            'jenkins.scm.impl.trait.WildcardSCMHeadFilterTrait', {
                'plugin': 'scm-api',
            }
        )
        wscmf_name_mapping = [
            ('includes', 'includes', ''),
            ('excludes', 'excludes', '')
        ]
        helpers.convert_mapping_to_xml(
            wscmf_name,
            data.get('filter-by-name-wildcard', ''),
            wscmf_name_mapping,
            fail_required=True)

    # handle the default git extensions like:
    # - clean
    # - shallow-clone
    # - timeout
    # - do-not-fetch-tags
    # - submodule
    # - prune
    # - wipe-workspace
    # - use-author
    git_extensions(traits, data)


def gerrit_scm(xml_parent, data):
    """Configure Gerrit SCM

    Requires the :jenkins-wiki:`Gerrit Code Review Plugin
    <Gerrit+Code+Review+Plugin>`.

    :arg str url: The git url. (required)
    :arg str credentials-id: The credential to use to connect to the GIT URL.
    :arg bool ignore-on-push-notifications: If a job should not trigger upon
        push notifications. (default false)
    :arg list(str) refspecs: Which refspecs to look for.
        (default ``['+refs/changes/*:refs/remotes/@{remote}/*',
        '+refs/heads/*:refs/remotes/@{remote}/*']``)
    :arg str includes: Comma-separated list of branches to be included.
        (default '*')
    :arg str excludes: Comma-separated list of branches to be excluded.
        (default '')
    :arg list build-strategies: Provides control over whether to build a branch
        (or branch like things such as change requests and tags) whenever it is
        discovered initially or a change from the previous revision has been
        detected. (optional)
        Refer to :func:`~build_strategies <build_strategies>`.

    Minimal Example:

    .. literalinclude::
       /../../tests/multibranch/fixtures/scm_gerrit_minimal.yaml

    Full Example:

    .. literalinclude::
       /../../tests/multibranch/fixtures/scm_gerrit_full.yaml
    """
    source = XML.SubElement(xml_parent, 'source', {
        'class': 'jenkins.plugins.gerrit.GerritSCMSource',
        'plugin': 'gerrit',
    })
    source_mapping = [
        ('', 'id', '-'.join(['gr', data.get('url', '')])),
        ('url', 'remote', None),
        ('credentials-id', 'credentialsId', ''),
        ('includes', 'includes', '*'),
        ('excludes', 'excludes', ''),
        ('ignore-on-push-notifications', 'ignoreOnPushNotifications', True),
    ]
    helpers.convert_mapping_to_xml(
        source, data, source_mapping, fail_required=True)

    source_mapping_optional = [
        ('api-uri', 'apiUri', None),
    ]
    helpers.convert_mapping_to_xml(
        source, data, source_mapping_optional, fail_required=False)

    # Traits
    traits = XML.SubElement(source, 'traits')
    XML.SubElement(traits,
        'jenkins.plugins.gerrit.traits.ChangeDiscoveryTrait')

    # Refspec Trait
    refspec_trait = XML.SubElement(
        traits, 'jenkins.plugins.git.traits.RefSpecsSCMSourceTrait', {
            'plugin': 'git',
        }
    )
    templates = XML.SubElement(refspec_trait, 'templates')
    refspecs = data.get('refspecs', [
        '+refs/changes/*:refs/remotes/@{remote}/*',
        '+refs/heads/*:refs/remotes/@{remote}/*',
    ])
    # convert single string to list
    if isinstance(refspecs, six.string_types):
        refspecs = [refspecs]
    for x in refspecs:
        e = XML.SubElement(
            templates, ('jenkins.plugins.git.traits'
            '.RefSpecsSCMSourceTrait_-RefSpecTemplate'))
        XML.SubElement(e, 'value').text = x

    if data.get('build-strategies', None):
        build_strategies(xml_parent, data)


def git_scm(xml_parent, data):
    """Configure Git SCM

    Requires the :jenkins-wiki:`Git Plugin <Git+Plugin>`.

    :arg str url: The git repo url. (required)
    :arg str credentials-id: The credential to use to connect to the GIT repo.
        (default '')

    :arg bool discover-branches: Discovers branches on the repository.
        (default true)
    :arg bool discover-tags: Discovers tags on the repository.
        (default false)
    :arg bool ignore-on-push-notifications: If a job should not trigger upon
        push notifications. (default false)
    :arg str head-filter-regex: A regular expression for filtering
        discovered source branches. Requires the :jenkins-wiki:`SCM API Plugin
        <SCM+API+Plugin>`.
    :arg list build-strategies: Provides control over whether to build a branch
        (or branch like things such as change requests and tags) whenever it is
        discovered initially or a change from the previous revision has been
        detected. (optional)
        Refer to :func:`~build_strategies <build_strategies>`.

    :extensions:

        * **clean** (`dict`)
            * **after** (`bool`) - Clean the workspace after checkout
            * **before** (`bool`) - Clean the workspace before checkout
        * **prune** (`bool`) - Prune remote branches (default false)
        * **shallow-clone** (`bool`) - Perform shallow clone (default false)
        * **depth** (`int`) - Set shallow clone depth (default 1)
        * **do-not-fetch-tags** (`bool`) - Perform a clone without tags
            (default false)
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

    Minimal Example:

    .. literalinclude:: /../../tests/multibranch/fixtures/scm_git_minimal.yaml

    Full Example:

    .. literalinclude:: /../../tests/multibranch/fixtures/scm_git_full.yaml
    """
    source = XML.SubElement(xml_parent, 'source', {
        'class': 'jenkins.plugins.git.GitSCMSource',
        'plugin': 'git',
    })
    source_mapping = [
        ('', 'id', '-'.join(['gt', data.get('url', '')])),
        ('url', 'remote', None),
        ('credentials-id', 'credentialsId', ''),
    ]
    helpers.convert_mapping_to_xml(
        source, data, source_mapping, fail_required=True)

    ##########
    # Traits #
    ##########

    traits_path = 'jenkins.plugins.git.traits'
    traits = XML.SubElement(source, 'traits')

    if data.get('discover-branches', True):
        XML.SubElement(traits, ''.join([traits_path, '.BranchDiscoveryTrait']))

    if data.get('discover-tags', False):
        XML.SubElement(traits, ''.join([traits_path, '.TagDiscoveryTrait']))

    if data.get('ignore-on-push-notifications', False):
        XML.SubElement(
            traits, ''.join([traits_path, '.IgnoreOnPushNotificationTrait']))

    if data.get('head-filter-regex', None):
        rshf = XML.SubElement(traits,
            'jenkins.scm.impl.trait.RegexSCMHeadFilterTrait')
        XML.SubElement(rshf, 'regex').text = data.get('head-filter-regex')

    if data.get('build-strategies', None):
        build_strategies(xml_parent, data)

    # handle the default git extensions like:
    # - clean
    # - shallow-clone
    # - timeout
    # - do-not-fetch-tags
    # - submodule
    # - prune
    # - wipe-workspace
    # - use-author
    git_extensions(traits, data)


def github_scm(xml_parent, data):
    """Configure GitHub SCM

    Requires the :jenkins-wiki:`GitHub Branch Source Plugin
    <GitHub+Branch+Source+Plugin>`.

    :arg str api-uri: The GitHub API uri for hosted / on-site GitHub. Must
        first be configured in Global Configuration. (default GitHub)
    :arg bool ssh-checkout: Checkout over SSH.

        * **credentials** ('str'): Credentials to use for
            checkout of the repo over ssh.

    :arg str credentials-id: Credentials used to scan branches and pull
        requests, check out sources and mark commit statuses. (optional)
    :arg str repo-owner: Specify the name of the GitHub Organization or
        GitHub User Account. (required)
    :arg str repo: The GitHub repo. (required)

    :arg str branch-discovery: Discovers branches on the repository.
        Valid options: no-pr, only-pr, all, false. (default 'no-pr')
    :arg str discover-pr-forks-strategy: Fork strategy. Valid options:
        merge-current, current, both, false. (default 'merge-current')
    :arg str discover-pr-forks-trust: Discovers pull requests where the origin
        repository is a fork of the target repository.
        Valid options: contributors, everyone, permission or nobody.
        (default 'contributors')
    :arg str discover-pr-origin: Discovers pull requests where the origin
        repository is the same as the target repository.
        Valid options: merge-current, current, both.  (default 'merge-current')
    :arg bool discover-tags: Discovers tags on the repository.
        (default false)
    :arg list build-strategies: Provides control over whether to build a branch
        (or branch like things such as change requests and tags) whenever it is
        discovered initially or a change from the previous revision has been
        detected. (optional)
        Refer to :func:`~build_strategies <build_strategies>`.

    :extensions:

        * **clean** (`dict`)
            * **after** (`bool`) - Clean the workspace after checkout
            * **before** (`bool`) - Clean the workspace before checkout
        * **prune** (`bool`) - Prune remote branches (default false)
        * **shallow-clone** (`bool`) - Perform shallow clone (default false)
        * **depth** (`int`) - Set shallow clone depth (default 1)
        * **do-not-fetch-tags** (`bool`) - Perform a clone without tags
            (default false)
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

    Minimal Example:

    .. literalinclude::
       /../../tests/multibranch/fixtures/scm_github_minimal.yaml

    Full Example:

    .. literalinclude::
       /../../tests/multibranch/fixtures/scm_github_full.yaml
    """
    github_path = 'org.jenkinsci.plugins.github_branch_source'
    github_path_dscore = 'org.jenkinsci.plugins.github__branch__source'

    source = XML.SubElement(xml_parent, 'source', {
        'class': ''.join([github_path, '.GitHubSCMSource']),
        'plugin': 'github-branch-source',
    })
    mapping = [
        ('', 'id', '-'.join(['gh', data.get('repo-owner', ''),
            data.get('repo', '')])),
        ('repo-owner', 'repoOwner', None),
        ('repo', 'repository', None),
    ]
    helpers.convert_mapping_to_xml(
        source, data, mapping, fail_required=True)

    mapping_optional = [
        ('api-uri', 'apiUri', None),
        ('credentials-id', 'credentialsId', None),
    ]
    helpers.convert_mapping_to_xml(
        source, data, mapping_optional, fail_required=False)

    traits = XML.SubElement(source, 'traits')

    # no-pr value is assumed if branch-discovery not mentioned.
    if data.get('branch-discovery', 'no-pr'):
        bd = XML.SubElement(traits, ''.join([
            github_path_dscore, '.BranchDiscoveryTrait']))
        bd_strategy = {
            'no-pr': '1',
            'only-pr': '2',
            'all': '3',
        }
        bd_mapping = [
            ('branch-discovery', 'strategyId', 'no-pr', bd_strategy)
        ]
        helpers.convert_mapping_to_xml(
            bd, data, bd_mapping, fail_required=True)

    if data.get('ssh-checkout', None):
        cossh = XML.SubElement(
            traits, ''.join([
                github_path_dscore, '.SSHCheckoutTrait'
            ])
        )
        if not isinstance(data.get('ssh-checkout'), bool):
            cossh_credentials = [
                ('credentials', 'credentialsId', ''),
            ]
            helpers.convert_mapping_to_xml(
                cossh,
                data.get('ssh-checkout'),
                cossh_credentials,
                fail_required=True)

    if data.get('discover-tags', False):
        XML.SubElement(
            traits, ''.join([
                github_path_dscore, '.TagDiscoveryTrait'
            ])
        )

    if data.get('discover-pr-forks-strategy', 'merged-current'):
        dprf = XML.SubElement(
            traits, ''.join([
                github_path_dscore, '.ForkPullRequestDiscoveryTrait'
            ])
        )
        dprf_strategy = {
            'merge-current': '1',
            'current': '2',
            'both': '3',
        }
        dprf_mapping = [
            ('discover-pr-forks-strategy', 'strategyId', 'merge-current',
            dprf_strategy)
        ]
        helpers.convert_mapping_to_xml(
            dprf, data, dprf_mapping, fail_required=True)

        trust = data.get('discover-pr-forks-trust', 'contributors')
        trust_map = {
            'contributors': ''.join([
                github_path,
                '.ForkPullRequestDiscoveryTrait$TrustContributors']),
            'everyone': ''.join([
                github_path,
                '.ForkPullRequestDiscoveryTrait$TrustEveryone']),
            'permission': ''.join([
                github_path,
                '.ForkPullRequestDiscoveryTrait$TrustPermission']),
            'nobody': ''.join([
                github_path,
                '.ForkPullRequestDiscoveryTrait$TrustNobody']),
        }
        if trust not in trust_map:
            raise InvalidAttributeError('discover-pr-forks-trust',
                                        trust,
                                        trust_map.keys())
        XML.SubElement(dprf, 'trust').attrib['class'] = trust_map[trust]

    dpro_strategy = data.get('discover-pr-origin', 'merge-current')
    dpro = XML.SubElement(traits, ''.join([
        github_path_dscore,
        '.OriginPullRequestDiscoveryTrait'
    ]))
    dpro_strategy_map = {
        'merge-current': '1',
        'current': '2',
        'both': '3',
    }
    if dpro_strategy not in dpro_strategy_map:
        raise InvalidAttributeError('discover-pr-origin',
                                    dpro_strategy,
                                    dpro_strategy_map.keys())
    dpro_mapping = [
        ('discover-pr-origin', 'strategyId', 'merge-current',
        dpro_strategy_map)
    ]
    helpers.convert_mapping_to_xml(
        dpro, data, dpro_mapping, fail_required=True)

    if data.get('build-strategies', None):
        build_strategies(xml_parent, data)

    # handle the default git extensions like:
    # - clean
    # - shallow-clone
    # - timeout
    # - do-not-fetch-tags
    # - submodule
    # - prune
    # - wipe-workspace
    # - use-author
    git_extensions(traits, data)


def build_strategies(xml_parent, data):
    """Configure Basic Branch Build Strategies.

    Requires the :jenkins-wiki:`Basic Branch Build Strategies Plugin
    <Basic+Branch+Build+Strategies+Plugin>`.

    :arg list build-strategies: Definition of build strategies.

        * **tags** (dict): Builds tags
            * **ignore-tags-newer-than** (int) The number of days since the tag
                was created before it is eligible for automatic building.
                (optional, default -1)
            * **ignore-tags-older-than** (int) The number of days since the tag
                was created after which it is no longer eligible for automatic
                building. (optional, default -1)
        * **change-request** (dict): Builds change requests / pull requests
            * **ignore-target-only-changes** (bool) Ignore rebuilding merge
                branches when only the target branch changed.
                (optional, default false)
        * **regular-branches** (bool): Builds regular branches whenever a
            change is detected. (optional, default None)
        * **named-branches** (list): Builds named branches whenever a change
          is detected.

            * **exact-name** (dict) Matches the name verbatim.
                * **name** (str) The name to match. (optional)
                * **case-sensitive** (bool) Check this box if the name should
                    be matched case sensitively. (default false)
            * **regex-name** (dict) Matches the name against a regular
              expression.

                * **regex** (str) A Java regular expression to restrict the
                    names. Names that do not match the supplied regular
                    expression will be ignored. (default `^.*$`)
                * **case-sensitive** (bool) Check this box if the name should
                    be matched case sensitively. (default false)
            * **wildcards-name** (dict) Matches the name against an
              include/exclude set of wildcards.

                * **includes** (str) Space-separated list of name patterns to
                    consider. You may use `*` as a wildcard;
                    for example: `master release*` (default `*`)
                * **excludes** (str) Name patterns to ignore even if matched
                    by the includes list. For example: release (optional)

    """

    basic_build_strategies = 'jenkins.branch.buildstrategies.basic'
    bbs = XML.SubElement(xml_parent, 'buildStrategies')
    for bbs_list in data.get('build-strategies', None):
        if 'tags' in bbs_list:
            tags = bbs_list['tags']
            tags_elem = XML.SubElement(bbs, ''.join([basic_build_strategies,
            '.TagBuildStrategyImpl']), {
                'plugin': 'basic-branch-build-strategies',
            })

            newer_than = -1
            if ('ignore-tags-newer-than' in tags and
                    tags['ignore-tags-newer-than'] >= 0):
                newer_than = str(tags['ignore-tags-newer-than'] * 86400000)
            XML.SubElement(tags_elem, 'atMostMillis').text = str(newer_than)

            older_than = -1
            if ('ignore-tags-older-than' in tags and
                    tags['ignore-tags-older-than'] >= 0):
                older_than = str(tags['ignore-tags-older-than'] * 86400000)
            XML.SubElement(tags_elem, 'atLeastMillis').text = str(older_than)

        if bbs_list.get('regular-branches', False):
            XML.SubElement(bbs, ''.join([basic_build_strategies,
            '.BranchBuildStrategyImpl']), {
                'plugin': 'basic-branch-build-strategies',
            })

        if 'change-request' in bbs_list:
            cr = bbs_list['change-request']
            cr_elem = XML.SubElement(bbs, ''.join([basic_build_strategies,
            '.ChangeRequestBuildStrategyImpl']), {
                'plugin': 'basic-branch-build-strategies',
            })
            itoc = cr.get('ignore-target-only-changes', False)
            XML.SubElement(cr_elem, 'ignoreTargetOnlyChanges').text = (
                str(itoc).lower())

        if 'named-branches' in bbs_list:
            named_branch_elem = XML.SubElement(bbs, ''.join(
                [basic_build_strategies, '.NamedBranchBuildStrategyImpl']), {
                'plugin': 'basic-branch-build-strategies',
            })

            filters = XML.SubElement(named_branch_elem, 'filters')

            for nb in bbs_list['named-branches']:
                if 'exact-name' in nb:
                    exact_name_elem = XML.SubElement(filters, ''.join(
                        [basic_build_strategies,
                        '.NamedBranchBuildStrategyImpl',
                        '_-ExactNameFilter']))
                    exact_name_mapping = [
                        ('name', 'name', ''),
                        ('case-sensitive', 'caseSensitive', False)
                    ]
                    helpers.convert_mapping_to_xml(
                        exact_name_elem,
                        nb['exact-name'],
                        exact_name_mapping,
                        fail_required=False)

                if 'regex-name' in nb:
                    regex_name_elem = XML.SubElement(filters, ''.join([
                        basic_build_strategies,
                        '.NamedBranchBuildStrategyImpl',
                        '_-RegexNameFilter']))
                    regex_name_mapping = [
                        ('regex', 'regex', '^.*$'),
                        ('case-sensitive', 'caseSensitive', False)
                    ]
                    helpers.convert_mapping_to_xml(
                        regex_name_elem, nb['regex-name'],
                        regex_name_mapping, fail_required=False)

                if 'wildcards-name' in nb:
                    wildcards_name_elem = XML.SubElement(filters, ''.join([
                        basic_build_strategies,
                        '.NamedBranchBuildStrategyImpl',
                        '_-WildcardsNameFilter']))
                    wildcards_name_mapping = [
                        ('includes', 'includes', '*'),
                        ('excludes', 'excludes', '')
                    ]
                    helpers.convert_mapping_to_xml(
                        wildcards_name_elem,
                        nb['wildcards-name'],
                        wildcards_name_mapping,
                        fail_required=False)
