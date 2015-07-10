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


import xml.etree.ElementTree as XML
import jenkins_jobs.modules.base
from jenkins_jobs.errors import JenkinsJobsException
import logging


def builds_chain_fingerprinter(parser, xml_parent, data):
    """yaml: builds-chain-fingerprinter
    Builds chain fingerprinter.
    Requires the Jenkins :jenkins-wiki:`Builds chain fingerprinter Plugin
    <Builds+chain+fingerprinter>`.

    :arg bool per-builds-chain: enable builds hierarchy fingerprinting
        (default False)
    :arg bool per-job-chain: enable jobs hierarchy fingerprinting
        (default False)

    Example:

    .. literalinclude:: /../../tests/properties/fixtures/fingerprinter.yaml
    """
    fingerprinter = XML.SubElement(xml_parent,
                                   'org.jenkinsci.plugins.'
                                   'buildschainfingerprinter.'
                                   'AutomaticFingerprintJobProperty')
    XML.SubElement(fingerprinter, 'isPerBuildsChainEnabled').text = str(
        data.get('per-builds-chain', False)).lower()
    XML.SubElement(fingerprinter, 'isPerJobsChainEnabled').text = str(
        data.get('per-job-chain', False)).lower()


def ownership(parser, xml_parent, data):
    """yaml: ownership
    Plugin provides explicit ownership for jobs and slave nodes.
    Requires the Jenkins :jenkins-wiki:`Ownership Plugin <Ownership+Plugin>`.

    :arg bool enabled: whether ownership enabled (default : true)
    :arg str owner: the owner of job
    :arg list co-owners: list of job co-owners

    Example:

    .. literalinclude:: /../../tests/properties/fixtures/ownership.yaml
    """
    ownership_plugin = \
        XML.SubElement(xml_parent,
                       'com.synopsys.arc.'
                       'jenkins.plugins.ownership.jobs.JobOwnerJobProperty')
    ownership = XML.SubElement(ownership_plugin, 'ownership')
    owner = str(data.get('enabled', True)).lower()
    XML.SubElement(ownership, 'ownershipEnabled').text = owner

    XML.SubElement(ownership, 'primaryOwnerId').text = data.get('owner')

    coownersIds = XML.SubElement(ownership, 'coownersIds')
    for coowner in data.get('co-owners', []):
        XML.SubElement(coownersIds, 'string').text = coowner


def promoted_build(parser, xml_parent, data):
    """yaml: promoted-build
    Marks a build for promotion. A promotion process with an identical
    name must be created via the web interface in the job in order for the job
    promotion to persist. Promotion processes themselves cannot be configured
    by jenkins-jobs due to the separate storage of plugin configuration files.
    Requires the Jenkins :jenkins-wiki:`Promoted Builds Plugin
    <Promoted+Builds+Plugin>`.

    :arg list names: the promoted build names

    Example::

      properties:
        - promoted-build:
            names:
              - "Release to QA"
              - "Jane Must Approve"
    """
    promoted = XML.SubElement(xml_parent, 'hudson.plugins.promoted__builds.'
                                          'JobPropertyImpl')
    names = data.get('names', [])
    if names:
        active_processes = XML.SubElement(promoted, 'activeProcessNames')
        for n in names:
            XML.SubElement(active_processes, 'string').text = str(n)


def github(parser, xml_parent, data):
    """yaml: github
    Sets the GitHub URL for the project.

    :arg str url: the GitHub URL

    Example::

      properties:
        - github:
            url: https://github.com/openstack-infra/jenkins-job-builder/
    """
    github = XML.SubElement(xml_parent,
                            'com.coravy.hudson.plugins.github.'
                            'GithubProjectProperty')
    github_url = XML.SubElement(github, 'projectUrl')
    github_url.text = data['url']


def least_load(parser, xml_parent, data):
    """yaml: least-load
    Enables the Least Load Plugin.
    Requires the Jenkins :jenkins-wiki:`Least Load Plugin <Least+Load+Plugin>`.

    :arg bool disabled: whether or not leastload is disabled (default True)

    Example:

    .. literalinclude:: /../../tests/properties/fixtures/least-load002.yaml
    """
    least = XML.SubElement(xml_parent,
                           'org.bstick12.jenkinsci.plugins.leastload.'
                           'LeastLoadDisabledProperty')

    XML.SubElement(least, 'leastLoadDisabled').text = str(
        data.get('disabled', True)).lower()


def throttle(parser, xml_parent, data):
    """yaml: throttle
    Throttles the number of builds for this job.
    Requires the Jenkins :jenkins-wiki:`Throttle Concurrent Builds Plugin
    <Throttle+Concurrent+Builds+Plugin>`.

    :arg int max-per-node: max concurrent builds per node (default 0)
    :arg int max-total: max concurrent builds (default 0)
    :arg bool enabled: whether throttling is enabled (default True)
    :arg str option: throttle `project` or `category`
    :arg list categories: multiproject throttle categories

    Example::

      properties:
        - throttle:
            max-total: 4
            categories:
              - cat1
              - cat2

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
    if data.get('enabled', True):
        XML.SubElement(throttle, 'throttleEnabled').text = 'true'
    else:
        XML.SubElement(throttle, 'throttleEnabled').text = 'false'
    cat = data.get('categories', [])
    if cat:
        cn = XML.SubElement(throttle, 'categories')
        for c in cat:
            XML.SubElement(cn, 'string').text = str(c)

    XML.SubElement(throttle, 'throttleOption').text = data.get('option')
    XML.SubElement(throttle, 'configVersion').text = '1'


def sidebar(parser, xml_parent, data):
    """yaml: sidebar
    Allows you to add links in the sidebar.
    Requires the Jenkins :jenkins-wiki:`Sidebar Plugin <Sidebar+Plugin>`.

    :arg str url: url to link to (optional)
    :arg str text: text for the link (optional)
    :arg str icon: path to icon (optional)

    Example:

    .. literalinclude:: /../../tests/properties/fixtures/sidebar02.yaml
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


def inject(parser, xml_parent, data):
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


def authenticated_build(parser, xml_parent, data):
    """yaml: authenticated-build
    Specifies an authorization matrix where only authenticated users
    may trigger a build.

    DEPRECATED

    Example::

      properties:
        - authenticated-build
    """
    # TODO: generalize this
    if data:
        security = XML.SubElement(xml_parent,
                                  'hudson.security.'
                                  'AuthorizationMatrixProperty')
        XML.SubElement(security, 'permission').text = \
            'hudson.model.Item.Build:authenticated'


def authorization(parser, xml_parent, data):
    """yaml: authorization
    Specifies an authorization matrix

    The available rights are:
      job-delete
      job-configure
      job-read
      job-extended-read
      job-discover
      job-build
      job-workspace
      job-cancel
      run-delete
      run-update
      scm-tag

    Example::

      properties:
        - authorization:
            admin:
              - job-delete
              - job-configure
              - job-read
              - job-discover
              - job-build
              - job-workspace
              - job-cancel
              - run-delete
              - run-update
              - scm-tag
            anonymous:
              - job-discover
              - job-read
              - job-extended-read
    """

    mapping = {
        'job-delete': 'hudson.model.Item.Delete',
        'job-configure': 'hudson.model.Item.Configure',
        'job-read': 'hudson.model.Item.Read',
        'job-extended-read': 'hudson.model.Item.ExtendedRead',
        'job-discover': 'hudson.model.Item.Discover',
        'job-build': 'hudson.model.Item.Build',
        'job-workspace': 'hudson.model.Item.Workspace',
        'job-cancel': 'hudson.model.Item.Cancel',
        'run-delete': 'hudson.model.Run.Delete',
        'run-update': 'hudson.model.Run.Update',
        'scm-tag': 'hudson.scm.SCM.Tag'
    }

    if data:
        matrix = XML.SubElement(xml_parent,
                                'hudson.security.AuthorizationMatrixProperty')
        for (username, perms) in data.items():
            for perm in perms:
                pe = XML.SubElement(matrix, 'permission')
                pe.text = "{0}:{1}".format(mapping[perm], username)


def extended_choice(parser, xml_parent, data):
    """yaml: extended-choice
    Use of this config option is deprecated.  You should use the
    `extended-choice` option in the parameter section of the job configuration
    instead.
    """
    logger = logging.getLogger("%s:extended_choice" % __name__)
    logger.warn('Use of the extended-choice property is deprecated.  You '
                'should use the extended-choice option in the parameter '
                'section instead.')
    definition = XML.SubElement(xml_parent,
                                'hudson.model.ParametersDefinitionProperty')
    definitions = XML.SubElement(definition, 'parameterDefinitions')
    parser.registry.dispatch('parameter', parser, definitions,
                             {'extended-choice': data})


def priority_sorter(parser, xml_parent, data):
    """yaml: priority-sorter
    Allows simple ordering of builds, using a configurable job priority.

    Requires the Jenkins :jenkins-wiki:`Priority Sorter Plugin
    <Priority+Sorter+Plugin>`.

    :arg int priority: Priority of the job.  Higher value means higher
        priority, with 100 as the standard priority. (required)

    Example::

        properties:
          - priority-sorter:
              priority: 150
    """
    priority_sorter_tag = XML.SubElement(xml_parent,
                                         'hudson.queueSorter.'
                                         'PrioritySorterJobProperty')
    XML.SubElement(priority_sorter_tag, 'priority').text = str(
        data['priority'])


def build_blocker(parser, xml_parent, data):
    """yaml: build-blocker
    This plugin keeps the actual job in the queue
    if at least one name of currently running jobs
    is matching with one of the given regular expressions.

    Requires the Jenkins :jenkins-wiki:`Build Blocker Plugin
    <Build+Blocker+Plugin>`.

    :arg bool use-build-blocker: Enable or disable build blocker
        (optional) (default true)
    :arg list blocking-jobs: One regular expression per line
        to select blocking jobs by their names. (required)


    Example::

        properties:
          - build-blocker:
              use-build-blocker: true
              blocking-jobs:
                - ".*-deploy"
                - "^maintenance.*"
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


def copyartifact(parser, xml_parent, data):
    """yaml: copyartifact
    Specify a list of projects that have access to copy the artifacts of
    this project.

    Requires the Jenkins :jenkins-wiki:`Copy Artifact plugin
    <Copy+Artifact+Plugin>`.

    :arg string projects: comma separated list of projects that can copy
        artifacts of this project. Wild card character '*' is available.


    Example:

    .. literalinclude:: \
            /../../tests/properties/fixtures/copyartifact.yaml

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
    XML.SubElement(projectlist, 'string').text = data.get('projects')


def batch_tasks(parser, xml_parent, data):
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

        :Task: * **name** (`str`) Task name.
               * **script** (`str`) Task script.

    Example:

    .. literalinclude:: /../../tests/properties/fixtures/batch-task.yaml

    """
    pdef = XML.SubElement(xml_parent,
                          'hudson.plugins.batch__task.BatchTaskProperty')
    tasks = XML.SubElement(pdef, 'tasks')
    for task in data:
        batch_task = XML.SubElement(tasks,
                                    'hudson.plugins.batch__task.BatchTask')
        XML.SubElement(batch_task, 'name').text = task['name']
        XML.SubElement(batch_task, 'script').text = task['script']


def heavy_job(parser, xml_parent, data):
    """yaml: heavy-job
    This plugin allows you to define "weight" on each job,
    and making each job consume that many executors

    Requires the Jenkins :jenkins-wiki:`Heavy Job Plugin <Heavy+Job+Plugin>`.

    :arg int weight: Specify the total number of executors
        that this job should occupy (default 1)


    Example:

    .. literalinclude:: /../../tests/properties/fixtures/heavy-job.yaml

    """
    heavyjob = XML.SubElement(xml_parent,
                              'hudson.plugins.'
                              'heavy__job.HeavyJobProperty')
    XML.SubElement(heavyjob, 'weight').text = str(
        data.get('weight', 1))


def slave_utilization(parser, xml_parent, data):
    """yaml: slave-utilization
    This plugin allows you to specify the percentage of a slave's capacity a
    job wants to use.

    Requires the Jenkins :jenkins-wiki:`Slave Utilization Plugin
    <Slave+Utilization+Plugin>`.

    :arg int slave-percentage: Specify the percentage of a slave's execution
        slots that this job should occupy (default: 0)
    :arg bool single-instance-per-slave: Control whether concurrent instances
        of this job will be permitted to run in parallel on a single slave
        (default: False)

    Example:

    .. literalinclude:: \
            /../../tests/properties/fixtures/slave-utilization1.yaml
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


def delivery_pipeline(parser, xml_parent, data):
    """yaml: delivery-pipeline
    Requires the Jenkins :jenkins-wiki:`Delivery Pipeline Plugin
    <Delivery+Pipeline+Plugin>`.

    :arg str stage: Name of the stage for this job (default: '')
    :arg str task: Name of the task for this job (default: '')

    Example:

    .. literalinclude:: \
            /../../tests/properties/fixtures/delivery-pipeline1.yaml

    """
    pipeline = XML.SubElement(xml_parent,
                              'se.diabol.jenkins.pipeline.'
                              'PipelineProperty')
    XML.SubElement(pipeline, 'stageName').text = data.get('stage', '')
    XML.SubElement(pipeline, 'taskName').text = data.get('task', '')


def zeromq_event(parser, xml_parent, data):
    """yaml: zeromq-event
    This is a Jenkins plugin that will publish Jenkins Job run events
    (start, complete, finish) to a ZMQ PUB socket.

    Requires the Jenkins `ZMQ Event Publisher.
    <https://git.openstack.org/cgit/openstack-infra/zmq-event-publisher>`_

    Example:

    .. literalinclude:: \
            /../../tests/properties/fixtures/zeromq-event.yaml

    """

    zmq_event = XML.SubElement(xml_parent,
                               'org.jenkinsci.plugins.'
                               'ZMQEventPublisher.HudsonNotificationProperty')
    XML.SubElement(zmq_event, 'enabled').text = 'true'


class Properties(jenkins_jobs.modules.base.Base):
    sequence = 20

    component_type = 'property'
    component_list_type = 'properties'

    def gen_xml(self, parser, xml_parent, data):
        properties = xml_parent.find('properties')
        if properties is None:
            properties = XML.SubElement(xml_parent, 'properties')

        for prop in data.get('properties', []):
            self.registry.dispatch('property', parser, properties, prop)
