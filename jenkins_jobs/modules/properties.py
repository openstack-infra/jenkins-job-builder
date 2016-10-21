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
The Properties module supplies a wide range of options that are
implemented as Jenkins job properties.

**Component**: properties
  :Macro: property
  :Entry Point: jenkins_jobs.properties

Example::

  job:
    name: test_job

    properties:
      - github:
          url: https://github.com/openstack-infra/jenkins-job-builder/
"""

import logging
import pkg_resources
import xml.etree.ElementTree as XML

from jenkins_jobs.errors import InvalidAttributeError
from jenkins_jobs.errors import JenkinsJobsException
from jenkins_jobs.errors import MissingAttributeError
import jenkins_jobs.modules.base
import jenkins_jobs.modules.helpers as helpers


def builds_chain_fingerprinter(registry, xml_parent, data):
    """yaml: builds-chain-fingerprinter
    Builds chain fingerprinter.
    Requires the Jenkins :jenkins-wiki:`Builds chain fingerprinter Plugin
    <Builds+chain+fingerprinter>`.

    :arg bool per-builds-chain: enable builds hierarchy fingerprinting
        (default false)
    :arg bool per-job-chain: enable jobs hierarchy fingerprinting
        (default false)

    Example:

    .. literalinclude:: /../../tests/properties/fixtures/fingerprinter.yaml
       :language: yaml
    """
    fingerprinter = XML.SubElement(xml_parent,
                                   'org.jenkinsci.plugins.'
                                   'buildschainfingerprinter.'
                                   'AutomaticFingerprintJobProperty')
    XML.SubElement(fingerprinter, 'isPerBuildsChainEnabled').text = str(
        data.get('per-builds-chain', False)).lower()
    XML.SubElement(fingerprinter, 'isPerJobsChainEnabled').text = str(
        data.get('per-job-chain', False)).lower()


def ownership(registry, xml_parent, data):
    """yaml: ownership
    Plugin provides explicit ownership for jobs and slave nodes.
    Requires the Jenkins :jenkins-wiki:`Ownership Plugin <Ownership+Plugin>`.

    :arg bool enabled: whether ownership enabled (default : true)
    :arg str owner: the owner of job
    :arg list co-owners: list of job co-owners

    Example:

    .. literalinclude:: /../../tests/properties/fixtures/ownership.yaml
       :language: yaml
    """
    ownership_plugin = XML.SubElement(
        xml_parent,
        'com.synopsys.arc.jenkins.plugins.ownership.jobs.JobOwnerJobProperty')
    ownership = XML.SubElement(ownership_plugin, 'ownership')
    owner = str(data.get('enabled', True)).lower()
    XML.SubElement(ownership, 'ownershipEnabled').text = owner

    XML.SubElement(ownership, 'primaryOwnerId').text = data.get('owner')

    coownersIds = XML.SubElement(ownership, 'coownersIds')
    for coowner in data.get('co-owners', []):
        XML.SubElement(coownersIds, 'string').text = coowner


def promoted_build(registry, xml_parent, data):
    """yaml: promoted-build
    Marks a build for promotion. A promotion process with an identical
    name must be created via the web interface in the job in order for the job
    promotion to persist. Promotion processes themselves cannot be configured
    by jenkins-jobs due to the separate storage of plugin configuration files.
    Requires the Jenkins :jenkins-wiki:`Promoted Builds Plugin
    <Promoted+Builds+Plugin>`.

    :arg list names: the promoted build names (optional)

    Example:

    .. literalinclude:: /../../tests/properties/fixtures/promoted_build.yaml
       :language: yaml
    """
    promoted = XML.SubElement(xml_parent, 'hudson.plugins.promoted__builds.'
                                          'JobPropertyImpl')
    names = data.get('names', [])
    if names:
        active_processes = XML.SubElement(promoted, 'activeProcessNames')
        for n in names:
            XML.SubElement(active_processes, 'string').text = str(n)


def gitbucket(parser, xml_parent, data):
    """yaml: gitbucket
    Integrate GitBucket to Jenkins.
    Requires the Jenkins :jenkins-wiki:`GitBucket Plugin <GitBucket+Plugin>`.

    :arg str url: GitBucket URL to issue (required)
    :arg bool link-enabled: Enable hyperlink to issue (default false)

    Minimal Example:

    .. literalinclude:: /../../tests/properties/fixtures/gitbucket-minimal.yaml
       :language: yaml

    Full Example:

    .. literalinclude:: /../../tests/properties/fixtures/gitbucket-full.yaml
       :language: yaml
    """
    gitbucket = XML.SubElement(
        xml_parent, 'org.jenkinsci.plugins.gitbucket.GitBucketProjectProperty')
    gitbucket.set('plugin', 'gitbucket')

    mapping = [
        ('url', 'url', None),
        ('link-enabled', 'linkEnabled', False),
    ]
    helpers.convert_mapping_to_xml(
        gitbucket, data, mapping, fail_required=True)


def github(registry, xml_parent, data):
    """yaml: github
    Sets the GitHub URL for the project.

    :arg str url: the GitHub URL (required)
    :arg str display-name: This value will be used as context name for commit
        status if status builder or status publisher is defined for this
        project. (>= 1.14.1) (default '')

    Minimal Example:

    .. literalinclude:: /../../tests/properties/fixtures/github-minimal.yaml
       :language: yaml

    Full Example:

    .. literalinclude:: /../../tests/properties/fixtures/github-full.yaml
       :language: yaml
    """
    github = XML.SubElement(
        xml_parent, 'com.coravy.hudson.plugins.github.GithubProjectProperty')
    github.set('plugin', 'github')

    mapping = [
        ('url', 'projectUrl', None),
        ('display-name', 'displayName', ''),
    ]
    helpers.convert_mapping_to_xml(github, data, mapping, fail_required=True)


def gitlab(registry, xml_parent, data):
    """yaml: gitlab
    Sets the GitLab connection for the project. Configured via Jenkins Global
    Configuration.
    Requires the Jenkins :jenkins-wiki:`GitLab Plugin <GitLab+Plugin>`.

    :arg str connection: the GitLab connection name (required)

    Example:

    .. literalinclude:: /../../tests/properties/fixtures/gitlab.yaml
       :language: yaml
    """
    gitlab = XML.SubElement(xml_parent,
                            'com.dabsquared.gitlabjenkins.connection.'
                            'GitLabConnectionProperty')
    try:
        XML.SubElement(gitlab, 'gitLabConnection').text = data['connection']
    except KeyError as e:
        raise MissingAttributeError(e)


def least_load(registry, xml_parent, data):
    """yaml: least-load
    Enables the Least Load Plugin.
    Requires the Jenkins :jenkins-wiki:`Least Load Plugin <Least+Load+Plugin>`.

    :arg bool disabled: whether or not leastload is disabled (default true)

    Example:

    .. literalinclude:: /../../tests/properties/fixtures/least-load002.yaml
       :language: yaml
    """
    least = XML.SubElement(xml_parent,
                           'org.bstick12.jenkinsci.plugins.leastload.'
                           'LeastLoadDisabledProperty')

    XML.SubElement(least, 'leastLoadDisabled').text = str(
        data.get('disabled', True)).lower()


def throttle(registry, xml_parent, data):
    """yaml: throttle
    Throttles the number of builds for this job.
    Requires the Jenkins :jenkins-wiki:`Throttle Concurrent Builds Plugin
    <Throttle+Concurrent+Builds+Plugin>`.

    :arg str option: throttle `project` (throttle the project alone)
         or `category` (throttle the project as part of one or more categories)
    :arg int max-per-node: max concurrent builds per node (default 0)
    :arg int max-total: max concurrent builds (default 0)
    :arg bool enabled: whether throttling is enabled (default true)
    :arg list categories: multiproject throttle categories
    :arg bool matrix-builds: throttle matrix master builds (default true)
    :arg bool matrix-configs: throttle matrix config builds (default false)

    Example:

    .. literalinclude:: /../../tests/properties/fixtures/throttle001.yaml
       :language: yaml
    """
    throttle = XML.SubElement(xml_parent,
                              'hudson.plugins.throttleconcurrents.'
                              'ThrottleJobProperty')
    XML.SubElement(throttle, 'maxConcurrentPerNode').text = str(
        data.get('max-per-node', '0'))
    XML.SubElement(throttle, 'maxConcurrentTotal').text = str(
        data.get('max-total', '0'))
    # TODO: What's "categories"?
    # XML.SubElement(throttle, 'categories')
    XML.SubElement(throttle, 'throttleEnabled').text = str(
        data.get('enabled', True)).lower()
    cat = data.get('categories', [])
    if cat:
        cn = XML.SubElement(throttle, 'categories')
        for c in cat:
            XML.SubElement(cn, 'string').text = str(c)

    options_list = ('category', 'project')
    option = data.get('option')
    if option not in options_list:
        raise InvalidAttributeError('option', option, options_list)

    XML.SubElement(throttle, 'throttleOption').text = option
    XML.SubElement(throttle, 'configVersion').text = '1'

    matrixopt = XML.SubElement(throttle, 'matrixOptions')
    XML.SubElement(matrixopt, 'throttleMatrixBuilds').text = str(
        data.get('matrix-builds', True)).lower()
    XML.SubElement(matrixopt, 'throttleMatrixConfigurations').text = str(
        data.get('matrix-configs', False)).lower()


def sidebar(registry, xml_parent, data):
    """yaml: sidebar
    Allows you to add links in the sidebar.
    Requires the Jenkins :jenkins-wiki:`Sidebar-Link Plugin
    <Sidebar-Link+Plugin>`.

    :arg str url: url to link to (optional)
    :arg str text: text for the link (optional)
    :arg str icon: path to icon (optional)

    Example:

    .. literalinclude:: /../../tests/properties/fixtures/sidebar02.yaml
       :language: yaml
    """
    sidebar = xml_parent.find('hudson.plugins.sidebar__link.ProjectLinks')
    if sidebar is None:
        sidebar = XML.SubElement(xml_parent,
                                 'hudson.plugins.sidebar__link.ProjectLinks')
        links = XML.SubElement(sidebar, 'links')
    else:
        links = sidebar.find('links')
    action = XML.SubElement(links, 'hudson.plugins.sidebar__link.LinkAction')
    XML.SubElement(action, 'url').text = str(data.get('url', ''))
    XML.SubElement(action, 'text').text = str(data.get('text', ''))
    XML.SubElement(action, 'icon').text = str(data.get('icon', ''))


def inject(registry, xml_parent, data):
    """yaml: inject
    Allows you to inject environment variables into the build.
    Requires the Jenkins :jenkins-wiki:`Env Inject Plugin <EnvInject+Plugin>`.

    :arg str properties-file: file to read with properties (optional)
    :arg str properties-content: key=value properties (optional)
    :arg str script-file: file with script to run (optional)
    :arg str script-content: script to run (optional)
    :arg str groovy-content: groovy script to run (optional)
    :arg bool load-from-master: load files from master (default false)
    :arg bool enabled: injection enabled (default true)
    :arg bool keep-system-variables: keep system variables (default true)
    :arg bool keep-build-variables: keep build variable (default true)
    :arg bool override-build-parameters: override build parameters
        (default false)

    Example:

    .. literalinclude:: /../../tests/properties/fixtures/inject001.yaml
       :language: yaml

    """
    inject = XML.SubElement(xml_parent,
                            'EnvInjectJobProperty')
    info = XML.SubElement(inject, 'info')

    jenkins_jobs.modules.base.add_nonblank_xml_subelement(
        info, 'propertiesFilePath', data.get('properties-file'))
    jenkins_jobs.modules.base.add_nonblank_xml_subelement(
        info, 'propertiesContent', data.get('properties-content'))
    jenkins_jobs.modules.base.add_nonblank_xml_subelement(
        info, 'scriptFilePath', data.get('script-file'))
    jenkins_jobs.modules.base.add_nonblank_xml_subelement(
        info, 'scriptContent', data.get('script-content'))
    jenkins_jobs.modules.base.add_nonblank_xml_subelement(
        info, 'groovyScriptContent', data.get('groovy-content'))

    XML.SubElement(info, 'loadFilesFromMaster').text = str(
        data.get('load-from-master', False)).lower()
    XML.SubElement(inject, 'on').text = str(
        data.get('enabled', True)).lower()
    XML.SubElement(inject, 'keepJenkinsSystemVariables').text = str(
        data.get('keep-system-variables', True)).lower()
    XML.SubElement(inject, 'keepBuildVariables').text = str(
        data.get('keep-build-variables', True)).lower()
    XML.SubElement(inject, 'overrideBuildParameters').text = str(
        data.get('override-build-parameters', False)).lower()


def authenticated_build(registry, xml_parent, data):
    """yaml: authenticated-build
    Specifies an authorization matrix where only authenticated users
    may trigger a build.

    .. deprecated:: 0.1.0. Please use :ref:`authorization <authorization>`.

    Example:

    .. literalinclude::
        /../../tests/properties/fixtures/authenticated_build.yaml
       :language: yaml

    """
    # TODO: generalize this
    security = XML.SubElement(xml_parent,
                              'hudson.security.'
                              'AuthorizationMatrixProperty')
    XML.SubElement(security, 'permission').text = (
        'hudson.model.Item.Build:authenticated')


def authorization(registry, xml_parent, data):
    """yaml: authorization
    Specifies an authorization matrix

    .. _authorization:

    :arg list <name>: `<name>` is the name of the group or user, containing
        the list of rights to grant.

       :<name> rights:
            * **credentials-create**
            * **credentials-delete**
            * **credentials-manage-domains**
            * **credentials-update**
            * **credentials-view**
            * **job-build**
            * **job-cancel**
            * **job-configure**
            * **job-delete**
            * **job-discover**
            * **job-extended-read**
            * **job-move**
            * **job-read**
            * **job-status**
            * **job-workspace**
            * **ownership-jobs**
            * **run-delete**
            * **run-update**
            * **scm-tag**

    Example:

    .. literalinclude:: /../../tests/properties/fixtures/authorization.yaml
       :language: yaml
    """

    credentials = 'com.cloudbees.plugins.credentials.CredentialsProvider.'
    ownership = 'com.synopsys.arc.jenkins.plugins.ownership.OwnershipPlugin.'

    mapping = {
        'credentials-create': ''.join((credentials, 'Create')),
        'credentials-delete': ''.join((credentials, 'Delete')),
        'credentials-manage-domains': ''.join((credentials, 'ManageDomains')),
        'credentials-update': ''.join((credentials, 'Update')),
        'credentials-view': ''.join((credentials, 'View')),
        'job-build': 'hudson.model.Item.Build',
        'job-cancel': 'hudson.model.Item.Cancel',
        'job-configure': 'hudson.model.Item.Configure',
        'job-delete': 'hudson.model.Item.Delete',
        'job-discover': 'hudson.model.Item.Discover',
        'job-extended-read': 'hudson.model.Item.ExtendedRead',
        'job-move': 'hudson.model.Item.Move',
        'job-read': 'hudson.model.Item.Read',
        'job-status': 'hudson.model.Item.ViewStatus',
        'job-workspace': 'hudson.model.Item.Workspace',
        'ownership-jobs': ''.join((ownership, 'Jobs')),
        'run-delete': 'hudson.model.Run.Delete',
        'run-update': 'hudson.model.Run.Update',
        'scm-tag': 'hudson.scm.SCM.Tag',
    }

    if data:
        matrix = XML.SubElement(xml_parent,
                                'hudson.security.AuthorizationMatrixProperty')
        for (username, perms) in data.items():
            for perm in perms:
                pe = XML.SubElement(matrix, 'permission')
                try:
                    pe.text = "{0}:{1}".format(mapping[perm], username)
                except KeyError:
                    raise InvalidAttributeError(username, perm, mapping.keys())


def priority_sorter(registry, xml_parent, data):
    """yaml: priority-sorter
    Allows simple ordering of builds, using a configurable job priority.

    Requires the Jenkins :jenkins-wiki:`Priority Sorter Plugin
    <Priority+Sorter+Plugin>`.

    :arg int priority: Priority of the job.  Higher value means higher
        priority, with 100 as the standard priority. (required)

    Example:

    .. literalinclude:: /../../tests/properties/fixtures/priority_sorter.yaml
       :language: yaml
    """
    priority_sorter_tag = XML.SubElement(xml_parent,
                                         'hudson.queueSorter.'
                                         'PrioritySorterJobProperty')
    try:
        XML.SubElement(priority_sorter_tag, 'priority').text = str(
            data['priority'])
    except KeyError as e:
        raise MissingAttributeError(e)


def build_blocker(registry, xml_parent, data):
    """yaml: build-blocker
    This plugin keeps the actual job in the queue
    if at least one name of currently running jobs
    is matching with one of the given regular expressions.

    Requires the Jenkins :jenkins-wiki:`Build Blocker Plugin
    <Build+Blocker+Plugin>`.

    :arg bool use-build-blocker: Enable or disable build blocker (default true)
    :arg list blocking-jobs: One regular expression per line to select
        blocking jobs by their names. (required)
    :arg str block-level: block build globally ('GLOBAL') or per node ('NODE')
        (default 'GLOBAL')
    :arg str queue-scanning: scan build queue for all builds ('ALL') or only
        buildable builds ('BUILDABLE') (default 'DISABLED'))

    Example:

    .. literalinclude::
        /../../tests/properties/fixtures/build-blocker01.yaml
       :language: yaml
    """
    blocker = XML.SubElement(xml_parent,
                             'hudson.plugins.'
                             'buildblocker.BuildBlockerProperty')
    if data is None or 'blocking-jobs' not in data:
        raise JenkinsJobsException('blocking-jobs field is missing')
    elif data.get('blocking-jobs', None) is None:
        raise JenkinsJobsException('blocking-jobs list must not be empty')
    XML.SubElement(blocker, 'useBuildBlocker').text = str(
        data.get('use-build-blocker', True)).lower()
    jobs = ''
    for value in data['blocking-jobs']:
        jobs = jobs + value + '\n'
    XML.SubElement(blocker, 'blockingJobs').text = jobs

    block_level_list = ('GLOBAL', 'NODE')
    block_level = data.get('block-level', 'GLOBAL')
    if block_level not in block_level_list:
        raise InvalidAttributeError('block-level',
                                    block_level,
                                    block_level_list)
    XML.SubElement(blocker, 'blockLevel').text = block_level

    queue_scanning_list = ('DISABLED', 'ALL', 'BUILDABLE')
    queue_scanning = data.get('queue-scanning', 'DISABLED')
    if queue_scanning not in queue_scanning_list:
        raise InvalidAttributeError('queue-scanning',
                                    queue_scanning,
                                    queue_scanning_list)
    XML.SubElement(blocker, 'scanQueueFor').text = queue_scanning


def copyartifact(registry, xml_parent, data):
    """yaml: copyartifact
    Specify a list of projects that have access to copy the artifacts of
    this project.

    Requires the Jenkins :jenkins-wiki:`Copy Artifact plugin
    <Copy+Artifact+Plugin>`.

    :arg str projects: comma separated list of projects that can copy
        artifacts of this project. Wild card character '*' is available.

    Example:

    .. literalinclude::
        /../../tests/properties/fixtures/copyartifact.yaml
       :language: yaml

    """
    copyartifact = XML.SubElement(xml_parent,
                                  'hudson.plugins.'
                                  'copyartifact.'
                                  'CopyArtifactPermissionProperty',
                                  plugin='copyartifact')
    if not data or not data.get('projects', None):
        raise JenkinsJobsException("projects string must exist and "
                                   "not be empty")
    projectlist = XML.SubElement(copyartifact, 'projectNameList')
    for project in str(data.get('projects')).split(','):
        XML.SubElement(projectlist, 'string').text = project


def batch_tasks(registry, xml_parent, data):
    """yaml: batch-tasks
    Batch tasks can be tasks for events like releases, integration, archiving,
    etc. In this way, anyone in the project team can execute them in a way that
    leaves a record.

    A batch task consists of a shell script and a name. When you execute
    a build, the shell script gets run on the workspace, just like a build.
    Batch tasks and builds "lock" the workspace, so when one of those
    activities is in progress, all the others will block in the queue.

    Requires the Jenkins :jenkins-wiki:`Batch Task Plugin <Batch+Task+Plugin>`.

    :arg list batch-tasks: Batch tasks.

        :Tasks:
            * **name** (`str`) Task name.
            * **script** (`str`) Task script.

    Example:

    .. literalinclude:: /../../tests/properties/fixtures/batch-task.yaml
       :language: yaml

    """
    pdef = XML.SubElement(xml_parent,
                          'hudson.plugins.batch__task.BatchTaskProperty')
    tasks = XML.SubElement(pdef, 'tasks')
    for task in data:
        batch_task = XML.SubElement(tasks,
                                    'hudson.plugins.batch__task.BatchTask')
        XML.SubElement(batch_task, 'name').text = task['name']
        XML.SubElement(batch_task, 'script').text = task['script']


def heavy_job(registry, xml_parent, data):
    """yaml: heavy-job
    This plugin allows you to define "weight" on each job,
    and making each job consume that many executors

    Requires the Jenkins :jenkins-wiki:`Heavy Job Plugin <Heavy+Job+Plugin>`.

    :arg int weight: Specify the total number of executors
        that this job should occupy (default 1)

    Example:

    .. literalinclude:: /../../tests/properties/fixtures/heavy-job.yaml
       :language: yaml

    """
    heavyjob = XML.SubElement(xml_parent,
                              'hudson.plugins.'
                              'heavy__job.HeavyJobProperty')
    XML.SubElement(heavyjob, 'weight').text = str(
        data.get('weight', 1))


def slave_utilization(registry, xml_parent, data):
    """yaml: slave-utilization
    This plugin allows you to specify the percentage of a slave's capacity a
    job wants to use.

    Requires the Jenkins :jenkins-wiki:`Slave Utilization Plugin
    <Slave+Utilization+Plugin>`.

    :arg int slave-percentage: Specify the percentage of a slave's execution
        slots that this job should occupy (default 0)
    :arg bool single-instance-per-slave: Control whether concurrent instances
        of this job will be permitted to run in parallel on a single slave
        (default false)

    Example:

    .. literalinclude::
        /../../tests/properties/fixtures/slave-utilization1.yaml
       :language: yaml
    """
    utilization = XML.SubElement(
        xml_parent, 'com.suryagaddipati.jenkins.SlaveUtilizationProperty')
    percent = int(data.get('slave-percentage', 0))
    XML.SubElement(utilization, 'needsExclusiveAccessToNode'
                   ).text = 'true' if percent else 'false'
    XML.SubElement(utilization, 'slaveUtilizationPercentage'
                   ).text = str(percent)
    XML.SubElement(utilization, 'singleInstancePerSlave').text = str(
        data.get('single-instance-per-slave', False)).lower()


def delivery_pipeline(registry, xml_parent, data):
    """yaml: delivery-pipeline
    Requires the Jenkins :jenkins-wiki:`Delivery Pipeline Plugin
    <Delivery+Pipeline+Plugin>`.

    :arg str stage: Name of the stage for this job (default '')
    :arg str task: Name of the task for this job (default '')
    :arg str description: task description template for this job
        (default '')

    Minimal Example:

    .. literalinclude::
       /../../tests/properties/fixtures/delivery-pipeline-minimal.yaml
       :language: yaml

    Full Example:

    .. literalinclude::
       /../../tests/properties/fixtures/delivery-pipeline-full.yaml
       :language: yaml
    """
    pipeline = XML.SubElement(
        xml_parent, 'se.diabol.jenkins.pipeline.PipelineProperty')
    pipeline.set('plugin', 'delivery-pipeline-plugin')

    mapping = [
        ('stage', 'stageName', ''),
        ('task', 'taskName', ''),
        ('description', 'descriptionTemplate', ''),
    ]
    helpers.convert_mapping_to_xml(pipeline, data, mapping, fail_required=True)


def zeromq_event(registry, xml_parent, data):
    """yaml: zeromq-event
    This is a Jenkins plugin that will publish Jenkins Job run events
    (start, complete, finish) to a ZMQ PUB socket.

    Requires the Jenkins `ZMQ Event Publisher.
    <https://git.openstack.org/cgit/openstack-infra/zmq-event-publisher>`_

    Example:

    .. literalinclude::
        /../../tests/properties/fixtures/zeromq-event.yaml
       :language: yaml

    """

    zmq_event = XML.SubElement(xml_parent,
                               'org.jenkinsci.plugins.'
                               'ZMQEventPublisher.HudsonNotificationProperty')
    XML.SubElement(zmq_event, 'enabled').text = 'true'


def slack(registry, xml_parent, data):
    """yaml: slack
    Requires the Jenkins :jenkins-wiki:`Slack Plugin <Slack+Plugin>`

    When using Slack Plugin version < 2.0, Slack Plugin itself requires a
    publisher aswell as properties please note that you have to add the
    publisher to your job configuration aswell. When using Slack Plugin
    version >= 2.0, you should only configure the publisher.

    :arg bool notify-start: Send notification when the job starts
        (default false)
    :arg bool notify-success: Send notification on success. (default false)
    :arg bool notify-aborted: Send notification when job is aborted. (
        default false)
    :arg bool notify-not-built: Send notification when job set to NOT_BUILT
        status. (default false)
    :arg bool notify-unstable: Send notification when job becomes unstable.
        (default false)
    :arg bool notify-failure: Send notification when job fails.
        (default false)
    :arg bool notifiy-back-to-normal: Send notification when job is
        succeeding again after being unstable or failed. (default false)
    :arg bool 'notify-repeated-failure': Send notification when job is
        still failing after last failure. (default false)
    :arg bool include-test-summary: Include the test summary. (default
        False)
    :arg bool include-custom-message: Include a custom message into the
        notification. (default false)
    :arg str custom-message: Custom message to be included. (default '')
    :arg str room: A comma seperated list of rooms / channels to send
        the notifications to. (default '')

    Example:

    .. literalinclude::
        /../../tests/properties/fixtures/slack001.yaml
        :language: yaml
    """
    logger = logging.getLogger(__name__)

    plugin_info = registry.get_plugin_info('Slack Notification Plugin')
    plugin_ver = pkg_resources.parse_version(plugin_info.get('version', "0"))

    if plugin_ver >= pkg_resources.parse_version("2.0"):
        logger.warn(
            "properties section is not used with plugin version >= 2.0",
        )

    mapping = (
        ('notify-start', 'startNotification', False),
        ('notify-success', 'notifySuccess', False),
        ('notify-aborted', 'notifyAborted', False),
        ('notify-not-built', 'notifyNotBuilt', False),
        ('notify-unstable', 'notifyUnstable', False),
        ('notify-failure', 'notifyFailure', False),
        ('notify-back-to-normal', 'notifyBackToNormal', False),
        ('notify-repeated-failure', 'notifyRepeatedFailure', False),
        ('include-test-summary', 'includeTestSummary', False),
        ('include-custom-message', 'includeCustomMessage', False),
        ('custom-message', 'customMessage', ''),
        ('room', 'room', ''),
    )

    slack = XML.SubElement(
        xml_parent,
        'jenkins.plugins.slack.SlackNotifier_-SlackJobProperty',
    )

    # Ensure that custom-message is set when include-custom-message is set
    # to true.
    if data.get('include-custom-message', False):
        if not data.get('custom-message', ''):
            raise MissingAttributeError('custom-message')

    helpers.convert_mapping_to_xml(slack, data, mapping, fail_required=True)


def rebuild(registry, xml_parent, data):
    """yaml: rebuild
    This plug-in allows the user to rebuild a parameterized build without
    entering the parameters again.It will also allow the user to edit the
    parameters before rebuilding.
    Requires the Jenkins :jenkins-wiki:`Rebuild Plugin <Rebuild+Plugin>`.

    :arg bool auto-rebuild: Rebuild without asking for parameters
        (default false)
    :arg bool rebuild-disabled: Disable rebuilding for this job
        (default false)

    Minimal Example:

    .. literalinclude:: /../../tests/properties/fixtures/rebuild-minimal.yaml
       :language: yaml

    Full Example:

    .. literalinclude:: /../../tests/properties/fixtures/rebuild-full.yaml
       :language: yaml
    """
    sub_element = XML.SubElement(xml_parent,
                                 'com.sonyericsson.rebuild.RebuildSettings')
    sub_element.set('plugin', 'rebuild')

    mapping = [
        ('auto-rebuild', 'autoRebuild', False),
        ('rebuild-disabled', 'rebuildDisabled', False),
    ]
    helpers.convert_mapping_to_xml(
        sub_element, data, mapping, fail_required=True)


def build_discarder(registry, xml_parent, data):
    """yaml: build-discarder

    :arg int days-to-keep: Number of days to keep builds for (default -1)
    :arg int num-to-keep: Number of builds to keep (default -1)
    :arg int artifact-days-to-keep: Number of days to keep builds with
        artifacts (default -1)
    :arg int artifact-num-to-keep: Number of builds with artifacts to keep
        (default -1)

    Example:

    .. literalinclude::
        /../../tests/properties/fixtures/build-discarder-001.yaml
       :language: yaml

    .. literalinclude::
        /../../tests/properties/fixtures/build-discarder-002.yaml
       :language: yaml
    """
    base_sub = XML.SubElement(xml_parent,
                              'jenkins.model.BuildDiscarderProperty')
    strategy = XML.SubElement(base_sub, 'strategy')
    strategy.set('class', 'hudson.tasks.LogRotator')

    mappings = [
        ('days-to-keep', 'daysToKeep', -1),
        ('num-to-keep', 'numToKeep', -1),
        ('artifact-days-to-keep', 'artifactDaysToKeep', -1),
        ('artifact-num-to-keep', 'artifactNumToKeep', -1),
    ]
    helpers.convert_mapping_to_xml(
        strategy, data, mappings, fail_required=True)


class Properties(jenkins_jobs.modules.base.Base):
    sequence = 20

    component_type = 'property'
    component_list_type = 'properties'

    def gen_xml(self, xml_parent, data):
        properties = xml_parent.find('properties')
        if properties is None:
            properties = XML.SubElement(xml_parent, 'properties')

        for prop in data.get('properties', []):
            self.registry.dispatch('property', properties, prop)
