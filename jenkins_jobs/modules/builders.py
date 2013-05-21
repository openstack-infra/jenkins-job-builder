# opyright 2012 Hewlett-Packard Development Company, L.P.
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
    :arg bool flatten: Flatten directories (default: false)
    :arg str which-build: which build to get artifacts from
        (optional, default last-successful)
    :arg str build-number: specifies the build number to get when
        when specific-build is specified as which-build
    :arg str permalink: specifies the permalink to get when
        permalink is specified as which-build
    :arg bool stable: specifies to get only last stable build when
        last-successful is specified as which-build
    :arg bool fallback-to-last-successful: specifies to fallback to
        last successful build when upstream-build is specified as which-build
    :arg string param: specifies to use a build parameter to get the build when
        build-param is specified as which-build
    :which-build values:
      * **last-successful**
      * **specific-build**
      * **last-saved**
      * **upstream-build**
      * **permalink**
      * **workspace-latest**
      * **build-param**
    :permalink values:
      * **last**
      * **last-stable**
      * **last-successful**
      * **last-failed**
      * **last-unstable**
      * **last-unsuccessful**


    Example::

      builders:
        - copyartifact:
            project: foo
            filter: *.tar.gz
            target: /home/foo
            which-build: specific-build
            build-number: 123
            flatten: true

    """
    t = XML.SubElement(xml_parent, 'hudson.plugins.copyartifact.CopyArtifact')
    #'project' element is used for copy artifact version 1.26+
    XML.SubElement(t, 'project').text = data["project"]
    #'projectName' element is used for copy artifact version 1.25-
    XML.SubElement(t, 'projectName').text = data["project"]
    XML.SubElement(t, 'filter').text = data.get("filter", "")
    XML.SubElement(t, 'target').text = data.get("target", "")
    flatten = data.get("flatten", False)
    XML.SubElement(t, 'flatten').text = str(flatten).lower()
    select = data.get('which-build', 'last-successful')
    selectdict = {'last-successful': 'StatusBuildSelector',
                  'specific-build': 'SpecificBuildSelector',
                  'last-saved': 'SavedBuildSelector',
                  'upstream-build': 'TriggeredBuildSelector',
                  'permalink': 'PermalinkBuildSelector',
                  'workspace-latest': 'WorkspaceSelector',
                  'build-param': 'ParameterizedBuildSelector'}
    if select not in selectdict:
        raise Exception("which-build entered is not valid must be one of: " +
                        "last-successful, specific-build, last-saved, " +
                        "upstream-build, permalink, workspace-latest, " +
                        " or build-param")
    permalink = data.get('permalink', 'last')
    permalinkdict = {'last': 'lastBuild',
                     'last-stable': 'lastStableBuild',
                     'last-successful': 'lastSuccessfulBuild',
                     'last-failed': 'lastFailedBuild',
                     'last-unstable': 'lastUnstableBuild',
                     'last-unsuccessful': 'lastUnsuccessfulBuild'}
    if permalink not in permalinkdict:
        raise Exception("permalink entered is not valid must be one of: " +
                        "last, last-stable, last-successful, last-failed, " +
                        "last-unstable, or last-unsuccessful")
    selector = XML.SubElement(t, 'selector',
                                 {'class': 'hudson.plugins.copyartifact.' +
                                 selectdict[select]})
    if select == 'specific-build':
        XML.SubElement(selector, 'buildNumber').text = data['build-number']
    if select == 'last-successful':
        XML.SubElement(selector, 'stable').text = str(
            data.get('stable', 'false')).lower()
    if select == 'upstream-build':
        XML.SubElement(selector, 'fallbackToLastSuccessful').text = str(
            data.get('fallback-to-last-successful', 'false')).lower()
    if select == 'permalink':
        XML.SubElement(selector, 'id').text = permalinkdict[permalink]
    if select == 'build-param':
        XML.SubElement(selector, 'parameterName').text = data['param']


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
    :arg str java-opts: java options for ant, can have multiples,
        must be in quotes (optional)


    Example specifying the build file too and several targets::

        builders:
          - ant:
             targets: "debug test install"
             buildfile: "build.xml"
             properties:
                builddir: "/tmp/"
                failonerror: true
             java-opts:
                - "-ea"
                - "-Xmx512m"
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
        if setting == 'java-opts':
            javaopts = data['java-opts']
            jopt_string = ' '.join(javaopts)
            jopt_element = XML.SubElement(ant, 'antOpts')
            jopt_element.text = jopt_string

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
    :arg bool current-parameters: Whether to include the
      parameters passed to the current build to the
      triggered job.
    :arg bool svn-revision: Whether to pass the svn revision
      to the triggered job
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
        if(project_def.get('svn-revision')):
            XML.SubElement(tconfigs,
                           'hudson.plugins.parameterizedtrigger.'
                           'SubversionRevisionBuildParameters')
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
    jenkins_jobs.modules.base.add_nonblank_xml_subelement(
        info, 'propertiesFilePath', data.get('properties-file'))
    jenkins_jobs.modules.base.add_nonblank_xml_subelement(
        info, 'propertiesContent', data.get('properties-content'))


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
    Execute gradle tasks.  Requires the Jenkins `Gradle Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/Gradle+Plugin>`_

    :arg str tasks: List of tasks to execute
    :arg str gradle-name: Use a custom gradle name (optional)
    :arg bool wrapper: use gradle wrapper (default false)
    :arg bool executable: make gradlew executable (default false)
    :arg list switches: Switches for gradle, can have multiples

    Example::

      builders:
        - gradle:
            gradle-name: "gradle-1.2"
            wrapper: true
            executable: true
            switches:
              - "-g /foo/bar/.gradle"
              - "-PmavenUserName=foobar"
            tasks: |
                   init
                   build
                   tests
    """
    gradle = XML.SubElement(xml_parent, 'hudson.plugins.gradle.Gradle')
    XML.SubElement(gradle, 'description').text = ''
    XML.SubElement(gradle, 'tasks').text = data['tasks']
    XML.SubElement(gradle, 'rootBuildScriptDir').text = ''
    XML.SubElement(gradle, 'buildFile').text = ''
    XML.SubElement(gradle, 'gradleName').text = data.get(
        'gradle-name', '')
    XML.SubElement(gradle, 'useWrapper').text = str(data.get(
        'wrapper', False)).lower()
    XML.SubElement(gradle, 'makeExecutable').text = str(data.get(
        'executable', False)).lower()
    switch_string = '\n'.join(data.get('switches', []))
    XML.SubElement(gradle, 'switches').text = switch_string


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


def msbuild(parser, xml_parent, data):
    """yaml: msbuild
    Build .NET project using msbuild.  Requires the `Jenkins MSBuild Plugin
    <https://wiki.jenkins-ci.org/display/JENKINS/MSBuild+Plugin>`_.

    :arg str msbuild-version: which msbuild configured in Jenkins to use
      (optional)
    :arg str solution-file: location of the solution file to build
    :arg str extra-parameters: extra parameters to pass to msbuild (optional)
    :arg bool pass-build-variables: should build variables be passed
      to msbuild (defaults to true)
    :arg bool continue-on-build-failure: should the build continue if
      msbuild returns an error (defaults to false)

    Example::

      builders:
        - msbuild:
            solution-file: "MySolution.sln"
            msbuild-version: "msbuild-4.0"
            extra-parameters: "/maxcpucount:4"
            pass-build-variables: False
            continue-on-build-failure: True

    """
    msbuilder = XML.SubElement(xml_parent,
                               'hudson.plugins.msbuild.MsBuildBuilder')
    XML.SubElement(msbuilder, 'msBuildName').text = data.get('msbuild-version',
                                                             '(Default)')
    XML.SubElement(msbuilder, 'msBuildFile').text = data['solution-file']
    XML.SubElement(msbuilder, 'cmdLineArgs').text = \
        data.get('extra-parameters', '')
    XML.SubElement(msbuilder, 'buildVariablesAsProperties').text = \
        str(data.get('pass-build-variables', True)).lower()
    XML.SubElement(msbuilder, 'continueOnBuildFailure').text = \
        str(data.get('continue-on-build-failure', False)).lower()


def create_builders(parser, step):
    dummy_parent = XML.Element("dummy")
    parser.registry.dispatch('builder', parser, dummy_parent, step)
    return list(dummy_parent)


def conditional_step(parser, xml_parent, data):
    """yaml: conditional_step
    Conditionaly execute some build steps.  Requires the Jenkins `Conditional
    BuildStep Plugin`_.

    Depending on the number of declared steps, a `Conditional step (single)`
    or a `Conditional steps (multiple)` is created in Jenkins.

    :arg str condition-kind: Condition kind that must be verified before the
      steps are executed. Valid values and their additional attributes are
      described in the conditions_ table.
    :arg str on-evaluation-failure: What should be the outcome of the build
      if the evaluation of the condition fails. Possible values are `fail`,
      `mark-unstable`, `run-and-mark-unstable`, `run` and `dont-run`.
      Default is `fail`.
    :arg list steps: List of steps to run if the condition is verified. Items
      in the list can be any builder known by Jenkins Job Builder.

    .. _conditions:

    ================== ====================================================
    Condition kind     Description
    ================== ====================================================
    always             Condition is always verified
    never              Condition is never verified
    boolean-expression Run the step if the expression expends to a
                       representation of true

                         :condition-expression: Expression to expand
    shell              Run the step if the shell command succeed

                         :condition-command: Shell command to execute
    windows-shell      Similar to shell, except that commands will be
                       executed by cmd, under Windows

                         :condition-command: Command to execute
    file-exists        Run the step if a file exists

                         :condition-filename: Check existence of this file
                         :condition-basedir: If condition-filename is
                           relative, it will be considered relative to
                           either `workspace`, `artifact-directory`,
                           or `jenkins-home`. Default is `workspace`.
    ================== ====================================================

    Example::

      builders:
        - conditional_step:
            condition-kind: boolean-expression
            condition-expression: "${ENV,var=IS_STABLE_BRANCH}"
            on-evaluation-failure: mark-unstable
            steps:
                - shell: "echo Making extra checks"

    .. _Conditional BuildStep Plugin: https://wiki.jenkins-ci.org/display/
        JENKINS/Conditional+BuildStep+Plugin
    """

    def build_condition(cdata):
        kind = cdata['condition-kind']
        ctag = XML.SubElement(root_tag, condition_tag)
        if kind == "always":
            ctag.set('class',
                     'org.jenkins_ci.plugins.run_condition.core.AlwaysRun')
        elif kind == "never":
            ctag.set('class',
                     'org.jenkins_ci.plugins.run_condition.core.NeverRun')
        elif kind == "boolean-expression":
            ctag.set('class',
                     'org.jenkins_ci.plugins.run_condition.core.'
                     'BooleanCondition')
            XML.SubElement(ctag, "token").text = cdata['condition-expression']
        elif kind == "shell":
            ctag.set('class',
                     'org.jenkins_ci.plugins.run_condition.contributed.'
                     'ShellCondition')
            XML.SubElement(ctag, "command").text = cdata['condition-command']
        elif kind == "windows-shell":
            ctag.set('class',
                     'org.jenkins_ci.plugins.run_condition.contributed.'
                     'BatchFileCondition')
            XML.SubElement(ctag, "command").text = cdata['condition-command']
        elif kind == "file-exists":
            ctag.set('class',
                     'org.jenkins_ci.plugins.run_condition.core.'
                     'FileExistsCondition')
            XML.SubElement(ctag, "file").text = cdata['condition-filename']
            basedir = cdata.get('condition-basedir', 'workspace')
            basedir_tag = XML.SubElement(ctag, "baseDir")
            if "workspace" == basedir:
                basedir_tag.set('class',
                                'org.jenkins_ci.plugins.run_condition.common.'
                                'BaseDirectory$Workspace')
            elif "artifact-directory" == basedir:
                basedir_tag.set('class',
                                'org.jenkins_ci.plugins.run_condition.common.'
                                'BaseDirectory$ArtifactsDir')
            elif "jenkins-home" == basedir:
                basedir_tag.set('class',
                                'org.jenkins_ci.plugins.run_condition.common.'
                                'BaseDirectory$JenkinsHome')

    def build_step(parent, step):
        for edited_node in create_builders(parser, step):
            if not has_multiple_steps:
                edited_node.set('class', edited_node.tag)
                edited_node.tag = 'buildStep'
            parent.append(edited_node)

    cond_builder_tag = 'org.jenkinsci.plugins.conditionalbuildstep.'    \
        'singlestep.SingleConditionalBuilder'
    cond_builders_tag = 'org.jenkinsci.plugins.conditionalbuildstep.'   \
        'ConditionalBuilder'
    steps = data['steps']
    has_multiple_steps = len(steps) > 1

    if has_multiple_steps:
        root_tag = XML.SubElement(xml_parent, cond_builders_tag)
        steps_parent = XML.SubElement(root_tag, "conditionalbuilders")
        condition_tag = "runCondition"
    else:
        root_tag = XML.SubElement(xml_parent, cond_builder_tag)
        steps_parent = root_tag
        condition_tag = "condition"

    build_condition(data)
    evaluation_classes_pkg = 'org.jenkins_ci.plugins.run_condition'
    evaluation_classes = {
        'fail': evaluation_classes_pkg + '.BuildStepRunner$Fail',
        'mark-unstable': evaluation_classes_pkg + '.BuildStepRunner$Unstable',
        'run-and-mark-unstable': evaluation_classes_pkg +
        'BuildStepRunner$RunUnstable',
        'run': evaluation_classes_pkg + '.BuildStepRunner$Run',
        'dont-run': evaluation_classes_pkg + 'BuildStepRunner$DontRun',
    }
    evaluation_class = evaluation_classes[data.get('on-evaluation-failure',
                                                   'fail')]
    XML.SubElement(root_tag, "runner").set('class',
                                           evaluation_class)
    for step in steps:
        build_step(steps_parent, step)


def maven_target(parser, xml_parent, data):
    """yaml: maven-target
    Execute top-level Maven targets

    :arg str goals: Goals to execute
    :arg str properties: Properties for maven, can have multiples
    :arg str pom: Location of pom.xml (defaults to pom.xml)
    :arg str maven-version: Installation of maven which should be used
      (optional)

    Example::

      builders:
        - maven-target:
            maven-version: Maven3
            pom: parent/pom.xml
            goals: clean
            properties:
              - foo=bar
              - bar=foo
    """
    maven = XML.SubElement(xml_parent, 'hudson.tasks.Maven')
    XML.SubElement(maven, 'targets').text = data['goals']
    prop_string = '\n'.join(data.get('properties', []))
    XML.SubElement(maven, 'properties').text = prop_string
    if 'maven-version' in data:
        XML.SubElement(maven, 'mavenName').text = str(data['maven-version'])
    if 'pom' in data:
        XML.SubElement(maven, 'pom').text = str(data['pom'])
    XML.SubElement(maven, 'usePrivateRepository').text = 'false'
    XML.SubElement(maven, 'settings', {
                   'class': 'jenkins.mvn.DefaultSettingsProvider'})
    XML.SubElement(maven, 'globalSettings', {
                   'class': 'jenkins.mvn.DefaultGlobalSettingsProvider'})


def multijob(parser, xml_parent, data):
    """yaml: multijob
    Define a multijob phase. Requires the Jenkins `Multijob Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/Multijob+Plugin>`_

    This builder may only be used in \
    :py:class:`jenkins_jobs.modules.project_multijob.MultiJob` projects.

    :arg str name: MultiJob phase name
    :arg str condition: when to trigger the other job (default 'SUCCESSFUL')
    :arg list projects: list of projects to include in the MultiJob phase

      :Project: * **name** (`str`) -- Project name
                * **current-parameters** (`bool`) -- Pass current build
                  parameters to the other job (default false)
                * **git-revision** (`bool`) -- Pass current git-revision
                  to the other job (default false)
                * **property-file** (`str`) -- Pass properties from file
                  to the other job (optional)
                * **predefined-parameters** (`str`) -- Pass predefined
                  parameters to the other job (optional)

    Example::

      builders:
        - multijob:
            name: PhaseOne
            condition: SUCCESSFUL
            projects:
              - name: PhaseOneJobA
                current-parameters: true
                git-revision: true
              - name: PhaseOneJobB
                current-parameters: true
                property-file: build.props
        - multijob:
            name: PhaseTwo
            condition: UNSTABLE
            projects:
              - name: PhaseTwoJobA
                current-parameters: true
                predefined-parameters: foo=bar
              - name: PhaseTwoJobB
                current-parameters: false


    """
    builder = XML.SubElement(xml_parent, 'com.tikal.jenkins.plugins.multijob.'
                                         'MultiJobBuilder')
    XML.SubElement(builder, 'phaseName').text = data['name']

    condition = data.get('condition', 'SUCCESSFUL')
    XML.SubElement(builder, 'continuationCondition').text = condition

    phaseJobs = XML.SubElement(builder, 'phaseJobs')

    for project in data.get('projects', []):
        phaseJob = XML.SubElement(phaseJobs, 'com.tikal.jenkins.plugins.'
                                             'multijob.PhaseJobsConfig')

        XML.SubElement(phaseJob, 'jobName').text = project['name']

        # Pass through the current build params
        currParams = str(project.get('current-parameters', False)).lower()
        XML.SubElement(phaseJob, 'currParams').text = currParams

        # Pass through other params
        configs = XML.SubElement(phaseJob, 'configs')

        # Git Revision
        if project.get('git-revision', False):
            param = XML.SubElement(configs,
                                   'hudson.plugins.git.'
                                   'GitRevisionBuildParameters')
            combine = XML.SubElement(param, 'combineQueuedCommits')
            combine.text = 'false'

        # Properties File
        properties_file = project.get('property-file', False)
        if properties_file:
            param = XML.SubElement(configs,
                                   'hudson.plugins.parameterizedtrigger.'
                                   'FileBuildParameters')

            propertiesFile = XML.SubElement(param, 'propertiesFile')
            propertiesFile.text = properties_file

            failOnMissing = XML.SubElement(param, 'failTriggerOnMissing')
            failOnMissing.text = 'true'

        # Predefined Parameters
        predefined_parameters = project.get('predefined-parameters', False)
        if predefined_parameters:
            param = XML.SubElement(configs,
                                   'hudson.plugins.parameterizedtrigger.'
                                   'PredefinedBuildParameters')
            properties = XML.SubElement(param, 'properties')
            properties.text = predefined_parameters


def grails(parser, xml_parent, data):
    """yaml: grails
    Execute a grails build step. Requires the `Jenkins Grails Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/Grails+Plugin>`_

    :arg bool use-wrapper: Use a grails wrapper (default false)
    :arg str name: Select a grails installation to use (optional)
    :arg bool force-upgrade: Run 'grails upgrade --non-interactive'
                             first (default false)
    :arg bool non-interactive: append --non-interactive to all build targets
                               (default false)
    :arg str targets: Specify target(s) to run separated by spaces
    :arg str server-port: Specify a value for the server.port system
                          property (optional)
    :arg str work-dir: Specify a value for the grails.work.dir system
                       property (optional)
    :arg str project-dir: Specify a value for the grails.project.work.dir
                          system property (optional)
    :arg str base-dir: Specify a path to the root of the Grails
                       project (optional)
    :arg str properties: Additional system properties to set (optional)
    :arg bool plain-output: append --plain-output to all build targets
                            (default false)
    :arg bool stack-trace: append --stack-trace to all build targets
                           (default false)
    :arg bool verbose: append --verbose to all build targets
                       (default false)
    :arg bool refresh-dependencies: append --refresh-dependencies to all
                                    build targets (default false)

    Example::

      builders:
        - grails:
            use-wrapper: "true"
            name: "grails-2.2.2"
            force-upgrade: "true"
            non-interactive: "true"
            targets: "war ear"
            server-port: "8003"
            work-dir: "./grails-work"
            project-dir: "./project-work"
            base-dir: "./grails/project"
            properties: "program.name=foo"
            plain-output: "true"
            stack-trace: "true"
            verbose: "true"
            refresh-dependencies: "true"


    """
    grails = XML.SubElement(xml_parent, 'com.g2one.hudson.grails.'
                                        'GrailsBuilder')
    XML.SubElement(grails, 'targets').text = data['targets']
    XML.SubElement(grails, 'name').text = data.get(
        'name', '(Default)')
    XML.SubElement(grails, 'grailsWorkDir').text = data.get(
        'work-dir', '')
    XML.SubElement(grails, 'projectWorkDir').text = data.get(
        'project-dir', '')
    XML.SubElement(grails, 'projectBaseDir').text = data.get(
        'base-dir', '')
    XML.SubElement(grails, 'serverPort').text = data.get(
        'server-port', '')
    XML.SubElement(grails, 'properties').text = data.get(
        'properties', '')
    XML.SubElement(grails, 'forceUpgrade').text = str(
        data.get('force-upgrade', 'false')).lower()
    XML.SubElement(grails, 'nonInteractive').text = str(
        data.get('non-interactive', 'false')).lower()
    XML.SubElement(grails, 'useWrapper').text = str(
        data.get('use-wrapper', 'false')).lower()
    XML.SubElement(grails, 'plainOutput').text = str(
        data.get('plain-output', 'false')).lower()
    XML.SubElement(grails, 'stackTrace').text = str(
        data.get('stack-trace', 'false')).lower()
    XML.SubElement(grails, 'verbose').text = str(
        data.get('verbose', 'false')).lower()
    XML.SubElement(grails, 'refreshDependencies').text = str(
        data.get('refresh-dependencies', 'false')).lower()


class Builders(jenkins_jobs.modules.base.Base):
    sequence = 60

    component_type = 'builder'
    component_list_type = 'builders'

    def gen_xml(self, parser, xml_parent, data):

        for alias in ['prebuilders', 'builders', 'postbuilders']:
            if alias in data:
                builders = XML.SubElement(xml_parent, alias)
                for builder in data[alias]:
                    self.registry.dispatch('builder', parser, builders,
                                           builder)

        # Make sure freestyle projects always have a <builders> entry
        # or Jenkins v1.472 (at least) will NPE.
        project_type = data.get('project-type', 'freestyle')
        if project_type in ('freestyle', 'matrix') and 'builders' not in data:
            XML.SubElement(xml_parent, 'builders')
