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
          url: https://github.com/openstack-ci/jenkins-job-builder/
"""


import xml.etree.ElementTree as XML
import jenkins_jobs.modules.base
from jenkins_jobs.errors import JenkinsJobsException


def ownership(parser, xml_parent, data):
    """yaml: ownership
    Plugin provides explicit ownership for jobs and slave nodes.
    Requires the Jenkins `Ownership Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/Ownership+Plugin>`_

    :arg bool enabled: whether ownership enabled (default : true)
    :arg str owner: the owner of job
    :arg list co-owners: list of job co-owners

    Example::

        properties:
         - ownership:
            owner: abraverm
            co-owners:
             - lbednar
             - edolinin
    """
    ownership_plugin = \
        XML.SubElement(xml_parent,
                       'com.synopsys.arc.'
                       'jenkins.plugins.ownership.jobs.JobOwnerJobProperty')
    ownership = XML.SubElement(ownership_plugin, 'ownership')
    owner = str(data.get('enabled', True)).lower()
    XML.SubElement(ownership, 'ownershipEnabled').text = owner

    XML.SubElement(ownership, 'primaryOwnerId').text = data.get('owner')

    coowners = data.get('co-owners', [])
    if coowners:
        coownersIds = XML.SubElement(ownership, 'coownersIds')
        for coowner in coowners:
            XML.SubElement(coownersIds, 'string').text = coowner


def promoted_build(parser, xml_parent, data):
    """yaml: promoted-build
    Marks a build for promotion. A promotion process with an identical
    name must be created via the web interface in the job in order for the job
    promotion to persist. Promotion processes themselves cannot be configured
    by jenkins-jobs due to the separate storage of plugin configuration files.
    Requires the Jenkins `Promoted Builds Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/Promoted+Builds+Plugin>`_

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
            url: https://github.com/openstack-ci/jenkins-job-builder/
    """
    github = XML.SubElement(xml_parent,
                            'com.coravy.hudson.plugins.github.'
                            'GithubProjectProperty')
    github_url = XML.SubElement(github, 'projectUrl')
    github_url.text = data['url']


def throttle(parser, xml_parent, data):
    """yaml: throttle
    Throttles the number of builds for this job.
    Requires the Jenkins `Throttle Concurrent Builds Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/
    Throttle+Concurrent+Builds+Plugin>`_

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
    #XML.SubElement(throttle, 'categories')
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


def inject(parser, xml_parent, data):
    """yaml: inject
    Allows you to inject evironment variables into the build.
    Requires the Jenkins `Env Inject Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/EnvInject+Plugin>`_

    :arg str properties-file: file to read with properties (optional)
    :arg str properties-content: key=value properties (optional)
    :arg str script-file: file with script to run (optional)
    :arg str script-content: script to run (optional)
    :arg str groovy-content: groovy script to run (optional)
    :arg bool load-from-master: load files from master (default false)
    :arg bool enabled: injection enabled (default true)
    :arg bool keep-system-variables: keep system variables (default true)
    :arg bool keep-build-variables: keep build variable (default true)

    Example::

      properties:
        - inject:
            properties-content: FOO=bar
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
    """

    mapping = {
        'job-delete': 'hudson.model.Item.Delete',
        'job-configure': 'hudson.model.Item.Configure',
        'job-read': 'hudson.model.Item.Read',
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
    Creates an extended choice property where values can be read from a file
    Requires the Jenkins `Extended Choice Parameter Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/
    Extended+Choice+Parameter+plugin>`_

    :arg string name: name of the property
    :arg string description: description of the property (optional, default '')
    :arg string property-file: location of property file to read from
        (optional, default '')
    :arg string property-key: key for the property-file (optional, default '')
    :arg bool quote-value: whether to put quotes around the property
        when passing to Jenkins (optional, default false)
    :arg string visible-items: number of items to show in the list
        (optional, default 5)
    :arg string type: type of select (optional, default single-select)
    :arg string value: comma separated list of values for the single select
        or multi-select box (optional, default '')
    :arg string default-value: used to set the initial selection of the
        single-select or multi-select box (optional, default '')
    :arg string default-property-file: location of property file when default
        value needs to come from a property file (optional, default '')
    :arg string default-property-key: key for the default property file
        (optional, default '')

    Example::

      properties:
        - extended-choice:
            name: FOO
            description: A foo property
            property-file: /home/foo/property.prop
            property-key: key
            quote-value: true
            visible-items: 10
            type: multi-select
            value: foo,bar,select
            default-value: foo
            default-property-file: /home/property.prop
            default-property-key: fookey
    """
    definition = XML.SubElement(xml_parent,
                                'hudson.model.ParametersDefinitionProperty')
    definitions = XML.SubElement(definition, 'parameterDefinitions')
    extended = XML.SubElement(definitions, 'com.cwctravel.hudson.plugins.'
                                           'extended__choice__parameter.'
                                           'ExtendedChoiceParameterDefinition')
    XML.SubElement(extended, 'name').text = data['name']
    XML.SubElement(extended, 'description').text = data.get('description', '')
    XML.SubElement(extended, 'quoteValue').text = str(data.get('quote-value',
                                                      False)).lower()
    XML.SubElement(extended, 'visibleItemCount').text = data.get(
        'visible-items', '5')
    choice = data.get('type', 'single-select')
    choicedict = {'single-select': 'PT_SINGLE_SELECT',
                  'multi-select': 'PT_MULTI_SELECT',
                  'radio': 'PT_RADIO',
                  'checkbox': 'PT_CHECKBOX'}
    if choice not in choicedict:
        raise JenkinsJobsException("Type entered is not valid, must be one "
                                   "of: single-select, multi-select, radio, "
                                   "or checkbox")
    XML.SubElement(extended, 'type').text = choicedict[choice]
    XML.SubElement(extended, 'value').text = data.get('value', '')
    XML.SubElement(extended, 'propertyFile').text = data.get('property-file',
                                                             '')
    XML.SubElement(extended, 'propertyKey').text = data.get('property-key', '')
    XML.SubElement(extended, 'defaultValue').text = data.get('default-value',
                                                             '')
    XML.SubElement(extended, 'defaultPropertyFile').text = data.get(
        'default-property-file', '')
    XML.SubElement(extended, 'defaultPropertyKey').text = data.get(
        'default-property-key', '')


def priority_sorter(parser, xml_parent, data):
    """yaml: priority-sorter
    Allows simple ordering of builds, using a configurable job priority.

    Requires the Jenkins `Priority Sorter Plugin
    <https://wiki.jenkins-ci.org/display/JENKINS/Priority+Sorter+Plugin>`_.

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

    Requires the Jenkins `Build Blocker Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/Build+Blocker+Plugin>`_

    :arg bool use-build-blocker: Enable or disable build blocker
        (optional, defaults to True)
    :arg list blocking-jobs: One regular expression per line
        to select blocking jobs by their names. (required)


    Example::

        properties:
          - build-blocker:
              use-build-blocker: true
              blocking-jobs:
                - ".*-deploy"
                - "^maintainance.*"
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


def batch_tasks(parser, xml_parent, data):
    """yaml: batch-tasks
    Batch tasks can be tasks for events like releases, integration, archiving,
    etc. In this way, anyone in the project team can execute them in a way that
    leaves a record.

    A batch task consists of a shell script and a name. When you execute
    a build, the shell script gets run on the workspace, just like a build.
    Batch tasks and builds "lock" the workspace, so when one of those
    activities is in progress, all the others will block in the queue.

    Requires the Jenkins `Batch Task Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/Batch+Task+Plugin>`_

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
