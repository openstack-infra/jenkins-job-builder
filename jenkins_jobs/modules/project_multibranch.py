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

Job examples:

.. literalinclude:: /../../tests/multibranch/fixtures/multibranch_defaults.yaml

.. literalinclude:: /../../tests/multibranch/fixtures/multi_scm_full.yaml

"""
import collections
import logging
import xml.etree.ElementTree as XML
import jenkins_jobs.modules.base
import jenkins_jobs.modules.helpers as helpers
import uuid
import six

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
        XML.SubElement(factory, 'scriptPath').text = 'Jenkinsfile'

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
        ('', 'id', str(uuid.uuid4())),
        ('repo-owner', 'repoOwner', None),
        ('repo', 'repository', None),
    ]
    helpers.convert_mapping_to_xml(
        source, data, source_mapping, fail_required=True)

    mapping_optional = [
        ('credentials-id', 'credentialsId', None),
    ]
    helpers.convert_mapping_to_xml(
        source, data, mapping_optional, fail_required=False)

    XML.SubElement(source, 'traits')


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
        ('', 'id', str(uuid.uuid4())),
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


def git_scm(xml_parent, data):
    """Configure Git SCM

    Requires the :jenkins-wiki:`Git Plugin <Git+Plugin>`.

    :arg str url: The git repo url. (required)
    :arg str credentials-id: The credential to use to connect to the GIT repo.
        (default '')

    :arg bool discover-branches: Discovers branches on the repository.
        (default true)
    :arg bool ignore-on-push-notifications: If a job should not trigger upon
        push notifications. (default false)

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
        ('', 'id', str(uuid.uuid4())),
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

    if data.get('ignore-on-push-notifications', False):
        XML.SubElement(
            traits, ''.join([traits_path, '.IgnoreOnPushNotificationTrait']))


def github_scm(xml_parent, data):
    """Configure GitHub SCM

    Requires the :jenkins-wiki:`GitHub Branch Source Plugin
    <GitHub+Branch+Source+Plugin>`.

    :arg str api-uri: The GitHub API uri for hosted / on-site GitHub. Must
        first be configured in Global Configuration. (default GitHub)
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
        ('', 'id', str(uuid.uuid4())),
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
