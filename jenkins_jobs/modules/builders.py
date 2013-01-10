# Copyright 2012 Hewlett-Packard Development Company, L.P.
# Copyright 2012 Varnish Software AS
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
Builders define actions that the Jenkins job should execute.  Examples
include shell scripts or maven targets.  The ``builders`` attribute in
the :ref:`Job` definition accepts a list of builders to invoke.  They
may be components defined below, locally defined macros (using the top
level definition of ``builder:``, or locally defined components found
via the ``jenkins_jobs.builders`` entry point.

**Component**: builders
  :Macro: builder
  :Entry Point: jenkins_jobs.builders

Example::

  job:
    name: test_job

    builders:
      - shell: "make test"

"""


import xml.etree.ElementTree as XML
import jenkins_jobs.modules.base
import logging

logger = logging.getLogger(__name__)


def shell(parser, xml_parent, data):
    """yaml: shell
    Execute a shell command.

    :Parameter: the shell command to execute

    Example::

      builders:
        - shell: "make test"

    """
    shell = XML.SubElement(xml_parent, 'hudson.tasks.Shell')
    XML.SubElement(shell, 'command').text = data


def copyartifact(parser, xml_parent, data):
    """yaml: copyartifact

    Copy artifact from another project.  Requires the Jenkins `Copy Artifact
    plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/Copy+Artifact+Plugin>`_

    :arg str project: Project to copy from
    :arg str filter: what files to copy
    :arg str target: Target base directory for copy, blank means use workspace


    Example::

      builders:
        - copyartifact:
            project: foo
            filter: *.tar.gz

    """
    t = XML.SubElement(xml_parent, 'hudson.plugins.copyartifact.CopyArtifact')
    XML.SubElement(t, 'projectName').text = data["project"]
    XML.SubElement(t, 'filter').text = data.get("filter", "")
    XML.SubElement(t, 'target').text = data.get("target", "")


def ant(parser, xml_parent, data):
    """yaml: ant
    Execute an ant target.  Requires the Jenkins `Ant Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/Ant+Plugin>`_

    To setup this builder you can either reference the list of targets
    or use named parameters. Below is a description of both forms:

    *1) Listing targets:*

    After the ant directive, simply pass as argument a space separated list
    of targets to build.

    :Parameter: space separated list of Ant targets
    :arg str ant-name: the name of the ant installation,
        defaults to 'default' (optional)

    Example to call two Ant targets::

        builders:
          - ant: "target1 target2"
             ant-name: "Standard Ant"

    The build file would be whatever the Jenkins Ant Plugin is set to use
    per default (i.e build.xml in the workspace root).

    *2) Using named parameters:*

    :arg str targets: the space separated list of ANT targets.
    :arg str buildfile: the path to the ANT build file.
    :arg list properties: Passed to ant script using -Dkey=value (optional)
    :arg str ant-name: the name of the ant installation,
        defaults to 'default' (optional)


    Example specifying the build file too and several targets::

        builders:
          - ant:
             targets: "debug test install"
             buildfile: "build.xml"
             properties:
                builddir: "/tmp/"
                failonerror: true
             ant-name: "Standard Ant"

    """
    ant = XML.SubElement(xml_parent, 'hudson.tasks.Ant')

    if type(data) is str:
        # Support for short form: -ant: "target"
        data = {'targets': data}
    for setting, value in data.iteritems():
        if setting == 'targets':
            targets = XML.SubElement(ant, 'targets')
            targets.text = value
        if setting == 'buildfile':
            buildfile = XML.SubElement(ant, 'buildFile')
            buildfile.text = value
        if setting == 'properties':
            properties = data['properties']
            prop_string = ''
            for prop, val in properties.items():
                prop_string += "%s=%s\n" % (prop, val)
            prop_element = XML.SubElement(ant, 'properties')
            prop_element.text = prop_string

    XML.SubElement(ant, 'antName').text = data.get('ant-name', 'default')


def trigger_builds(parser, xml_parent, data):
    """yaml: trigger-builds
    Trigger builds of other jobs.
    Requires the Jenkins `Parameterized Trigger Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/
    Parameterized+Trigger+Plugin>`_

    :arg str project: the Jenkins project to trigger
    :arg str predefined-parameters:
      key/value pairs to be passed to the job (optional)
    :arg bool block: whether to wait for the triggered jobs
      to finish or not (default false)

    Example::

      builders:
        - trigger-builds:
            - project: "build_started"
              predefined-parameters:
                FOO="bar"
              block: true

    """
    tbuilder = XML.SubElement(xml_parent,
                              'hudson.plugins.parameterizedtrigger.'
                              'TriggerBuilder')
    configs = XML.SubElement(tbuilder, 'configs')
    for project_def in data:
        if 'project' not in project_def or project_def['project'] == '':
            logger.debug("No project specified - skipping trigger-build")
            continue
        tconfig = XML.SubElement(configs,
                                 'hudson.plugins.parameterizedtrigger.'
                                 'BlockableBuildTriggerConfig')
        tconfigs = XML.SubElement(tconfig, 'configs')
        if(project_def.get('current-parameters')):
            XML.SubElement(tconfigs,
                           'hudson.plugins.parameterizedtrigger.'
                           'CurrentBuildParameters')
        if 'predefined-parameters' in project_def:
            params = XML.SubElement(tconfigs,
                                    'hudson.plugins.parameterizedtrigger.'
                                    'PredefinedBuildParameters')
            properties = XML.SubElement(params, 'properties')
            properties.text = project_def['predefined-parameters']
        if(len(list(tconfigs)) == 0):
            tconfigs.set('class', 'java.util.Collections$EmptyList')
        projects = XML.SubElement(tconfig, 'projects')
        projects.text = project_def['project']
        condition = XML.SubElement(tconfig, 'condition')
        condition.text = 'ALWAYS'
        trigger_with_no_params = XML.SubElement(tconfig,
                                                'triggerWithNoParameters')
        trigger_with_no_params.text = 'false'
        build_all_nodes_with_label = XML.SubElement(tconfig,
                                                    'buildAllNodesWithLabel')
        build_all_nodes_with_label.text = 'false'
        block = project_def.get('block', False)
        if(block):
            block = XML.SubElement(tconfig, 'block')
            bsft = XML.SubElement(block, 'buildStepFailureThreshold')
            XML.SubElement(bsft, 'name').text = 'FAILURE'
            XML.SubElement(bsft, 'ordinal').text = '2'
            XML.SubElement(bsft, 'color').text = 'RED'
            ut = XML.SubElement(block, 'unstableThreshold')
            XML.SubElement(ut, 'name').text = 'UNSTABLE'
            XML.SubElement(ut, 'ordinal').text = '1'
            XML.SubElement(ut, 'color').text = 'Yellow'
            ft = XML.SubElement(block, 'failureThreshold')
            XML.SubElement(ft, 'name').text = 'FAILURE'
            XML.SubElement(ft, 'ordinal').text = '2'
            XML.SubElement(ft, 'color').text = 'RED'
    # If configs is empty, remove the entire tbuilder tree.
    if(len(configs) == 0):
        logger.debug("Pruning empty TriggerBuilder tree.")
        xml_parent.remove(tbuilder)


def builders_from(parser, xml_parent, data):
    """yaml: builders-from
    Use builders from another project.
    Requires the Jenkins `Template Project Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/Template+Project+Plugin>`_

    :arg str projectName: the name of the other project

    Example::

      builders:
        - builders-from:
            - project: "base-build"
    """
    pbs = XML.SubElement(xml_parent,
                         'hudson.plugins.templateproject.ProxyBuilder')
    XML.SubElement(pbs, 'projectName').text = data


def inject(parser, xml_parent, data):
    """yaml: inject
    Inject an environment for the job.
    Requires the Jenkins `EnvInject Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/EnvInject+Plugin>`_

    :arg str properties-file: the name of the property file (optional)
    :arg str properties-content: the properties content (optional)

    Example::

      builders:
        - inject:
            properties-file: example.prop
            properties-content: EXAMPLE=foo-bar
    """
    eib = XML.SubElement(xml_parent, 'EnvInjectBuilder')
    info = XML.SubElement(eib, 'info')
    propfile = data.get('properties-file', '')
    XML.SubElement(info, 'propertiesFilePath').text = propfile
    propcontent = data.get('properties-content', '')
    XML.SubElement(info, 'propertiesContent').text = propcontent


def artifact_resolver(parser, xml_parent, data):
    """yaml: artifact-resolver
    Allows one to resolve artifacts from a maven repository like nexus
    (without having maven installed)
    Requires the Jenkins `Repository Connector Plugin
    <https://wiki.jenkins-ci.org/display/JENKINS/Repository+Connector+Plugin>`_

    :arg bool fail-on-error: Whether to fail the build on error (default false)
    :arg bool repository-logging: Enable repository logging (default false)
    :arg str target-directory: Where to resolve artifacts to
    :arg list artifacts: list of artifacts to resolve

      :Artifact: * **group-id** (`str`) -- Group ID of the artifact
                 * **artifact-id** (`str`) -- Artifact ID of the artifact
                 * **version** (`str`) -- Version of the artifact
                 * **classifier** (`str`) -- Classifier of the artifact
                   (default '')
                 * **extension** (`str`) -- Extension of the artifact
                   (default 'jar')
                 * **target-file-name** (`str`) -- What to name the artifact
                   (default '')

    Example::

      builders:
        - artifact-resolver:
            fail-on-error: true
            repository-logging: true
            target-directory: foo
            artifacts:
              - group-id: commons-logging
                artifact-id: commons-logging
                version: 1.1
                classifier: src
                extension: jar
                target-file-name: comm-log.jar
              - group-id: commons-lang
                artifact-id: commons-lang
                version: 1.2
    """
    ar = XML.SubElement(xml_parent,
                        'org.jvnet.hudson.plugins.repositoryconnector.'
                        'ArtifactResolver')
    XML.SubElement(ar, 'targetDirectory').text = data['target-directory']
    artifacttop = XML.SubElement(ar, 'artifacts')
    artifacts = data['artifacts']
    for artifact in artifacts:
        rcartifact = XML.SubElement(artifacttop,
                                    'org.jvnet.hudson.plugins.'
                                    'repositoryconnector.Artifact')
        XML.SubElement(rcartifact, 'groupId').text = artifact['group-id']
        XML.SubElement(rcartifact, 'artifactId').text = artifact['artifact-id']
        XML.SubElement(rcartifact, 'classifier').text = artifact.get(
            'classifier', '')
        XML.SubElement(rcartifact, 'version').text = artifact['version']
        XML.SubElement(rcartifact, 'extension').text = artifact.get(
            'extension', 'jar')
        XML.SubElement(rcartifact, 'targetFileName').text = artifact.get(
            'target-file-name', '')
    XML.SubElement(ar, 'failOnError').text = str(data.get(
        'fail-on-error', False)).lower()
    XML.SubElement(ar, 'enableRepoLogging').text = str(data.get(
        'repository-logging', False)).lower()
    XML.SubElement(ar, 'snapshotUpdatePolicy').text = 'never'
    XML.SubElement(ar, 'releaseUpdatePolicy').text = 'never'
    XML.SubElement(ar, 'snapshotChecksumPolicy').text = 'warn'
    XML.SubElement(ar, 'releaseChecksumPolicy').text = 'warn'


def gradle(parser, xml_parent, data):
    """yaml: gradle
    Execute gradle tasks.  Requires the Jenkins 'Gradle Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/Gradle+Plugin>`_

    :arg str tasks: List of tasks to execute
    :arg bool wrapper: use gradle wrapper (default false)
    :arg bool executable: make gradlew executable (default false)

    Example::

      builders:
        - gradle:
            wrapper: true
            executable: true
            tasks: |
                   init
                   build
                   tests
    """
    gradle = XML.SubElement(xml_parent, 'hudson.plugins.gradle.Gradle')
    XML.SubElement(gradle, 'description').text = ''
    XML.SubElement(gradle, 'switches').text = ''
    XML.SubElement(gradle, 'tasks').text = data['tasks']
    XML.SubElement(gradle, 'rootBuildScriptDir').text = ''
    XML.SubElement(gradle, 'buildFile').text = ''
    XML.SubElement(gradle, 'useWrapper').text = str(data.get(
        'wrapper', False)).lower()
    XML.SubElement(gradle, 'makeExecutable').text = str(data.get(
        'executable', False)).lower()


def batch(parser, xml_parent, data):
    """yaml: batch
    Execute a batch command.

    :Parameter: the batch command to execute

    Example::

      builders:
        - batch: "foo/foo.bat"

    """
    batch = XML.SubElement(xml_parent, 'hudson.tasks.BatchFile')
    XML.SubElement(batch, 'command').text = data


class Builders(jenkins_jobs.modules.base.Base):
    sequence = 60

    def gen_xml(self, parser, xml_parent, data):

        for alias in ['prebuilders', 'builders', 'postbuilders']:
            if alias in data:
                builders = XML.SubElement(xml_parent, alias)
                for builder in data[alias]:
                    self._dispatch('builder', 'builders',
                                   parser, builders, builder)

        # Make sure freestyle projects always have a <builders> entry
        # or Jenkins v1.472 (at least) will NPE.
        project_type = data.get('project-type', 'freestyle')
        if project_type in ('freestyle', 'matrix') and 'builders' not in data:
            XML.SubElement(xml_parent, 'builders')
