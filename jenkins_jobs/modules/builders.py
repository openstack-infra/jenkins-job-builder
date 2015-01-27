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
from jenkins_jobs.modules import hudson_model
from jenkins_jobs.modules.helpers import config_file_provider_builder
from jenkins_jobs.modules.helpers import config_file_provider_settings
from jenkins_jobs.errors import (JenkinsJobsException,
                                 MissingAttributeError,
                                 InvalidAttributeError)
import logging

logger = logging.getLogger(__name__)


def shell(parser, xml_parent, data):
    """yaml: shell
    Execute a shell command.

    :arg str parameter: the shell command to execute

    Example:

    .. literalinclude:: /../../tests/builders/fixtures/shell.yaml
       :language: yaml

    """
    shell = XML.SubElement(xml_parent, 'hudson.tasks.Shell')
    XML.SubElement(shell, 'command').text = data


def python(parser, xml_parent, data):
    """yaml: python
    Execute a python command. Requires the Jenkins :jenkins-wiki:`Python plugin
    <Python+Plugin>`.

    :arg str parameter: the python command to execute

    Example:

    .. literalinclude:: /../../tests/builders/fixtures/python.yaml
       :language: yaml

    """
    python = XML.SubElement(xml_parent, 'hudson.plugins.python.Python')
    XML.SubElement(python, 'command').text = data


def copyartifact(parser, xml_parent, data):
    """yaml: copyartifact

    Copy artifact from another project. Requires the :jenkins-wiki:`Copy
    Artifact plugin <Copy+Artifact+Plugin>`.

    :arg str project: Project to copy from
    :arg str filter: what files to copy
    :arg str target: Target base directory for copy, blank means use workspace
    :arg bool flatten: Flatten directories (default: false)
    :arg bool optional: If the artifact is missing (for any reason) and
        optional is true, the build won't fail because of this builder
        (default: false)
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
    :arg string parameter-filters: Filter matching jobs based on these
        parameters (optional)
    :which-build values:
      * **last-successful**
      * **last-completed**
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


    Example:

    .. literalinclude:: ../../tests/builders/fixtures/copy-artifact001.yaml
       :language: yaml
    """
    t = XML.SubElement(xml_parent, 'hudson.plugins.copyartifact.CopyArtifact')
    # Warning: this only works with copy artifact version 1.26+,
    # for copy artifact version 1.25- the 'projectName' element needs
    # to be used instead of 'project'
    XML.SubElement(t, 'project').text = data["project"]
    XML.SubElement(t, 'filter').text = data.get("filter", "")
    XML.SubElement(t, 'target').text = data.get("target", "")
    flatten = data.get("flatten", False)
    XML.SubElement(t, 'flatten').text = str(flatten).lower()
    optional = data.get('optional', False)
    XML.SubElement(t, 'optional').text = str(optional).lower()
    XML.SubElement(t, 'parameters').text = data.get("parameter-filters", "")
    select = data.get('which-build', 'last-successful')
    selectdict = {'last-successful': 'StatusBuildSelector',
                  'last-completed': 'LastCompletedBuildSelector',
                  'specific-build': 'SpecificBuildSelector',
                  'last-saved': 'SavedBuildSelector',
                  'upstream-build': 'TriggeredBuildSelector',
                  'permalink': 'PermalinkBuildSelector',
                  'workspace-latest': 'WorkspaceSelector',
                  'build-param': 'ParameterizedBuildSelector'}
    if select not in selectdict:
        raise InvalidAttributeError('which-build',
                                    select,
                                    selectdict.keys())
    permalink = data.get('permalink', 'last')
    permalinkdict = {'last': 'lastBuild',
                     'last-stable': 'lastStableBuild',
                     'last-successful': 'lastSuccessfulBuild',
                     'last-failed': 'lastFailedBuild',
                     'last-unstable': 'lastUnstableBuild',
                     'last-unsuccessful': 'lastUnsuccessfulBuild'}
    if permalink not in permalinkdict:
        raise InvalidAttributeError('permalink',
                                    permalink,
                                    permalinkdict.keys())
    selector = XML.SubElement(t, 'selector',
                              {'class': 'hudson.plugins.copyartifact.' +
                               selectdict[select]})
    if select == 'specific-build':
        XML.SubElement(selector, 'buildNumber').text = data['build-number']
    if select == 'last-successful':
        XML.SubElement(selector, 'stable').text = str(
            data.get('stable', False)).lower()
    if select == 'upstream-build':
        XML.SubElement(selector, 'fallbackToLastSuccessful').text = str(
            data.get('fallback-to-last-successful', False)).lower()
    if select == 'permalink':
        XML.SubElement(selector, 'id').text = permalinkdict[permalink]
    if select == 'build-param':
        XML.SubElement(selector, 'parameterName').text = data['param']


def change_assembly_version(parser, xml_parent, data):
    """yaml: change-assembly-version
    Change the assembly version.
    Requires the Jenkins :jenkins-wiki:`Change Assembly Version
    <Change+Assembly+Version>`.

    :arg str version: Set the new version number for replace (default 1.0.0)
    :arg str assemblyFile: The file name to search (default AssemblyInfo.cs)

    Example:

    .. literalinclude:: \
    /../../tests/builders/fixtures/changeassemblyversion001.yaml
       :language: yaml
    """

    cav_builder_tag = 'org.jenkinsci.plugins.changeassemblyversion.' \
        'ChangeAssemblyVersion'
    cav = XML.SubElement(xml_parent, cav_builder_tag)
    XML.SubElement(cav, 'task').text = data.get('version', '1.0.0')
    XML.SubElement(cav, 'assemblyFile').text = str(
        data.get('assembly-file', 'AssemblyInfo.cs'))


def ant(parser, xml_parent, data):
    """yaml: ant
    Execute an ant target. Requires the Jenkins :jenkins-wiki:`Ant Plugin
    <Ant+Plugin>`.

    To setup this builder you can either reference the list of targets
    or use named parameters. Below is a description of both forms:

    *1) Listing targets:*

    After the ant directive, simply pass as argument a space separated list
    of targets to build.

    :Parameter: space separated list of Ant targets

    Example to call two Ant targets:

    .. literalinclude:: ../../tests/builders/fixtures/ant001.yaml
       :language: yaml

    The build file would be whatever the Jenkins Ant Plugin is set to use
    per default (i.e build.xml in the workspace root).

    *2) Using named parameters:*

    :arg str targets: the space separated list of ANT targets.
    :arg str buildfile: the path to the ANT build file.
    :arg list properties: Passed to ant script using -Dkey=value (optional)
    :arg str ant-name: the name of the ant installation,
        (default 'default') (optional)
    :arg str java-opts: java options for ant, can have multiples,
        must be in quotes (optional)


    Example specifying the build file too and several targets:

    .. literalinclude:: ../../tests/builders/fixtures/ant002.yaml
       :language: yaml
    """
    ant = XML.SubElement(xml_parent, 'hudson.tasks.Ant')

    if type(data) is str:
        # Support for short form: -ant: "target"
        data = {'targets': data}
    for setting, value in sorted(data.items()):
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


def trigger_remote(parser, xml_parent, data):
    """yaml: trigger-remote
    Trigger build of job on remote Jenkins instance.

    :jenkins-wiki:`Parameterized Remote Trigger Plugin
    <Parameterized+Remote+Trigger+Plugin>`

    Please note that this plugin requires system configuration on the Jenkins
    Master that is unavailable from individual job views; specifically, one
    must add remote jenkins servers whose 'Display Name' field are what make up
    valid fields on the `remote-jenkins-name` attribute below.

    :arg str remote-jenkins-name: the remote Jenkins server (required)
    :arg str job: the Jenkins project to trigger on the remote Jenkins server
      (required)
    :arg bool should-not-fail-build:
      if true, remote job failure will not lead current job to fail
      (default false)
    :arg bool prevent-remote-build-queue:
      if true, wait to trigger remote builds until no other builds
      (default false)
    :arg bool block: whether to wait for the trigger jobs to finish or not
      (default true)
    :arg str poll-interval: polling interval in seconds for checking statues of
      triggered remote job, only necessary if current job is configured to
      block
      (default 10)
    :arg str connection-retry-limit: number of connection attempts to remote
      Jenkins server before giving up.
      (default 5)
    :arg str predefined-parameters: predefined parameters to send to the remote
      job when triggering it
      (optional)
    :arg str property-file: file in workspace of current job containing
      additional parameters to be set on remote job
      (optional)

    Example:

    .. literalinclude:: \
    /../../tests/builders/fixtures/trigger-remote/trigger-remote001.yaml
       :language: yaml
    """
    triggerr = XML.SubElement(xml_parent,
                              'org.jenkinsci.plugins.'
                              'ParameterizedRemoteTrigger.'
                              'RemoteBuildConfiguration')
    XML.SubElement(triggerr,
                   'remoteJenkinsName').text = data.get('remote-jenkins-name')
    XML.SubElement(triggerr, 'token').text = data.get('token', '')

    for attribute in ['job', 'remote-jenkins-name']:
        if attribute not in data:
            raise MissingAttributeError(attribute, "builders.trigger-remote")
        if data[attribute] == '':
            raise InvalidAttributeError(attribute,
                                        data[attribute],
                                        "builders.trigger-remote")

    XML.SubElement(triggerr, 'job').text = data.get('job')

    XML.SubElement(triggerr, 'shouldNotFailBuild').text = str(
        data.get('should-not-fail-build', False)).lower()

    XML.SubElement(triggerr,
                   'pollInterval').text = str(data.get('poll-interval', 10))
    XML.SubElement(triggerr, 'connectionRetryLimit').text = str(
        data.get('connection-retry-limit', 5))

    XML.SubElement(triggerr, 'preventRemoteBuildQueue').text = str(
        data.get('prevent-remote-build-queue', False)).lower()

    XML.SubElement(triggerr, 'blockBuildUntilComplete').text = str(
        data.get('block', True)).lower()

    if 'predefined-parameters' in data:
        parameters = XML.SubElement(triggerr, 'parameters')
        parameters.text = data.get('predefined-parameters', '')
        params_list = parameters.text.split("\n")

        parameter_list = XML.SubElement(triggerr, 'parameterList')
        for param in params_list:
            if param == '':
                continue
            tmp = XML.SubElement(parameter_list, 'string')
            tmp.text = param

    if 'property-file' in data and data['property-file'] != '':
        XML.SubElement(triggerr, 'loadParamsFromFile').text = 'true'
        XML.SubElement(triggerr,
                       'parameterFile').text = data.get('property-file')
    else:
        XML.SubElement(triggerr, 'loadParamsFromFile').text = 'false'

    XML.SubElement(triggerr, 'overrideAuth').text = "false"


def trigger_builds(parser, xml_parent, data):
    """yaml: trigger-builds
    Trigger builds of other jobs.
    Requires the Jenkins :jenkins-wiki:`Parameterized Trigger Plugin
    <Parameterized+Trigger+Plugin>`.

    :arg list project: the Jenkins project to trigger
    :arg str predefined-parameters:
      key/value pairs to be passed to the job (optional)
    :arg list bool-parameters:

      :Bool: * **name** (`str`) -- Parameter name
             * **value** (`bool`) -- Value to set (default false)

    :arg str property-file:
      Pass properties from file to the other job (optional)
    :arg bool property-file-fail-on-missing:
      Don't trigger if any files are missing (optional)
      (default true)
    :arg bool current-parameters: Whether to include the
      parameters passed to the current build to the
      triggered job.
    :arg str node-label-name: Define a name for the NodeLabel parameter to be
      set. Used in conjunction with node-label. Requires NodeLabel Parameter
      Plugin (optional)
    :arg str node-label: Label of the nodes where build should be triggered.
      Used in conjunction with node-label-name.  Requires NodeLabel Parameter
      Plugin (optional)
    :arg bool svn-revision: Whether to pass the svn revision
      to the triggered job
    :arg bool git-revision: Whether to pass the git revision
      to the triggered job
    :arg bool block: whether to wait for the triggered jobs
      to finish or not (default false)
    :arg dict block-thresholds: Fail builds and/or mark as failed or unstable
      based on thresholds. Only apply if block parameter is true (optional)

      * **build-step-failure-threshold** (`str`)
        ['never', 'SUCCESS', 'UNSTABLE', 'FAILURE'] (default: 'FAILURE')
      * **unstable-threshold** (`str`)
        ['never', 'SUCCESS', 'UNSTABLE', 'FAILURE'] (default: 'UNSTABLE')
      * **failure-threshold** (`str`)
        ['never', 'SUCCESS', 'UNSTABLE', 'FAILURE'] (default: 'FAILURE')

    :arg bool same-node: Use the same node for the triggered builds that was
      used for this build (optional)
    :arg list parameter-factories: list of parameter factories

      :Factory: * **factory** (`str`) **filebuild** -- For every property file,
                  invoke one build
                * **file-pattern** (`str`) -- File wildcard pattern
                * **no-files-found-action** (`str`) -- Action to perform when
                  no files found  (optional) ['FAIL', 'SKIP', 'NOPARMS']
                  (default 'SKIP')

      :Factory: * **factory** (`str`) **binaryfile** -- For every matching
                  file, invoke one build
                * **file-pattern** (`str`) -- Artifact ID of the artifact
                * **no-files-found-action** (`str`) -- Action to perform when
                  no files found  (optional) ['FAIL', 'SKIP', 'NOPARMS']
                  (default 'SKIP')

      :Factory: * **factory** (`str`) **counterbuild** -- Invoke i=0...N builds
                * **from** (`int`) -- Artifact ID of the artifact
                * **to** (`int`) -- Version of the artifact
                * **step** (`int`) -- Classifier of the artifact
                * **parameters** (`str`) -- KEY=value pairs, one per line
                  (default '')
                * **validation-fail** (`str`) -- Action to perform when
                  stepping validation fails  (optional)
                  ['FAIL', 'SKIP', 'NOPARMS']
                  (default 'FAIL')

      :Factory: * **factory** (`str`) **allnodesforlabel** -- Trigger a build
                  on all nodes having specific label. Requires NodeLabel
                  Parameter Plugin (optional)
                * **name** (`str`) -- Name of the parameter to set (optional)
                * **node-label** (`str`) -- Label of the nodes where build
                  should be triggered
                * **ignore-offline-nodes** (`bool`) -- Don't trigger build on
                  offline nodes (optional)
                  (default true)

    Examples:

    Basic usage with yaml list of projects.

    .. literalinclude::
       /../../tests/builders/fixtures/trigger-builds/project-list.yaml
       :language: yaml

    Basic usage with passing svn revision through.

    .. literalinclude:: /../../tests/builders/fixtures/trigger-builds001.yaml
       :language: yaml

    Basic usage with passing git revision through.

    .. literalinclude:: /../../tests/builders/fixtures/trigger-builds006.yaml
       :language: yaml

    Example with all supported parameter factories.

    .. literalinclude:: \
    /../../tests/builders/fixtures/trigger-builds-configfactory-multi.yaml
       :language: yaml
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
        if(project_def.get('git-revision')):
            params = XML.SubElement(tconfigs,
                                    'hudson.plugins.git.'
                                    'GitRevisionBuildParameters')
            combine = XML.SubElement(params, 'combineQueuedCommits')
            combine.text = 'false'
        if(project_def.get('same-node')):
            XML.SubElement(tconfigs,
                           'hudson.plugins.parameterizedtrigger.'
                           'NodeParameters')
        if 'property-file' in project_def:
            params = XML.SubElement(tconfigs,
                                    'hudson.plugins.parameterizedtrigger.'
                                    'FileBuildParameters')
            propertiesFile = XML.SubElement(params, 'propertiesFile')
            propertiesFile.text = project_def['property-file']
            failTriggerOnMissing = XML.SubElement(params,
                                                  'failTriggerOnMissing')
            failTriggerOnMissing.text = str(project_def.get(
                'property-file-fail-on-missing', True)).lower()

        if 'predefined-parameters' in project_def:
            params = XML.SubElement(tconfigs,
                                    'hudson.plugins.parameterizedtrigger.'
                                    'PredefinedBuildParameters')
            properties = XML.SubElement(params, 'properties')
            properties.text = project_def['predefined-parameters']

        if 'bool-parameters' in project_def:
            params = XML.SubElement(tconfigs,
                                    'hudson.plugins.parameterizedtrigger.'
                                    'BooleanParameters')
            configs = XML.SubElement(params, 'configs')
            for bool_param in project_def['bool-parameters']:
                param = XML.SubElement(configs,
                                       'hudson.plugins.parameterizedtrigger.'
                                       'BooleanParameterConfig')
                XML.SubElement(param, 'name').text = str(bool_param['name'])
                XML.SubElement(param, 'value').text = str(
                    bool_param.get('value', False)).lower()

        if 'node-label-name' in project_def and 'node-label' in project_def:
            node = XML.SubElement(tconfigs, 'org.jvnet.jenkins.plugins.'
                                  'nodelabelparameter.parameterizedtrigger.'
                                  'NodeLabelBuildParameter')
            XML.SubElement(node, 'name').text = \
                project_def.get('node-label-name')
            XML.SubElement(node, 'nodeLabel').text = \
                project_def.get('node-label')

        if(len(list(tconfigs)) == 0):
            tconfigs.set('class', 'java.util.Collections$EmptyList')

        if 'parameter-factories' in project_def:
            fconfigs = XML.SubElement(tconfig, 'configFactories')

            supported_factories = ['filebuild',
                                   'binaryfile',
                                   'counterbuild',
                                   'allnodesforlabel']
            supported_actions = ['SKIP', 'NOPARMS', 'FAIL']
            for factory in project_def['parameter-factories']:

                if factory['factory'] not in supported_factories:
                    raise InvalidAttributeError('factory',
                                                factory['factory'],
                                                supported_factories)

                if factory['factory'] == 'filebuild':
                    params = XML.SubElement(
                        fconfigs,
                        'hudson.plugins.parameterizedtrigger.'
                        'FileBuildParameterFactory')
                if factory['factory'] == 'binaryfile':
                    params = XML.SubElement(
                        fconfigs,
                        'hudson.plugins.parameterizedtrigger.'
                        'BinaryFileParameterFactory')
                    parameterName = XML.SubElement(params, 'parameterName')
                    parameterName.text = factory['parameter-name']
                if (factory['factory'] == 'filebuild' or
                        factory['factory'] == 'binaryfile'):
                    filePattern = XML.SubElement(params, 'filePattern')
                    filePattern.text = factory['file-pattern']
                    noFilesFoundAction = XML.SubElement(
                        params,
                        'noFilesFoundAction')
                    noFilesFoundActionValue = str(factory.get(
                        'no-files-found-action', 'SKIP'))
                    if noFilesFoundActionValue not in supported_actions:
                        raise InvalidAttributeError('no-files-found-action',
                                                    noFilesFoundActionValue,
                                                    supported_actions)
                    noFilesFoundAction.text = noFilesFoundActionValue
                if factory['factory'] == 'counterbuild':
                    params = XML.SubElement(
                        fconfigs,
                        'hudson.plugins.parameterizedtrigger.'
                        'CounterBuildParameterFactory')
                    fromProperty = XML.SubElement(params, 'from')
                    fromProperty.text = str(factory['from'])
                    toProperty = XML.SubElement(params, 'to')
                    toProperty.text = str(factory['to'])
                    stepProperty = XML.SubElement(params, 'step')
                    stepProperty.text = str(factory['step'])
                    paramExpr = XML.SubElement(params, 'paramExpr')
                    paramExpr.text = str(factory.get(
                        'parameters', ''))
                    validationFail = XML.SubElement(params, 'validationFail')
                    validationFailValue = str(factory.get(
                        'validation-fail', 'FAIL'))
                    if validationFailValue not in supported_actions:
                        raise InvalidAttributeError('validation-fail',
                                                    validationFailValue,
                                                    supported_actions)
                    validationFail.text = validationFailValue
                if factory['factory'] == 'allnodesforlabel':
                    params = XML.SubElement(
                        fconfigs,
                        'org.jvnet.jenkins.plugins.nodelabelparameter.'
                        'parameterizedtrigger.'
                        'AllNodesForLabelBuildParameterFactory')
                    nameProperty = XML.SubElement(params, 'name')
                    nameProperty.text = str(factory.get(
                        'name', ''))
                    nodeLabel = XML.SubElement(params, 'nodeLabel')
                    nodeLabel.text = str(factory['node-label'])
                    ignoreOfflineNodes = XML.SubElement(
                        params,
                        'ignoreOfflineNodes')
                    ignoreOfflineNodes.text = str(factory.get(
                        'ignore-offline-nodes', True)).lower()

        projects = XML.SubElement(tconfig, 'projects')
        if isinstance(project_def['project'], list):
            projects.text = ",".join(project_def['project'])
        else:
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
        if block:
            block = XML.SubElement(tconfig, 'block')
            supported_thresholds = [['build-step-failure-threshold',
                                     'buildStepFailureThreshold',
                                     'FAILURE'],
                                    ['unstable-threshold',
                                     'unstableThreshold',
                                     'UNSTABLE'],
                                    ['failure-threshold',
                                     'failureThreshold',
                                     'FAILURE']]
            supported_threshold_values = ['never',
                                          hudson_model.SUCCESS['name'],
                                          hudson_model.UNSTABLE['name'],
                                          hudson_model.FAILURE['name']]
            thrsh = project_def.get('block-thresholds', False)
            for toptname, txmltag, tvalue in supported_thresholds:
                if thrsh:
                    tvalue = thrsh.get(toptname, tvalue)
                if tvalue.lower() == supported_threshold_values[0]:
                    continue
                if tvalue.upper() not in supported_threshold_values:
                    raise InvalidAttributeError(toptname,
                                                tvalue,
                                                supported_threshold_values)
                th = XML.SubElement(block, txmltag)
                XML.SubElement(th, 'name').text = hudson_model.THRESHOLDS[
                    tvalue.upper()]['name']
                XML.SubElement(th, 'ordinal').text = hudson_model.THRESHOLDS[
                    tvalue.upper()]['ordinal']
                XML.SubElement(th, 'color').text = hudson_model.THRESHOLDS[
                    tvalue.upper()]['color']
                XML.SubElement(th, 'completeBuild').text = "true"

    # If configs is empty, remove the entire tbuilder tree.
    if(len(configs) == 0):
        logger.debug("Pruning empty TriggerBuilder tree.")
        xml_parent.remove(tbuilder)


def builders_from(parser, xml_parent, data):
    """yaml: builders-from
    Use builders from another project.
    Requires the Jenkins :jenkins-wiki:`Template Project Plugin
    <Template+Project+Plugin>`.

    :arg str projectName: the name of the other project

    Example:

    .. literalinclude:: ../../tests/builders/fixtures/builders-from.yaml
       :language: yaml
    """
    pbs = XML.SubElement(xml_parent,
                         'hudson.plugins.templateproject.ProxyBuilder')
    XML.SubElement(pbs, 'projectName').text = data


def inject(parser, xml_parent, data):
    """yaml: inject
    Inject an environment for the job.
    Requires the Jenkins :jenkins-wiki:`EnvInject Plugin
    <EnvInject+Plugin>`.

    :arg str properties-file: the name of the property file (optional)
    :arg str properties-content: the properties content (optional)
    :arg str script-file: the name of a script file to run (optional)
    :arg str script-content: the script content (optional)

    Example:

    .. literalinclude:: ../../tests/builders/fixtures/inject.yaml
       :language: yaml
    """
    eib = XML.SubElement(xml_parent, 'EnvInjectBuilder')
    info = XML.SubElement(eib, 'info')
    jenkins_jobs.modules.base.add_nonblank_xml_subelement(
        info, 'propertiesFilePath', data.get('properties-file'))
    jenkins_jobs.modules.base.add_nonblank_xml_subelement(
        info, 'propertiesContent', data.get('properties-content'))
    jenkins_jobs.modules.base.add_nonblank_xml_subelement(
        info, 'scriptFilePath', data.get('script-file'))
    jenkins_jobs.modules.base.add_nonblank_xml_subelement(
        info, 'scriptContent', data.get('script-content'))


def artifact_resolver(parser, xml_parent, data):
    """yaml: artifact-resolver
    Allows one to resolve artifacts from a maven repository like nexus
    (without having maven installed)
    Requires the Jenkins :jenkins-wiki:`Repository Connector Plugin
    <Repository+Connector+Plugin>`.

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

    Example:

    .. literalinclude:: ../../tests/builders/fixtures/artifact-resolver.yaml
       :language: yaml
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
    Execute gradle tasks. Requires the Jenkins :jenkins-wiki:`Gradle Plugin
    <Gradle+Plugin>`.

    :arg str tasks: List of tasks to execute
    :arg str gradle-name: Use a custom gradle name (optional)
    :arg bool wrapper: use gradle wrapper (default false)
    :arg bool executable: make gradlew executable (default false)
    :arg list switches: Switches for gradle, can have multiples
    :arg bool use-root-dir: Whether to run the gradle script from the
        top level directory or from a different location (default false)
    :arg str root-build-script-dir: If your workspace has the
        top-level build.gradle in somewhere other than the module
        root directory, specify the path (relative to the module
        root) here, such as ${workspace}/parent/ instead of just
        ${workspace}.

    Example:

    .. literalinclude:: ../../tests/builders/fixtures/gradle.yaml
       :language: yaml
    """
    gradle = XML.SubElement(xml_parent, 'hudson.plugins.gradle.Gradle')
    XML.SubElement(gradle, 'description').text = ''
    XML.SubElement(gradle, 'tasks').text = data['tasks']
    XML.SubElement(gradle, 'buildFile').text = ''
    XML.SubElement(gradle, 'rootBuildScriptDir').text = data.get(
        'root-build-script-dir', '')
    XML.SubElement(gradle, 'gradleName').text = data.get(
        'gradle-name', '')
    XML.SubElement(gradle, 'useWrapper').text = str(data.get(
        'wrapper', False)).lower()
    XML.SubElement(gradle, 'makeExecutable').text = str(data.get(
        'executable', False)).lower()
    switch_string = '\n'.join(data.get('switches', []))
    XML.SubElement(gradle, 'switches').text = switch_string
    XML.SubElement(gradle, 'fromRootBuildScriptDir').text = str(data.get(
        'use-root-dir', False)).lower()


def _groovy_common_scriptSource(data):
    """Helper function to generate the XML element common to groovy builders
    """

    scriptSource = XML.Element("scriptSource")
    if 'command' in data and 'file' in data:
        raise JenkinsJobsException("Use just one of 'command' or 'file'")

    if 'command' in data:
        command = XML.SubElement(scriptSource, 'command')
        command.text = str(data['command'])
        scriptSource.set('class', 'hudson.plugins.groovy.StringScriptSource')
    elif 'file' in data:
        scriptFile = XML.SubElement(scriptSource, 'scriptFile')
        scriptFile.text = str(data['file'])
        scriptSource.set('class', 'hudson.plugins.groovy.FileScriptSource')
    else:
        raise JenkinsJobsException("A groovy command or file is required")

    return scriptSource


def groovy(parser, xml_parent, data):
    """yaml: groovy
    Execute a groovy script or command.
    Requires the Jenkins :jenkins-wiki:`Groovy Plugin <Groovy+plugin>`.

    :arg str file: Groovy file to run.
      (Alternative: you can chose a command instead)
    :arg str command: Groovy command to run.
      (Alternative: you can chose a script file instead)
    :arg str version: Groovy version to use. (default '(Default)')
    :arg str parameters: Parameters for the Groovy executable. (optional)
    :arg str script-parameters: These parameters will be passed to the script.
      (optional)
    :arg str properties: Instead of passing properties using the -D parameter
      you can define them here. (optional)
    :arg str java-opts: Direct access to JAVA_OPTS. Properties allows only
      -D properties, while sometimes also other properties like -XX need to
      be setup. It can be done here. This line is appended at the end of
      JAVA_OPTS string. (optional)
    :arg str class-path: Specify script classpath here. Each line is one
      class path item. (optional)

    Examples:

    .. literalinclude:: ../../tests/builders/fixtures/groovy001.yaml
       :language: yaml
    .. literalinclude:: ../../tests/builders/fixtures/groovy002.yaml
       :language: yaml
    """

    root_tag = 'hudson.plugins.groovy.Groovy'
    groovy = XML.SubElement(xml_parent, root_tag)

    groovy.append(_groovy_common_scriptSource(data))
    XML.SubElement(groovy, 'groovyName').text = \
        str(data.get('version', "(Default)"))
    XML.SubElement(groovy, 'parameters').text = str(data.get('parameters', ""))
    XML.SubElement(groovy, 'scriptParameters').text = \
        str(data.get('script-parameters', ""))
    XML.SubElement(groovy, 'properties').text = str(data.get('properties', ""))
    XML.SubElement(groovy, 'javaOpts').text = str(data.get('java-opts', ""))
    XML.SubElement(groovy, 'classPath').text = str(data.get('class-path', ""))


def system_groovy(parser, xml_parent, data):
    """yaml: system-groovy
    Execute a system groovy script or command.
    Requires the Jenkins :jenkins-wiki:`Groovy Plugin <Groovy+plugin>`.

    :arg str file: Groovy file to run.
      (Alternative: you can chose a command instead)
    :arg str command: Groovy command to run.
      (Alternative: you can chose a script file instead)
    :arg str bindings: Define variable bindings (in the properties file
      format). Specified variables can be addressed from the script. (optional)
    :arg str class-path: Specify script classpath here. Each line is one class
      path item. (optional)

    Examples:

    .. literalinclude:: ../../tests/builders/fixtures/system-groovy001.yaml
       :language: yaml
    .. literalinclude:: ../../tests/builders/fixtures/system-groovy002.yaml
       :language: yaml
    """

    root_tag = 'hudson.plugins.groovy.SystemGroovy'
    sysgroovy = XML.SubElement(xml_parent, root_tag)
    sysgroovy.append(_groovy_common_scriptSource(data))
    XML.SubElement(sysgroovy, 'bindings').text = str(data.get('bindings', ""))
    XML.SubElement(sysgroovy, 'classpath').text = \
        str(data.get('class-path', ""))


def batch(parser, xml_parent, data):
    """yaml: batch
    Execute a batch command.

    :Parameter: the batch command to execute

    Example:

    .. literalinclude:: ../../tests/builders/fixtures/batch.yaml
       :language: yaml
    """
    batch = XML.SubElement(xml_parent, 'hudson.tasks.BatchFile')
    XML.SubElement(batch, 'command').text = data


def powershell(parser, xml_parent, data):
    """yaml: powershell
    Execute a powershell command. Requires the :jenkins-wiki:`Powershell Plugin
    <PowerShell+Plugin>`.

    :Parameter: the powershell command to execute

    Example:

    .. literalinclude:: ../../tests/builders/fixtures/powershell.yaml
       :language: yaml
    """
    ps = XML.SubElement(xml_parent, 'hudson.plugins.powershell.PowerShell')
    XML.SubElement(ps, 'command').text = data


def msbuild(parser, xml_parent, data):
    """yaml: msbuild
    Build .NET project using msbuild. Requires the :jenkins-wiki:`Jenkins
    MSBuild Plugin <MSBuild+Plugin>`.

    :arg str msbuild-version: which msbuild configured in Jenkins to use
      (optional)
    :arg str solution-file: location of the solution file to build
    :arg str extra-parameters: extra parameters to pass to msbuild (optional)
    :arg bool pass-build-variables: should build variables be passed
      to msbuild (default true)
    :arg bool continue-on-build-failure: should the build continue if
      msbuild returns an error (default false)

    Example:

    .. literalinclude:: ../../tests/builders/fixtures/msbuild.yaml
       :language: yaml
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
    """yaml: conditional-step
    Conditionally execute some build steps. Requires the Jenkins
    :jenkins-wiki:`Conditional BuildStep Plugin
    <Conditional+BuildStep+Plugin>`.

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
    strings-match      Run the step if two strings match

                         :condition-string1: First string
                         :condition-string2: Second string
                         :condition-case-insensitive: Case insensitive
                           defaults to false
    current-status     Run the build step if the current build status is
                       within the configured range

                         :condition-worst: Accepted values are SUCCESS,
                           UNSTABLE, FAILURE, NOT_BUILD, ABORTED
                         :condition-best: Accepted values are SUCCESS,
                           UNSTABLE, FAILURE, NOT_BUILD, ABORTED

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
    not                Run the step if the inverse of the condition-operand
                       is true

                         :condition-operand: Condition to evaluate.  Can be
                           any supported conditional-step condition.
    ================== ====================================================

    Example:

    .. literalinclude:: \
    /../../tests/builders/fixtures/conditional-step-success-failure.yaml
       :language: yaml
    .. literalinclude:: \
    /../../tests/builders/fixtures/conditional-step-not-file-exists.yaml
       :language: yaml
    """
    def build_condition(cdata, cond_root_tag):
        kind = cdata['condition-kind']
        ctag = XML.SubElement(cond_root_tag, condition_tag)
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
        elif kind == "strings-match":
            ctag.set('class',
                     'org.jenkins_ci.plugins.run_condition.core.'
                     'StringsMatchCondition')
            XML.SubElement(ctag, "arg1").text = cdata['condition-string1']
            XML.SubElement(ctag, "arg2").text = cdata['condition-string2']
            XML.SubElement(ctag, "ignoreCase").text = str(cdata.get(
                'condition-case-insensitive', False)).lower()
        elif kind == "current-status":
            ctag.set('class',
                     'org.jenkins_ci.plugins.run_condition.core.'
                     'StatusCondition')
            wr = XML.SubElement(ctag, 'worstResult')
            wr_name = cdata['condition-worst']
            if wr_name not in hudson_model.THRESHOLDS:
                raise JenkinsJobsException(
                    "threshold must be one of %s" %
                    ", ".join(hudson_model.THRESHOLDS.keys()))
            wr_threshold = hudson_model.THRESHOLDS[wr_name]
            XML.SubElement(wr, "name").text = wr_threshold['name']
            XML.SubElement(wr, "ordinal").text = wr_threshold['ordinal']
            XML.SubElement(wr, "color").text = wr_threshold['color']
            XML.SubElement(wr, "completeBuild").text = \
                str(wr_threshold['complete']).lower()

            br = XML.SubElement(ctag, 'bestResult')
            br_name = cdata['condition-best']
            if br_name not in hudson_model.THRESHOLDS:
                raise JenkinsJobsException(
                    "threshold must be one of %s" %
                    ", ".join(hudson_model.THRESHOLDS.keys()))
            br_threshold = hudson_model.THRESHOLDS[br_name]
            XML.SubElement(br, "name").text = br_threshold['name']
            XML.SubElement(br, "ordinal").text = br_threshold['ordinal']
            XML.SubElement(br, "color").text = br_threshold['color']
            XML.SubElement(br, "completeBuild").text = \
                str(wr_threshold['complete']).lower()
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
        elif kind == "not":
            ctag.set('class',
                     'org.jenkins_ci.plugins.run_condition.logic.Not')
            notcondition = cdata['condition-operand']
            build_condition(notcondition, ctag)

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

    build_condition(data, root_tag)
    evaluation_classes_pkg = 'org.jenkins_ci.plugins.run_condition'
    evaluation_classes = {
        'fail': evaluation_classes_pkg + '.BuildStepRunner$Fail',
        'mark-unstable': evaluation_classes_pkg + '.BuildStepRunner$Unstable',
        'run-and-mark-unstable': evaluation_classes_pkg +
        '.BuildStepRunner$RunUnstable',
        'run': evaluation_classes_pkg + '.BuildStepRunner$Run',
        'dont-run': evaluation_classes_pkg + '.BuildStepRunner$DontRun',
    }
    evaluation_class = evaluation_classes[data.get('on-evaluation-failure',
                                                   'fail')]
    XML.SubElement(root_tag, "runner").set('class',
                                           evaluation_class)
    for step in steps:
        build_step(steps_parent, step)


def maven_builder(parser, xml_parent, data):
    """yaml: maven-builder
    Execute Maven3 builder

    :arg str name: Name of maven installation from the configuration
    :arg str pom: Location of pom.xml (default 'pom.xml')
    :arg str goals: Goals to execute
    :arg str maven-opts: Additional options for maven (optional)

    Requires the Jenkins `Artifactory Plugin
    <https://wiki.jenkins-ci.org/display/JENKINS/Artifactory+Plugin>`_
    allows your build jobs to deploy artifacts automatically to Artifactory.

    Example:

    .. literalinclude:: /../../tests/builders/fixtures/maven-builder001.yaml
       :language: yaml
    """
    maven = XML.SubElement(xml_parent, 'org.jfrog.hudson.maven3.Maven3Builder')

    required = {
        'mavenName': 'name',
        'goals': 'goals',
    }

    for key in required:
        try:
            XML.SubElement(maven, key).text = data[required[key]]
        except KeyError:
            raise MissingAttributeError(required[key])

    XML.SubElement(maven, 'rootPom').text = data.get('pom', 'pom.xml')
    XML.SubElement(maven, 'mavenOpts').text = data.get('maven-opts', '')


def maven_target(parser, xml_parent, data):
    """yaml: maven-target
    Execute top-level Maven targets

    :arg str goals: Goals to execute
    :arg str properties: Properties for maven, can have multiples
    :arg str pom: Location of pom.xml (default 'pom.xml')
    :arg bool private-repository: Use private maven repository for this
      job (default false)
    :arg str maven-version: Installation of maven which should be used
      (optional)
    :arg str java-opts: java options for maven, can have multiples,
        must be in quotes (optional)
    :arg str settings: Path to use as user settings.xml
      It is possible to provide a ConfigFileProvider settings file, such as
      see CFP Example below. (optional)
    :arg str global-settings: Path to use as global settings.xml
      It is possible to provide a ConfigFileProvider settings file, such as
      see CFP Example below. (optional)

    Requires the Jenkins `Config File Provider Plugin
    <https://wiki.jenkins-ci.org/display/JENKINS/Config+File+Provider+Plugin>`_
    for the Config File Provider "settings" and "global-settings" config.

    Example:

    .. literalinclude:: /../../tests/builders/fixtures/maven-target-doc.yaml

    CFP Example:

    .. literalinclude:: /../../tests/builders/fixtures/maven-target002.yaml
       :language: yaml
    """
    maven = XML.SubElement(xml_parent, 'hudson.tasks.Maven')
    XML.SubElement(maven, 'targets').text = data['goals']
    prop_string = '\n'.join(data.get('properties', []))
    XML.SubElement(maven, 'properties').text = prop_string
    if 'maven-version' in data:
        XML.SubElement(maven, 'mavenName').text = str(data['maven-version'])
    if 'pom' in data:
        XML.SubElement(maven, 'pom').text = str(data['pom'])
    use_private = str(data.get('private-repository', False)).lower()
    XML.SubElement(maven, 'usePrivateRepository').text = use_private
    if 'java-opts' in data:
        javaoptions = ' '.join(data.get('java-opts', []))
        XML.SubElement(maven, 'jvmOptions').text = javaoptions
    config_file_provider_settings(maven, data)


def multijob(parser, xml_parent, data):
    """yaml: multijob
    Define a multijob phase. Requires the Jenkins
    :jenkins-wiki:`Multijob Plugin <Multijob+Plugin>`.

    This builder may only be used in \
    :py:class:`jenkins_jobs.modules.project_multijob.MultiJob` projects.

    :arg str name: MultiJob phase name
    :arg str condition: when to trigger the other job.
        Can be: 'SUCCESSFUL', 'UNSTABLE', 'COMPLETED', 'FAILURE'.
        (default 'SUCCESSFUL')

    :arg list projects: list of projects to include in the MultiJob phase

      :Project: * **name** (`str`) -- Project name
                * **current-parameters** (`bool`) -- Pass current build
                  parameters to the other job (default false)
                * **node-label-name** (`str`) -- Define a list of nodes
                  on which the job should be allowed to be executed on.
                  Requires NodeLabel Parameter Plugin (optional)
                * **node-label** (`str`) -- Define a label
                  of 'Restrict where this project can be run' on the fly.
                  Requires NodeLabel Parameter Plugin (optional)
                * **git-revision** (`bool`) -- Pass current git-revision
                  to the other job (default false)
                * **property-file** (`str`) -- Pass properties from file
                  to the other job (optional)
                * **predefined-parameters** (`str`) -- Pass predefined
                  parameters to the other job (optional)
                * **enable-condition** (`str`) -- Condition to run the
                  job in groovy script format (optional)
                * **kill-phase-on** (`str`) -- Stop the phase execution
                  on specific job status. Can be 'FAILURE', 'UNSTABLE',
                  'NEVER'. (optional)

    Example:

    .. literalinclude:: /../../tests/builders/fixtures/multibuild.yaml
       :language: yaml
    """
    builder = XML.SubElement(xml_parent, 'com.tikal.jenkins.plugins.multijob.'
                                         'MultiJobBuilder')
    XML.SubElement(builder, 'phaseName').text = data['name']

    condition = data.get('condition', 'SUCCESSFUL')
    conditions_available = ('SUCCESSFUL', 'UNSTABLE', 'COMPLETED', 'FAILURE')
    if condition not in conditions_available:
        raise JenkinsJobsException('Multijob condition must be one of: %s.'
                                   % ', '.join(conditions_available))
    XML.SubElement(builder, 'continuationCondition').text = condition

    phaseJobs = XML.SubElement(builder, 'phaseJobs')

    kill_status_list = ('FAILURE', 'UNSTABLE', 'NEVER')

    for project in data.get('projects', []):
        phaseJob = XML.SubElement(phaseJobs, 'com.tikal.jenkins.plugins.'
                                             'multijob.PhaseJobsConfig')

        XML.SubElement(phaseJob, 'jobName').text = project['name']

        # Pass through the current build params
        currParams = str(project.get('current-parameters', False)).lower()
        XML.SubElement(phaseJob, 'currParams').text = currParams

        # Pass through other params
        configs = XML.SubElement(phaseJob, 'configs')

        nodeLabelName = project.get('node-label-name')
        nodeLabel = project.get('node-label')
        if (nodeLabelName and nodeLabel):
            node = XML.SubElement(
                configs, 'org.jvnet.jenkins.plugins.nodelabelparameter.'
                         'parameterizedtrigger.NodeLabelBuildParameter')
            XML.SubElement(node, 'name').text = nodeLabelName
            XML.SubElement(node, 'nodeLabel').text = nodeLabel

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

        # Enable Condition
        enable_condition = project.get('enable-condition')
        if enable_condition is not None:
            XML.SubElement(
                phaseJob,
                'enableCondition'
            ).text = 'true'
            XML.SubElement(
                phaseJob,
                'condition'
            ).text = enable_condition

        # Kill phase on job status
        kill_status = project.get('kill-phase-on')
        if kill_status is not None:
            kill_status = kill_status.upper()
            if kill_status not in kill_status_list:
                raise JenkinsJobsException(
                    'multijob kill-phase-on must be one of: %s'
                    + ','.join(kill_status_list))
            XML.SubElement(
                phaseJob,
                'killPhaseOnJobResultCondition'
            ).text = kill_status


def config_file_provider(parser, xml_parent, data):
    """yaml: config-file-provider
    Provide configuration files (i.e., settings.xml for maven etc.)
    which will be copied to the job's workspace.
    Requires the Jenkins :jenkins-wiki:`Config File Provider Plugin
    <Config+File+Provider+Plugin>`.

    :arg list files: List of managed config files made up of three
      parameters

      :files: * **file-id** (`str`) -- The identifier for the managed config
                file
              * **target** (`str`) -- Define where the file should be created
                (optional)
              * **variable** (`str`) -- Define an environment variable to be
                used (optional)

    Example:

    .. literalinclude::
       ../../tests/builders/fixtures/config-file-provider01.yaml
       :language: yaml
    """
    cfp = XML.SubElement(xml_parent,
                         'org.jenkinsci.plugins.configfiles.builder.'
                         'ConfigFileBuildStep')
    cfp.set('plugin', 'config-file-provider')
    config_file_provider_builder(cfp, data)


def grails(parser, xml_parent, data):
    """yaml: grails
    Execute a grails build step. Requires the :jenkins-wiki:`Jenkins Grails
    Plugin <Grails+Plugin>`.

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

    Example:

    .. literalinclude:: ../../tests/builders/fixtures/grails.yaml
       :language: yaml
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
        data.get('force-upgrade', False)).lower()
    XML.SubElement(grails, 'nonInteractive').text = str(
        data.get('non-interactive', False)).lower()
    XML.SubElement(grails, 'useWrapper').text = str(
        data.get('use-wrapper', False)).lower()
    XML.SubElement(grails, 'plainOutput').text = str(
        data.get('plain-output', False)).lower()
    XML.SubElement(grails, 'stackTrace').text = str(
        data.get('stack-trace', False)).lower()
    XML.SubElement(grails, 'verbose').text = str(
        data.get('verbose', False)).lower()
    XML.SubElement(grails, 'refreshDependencies').text = str(
        data.get('refresh-dependencies', False)).lower()


def sbt(parser, xml_parent, data):
    """yaml: sbt
    Execute a sbt build step. Requires the Jenkins :jenkins-wiki:`Sbt Plugin
    <sbt+plugin>`.

    :arg str name: Select a sbt installation to use. If no name is
                   provided, the first in the list of defined SBT
                   builders will be used. (default to first in list)
    :arg str jvm-flags: Parameters to pass to the JVM (default '')
    :arg str actions: Select the sbt tasks to execute (default '')
    :arg str sbt-flags: Add flags to SBT launcher
                        (default '-Dsbt.log.noformat=true')
    :arg str subdir-path: Path relative to workspace to run sbt in (default '')

    Example:

    .. literalinclude:: ../../tests/builders/fixtures/sbt.yaml
       :language: yaml
    """
    sbt = XML.SubElement(xml_parent, 'org.jvnet.hudson.plugins.'
                                     'SbtPluginBuilder')
    XML.SubElement(sbt, 'name').text = data.get(
        'name', '')
    XML.SubElement(sbt, 'jvmFlags').text = data.get(
        'jvm-flags', '')
    XML.SubElement(sbt, 'sbtFlags').text = data.get(
        'sbt-flags', '-Dsbt.log.noformat=true')
    XML.SubElement(sbt, 'actions').text = data.get(
        'actions', '')
    XML.SubElement(sbt, 'subdirPath').text = data.get(
        'subdir-path', '')


def critical_block_start(parser, xml_parent, data):
    """yaml: critical-block-start
    Designate the start of a critical block. Must be used in conjuction with
    critical-block-end.

    Must also add a build wrapper (exclusion), specifying the resources that
    control the critical block. Otherwise, this will have no effect.

    Requires Jenkins :jenkins-wiki:`Exclusion Plugin <Exclusion-Plugin>`.

    Example::

      wrappers:
        - exclusion:
            resources:
              myresource1
      builders:
        - critical-block-start
        - ... other builders
        - critical-block-end

    """
    cbs = \
        XML.SubElement(xml_parent,
                       'org.jvnet.hudson.plugins.exclusion.CriticalBlockStart')
    cbs.set('plugin', 'Exclusion')


def critical_block_end(parser, xml_parent, data):
    """yaml: critical-block-end
    Designate the end of a critical block. Must be used in conjuction with
    critical-block-start.

    Must also add a build wrapper (exclusion), specifying the resources that
    control the critical block. Otherwise, this will have no effect.

    Requires Jenkins :jenkins-wiki:`Exclusion Plugin <Exclusion-Plugin>`.

    Example::

      wrappers:
        - exclusion:
            resources:
              myresource1
      builders:
        - critical-block-start
        - ... other builders
        - critical-block-end

    """
    cbs = \
        XML.SubElement(xml_parent,
                       'org.jvnet.hudson.plugins.exclusion.CriticalBlockEnd')
    cbs.set('plugin', 'Exclusion')


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


def shining_panda(parser, xml_parent, data):
    """yaml: shining-panda
    Execute a command inside various python environments. Requires the Jenkins
    :jenkins-wiki:`ShiningPanda plugin <ShiningPanda+Plugin>`.

    :arg str build-environment: Building environment to set up (Required).

        :build-environment values:
            * **python**: Use a python installation configured in Jenkins.
            * **custom**: Use a manually installed python.
            * **virtualenv**: Create a virtualenv

    For the **python** environment

    :arg str python-version: Name of the python installation to use.
        Must match one of the configured installations on server \
        configuration
        (default: System-CPython-2.7)

    For the **custom** environment:

    :arg str home: path to the home folder of the custom installation \
        (Required)

    For the **virtualenv** environment:

    :arg str python-version: Name of the python installation to use.
        Must match one of the configured installations on server \
        configuration
        (default: System-CPython-2.7)
    :arg str name: Name of this virtualenv. Two virtualenv builders with \
        the same name will use the same virtualenv installation (optional)
    :arg bool clear: If true, delete and recreate virtualenv on each build.
        (default: false)
    :arg bool use-distribute: if true use distribute, if false use \
        setuptools. (default: true)
    :arg bool system-site-packages: if true, give access to the global
        site-packages directory to the virtualenv. (default: false)

    Common to all environments:

    :arg str nature: Nature of the command field. (default: shell)

        :nature values:
            * **shell**: execute the Command contents with default shell
            * **xshell**: like **shell** but performs platform conversion \
                first
            * **python**: execute the Command contents with the Python \
                executable

    :arg str command: The command to execute
    :arg bool ignore-exit-code: mark the build as failure if any of the
        commands exits with a non-zero exit code. (default: false)

    Examples:

    .. literalinclude:: \
        /../../tests/builders/fixtures/shining-panda-pythonenv.yaml
       :language: yaml

    .. literalinclude:: \
        /../../tests/builders/fixtures/shining-panda-customenv.yaml
       :language: yaml

    .. literalinclude:: \
        /../../tests/builders/fixtures/shining-panda-virtualenv.yaml
       :language: yaml
    """

    pluginelementpart = 'jenkins.plugins.shiningpanda.builders.'
    buildenvdict = {'custom': 'CustomPythonBuilder',
                    'virtualenv': 'VirtualenvBuilder',
                    'python': 'PythonBuilder'}
    envs = (buildenvdict.keys())

    try:
        buildenv = data['build-environment']
    except KeyError:
        raise MissingAttributeError('build-environment')

    if buildenv not in envs:
        raise InvalidAttributeError('build-environment', buildenv, envs)

    t = XML.SubElement(xml_parent, '%s%s' %
                       (pluginelementpart, buildenvdict[buildenv]))

    if buildenv in ('python', 'virtualenv'):
        XML.SubElement(t, 'pythonName').text = data.get("python-version",
                                                        "System-CPython-2.7")

    if buildenv in ('custom'):
        try:
            homevalue = data["home"]
        except KeyError:
            raise JenkinsJobsException("'home' argument is required for the"
                                       " 'custom' environment")
        XML.SubElement(t, 'home').text = homevalue

    if buildenv in ('virtualenv'):
        XML.SubElement(t, 'home').text = data.get("name", "")
        clear = data.get("clear", False)
        XML.SubElement(t, 'clear').text = str(clear).lower()
        use_distribute = data.get('use-distribute', False)
        XML.SubElement(t, 'useDistribute').text = str(use_distribute).lower()
        system_site_packages = data.get('system-site-packages', False)
        XML.SubElement(t, 'systemSitePackages').text = str(
            system_site_packages).lower()

    # Common arguments
    nature = data.get('nature', 'shell')
    naturetuple = ('shell', 'xshell', 'python')
    if nature not in naturetuple:
        raise InvalidAttributeError('nature', nature, naturetuple)
    XML.SubElement(t, 'nature').text = nature
    XML.SubElement(t, 'command').text = data.get("command", "")
    ignore_exit_code = data.get('ignore-exit-code', False)
    XML.SubElement(t, 'ignoreExitCode').text = str(ignore_exit_code).lower()


def managed_script(parser, xml_parent, data):
    """yaml: managed-script
    This step allows to reference and execute a centrally managed
    script within your build. Requires the Jenkins
    :jenkins-wiki:`Managed Script Plugin <Managed+Script+Plugin>`.

    :arg str script-id: Id of script to execute (Required)
    :arg str type: Type of managed file (default: script)

        :type values:
            * **batch**: Execute managed windows batch
            * **script**: Execute managed script

    :arg list args: Arguments to be passed to referenced script

    Example:

    .. literalinclude:: /../../tests/builders/fixtures/managed-script.yaml
       :language: yaml

    .. literalinclude:: /../../tests/builders/fixtures/managed-winbatch.yaml
       :language: yaml
    """
    step_type = data.get('type', 'script').lower()
    if step_type == 'script':
        step = 'ScriptBuildStep'
        script_tag = 'buildStepId'
    elif step_type == 'batch':
        step = 'WinBatchBuildStep'
        script_tag = 'command'
    else:
        raise InvalidAttributeError('type', step_type, ['script', 'batch'])
    ms = XML.SubElement(xml_parent,
                        'org.jenkinsci.plugins.managedscripts.' + step)
    try:
        script_id = data['script-id']
    except KeyError:
        raise MissingAttributeError('script-id')
    XML.SubElement(ms, script_tag).text = script_id
    args = XML.SubElement(ms, 'buildStepArgs')
    for arg in data.get('args', []):
        XML.SubElement(args, 'string').text = arg


def cmake(parser, xml_parent, data):
    """yaml: cmake
    Execute a CMake target. Requires the Hudson `cmakebuilder Plugin.
    <http://wiki.hudson-ci.org/display/HUDSON/cmakebuilder+Plugin>`_

    :arg str source-dir: the source code directory relative to the workspace
        directory. (required)
    :arg str build-dir: The directory where the project will be built in.
        Relative to the workspace directory. (optional)
    :arg list install-dir: The directory where the project will be installed
        in, relative to the workspace directory. (optional)
    :arg list build-type: Sets the "build type" option. A custom type different
        than the default ones specified on the CMake plugin can also be set,
        which will be automatically used in the "Other Build Type" option of
        the plugin. (default: Debug)

        :type Default types present in the CMake plugin:
            * **Debug**
            * **Release**
            * **RelWithDebInfo**
            * **MinSizeRel**

    :arg list generator: The makefile generator (default: "Unix Makefiles").

        :type Possible generators:
            * **Borland Makefiles**
            * **CodeBlocks - MinGW Makefiles**
            * **CodeBlocks - Unix Makefiles**
            * **Eclipse CDT4 - MinGW Makefiles**
            * **Eclipse CDT4 - NMake Makefiles**
            * **Eclipse CDT4 - Unix Makefiles**
            * **MSYS Makefiles**
            * **MinGW Makefiles**
            * **NMake Makefiles**
            * **Unix Makefiles**
            * **Visual Studio 6**
            * **Visual Studio 7 .NET 2003**
            * **Visual Studio 8 2005**
            * **Visual Studio 8 2005 Win64**
            * **Visual Studio 9 2008**
            * **Visual Studio 9 2008 Win64**
            * **Watcom WMake**

    :arg str make-command: The make command (default: "make").
    :arg str install-command: The install command (default: "make install").
    :arg str preload-script: Path to a CMake preload script file. (optional)
    :arg str other-arguments: Other arguments to be added to the CMake
        call. (optional)
    :arg str custom-cmake-path: Path to cmake executable. (optional)
    :arg bool clean-build-dir: If true, delete the build directory before each
        build (default: false).
    :arg bool clean-install-dir: If true, delete the install dir before each
        build (default: false).

    Example:

    .. literalinclude:: ../../tests/builders/fixtures/cmake-complete.yaml
       :language: yaml
    """

    BUILD_TYPES = ['Debug', 'Release', 'RelWithDebInfo', 'MinSizeRel']

    cmake = XML.SubElement(xml_parent, 'hudson.plugins.cmake.CmakeBuilder')

    source_dir = XML.SubElement(cmake, 'sourceDir')
    try:
        source_dir.text = data['source-dir']
    except KeyError:
        raise MissingAttributeError('source-dir')

    build_dir = XML.SubElement(cmake, 'buildDir')
    build_dir.text = data.get('build-dir', '')

    install_dir = XML.SubElement(cmake, 'installDir')
    install_dir.text = data.get('install-dir', '')

    # The options buildType and otherBuildType work together on the CMake
    # plugin:
    #  * If the passed value is one of the predefined values, set buildType to
    #    it and otherBuildType to blank;
    #  * Otherwise, set otherBuildType to the value, and buildType to
    #    "Debug". The CMake plugin will ignore the buildType option.
    #
    # It is strange and confusing that the plugin author chose to do something
    # like that instead of simply passing a string "buildType" option, so this
    # was done to simplify it for the JJB user.
    build_type = XML.SubElement(cmake, 'buildType')
    build_type.text = data.get('build-type', BUILD_TYPES[0])

    other_build_type = XML.SubElement(cmake, 'otherBuildType')

    if(build_type.text not in BUILD_TYPES):
        other_build_type.text = build_type.text
        build_type.text = BUILD_TYPES[0]
    else:
        other_build_type.text = ''

    generator = XML.SubElement(cmake, 'generator')
    generator.text = data.get('generator', "Unix Makefiles")

    make_command = XML.SubElement(cmake, 'makeCommand')
    make_command.text = data.get('make-command', 'make')

    install_command = XML.SubElement(cmake, 'installCommand')
    install_command.text = data.get('install-command', 'make install')

    preload_script = XML.SubElement(cmake, 'preloadScript')
    preload_script.text = data.get('preload-script', '')

    other_cmake_args = XML.SubElement(cmake, 'cmakeArgs')
    other_cmake_args.text = data.get('other-arguments', '')

    custom_cmake_path = XML.SubElement(cmake, 'projectCmakePath')
    custom_cmake_path.text = data.get('custom-cmake-path', '')

    clean_build_dir = XML.SubElement(cmake, 'cleanBuild')
    clean_build_dir.text = str(data.get('clean-build-dir', False)).lower()

    clean_install_dir = XML.SubElement(cmake, 'cleanInstallDir')
    clean_install_dir.text = str(data.get('clean-install-dir',
                                          False)).lower()

    # The plugin generates this tag, but there doesn't seem to be anything
    # that can be configurable by it. Let's keep it to mantain compatibility:
    XML.SubElement(cmake, 'builderImpl')


def dsl(parser, xml_parent, data):
    """yaml: dsl
    Process Job DSL

    Requires the Jenkins :jenkins-wiki:`Job DSL plugin <Job+DSL+Plugin>`.

    :arg str script-text: dsl script which is Groovy code (Required if target
        is not specified)
    :arg str target: Newline separated list of DSL scripts, located in the
        Workspace. Can use wildcards like 'jobs/\*\*/\*.groovy' (Required
        if script-text is not specified)
    :arg str ignore-existing: Ignore previously generated jobs and views
    :arg str removed-job-action: Specifies what to do when a previously
        generated job is not referenced anymore (IGNORE (Default), DISABLE,
        DELETE)
    :arg str removed-view-action: Specifies what to do when a previously
        generated view is not referenced anymore (IGNORE (Default), DELETE)
    :arg str lookup-strategy: Determines how relative job names in DSL
        scripts are interpreted (JENKINS_ROOT (Default), SEED_JOB)
    :arg str additional-classpath: Newline separated list of additional
        classpath entries for the Job DSL scripts. All entries must be
        relative to the workspace root, e.g. build/classes/main.

    Example:

    .. literalinclude:: /../../tests/builders/fixtures/dsl.yaml
       :language: yaml

    """

    dsl = XML.SubElement(xml_parent,
                         'javaposse.jobdsl.plugin.ExecuteDslScripts')

    if data.get('script-text'):
        XML.SubElement(dsl, 'scriptText').text = data.get('script-text')
        XML.SubElement(dsl, 'usingScriptText').text = 'true'
    elif data.get('target'):
        XML.SubElement(dsl, 'target').text = data.get('target')
        XML.SubElement(dsl, 'usingScriptText').text = 'false'
    else:
        raise MissingAttributeError(['script-text', 'target'])

    XML.SubElement(dsl, 'ignoreExisting').text = str(data.get(
        'ignore-existing', False)).lower()

    supportedJobActions = ['IGNORE', 'DISABLE', 'DELETE']
    removedJobAction = data.get('removed-job-action',
                                supportedJobActions[0])
    if removedJobAction not in supportedJobActions:
        raise InvalidAttributeError('removed-job-action',
                                    removedJobAction,
                                    supportedJobActions)
    XML.SubElement(dsl, 'removedJobAction').text = removedJobAction

    supportedViewActions = ['IGNORE', 'DELETE']
    removedViewAction = data.get('removed-view-action',
                                 supportedViewActions[0])
    if removedViewAction not in supportedViewActions:
        raise InvalidAttributeError('removed-view-action',
                                    removedViewAction,
                                    supportedViewActions)
    XML.SubElement(dsl, 'removedViewAction').text = removedViewAction

    supportedLookupActions = ['JENKINS_ROOT', 'SEED_JOB']
    lookupStrategy = data.get('lookup-strategy',
                              supportedLookupActions[0])
    if lookupStrategy not in supportedLookupActions:
        raise InvalidAttributeError('lookup-strategy',
                                    lookupStrategy,
                                    supportedLookupActions)
    XML.SubElement(dsl, 'lookupStrategy').text = lookupStrategy

    XML.SubElement(dsl, 'additionalClasspath').text = data.get(
        'additional-classpath')


def github_notifier(parser, xml_parent, data):
    """yaml: github-notifier
    Set pending build status on Github commit.
    Requires the Jenkins :jenkins-wiki:`Github Plugin <GitHub+Plugin>`.

    Example:

    .. literalinclude:: /../../tests/builders/fixtures/github-notifier.yaml
    """
    XML.SubElement(xml_parent,
                   'com.cloudbees.jenkins.GitHubSetCommitStatusBuilder')


def ssh_builder(parser, xml_parent, data):
    """yaml: ssh-builder
    Executes command on remote host
    Requires the Jenkins `SSH plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/SSH+plugin>`_

    :arg str ssh-user-ip: user@ip:ssh_port of machine that was defined
                          in jenkins according to SSH plugin instructions
    :arg str command: command to run on remote server

    Example:

    .. literalinclude:: /../../tests/builders/fixtures/ssh-builder.yaml
    """
    builder = XML.SubElement(
        xml_parent, 'org.jvnet.hudson.plugins.SSHBuilder')
    try:
        XML.SubElement(builder, 'siteName').text = str(data['ssh-user-ip'])
        XML.SubElement(builder, 'command').text = str(data['command'])
    except KeyError as e:
        raise MissingAttributeError("'%s'" % e.args[0])


def sonar(parser, xml_parent, data):
    """yaml: sonar
    Invoke standalone Sonar analysis.
    Requires the Jenkins `Sonar Plugin.
    <http://docs.codehaus.org/pages/viewpage.action?pageId=116359341>`_

    :arg str sonar-name: Name of the Sonar installation.
    :arg str task: Task to run. (optional)
    :arg str project: Path to Sonar project properties file. (optional)
    :arg str properties: Sonar configuration properties. (optional)
    :arg str java-opts: Java options for Sonnar Runner. (optional)
    :arg str jdk: JDK to use (inherited from the job if omitted). (optional)

    Example:

    .. literalinclude:: /../../tests/builders/fixtures/sonar.yaml
    """
    sonar = XML.SubElement(xml_parent,
                           'hudson.plugins.sonar.SonarRunnerBuilder')
    XML.SubElement(sonar, 'installationName').text = data['sonar-name']
    XML.SubElement(sonar, 'task').text = data.get('task', '')
    XML.SubElement(sonar, 'project').text = data.get('project', '')
    XML.SubElement(sonar, 'properties').text = data.get('properties', '')
    XML.SubElement(sonar, 'javaOpts').text = data.get('java-opts', '')
    if 'jdk' in data:
        XML.SubElement(sonar, 'jdk').text = data['jdk']


def sonatype_clm(parser, xml_parent, data):
    """yaml: sonatype-clm
    Requires the Jenkins :jenkins-wiki:`Sonatype CLM Plugin
    <Sonatype+CLM+%28formerly+Insight+for+CI%29>`.

    :arg str application-name: Determines the policy elements to associate
        with this build. (Required)
    :arg bool fail-on-clm-server-failure: Controls the build outcome if there
        is a failure in communicating with the CLM server. (Default: false)
    :arg str stage: Controls the stage the policy evaluation will be run
        against on the CLM server. Valid stages: build, stage-release, release,
        operate. (Default: build)
    :arg str scan-targets: Pattern of files to include for scanning. (optional)
    :arg str module-excludes: Pattern of files to exclude. (optional)
    :arg str advanced-options: Options to be set on a case-by-case basis as
        advised by Sonatype Support. (optional)

    Example:

    .. literalinclude:: /../../tests/builders/fixtures/sonatype-clm01.yaml
    """
    clm = XML.SubElement(xml_parent,
                         'com.sonatype.insight.ci.hudson.PreBuildScan')
    clm.set('plugin', 'sonatype-clm-ci')

    if 'application-name' not in data:
        raise MissingAttributeError("application-name",
                                    "builders.sonatype-clm")
    XML.SubElement(clm, 'billOfMaterialsToken').text = str(
        data['application-name'])
    XML.SubElement(clm, 'failOnClmServerFailures').text = str(
        data.get('fail-on-clm-server-failure', False)).lower()

    SUPPORTED_STAGES = ['build', 'stage-release', 'release', 'operate']
    stage = str(data.get('stage', 'build')).lower()
    if stage not in SUPPORTED_STAGES:
        raise InvalidAttributeError("stage",
                                    stage,
                                    "builders.sonatype-clm",
                                    SUPPORTED_STAGES)
    XML.SubElement(clm, 'stageId').text = stage

    # Path Configs
    path_config = XML.SubElement(clm,
                                 'pathConfig')
    XML.SubElement(path_config, 'scanTargets').text = str(
        data.get('scan-targets', '')).lower()
    XML.SubElement(path_config, 'moduleExcludes').text = str(
        data.get('module-excludes', '')).lower()
    XML.SubElement(path_config, 'scanProperties').text = str(
        data.get('advanced-options', '')).lower()


def beaker(parser, xml_parent, data):
    """yaml: beaker
    Execute a beaker build step. Requires the Jenkins :jenkins-wiki:`Beaker
    Builder Plugin <Beaker+Builder+Plugin>`.

    :arg str content: Run job from string
                      (Alternative: you can choose a path instead)
    :arg str path: Run job from file
                   (Alternative: you can choose a content instead)
    :arg bool download-logs: Download Beaker log files (default false)

    Example:

    .. literalinclude:: ../../tests/builders/fixtures/beaker-path.yaml
       :language: yaml

    .. literalinclude:: ../../tests/builders/fixtures/beaker-content.yaml
       :language: yaml
    """
    beaker = XML.SubElement(xml_parent, 'org.jenkinsci.plugins.beakerbuilder.'
                                        'BeakerBuilder')
    jobSource = XML.SubElement(beaker, 'jobSource')
    if 'content' in data and 'path' in data:
        raise JenkinsJobsException("Use just one of 'content' or 'path'")
    elif 'content' in data:
        jobSourceClass = "org.jenkinsci.plugins.beakerbuilder.StringJobSource"
        jobSource.set('class', jobSourceClass)
        XML.SubElement(jobSource, 'jobContent').text = data['content']
    elif 'path' in data:
        jobSourceClass = "org.jenkinsci.plugins.beakerbuilder.FileJobSource"
        jobSource.set('class', jobSourceClass)
        XML.SubElement(jobSource, 'jobPath').text = data['path']
    else:
        raise JenkinsJobsException("Use one of 'content' or 'path'")

    XML.SubElement(beaker, 'downloadFiles').text = str(data.get(
        'download-logs', False)).lower()
