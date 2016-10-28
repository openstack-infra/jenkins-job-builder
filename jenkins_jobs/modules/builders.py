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

import logging
import xml.etree.ElementTree as XML

from jenkins_jobs.errors import InvalidAttributeError
from jenkins_jobs.errors import JenkinsJobsException
from jenkins_jobs.errors import MissingAttributeError
import jenkins_jobs.modules.base
import jenkins_jobs.modules.helpers as helpers
from jenkins_jobs.modules.helpers import append_git_revision_config
import pkg_resources
from jenkins_jobs.modules.helpers import cloudformation_init
from jenkins_jobs.modules.helpers import cloudformation_region_dict
from jenkins_jobs.modules.helpers import cloudformation_stack
from jenkins_jobs.modules.helpers import config_file_provider_builder
from jenkins_jobs.modules.helpers import config_file_provider_settings
from jenkins_jobs.modules.helpers import convert_mapping_to_xml
from jenkins_jobs.modules.helpers import copyartifact_build_selector
from jenkins_jobs.modules import hudson_model
from jenkins_jobs.modules.publishers import ssh

logger = logging.getLogger(__name__)


def shell(registry, xml_parent, data):
    """yaml: shell
    Execute a shell command.

    :arg str parameter: the shell command to execute

    Example:

    .. literalinclude:: /../../tests/builders/fixtures/shell.yaml
       :language: yaml

    """
    shell = XML.SubElement(xml_parent, 'hudson.tasks.Shell')
    XML.SubElement(shell, 'command').text = data


def python(registry, xml_parent, data):
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


def copyartifact(registry, xml_parent, data):
    """yaml: copyartifact

    Copy artifact from another project. Requires the :jenkins-wiki:`Copy
    Artifact plugin <Copy+Artifact+Plugin>`.

    Please note using the multijob-build for which-build argument requires
    the :jenkins-wiki:`Multijob plugin <Multijob+Plugin>`

    :arg str project: Project to copy from
    :arg str filter: what files to copy
    :arg str target: Target base directory for copy, blank means use workspace
    :arg bool flatten: Flatten directories (default false)
    :arg bool optional: If the artifact is missing (for any reason) and
        optional is true, the build won't fail because of this builder
        (default false)
    :arg bool do-not-fingerprint: Disable automatic fingerprinting of copied
        artifacts (default false)
    :arg str which-build: which build to get artifacts from
        (optional, default last-successful)

        :which-build values:
            * **last-successful**
            * **last-completed**
            * **specific-build**
            * **last-saved**
            * **upstream-build**
            * **permalink**
            * **workspace-latest**
            * **build-param**
            * **downstream-build**
            * **multijob-build**

    :arg str build-number: specifies the build number to get when
        when specific-build is specified as which-build
    :arg str permalink: specifies the permalink to get when
        permalink is specified as which-build

        :permalink values:
            * **last**
            * **last-stable**
            * **last-successful**
            * **last-failed**
            * **last-unstable**
            * **last-unsuccessful**

    :arg bool stable: specifies to get only last stable build when
        last-successful is specified as which-build
    :arg bool fallback-to-last-successful: specifies to fallback to
        last successful build when upstream-build is specified as which-build
    :arg string param: specifies to use a build parameter to get the build when
        build-param is specified as which-build
    :arg str upstream-project-name: specifies the project name of downstream
        when downstream-build is specified as which-build
    :arg str upstream-build-number: specifies the number of the build to
        find its downstream build when downstream-build is specified as
        which-build
    :arg string parameter-filters: Filter matching jobs based on these
        parameters (optional)


    Example:

    .. literalinclude:: ../../tests/builders/fixtures/copy-artifact001.yaml
       :language: yaml

    Multijob Example:

    .. literalinclude:: ../../tests/builders/fixtures/copy-artifact004.yaml
       :language: yaml
    """
    t = XML.SubElement(xml_parent, 'hudson.plugins.copyartifact.CopyArtifact')
    mappings = [
        # Warning: this only works with copy artifact version 1.26+,
        # for copy artifact version 1.25- the 'projectName' element needs
        # to be used instead of 'project'
        ('project', 'project', None),
        ('filter', 'filter', ''),
        ('target', 'target', ''),
        ('flatten', 'flatten', False),
        ('optional', 'optional', False),
        ('do-not-fingerprint', 'doNotFingerprintArtifacts', False),
        ('parameter-filters', 'parameters', '')
    ]
    convert_mapping_to_xml(t, data, mappings, fail_required=True)
    copyartifact_build_selector(t, data)


def change_assembly_version(registry, xml_parent, data):
    """yaml: change-assembly-version
    Change the assembly version.
    Requires the Jenkins :jenkins-wiki:`Change Assembly Version
    <Change+Assembly+Version>`.

    :arg str version: Set the new version number for replace (default 1.0.0)
    :arg str assemblyFile: The file name to search (default AssemblyInfo.cs)

    Example:

    .. literalinclude::
        /../../tests/builders/fixtures/changeassemblyversion001.yaml
       :language: yaml
    """

    cav_builder_tag = ('org.jenkinsci.plugins.changeassemblyversion.'
                       'ChangeAssemblyVersion')
    cav = XML.SubElement(xml_parent, cav_builder_tag)
    XML.SubElement(cav, 'task').text = data.get('version', '1.0.0')
    XML.SubElement(cav, 'assemblyFile').text = str(
        data.get('assembly-file', 'AssemblyInfo.cs'))


def fingerprint(registry, xml_parent, data):
    """yaml: fingerprint
    Adds the ability to generate fingerprints as build steps instead of waiting
    for a build to complete. Requires the Jenkins :jenkins-wiki:`Fingerprint
    Plugin <Fingerprint+Plugin>`.

    :arg str targets: Files to fingerprint (default '')

    Full Example:

    .. literalinclude::
        /../../tests/builders/fixtures/fingerprint-full.yaml
       :language: yaml

    Minimal Example:

    .. literalinclude::
        /../../tests/builders/fixtures/fingerprint-minimal.yaml
       :language: yaml
    """

    fingerprint = XML.SubElement(
        xml_parent, 'hudson.plugins.createfingerprint.CreateFingerprint')
    fingerprint.set('plugin', 'create-fingerprint')

    mapping = [('targets', 'targets', '')]
    convert_mapping_to_xml(fingerprint, data, mapping, fail_required=True)


def ant(registry, xml_parent, data):
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


def trigger_remote(registry, xml_parent, data):
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
    :arg bool should-not-fail-build: if true, remote job failure will not lead
        current job to fail (default false)
    :arg bool prevent-remote-build-queue: if true, wait to trigger remote
        builds until no other builds (default false)
    :arg bool block: whether to wait for the trigger jobs to finish or not
        (default true)
    :arg str poll-interval: polling interval in seconds for checking statues of
        triggered remote job, only necessary if current job is configured to
        block (default 10)
    :arg str connection-retry-limit: number of connection attempts to remote
        Jenkins server before giving up. (default 5)
    :arg str predefined-parameters: predefined parameters to send to the remote
        job when triggering it (optional)
    :arg str property-file: file in workspace of current job containing
        additional parameters to be set on remote job
        (optional)

    Example:

    .. literalinclude::
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


def trigger_builds(registry, xml_parent, data):
    """yaml: trigger-builds
    Trigger builds of other jobs.
    Requires the Jenkins :jenkins-wiki:`Parameterized Trigger Plugin
    <Parameterized+Trigger+Plugin>`.

    :arg list project: the Jenkins project to trigger
    :arg str predefined-parameters: key/value pairs to be passed to the job
        (optional)
    :arg list bool-parameters:

        :Bool:
            * **name** (`str`) -- Parameter name
            * **value** (`bool`) -- Value to set (default false)

    :arg str property-file:
        Pass properties from file to the other job (optional)
    :arg bool property-file-fail-on-missing:
        Don't trigger if any files are missing (default true)
    :arg bool current-parameters: Whether to include the parameters passed
        to the current build to the triggered job.
    :arg str node-label-name: Define a name for the NodeLabel parameter to be
        set. Used in conjunction with node-label. Requires NodeLabel Parameter
        Plugin (optional)
    :arg str node-label: Label of the nodes where build should be triggered.
        Used in conjunction with node-label-name.  Requires NodeLabel Parameter
        Plugin (optional)
    :arg str restrict-matrix-project: Filter that restricts the subset
        of the combinations that the triggered job will run (optional)
    :arg bool svn-revision: Whether to pass the svn revision to the triggered
        job (optional)
    :arg dict git-revision: Passes git revision to the triggered job
        (optional).

        * **combine-queued-commits** (bool): Whether to combine queued git
          hashes or not (default false)
    :arg bool block: whether to wait for the triggered jobs to finish or not
        (default false)
    :arg dict block-thresholds: Fail builds and/or mark as failed or unstable
        based on thresholds. Only apply if block parameter is true (optional)

        :block-thresholds:
            * **build-step-failure-threshold** (`str`) - build step failure
              threshold, valid values are 'never', 'SUCCESS', 'UNSTABLE', or
              'FAILURE'. (default 'FAILURE')
            * **unstable-threshold** (`str`) - unstable threshold, valid
              values are 'never', 'SUCCESS', 'UNSTABLE', or 'FAILURE'.
              (default 'UNSTABLE')
            * **failure-threshold** (`str`) - overall failure threshold, valid
              values are 'never', 'SUCCESS', 'UNSTABLE', or 'FAILURE'.
              (default 'FAILURE')

    :arg bool same-node: Use the same node for the triggered builds that was
        used for this build (optional)
    :arg list parameter-factories: list of parameter factories

        :Factory:
            * **factory** (`str`) **filebuild** -- For every property file,
              invoke one build
            * **file-pattern** (`str`) -- File wildcard pattern
            * **no-files-found-action** (`str`) -- Action to perform when
              no files found. Valid values 'FAIL', 'SKIP', or 'NOPARMS'.
              (default 'SKIP')

        :Factory:
            * **factory** (`str`) **binaryfile** -- For every matching
              file, invoke one build
            * **file-pattern** (`str`) -- Artifact ID of the artifact
            * **no-files-found-action** (`str`) -- Action to perform when
              no files found. Valid values 'FAIL', 'SKIP', or 'NOPARMS'.
              (default 'SKIP')

        :Factory:
            * **factory** (`str`) **counterbuild** -- Invoke i=0...N builds
            * **from** (`int`) -- Artifact ID of the artifact
            * **to** (`int`) -- Version of the artifact
            * **step** (`int`) -- Classifier of the artifact
            * **parameters** (`str`) -- KEY=value pairs, one per line
              (default '')
            * **validation-fail** (`str`) -- Action to perform when
              stepping validation fails. Valid values 'FAIL', 'SKIP', or
              'NOPARMS'. (default 'FAIL')

        :Factory:
            * **factory** (`str`) **allnodesforlabel** -- Trigger a build
              on all nodes having specific label. Requires NodeLabel
              Parameter Plugin (optional)
            * **name** (`str`) -- Name of the parameter to set (optional)
            * **node-label** (`str`) -- Label of the nodes where build
              should be triggered
            * **ignore-offline-nodes** (`bool`) -- Don't trigger build on
              offline nodes (default true)

        :Factory:
            * **factory** (`str`) **allonlinenodes** -- Trigger a build on
              every online node. Requires NodeLabel Parameter Plugin (optional)

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

    .. literalinclude::
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
            append_git_revision_config(tconfigs, project_def['git-revision'])

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
            XML.SubElement(node, 'name').text = project_def['node-label-name']
            XML.SubElement(node, 'nodeLabel').text = project_def['node-label']

        if 'restrict-matrix-project' in project_def:
            params = XML.SubElement(tconfigs,
                                    'hudson.plugins.parameterizedtrigger.'
                                    'matrix.MatrixSubsetBuildParameters')
            XML.SubElement(params, 'filter').text = project_def[
                'restrict-matrix-project']

        if(len(list(tconfigs)) == 0):
            tconfigs.set('class', 'java.util.Collections$EmptyList')

        if 'parameter-factories' in project_def:
            fconfigs = XML.SubElement(tconfig, 'configFactories')

            supported_factories = ['filebuild',
                                   'binaryfile',
                                   'counterbuild',
                                   'allnodesforlabel',
                                   'allonlinenodes']
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
                if factory['factory'] == 'allonlinenodes':
                    params = XML.SubElement(
                        fconfigs,
                        'org.jvnet.jenkins.plugins.nodelabelparameter.'
                        'parameterizedtrigger.'
                        'AllNodesBuildParameterFactory')

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


def builders_from(registry, xml_parent, data):
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


def http_request(registry, xml_parent, data):
    """yaml: http-request
    This plugin sends a http request to an url with some parameters.
    Requires the Jenkins :jenkins-wiki:`HTTP Request Plugin
    <HTTP+Request+Plugin>`.

    :arg str url: Specify an URL to be requested (required)
    :arg str mode: The http mode of the request (default GET)

        :mode values:
            * **GET**
            * **POST**
            * **PUT**
            * **DELETE**
            * **HEAD**
    :arg str content-type: Add 'Content-type: foo' HTTP request headers
        where foo is the http content-type the request is using.
        (default NOT_SET)
    :arg str accept-type: Add 'Accept: foo' HTTP request headers
        where foo is the http content-type to accept (default NOT_SET)

        :content-type and accept-type values:
            * **NOT_SET**
            * **TEXT_HTML**
            * **APPLICATION_JSON**
            * **APPLICATION_TAR**
            * **APPLICATION_ZIP**
            * **APPLICATION_OCTETSTREAM**
    :arg str output-file: Name of the file in which to write response data
        (default '')
    :arg int time-out: Specify a timeout value in seconds (default 0)
    :arg bool console-log: This allows you to turn off writing the response
        body to the log (default false)
    :arg bool pass-build: Should build parameters be passed to the URL
        being called (default false)
    :arg str valid-response-codes: Configure response code to mark an
        execution as success. You can configure simple code such as "200"
        or multiple codes separeted by comma(',') e.g. "200,404,500"
        Interval of codes should be in format From:To e.g. "100:399".
        The default (as if empty) is to fail to 4xx and 5xx.
        That means success from 100 to 399 "100:399"
        To ignore any response code use "100:599". (default '')
    :arg str valid-response-content: If set response must contain this string
        to mark an execution as success (default '')
    :arg str authentication-key: Authentication that will be used before this
        request. Authentications are created in global configuration under a
        key name that is selected here.
    :arg list custom-headers: list of header parameters

        :custom-header:
            * **name** (`str`) -- Name of the header
            * **value** (`str`) -- Value of the header

    Example:

    .. literalinclude:: ../../tests/builders/fixtures/http-request-minimal.yaml
       :language: yaml

    .. literalinclude::
       ../../tests/builders/fixtures/http-request-complete.yaml
       :language: yaml
    """

    http_request = XML.SubElement(xml_parent,
                                  'jenkins.plugins.http__request.HttpRequest')
    http_request.set('plugin', 'http_request')

    valid_modes = ['GET', 'POST', 'PUT', 'DELETE', 'HEAD']
    valid_types = ['NOT_SET', 'TEXT_HTML', 'APPLICATION_JSON',
                   'APPLICATION_TAR', 'APPLICATION_ZIP',
                   'APPLICATION_OCTETSTREAM']

    mappings = [
        ('url', 'url', None),
        ('mode', 'httpMode', 'GET', valid_modes),
        ('content-type', 'contentType', 'NOT_SET', valid_types),
        ('accept-type', 'acceptType', 'NOT_SET', valid_types),
        ('output-file', 'outputFile', ''),
        ('console-log', 'consoleLogResponseBody', False),
        ('pass-build', 'passBuildParameters', False),
        ('time-out', 'timeout', 0),
        ('valid-response-codes', 'validResponseCodes', ''),
        ('valid-response-content', 'validResponseContent', '')]
    convert_mapping_to_xml(http_request, data, mappings, fail_required=True)

    if 'authentication-key' in data:
        XML.SubElement(
            http_request, 'authentication').text = data['authentication-key']

    if 'custom-headers' in data:
        customHeader = XML.SubElement(http_request, 'customHeaders')
        header_mappings = [
            ('name', 'name', None),
            ('value', 'value', None)
        ]
        for customhead in data['custom-headers']:
            pair = XML.SubElement(customHeader, 'pair')
            convert_mapping_to_xml(pair,
                                   customhead,
                                   header_mappings,
                                   fail_required=True)


def inject(registry, xml_parent, data):
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


def kmap(registry, xml_parent, data):
    """yaml: kmap
    Publish mobile applications to your Keivox KMAP Private Mobile App Store.
    Requires the Jenkins :jenkins-wiki:`Keivox KMAP Private Mobile App Store
    Plugin <Keivox+KMAP+Private+Mobile+App+Store+Plugin>`.

    :arg str username: KMAP's user email with permissions to upload/publish
        applications to KMAP (required)
    :arg str password:  Password for the KMAP user uploading/publishing
        applications (required)
    :arg str url: KMAP's url. This url must always end with "/kmap-client/".
        For example: http://testing.keivox.com/kmap-client/ (required)
    :arg str categories: Categories' names. If you want to add the application
        to more than one category, write the categories between commas.
        (required)
    :arg str file-path: Path to the application's file (required)
    :arg str app-name: KMAP's application name (required)
    :arg str bundle: Bundle indentifier (default '')
    :arg str version: Application's version (required)
    :arg str description: Application's description (default '')
    :arg str icon-path: Path to the application's icon (default '')
    :arg bool publish-optional: Publish application after it has been uploaded
        to KMAP (default false)

        :publish-optional:
            * **groups** ('str') -- groups' names to publish the application
                (default '')
            * **users** ('str') -- users' names to publish the application
                (default '')
            * **notify-users** ('bool') -- Send notifications to the users and
                groups when publishing the application (default false)

    Minimal Example:

    .. literalinclude:: ../../tests/builders/fixtures/kmap-minimal.yaml
       :language: yaml

    Full Example:

    .. literalinclude:: ../../tests/builders/fixtures/kmap-full.yaml
       :language: yaml
    """
    kmap = XML.SubElement(
        xml_parent, 'org.jenkinsci.plugins.KmapJenkinsBuilder')

    kmap.set('plugin', 'kmap-jenkins')
    publish = data.get('publish-optional', False)

    mapping = [
        ('username', 'username', None),
        ('password', 'password', None),
        ('url', 'kmapClient', None),
        ('categories', 'categories', None),
        ('file-path', 'filePath', None),
        ('app-name', 'appName', None),
        ('bundle', 'bundle', ''),
        ('version', 'version', None),
        ('description', 'description', ''),
        ('icon-path', 'iconPath', ''),
    ]
    convert_mapping_to_xml(kmap, data, mapping, fail_required=True)

    if publish is True:
        publish_optional = XML.SubElement(kmap, 'publishOptional')
        publish_mapping = [
            ('groups', 'teams', ''),
            ('users', 'users', ''),
            ('notify-users', 'sendNotifications', False),
        ]
        convert_mapping_to_xml(
            publish_optional, data, publish_mapping, fail_required=True)


def artifact_resolver(registry, xml_parent, data):
    """yaml: artifact-resolver
    Allows one to resolve artifacts from a maven repository like nexus
    (without having maven installed)
    Requires the Jenkins :jenkins-wiki:`Repository Connector Plugin
    <Repository+Connector+Plugin>`.

    :arg bool fail-on-error: Whether to fail the build on error (default false)
    :arg bool repository-logging: Enable repository logging (default false)
    :arg str target-directory: Where to resolve artifacts to
    :arg list artifacts: list of artifacts to resolve

        :Artifact:
            * **group-id** (`str`) -- Group ID of the artifact
            * **artifact-id** (`str`) -- Artifact ID of the artifact
            * **version** (`str`) -- Version of the artifact
            * **classifier** (`str`) -- Classifier of the artifact (default '')
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


def doxygen(registry, xml_parent, data):
    """yaml: doxygen
    Builds doxygen HTML documentation. Requires the Jenkins
    :jenkins-wiki:`Doxygen plugin <Doxygen+Plugin>`.

    :arg str doxyfile: The doxyfile path (required)
    :arg str install: The doxygen installation to use (required)
    :arg bool ignore-failure: Keep executing build even on doxygen generation
        failure (default false)
    :arg bool unstable-warning: Mark the build as unstable if warnings are
        generated (default false)

    Example:

    .. literalinclude:: /../../tests/builders/fixtures/doxygen001.yaml
       :language: yaml

    """
    doxygen = XML.SubElement(xml_parent,
                             'hudson.plugins.doxygen.DoxygenBuilder')
    mappings = [
        ('doxyfile', 'doxyfilePath', None),
        ('install', 'installationName', None),
        ('ignore-failure', 'continueOnBuildFailure', False),
        ('unstable-warning', 'unstableIfWarnings', False)
    ]
    convert_mapping_to_xml(doxygen, data, mappings, fail_required=True)


def gradle(registry, xml_parent, data):
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


def groovy(registry, xml_parent, data):
    """yaml: groovy
    Execute a groovy script or command.
    Requires the Jenkins :jenkins-wiki:`Groovy Plugin <Groovy+plugin>`.

    :arg str file: Groovy file to run. (Alternative: you can chose a command
        instead)
    :arg str command: Groovy command to run. (Alternative: you can chose a
        script file instead)
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
    XML.SubElement(groovy, 'groovyName').text = str(
        data.get('version', "(Default)"))
    XML.SubElement(groovy, 'parameters').text = str(data.get('parameters', ""))
    XML.SubElement(groovy, 'scriptParameters').text = str(
        data.get('script-parameters', ""))
    XML.SubElement(groovy, 'properties').text = str(data.get('properties', ""))
    XML.SubElement(groovy, 'javaOpts').text = str(data.get('java-opts', ""))
    XML.SubElement(groovy, 'classPath').text = str(data.get('class-path', ""))


def system_groovy(registry, xml_parent, data):
    """yaml: system-groovy
    Execute a system groovy script or command.
    Requires the Jenkins :jenkins-wiki:`Groovy Plugin <Groovy+plugin>`.

    :arg str file: Groovy file to run. (Alternative: you can chose a command
        instead)
    :arg str command: Groovy command to run. (Alternative: you can chose a
        script file instead)
    :arg str bindings: Define variable bindings (in the properties file
        format). Specified variables can be addressed from the script.
        (optional)
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
    XML.SubElement(sysgroovy, 'classpath').text = str(
        data.get('class-path', ""))


def batch(registry, xml_parent, data):
    """yaml: batch
    Execute a batch command.

    :Parameter: the batch command to execute

    Example:

    .. literalinclude:: ../../tests/builders/fixtures/batch.yaml
       :language: yaml
    """
    batch = XML.SubElement(xml_parent, 'hudson.tasks.BatchFile')
    XML.SubElement(batch, 'command').text = data


def powershell(registry, xml_parent, data):
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


def msbuild(registry, xml_parent, data):
    """yaml: msbuild
    Build .NET project using msbuild. Requires the :jenkins-wiki:`Jenkins
    MSBuild Plugin <MSBuild+Plugin>`.

    :arg str msbuild-version: which msbuild configured in Jenkins to use
        (default '(Default)')
    :arg str solution-file: location of the solution file to build (required)
    :arg str extra-parameters: extra parameters to pass to msbuild (default '')
    :arg bool pass-build-variables: should build variables be passed
        to msbuild (default true)
    :arg bool continue-on-build-failure: should the build continue if
        msbuild returns an error (default false)
    :arg bool unstable-if-warnings: If set to true and warnings on compilation,
        the build will be unstable (>=1.20) (default false)

    Full Example:

    .. literalinclude:: ../../tests/builders/fixtures/msbuild-full.yaml
       :language: yaml

    Minimal Example:

    .. literalinclude:: ../../tests/builders/fixtures/msbuild-minimal.yaml
       :language: yaml
    """
    msbuilder = XML.SubElement(xml_parent,
                               'hudson.plugins.msbuild.MsBuildBuilder')
    msbuilder.set('plugin', 'msbuild')

    mapping = [
        ('msbuild-version', 'msBuildName', '(Default)'),
        ('solution-file', 'msBuildFile', None),
        ('extra-parameters', 'cmdLineArgs', ''),
        ('pass-build-variables', 'buildVariablesAsProperties', True),
        ('continue-on-build-failure', 'continueOnBuildFailure', False),
        ('unstable-if-warnings', 'unstableIfWarnings', False)
    ]
    convert_mapping_to_xml(msbuilder, data, mapping, fail_required=True)


def create_builders(registry, step):
    dummy_parent = XML.Element("dummy")
    registry.dispatch('builder', dummy_parent, step)
    return list(dummy_parent)


def conditional_step(registry, xml_parent, data):
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
        (default 'fail').
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

                         :condition-expression: Expression to expand (required)
    build-cause        Run if the current build has a specific cause

                         :cause: The cause why the build was triggered.
                           Following causes are supported -

                           :USER_CAUSE: build was triggered by a manual
                             interaction. (default)
                           :SCM_CAUSE: build was triggered by a SCM change.
                           :TIMER_CAUSE: build was triggered by a timer.
                           :CLI_CAUSE: build was triggered by via CLI interface
                           :REMOTE_CAUSE: build was triggered via remote
                             interface.
                           :UPSTREAM_CAUSE: build was triggered by an upstream
                             project.

                           Following supported if XTrigger plugin installed:

                           :FS_CAUSE: build was triggered by a file system
                             change (FSTrigger Plugin).
                           :URL_CAUSE: build was triggered by a URL change
                             (URLTrigger Plugin)
                           :IVY_CAUSE: build triggered by an Ivy dependency
                             version has change (IvyTrigger Plugin)
                           :SCRIPT_CAUSE: build was triggered by a script
                             (ScriptTrigger Plugin)
                           :BUILDRESULT_CAUSE: build was triggered by a
                             result of an other job (BuildResultTrigger Plugin)
                         :exclusive-cause: (bool) There might by multiple
                           casues causing a build to be triggered, with
                           this true, the cause must be the only one
                           causing this build this build to be triggered.
                           (default false)
    day-of-week        Only run on specific days of the week.

                         :day-selector: Days you want the build to run on.
                           Following values are supported -

                           :weekend: Saturday and Sunday (default).
                           :weekday: Monday - Friday.
                           :select-days: Selected days, defined by 'days'
                             below.
                           :days: True for days for which the build should
                             run. Definition needed only for 'select-days'
                             day-selector, at the same level as day-selector.
                             Define the days to run under this.

                             :SUN: Run on Sunday (default false)
                             :MON: Run on Monday (default false)
                             :TUES: Run on Tuesday (default false)
                             :WED: Run on Wednesday (default false)
                             :THURS: Run on Thursday (default false)
                             :FRI: Run on Friday (default false)
                             :SAT: Run on Saturday (default false)
                         :use-build-time: (bool) Use the build time instead of
                           the the time that the condition is evaluated.
                           (default false)
    execution-node     Run only on selected nodes.

                         :nodes: (list) List of nodes to execute on. (required)
    strings-match      Run the step if two strings match

                         :condition-string1: First string (optional)
                         :condition-string2: Second string (optional)
                         :condition-case-insensitive: Case insensitive
                           (default false)
    current-status     Run the build step if the current build status is
                       within the configured range

                         :condition-worst: Accepted values are SUCCESS,
                           UNSTABLE, FAILURE, NOT_BUILD, ABORTED
                           (default SUCCESS)
                         :condition-best: Accepted values are SUCCESS,
                           UNSTABLE, FAILURE, NOT_BUILD, ABORTED
                           (default SUCCESS)

    shell              Run the step if the shell command succeed

                         :condition-command: Shell command to execute
                           (optional)
    windows-shell      Similar to shell, except that commands will be
                       executed by cmd, under Windows

                         :condition-command: Command to execute (optional)
    file-exists        Run the step if a file exists

                         :condition-filename: Check existence of this file
                           (required)
                         :condition-basedir: If condition-filename is
                           relative, it will be considered relative to
                           either `workspace`, `artifact-directory`,
                           or `jenkins-home`. (default 'workspace')
    files-match        Run if one or more files match the selectors.

                         :include-pattern: (list str) List of Includes
                           Patterns. Since the separator in the patterns is
                           hardcoded as ',', any use of ',' would need
                           escaping. (optional)
                         :exclude-pattern: (list str) List of Excludes
                           Patterns. Since the separator in the patterns is
                           hardcoded as ',', any use of ',' would need
                           escaping. (optional)
                         :condition-basedir: Accepted values are `workspace`,
                           `artifact-directory`, or `jenkins-home`.
                           (default 'workspace')
    num-comp           Run if the numerical comparison is true.

                         :lhs: Left Hand Side. Must evaluate to a number.
                           (required)
                         :rhs: Right Hand Side. Must evaluate to a number.
                           (required)
                         :comparator: Accepted values are `less-than`,
                           `greater-than`, `equal`, `not-equal`,
                           `less-than-equal`, `greater-than-equal`.
                           (default 'less-than')
    regex-match        Run if the Expression matches the Label.

                         :regex: The regular expression used to match the label
                           (optional)
                         :label: The label that will be tested by the regular
                           expression. (optional)
    time               Only run during a certain period of the day.

                         :earliest-hour: Starting hour (default "09")
                         :earliest-min: Starting min (default "00")
                         :latest-hour: Ending hour (default "17")
                         :latest-min: Ending min (default "30")
                         :use-build-time: (bool) Use the build time instead of
                           the the time that the condition is evaluated.
                           (default false)
    not                Run the step if the inverse of the condition-operand
                       is true

                         :condition-operand: Condition to evaluate.  Can be
                           any supported conditional-step condition. (required)
    and                Run the step if logical and of all conditional-operands
                       is true

                         :condition-operands: (list) Conditions to evaluate.
                           Can be any supported conditional-step condition.
                           (required)
    or                 Run the step if logical or of all conditional-operands
                       is true

                         :condition-operands: (list) Conditions to evaluate.
                           Can be any supported conditional-step condition.
                           (required)
    ================== ====================================================

    Example:

    .. literalinclude::
        /../../tests/builders/fixtures/conditional-step-success-failure.yaml
       :language: yaml
    .. literalinclude::
        /../../tests/builders/fixtures/conditional-step-not-file-exists.yaml
       :language: yaml
    .. literalinclude::
        /../../tests/builders/fixtures/conditional-step-day-of-week001.yaml
       :language: yaml
    .. literalinclude::
        /../../tests/builders/fixtures/conditional-step-day-of-week003.yaml
       :language: yaml
    .. literalinclude::
        /../../tests/builders/fixtures/conditional-step-time.yaml
       :language: yaml
    .. literalinclude::
        /../../tests/builders/fixtures/conditional-step-regex-match.yaml
       :language: yaml
    .. literalinclude::
        /../../tests/builders/fixtures/conditional-step-or.yaml
       :language: yaml
    .. literalinclude::
        /../../tests/builders/fixtures/conditional-step-and.yaml
       :language: yaml
    """
    def build_condition(cdata, cond_root_tag):
        kind = cdata['condition-kind']
        ctag = XML.SubElement(cond_root_tag, condition_tag)
        core_prefix = 'org.jenkins_ci.plugins.run_condition.core.'
        logic_prefix = 'org.jenkins_ci.plugins.run_condition.logic.'
        if kind == "always":
            ctag.set('class', core_prefix + 'AlwaysRun')
        elif kind == "never":
            ctag.set('class', core_prefix + 'NeverRun')
        elif kind == "boolean-expression":
            ctag.set('class', core_prefix + 'BooleanCondition')
            try:
                XML.SubElement(ctag, "token").text = (
                    cdata['condition-expression'])
            except KeyError:
                raise MissingAttributeError('condition-expression')
        elif kind == "build-cause":
            ctag.set('class', core_prefix + 'CauseCondition')
            cause_list = ('USER_CAUSE', 'SCM_CAUSE', 'TIMER_CAUSE',
                          'CLI_CAUSE', 'REMOTE_CAUSE', 'UPSTREAM_CAUSE',
                          'FS_CAUSE', 'URL_CAUSE', 'IVY_CAUSE',
                          'SCRIPT_CAUSE', 'BUILDRESULT_CAUSE')
            cause_name = cdata.get('cause', 'USER_CAUSE')
            if cause_name not in cause_list:
                raise InvalidAttributeError('cause', cause_name, cause_list)
            XML.SubElement(ctag, "buildCause").text = cause_name
            XML.SubElement(ctag, "exclusiveCause").text = str(cdata.get(
                'exclusive-cause', False)).lower()
        elif kind == "day-of-week":
            ctag.set('class', core_prefix + 'DayCondition')
            day_selector_class_prefix = core_prefix + 'DayCondition$'
            day_selector_classes = {
                'weekend': day_selector_class_prefix + 'Weekend',
                'weekday': day_selector_class_prefix + 'Weekday',
                'select-days': day_selector_class_prefix + 'SelectDays',
            }
            day_selector = cdata.get('day-selector', 'weekend')
            if day_selector not in day_selector_classes:
                raise InvalidAttributeError('day-selector', day_selector,
                                            day_selector_classes)
            day_selector_tag = XML.SubElement(ctag, "daySelector")
            day_selector_tag.set('class', day_selector_classes[day_selector])
            if day_selector == "select-days":
                days_tag = XML.SubElement(day_selector_tag, "days")
                day_tag_text = ('org.jenkins__ci.plugins.run__condition.'
                                'core.DayCondition_-Day')
                inp_days = cdata.get('days') if cdata.get('days') else {}
                days = ['SUN', 'MON', 'TUES', 'WED', 'THURS', 'FRI', 'SAT']
                for day_no, day in enumerate(days, 1):
                    day_tag = XML.SubElement(days_tag, day_tag_text)
                    XML.SubElement(day_tag, "day").text = str(day_no)
                    XML.SubElement(day_tag, "selected").text = str(
                        inp_days.get(day, False)).lower()
            XML.SubElement(ctag, "useBuildTime").text = str(cdata.get(
                'use-build-time', False)).lower()
        elif kind == "execution-node":
            ctag.set('class', core_prefix + 'NodeCondition')
            allowed_nodes_tag = XML.SubElement(ctag, "allowedNodes")
            try:
                nodes_list = cdata['nodes']
            except KeyError:
                raise MissingAttributeError('nodes')
            for node in nodes_list:
                node_tag = XML.SubElement(allowed_nodes_tag, "string")
                node_tag.text = node
        elif kind == "strings-match":
            ctag.set('class', core_prefix + 'StringsMatchCondition')
            XML.SubElement(ctag, "arg1").text = cdata.get(
                'condition-string1', '')
            XML.SubElement(ctag, "arg2").text = cdata.get(
                'condition-string2', '')
            XML.SubElement(ctag, "ignoreCase").text = str(cdata.get(
                'condition-case-insensitive', False)).lower()
        elif kind == "current-status":
            ctag.set('class', core_prefix + 'StatusCondition')
            wr = XML.SubElement(ctag, 'worstResult')
            wr_name = cdata.get('condition-worst', 'SUCCESS')
            if wr_name not in hudson_model.THRESHOLDS:
                raise InvalidAttributeError('condition-worst', wr_name,
                                            hudson_model.THRESHOLDS.keys())
            wr_threshold = hudson_model.THRESHOLDS[wr_name]
            XML.SubElement(wr, "name").text = wr_threshold['name']
            XML.SubElement(wr, "ordinal").text = wr_threshold['ordinal']
            XML.SubElement(wr, "color").text = wr_threshold['color']
            XML.SubElement(wr, "completeBuild").text = str(
                wr_threshold['complete']).lower()

            br = XML.SubElement(ctag, 'bestResult')
            br_name = cdata.get('condition-best', 'SUCCESS')
            if br_name not in hudson_model.THRESHOLDS:
                raise InvalidAttributeError('condition-best', br_name,
                                            hudson_model.THRESHOLDS.keys())
            br_threshold = hudson_model.THRESHOLDS[br_name]
            XML.SubElement(br, "name").text = br_threshold['name']
            XML.SubElement(br, "ordinal").text = br_threshold['ordinal']
            XML.SubElement(br, "color").text = br_threshold['color']
            XML.SubElement(br, "completeBuild").text = str(
                wr_threshold['complete']).lower()
        elif kind == "shell":
            ctag.set('class',
                     'org.jenkins_ci.plugins.run_condition.contributed.'
                     'ShellCondition')
            XML.SubElement(ctag, "command").text = cdata.get(
                'condition-command', '')
        elif kind == "windows-shell":
            ctag.set('class',
                     'org.jenkins_ci.plugins.run_condition.contributed.'
                     'BatchFileCondition')
            XML.SubElement(ctag, "command").text = cdata.get(
                'condition-command', '')
        elif kind == "file-exists" or kind == "files-match":
            if kind == "file-exists":
                ctag.set('class', core_prefix + 'FileExistsCondition')
                try:
                    XML.SubElement(ctag, "file").text = (
                        cdata['condition-filename'])
                except KeyError:
                    raise MissingAttributeError('condition-filename')
            else:
                ctag.set('class', core_prefix + 'FilesMatchCondition')
                XML.SubElement(ctag, "includes").text = ",".join(cdata.get(
                    'include-pattern', ''))
                XML.SubElement(ctag, "excludes").text = ",".join(cdata.get(
                    'exclude-pattern', ''))
            basedir_class_prefix = ('org.jenkins_ci.plugins.run_condition.'
                                    'common.BaseDirectory$')
            basedir_classes = {
                'workspace': basedir_class_prefix + 'Workspace',
                'artifact-directory': basedir_class_prefix + 'ArtifactsDir',
                'jenkins-home': basedir_class_prefix + 'JenkinsHome'
            }
            basedir = cdata.get('condition-basedir', 'workspace')
            if basedir not in basedir_classes:
                raise InvalidAttributeError('condition-basedir', basedir,
                                            basedir_classes)
            XML.SubElement(ctag, "baseDir").set('class',
                                                basedir_classes[basedir])
        elif kind == "num-comp":
            ctag.set('class', core_prefix + 'NumericalComparisonCondition')
            try:
                XML.SubElement(ctag, "lhs").text = cdata['lhs']
                XML.SubElement(ctag, "rhs").text = cdata['rhs']
            except KeyError as e:
                raise MissingAttributeError(e.args[0])
            comp_class_prefix = core_prefix + 'NumericalComparisonCondition$'
            comp_classes = {
                'less-than': comp_class_prefix + 'LessThan',
                'greater-than': comp_class_prefix + 'GreaterThan',
                'equal': comp_class_prefix + 'EqualTo',
                'not-equal': comp_class_prefix + 'NotEqualTo',
                'less-than-equal': comp_class_prefix + 'LessThanOrEqualTo',
                'greater-than-equal': comp_class_prefix +
                'GreaterThanOrEqualTo'
            }
            comp = cdata.get('comparator', 'less-than')
            if comp not in comp_classes:
                raise InvalidAttributeError('comparator', comp, comp_classes)
            XML.SubElement(ctag, "comparator").set('class',
                                                   comp_classes[comp])
        elif kind == "regex-match":
            ctag.set('class', core_prefix + 'ExpressionCondition')
            XML.SubElement(ctag, "expression").text = cdata.get('regex', '')
            XML.SubElement(ctag, "label").text = cdata.get('label', '')
        elif kind == "time":
            ctag.set('class', core_prefix + 'TimeCondition')
            XML.SubElement(ctag, "earliestHours").text = cdata.get(
                'earliest-hour', '09')
            XML.SubElement(ctag, "earliestMinutes").text = cdata.get(
                'earliest-min', '00')
            XML.SubElement(ctag, "latestHours").text = cdata.get(
                'latest-hour', '17')
            XML.SubElement(ctag, "latestMinutes").text = cdata.get(
                'latest-min', '30')
            XML.SubElement(ctag, "useBuildTime").text = str(cdata.get(
                'use-build-time', False)).lower()
        elif kind == "not":
            ctag.set('class', logic_prefix + 'Not')
            try:
                notcondition = cdata['condition-operand']
            except KeyError:
                raise MissingAttributeError('condition-operand')
            build_condition(notcondition, ctag)
        elif kind == "and" or "or":
            if kind == "and":
                ctag.set('class', logic_prefix + 'And')
            else:
                ctag.set('class', logic_prefix + 'Or')
            conditions_tag = XML.SubElement(ctag, "conditions")
            container_tag_text = ('org.jenkins__ci.plugins.run__condition.'
                                  'logic.ConditionContainer')
            try:
                conditions_list = cdata['condition-operands']
            except KeyError:
                raise MissingAttributeError('condition-operands')
            for condition in conditions_list:
                conditions_container_tag = XML.SubElement(conditions_tag,
                                                          container_tag_text)
                build_condition(condition, conditions_container_tag)

    def build_step(parent, step):
        for edited_node in create_builders(registry, step):
            if not has_multiple_steps:
                edited_node.set('class', edited_node.tag)
                edited_node.tag = 'buildStep'
            parent.append(edited_node)

    cond_builder_tag = ('org.jenkinsci.plugins.conditionalbuildstep.'
                        'singlestep.SingleConditionalBuilder')
    cond_builders_tag = ('org.jenkinsci.plugins.conditionalbuildstep.'
                         'ConditionalBuilder')
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


def maven_builder(registry, xml_parent, data):
    """yaml: maven-builder
    Execute Maven3 builder

    Allows your build jobs to deploy artifacts automatically to Artifactory.

    Requires the Jenkins :jenkins-wiki:`Artifactory Plugin
    <Artifactory+Plugin>`.

    :arg str name: Name of maven installation from the configuration (required)
    :arg str pom: Location of pom.xml (default 'pom.xml')
    :arg str goals: Goals to execute (required)
    :arg str maven-opts: Additional options for maven (default '')

    Example:

    .. literalinclude:: /../../tests/builders/fixtures/maven-builder001.yaml
       :language: yaml
    """
    maven = XML.SubElement(xml_parent, 'org.jfrog.hudson.maven3.Maven3Builder')

    mapping = [
        ('name', 'mavenName', None),
        ('goals', 'goals', None),
        ('pom', 'rootPom', 'pom.xml'),
        ('maven-opts', 'mavenOpts', ''),
    ]
    convert_mapping_to_xml(maven, data, mapping, fail_required=True)


def maven_target(registry, xml_parent, data):
    """yaml: maven-target
    Execute top-level Maven targets.

    Requires the Jenkins :jenkins-wiki:`Config File Provider Plugin
    <Config+File+Provider+Plugin>` for the Config File Provider "settings"
    and "global-settings" config.

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
    :arg str settings-type: Type of settings file file|cfp. (default file)
    :arg str global-settings: Path to use as global settings.xml
        It is possible to provide a ConfigFileProvider settings file, such as
        see CFP Example below. (optional)
    :arg str global-settings-type: Type of settings file file|cfp. (default
        file)

    Example:

    .. literalinclude:: /../../tests/builders/fixtures/maven-target-doc.yaml
       :language: yaml

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


def multijob(registry, xml_parent, data):
    """yaml: multijob
    Define a multijob phase. Requires the Jenkins
    :jenkins-wiki:`Multijob Plugin <Multijob+Plugin>`.

    This builder may only be used in
    :py:class:`jenkins_jobs.modules.project_multijob.MultiJob` projects.

    :arg str name: MultiJob phase name
    :arg str condition: when to trigger the other job.
        Can be: 'SUCCESSFUL', 'UNSTABLE', 'COMPLETED', 'FAILURE', 'ALWAYS'.
        (default 'SUCCESSFUL')

    :arg list projects: list of projects to include in the MultiJob phase

        :Project:
            * **name** (`str`) -- Project name
            * **current-parameters** (`bool`) -- Pass current build
              parameters to the other job (default false)
            * **node-label-name** (`str`) -- Define a list of nodes
              on which the job should be allowed to be executed on.
              Requires NodeLabel Parameter Plugin (optional)
            * **node-label** (`str`) -- Define a label
              of 'Restrict where this project can be run' on the fly.
              Requires NodeLabel Parameter Plugin (optional)
            * **node-parameters** (`bool`) -- Use the same Node for
              the triggered builds that was used for this build. (optional)
            * **git-revision** (`bool`) -- Pass current git-revision
              to the other job (default false)
            * **property-file** (`str`) -- Pass properties from file
              to the other job (optional)
            * **predefined-parameters** (`str`) -- Pass predefined
              parameters to the other job (optional)
            * **abort-all-job** (`bool`) -- Kill allsubs job and the phase job,
              if this subjob is killed (default false)
            * **enable-condition** (`str`) -- Condition to run the
              job in groovy script format (optional)
            * **kill-phase-on** (`str`) -- Stop the phase execution
              on specific job status. Can be 'FAILURE', 'UNSTABLE',
              'NEVER'. (optional)
            * **restrict-matrix-project** (`str`) -- Filter that
              restricts the subset of the combinations that the
              downstream project will run (optional)
            * **retry** (`dict`): Enable retry strategy (optional)
                :retry:
                    * **max-retry** (`int`) -- Max number of retries
                      (default 0)
                    * **strategy-path** (`str`) -- Parsing rules path
                      (required)

    Example:

    .. literalinclude:: /../../tests/builders/fixtures/multibuild.yaml
       :language: yaml
    """
    builder = XML.SubElement(xml_parent, 'com.tikal.jenkins.plugins.multijob.'
                                         'MultiJobBuilder')
    XML.SubElement(builder, 'phaseName').text = data['name']

    condition = data.get('condition', 'SUCCESSFUL')
    conditions_available = ('SUCCESSFUL', 'UNSTABLE', 'COMPLETED', 'FAILURE',
                            'ALWAYS')
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

        # Node parameter
        if project.get('node-parameters', False):
            XML.SubElement(configs, 'hudson.plugins.parameterizedtrigger.'
                                    'NodeParameters')

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

        # Abort all other job
        abortAllJob = str(project.get('abort-all-job', False)).lower()
        XML.SubElement(phaseJob, 'abortAllJob').text = abortAllJob

        # Retry job
        retry = project.get('retry', False)
        if retry:
            try:
                rules_path = str(retry['strategy-path'])
                XML.SubElement(phaseJob, 'parsingRulesPath').text = rules_path
            except KeyError:
                raise MissingAttributeError('strategy-path')
            max_retry = retry.get('max-retry', 0)
            XML.SubElement(phaseJob, 'maxRetries').text = str(int(max_retry))
            XML.SubElement(phaseJob, 'enableRetryStrategy').text = 'true'
        else:
            XML.SubElement(phaseJob, 'enableRetryStrategy').text = 'false'

        # Restrict matrix jobs to a subset
        if project.get('restrict-matrix-project') is not None:
            subset = XML.SubElement(
                configs, 'hudson.plugins.parameterizedtrigger.'
                         'matrix.MatrixSubsetBuildParameters')
            XML.SubElement(
                subset, 'filter').text = project['restrict-matrix-project']

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


def config_file_provider(registry, xml_parent, data):
    """yaml: config-file-provider
    Provide configuration files (i.e., settings.xml for maven etc.)
    which will be copied to the job's workspace.
    Requires the Jenkins :jenkins-wiki:`Config File Provider Plugin
    <Config+File+Provider+Plugin>`.

    :arg list files: List of managed config files made up of three
        parameters

        :files:
            * **file-id** (`str`) -- The identifier for the managed config
              file
            * **target** (`str`) -- Define where the file should be created
              (default '')
            * **variable** (`str`) -- Define an environment variable to be
              used (default '')

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


def grails(registry, xml_parent, data):
    """yaml: grails
    Execute a grails build step. Requires the :jenkins-wiki:`Jenkins Grails
    Plugin <Grails+Plugin>`.

    :arg bool use-wrapper: Use a grails wrapper (default false)
    :arg str name: Select a grails installation to use (default '(Default)')
    :arg bool force-upgrade: Run 'grails upgrade --non-interactive'
        first (default false)
    :arg bool non-interactive: append --non-interactive to all build targets
        (default false)
    :arg str targets: Specify target(s) to run separated by spaces (required)
    :arg str server-port: Specify a value for the server.port system
        property (default '')
    :arg str work-dir: Specify a value for the grails.work.dir system
        property (default '')
    :arg str project-dir: Specify a value for the grails.project.work.dir
        system property (default '')
    :arg str base-dir: Specify a path to the root of the Grails
        project (default '')
    :arg str properties: Additional system properties to set (default '')
    :arg bool plain-output: append --plain-output to all build targets
        (default false)
    :arg bool stack-trace: append --stack-trace to all build targets
        (default false)
    :arg bool verbose: append --verbose to all build targets
        (default false)
    :arg bool refresh-dependencies: append --refresh-dependencies to all
        build targets (default false)

    Full Example:

    .. literalinclude:: ../../tests/builders/fixtures/grails-full.yaml
       :language: yaml

    Minimal Example:

    .. literalinclude:: ../../tests/builders/fixtures/grails-minimal.yaml
       :language: yaml
    """
    grails = XML.SubElement(xml_parent, 'com.g2one.hudson.grails.'
                                        'GrailsBuilder')
    grails.set('plugin', 'grails')

    mappings = [
        ('targets', 'targets', None),
        ('name', 'name', '(Default)'),
        ('work-dir', 'grailsWorkDir', ''),
        ('project-dir', 'projectWorkDir', ''),
        ('base-dir', 'projectBaseDir', ''),
        ('server-port', 'serverPort', ''),
        ('properties', 'properties', ''),
        ('force-upgrade', 'forceUpgrade', False),
        ('non-interactive', 'nonInteractive', False),
        ('use-wrapper', 'useWrapper', False),
        ('plain-output', 'plainOutput', False),
        ('stack-trace', 'stackTrace', False),
        ('verbose', 'verbose', False),
        ('refresh-dependencies', 'refreshDependencies', False),
    ]
    convert_mapping_to_xml(grails, data, mappings, fail_required=True)


def sbt(registry, xml_parent, data):
    """yaml: sbt
    Execute a sbt build step. Requires the Jenkins :jenkins-wiki:`Sbt Plugin
    <sbt+plugin>`.

    :arg str name: Select a sbt installation to use. If no name is
        provided, the first in the list of defined SBT builders will be
        used. (default to first in list)
    :arg str jvm-flags: Parameters to pass to the JVM (default '')
    :arg str actions: Select the sbt tasks to execute (default '')
    :arg str sbt-flags: Add flags to SBT launcher
        (default '-Dsbt.log.noformat=true')
    :arg str subdir-path: Path relative to workspace to run sbt in
        (default '')

    Example:

    .. literalinclude:: ../../tests/builders/fixtures/sbt.yaml
       :language: yaml
    """
    sbt = XML.SubElement(xml_parent, 'org.jvnet.hudson.plugins.'
                                     'SbtPluginBuilder')
    mappings = [
        ('name', 'name', ''),
        ('jvm-flags', 'jvmFlags', ''),
        ('sbt-flags', 'sbtFlags', '-Dsbt.log.noformat=true'),
        ('actions', 'actions', ''),
        ('subdir-path', 'subdirPath', ''),
    ]
    convert_mapping_to_xml(sbt, data, mappings, fail_required=True)


def critical_block_start(registry, xml_parent, data):
    """yaml: critical-block-start
    Designate the start of a critical block. Must be used in conjuction with
    critical-block-end.

    Must also add a build wrapper (exclusion), specifying the resources that
    control the critical block. Otherwise, this will have no effect.

    Requires Jenkins :jenkins-wiki:`Exclusion Plugin <Exclusion-Plugin>`.

    Example:

    .. literalinclude::
        ../../tests/yamlparser/fixtures/critical_block_complete001.yaml
       :language: yaml
    """
    cbs = XML.SubElement(
        xml_parent, 'org.jvnet.hudson.plugins.exclusion.CriticalBlockStart')
    cbs.set('plugin', 'Exclusion')


def critical_block_end(registry, xml_parent, data):
    """yaml: critical-block-end
    Designate the end of a critical block. Must be used in conjuction with
    critical-block-start.

    Must also add a build wrapper (exclusion), specifying the resources that
    control the critical block. Otherwise, this will have no effect.

    Requires Jenkins :jenkins-wiki:`Exclusion Plugin <Exclusion-Plugin>`.

    Example:

    .. literalinclude::
        ../../tests/yamlparser/fixtures/critical_block_complete001.yaml
       :language: yaml
    """
    cbs = XML.SubElement(
        xml_parent, 'org.jvnet.hudson.plugins.exclusion.CriticalBlockEnd')
    cbs.set('plugin', 'Exclusion')


def publish_over_ssh(registry, xml_parent, data):
    """yaml: publish-over-ssh
    Send files or execute commands over SSH.
    Requires the Jenkins :jenkins-wiki:`Publish over SSH Plugin
    <Publish+Over+SSH+Plugin>`.

    :arg str site: name of the ssh site
    :arg str target: destination directory
    :arg bool target-is-date-format: whether target is a date format. If true,
        raw text should be quoted (default false)
    :arg bool clean-remote: should the remote directory be deleted before
        transferring files (default false)
    :arg str source: source path specifier
    :arg str command: a command to execute on the remote server (optional)
    :arg int timeout: timeout in milliseconds for the Exec command (optional)
    :arg bool use-pty: run the exec command in pseudo TTY (default false)
    :arg str excludes: excluded file pattern (optional)
    :arg str remove-prefix: prefix to remove from uploaded file paths
        (optional)
    :arg bool fail-on-error: fail the build if an error occurs (default false)

    Example:

    .. literalinclude:: /../../tests/builders/fixtures/publish-over-ssh.yaml
       :language: yaml
    """
    ssh(registry, xml_parent, data)


def saltstack(parser, xml_parent, data):
    """yaml: saltstack

    Send a message to Salt API. Requires the :jenkins-wiki:`saltstack plugin
    <saltstack-plugin>`.

    :arg str servername: Salt master server name (required)
    :arg str authtype: Authentication type ('pam' or 'ldap', default 'pam')
    :arg str credentials: Credentials ID for which to authenticate to Salt
        master (required)
    :arg str target: Target minions (default '')
    :arg str targettype: Target type ('glob', 'pcre', 'list', 'grain',
        'pillar', 'nodegroup', 'range', or 'compound', default 'glob')
    :arg str function: Function to execute (default '')
    :arg str arguments: Salt function arguments (default '')
    :arg str kwarguments: Salt keyword arguments (default '')
    :arg bool saveoutput: Save Salt return data into environment variable
        (default false)
    :arg str clientinterface: Client interface type ('local', 'local-batch',
        or 'runner', default 'local')
    :arg bool wait: Wait for completion of command (default false)
    :arg str polltime: Number of seconds to wait before polling job completion
        status (default '')
    :arg str batchsize: Salt batch size, absolute value or %-age (default 100%)
    :arg str mods: Mods to runner (default '')
    :arg bool setpillardata: Set Pillar data (default false)
    :arg str pillarkey: Pillar key (default '')
    :arg str pillarvalue: Pillar value (default '')

    Minimal Example:

    .. literalinclude:: ../../tests/builders/fixtures/saltstack-minimal.yaml
       :language: yaml

    Full Example:

    .. literalinclude:: ../../tests/builders/fixtures/saltstack-full.yaml
       :language: yaml
    """
    saltstack = XML.SubElement(xml_parent, 'com.waytta.SaltAPIBuilder')

    supported_auth_types = ['pam', 'ldap']
    supported_target_types = ['glob', 'pcre', 'list', 'grain', 'pillar',
                              'nodegroup', 'range', 'compound']
    supported_client_interfaces = ['local', 'local-batch', 'runner']

    mapping = [
        ('servername', 'servername', None),
        ('credentials', 'credentialsId', None),
        ('authtype', 'authtype', 'pam', supported_auth_types),
        ('target', 'target', ''),
        ('targettype', 'targettype', 'glob', supported_target_types),
        ('clientinterface', 'clientInterface', 'local',
            supported_client_interfaces),
        ('function', 'function', ''),
        ('arguments', 'arguments', ''),
        ('kwarguments', 'kwarguments', ''),
        ('setpillardata', 'usePillar', False),
        ('pillarkey', 'pillarkey', ''),
        ('pillarvalue', 'pillarvalue', ''),
        ('wait', 'blockbuild', False),
        ('polltime', 'jobPollTime', ''),
        ('batchsize', 'batchSize', '100%'),
        ('mods', 'mods', ''),
        ('saveoutput', 'saveEnvVar', False)
    ]

    helpers.convert_mapping_to_xml(saltstack, data, mapping,
                                   fail_required=True)

    clientInterface = data.get('clientinterface', 'local')
    blockbuild = str(data.get('wait', False)).lower()
    jobPollTime = str(data.get('polltime', ''))
    batchSize = data.get('batchsize', '100%')
    mods = data.get('mods', '')
    usePillar = str(data.get('setpillardata', False)).lower()

    # Build the clientInterfaces structure, based on the
    # clientinterface setting
    clientInterfaces = XML.SubElement(saltstack, 'clientInterfaces')
    XML.SubElement(clientInterfaces, 'nullObject').text = 'false'

    ci_attrib = {
        'class': 'org.apache.commons.collections.map.ListOrderedMap',
        'serialization': 'custom'
    }
    properties = XML.SubElement(clientInterfaces, 'properties', ci_attrib)

    lomElement = 'org.apache.commons.collections.map.ListOrderedMap'
    listOrderedMap = XML.SubElement(properties, lomElement)

    default = XML.SubElement(listOrderedMap, 'default')
    ordered_map = XML.SubElement(listOrderedMap, 'map')

    insertOrder = XML.SubElement(default, 'insertOrder')

    ci_config = []
    if clientInterface == 'local':
        ci_config = [
            ('blockbuild', blockbuild),
            ('jobPollTime', jobPollTime),
            ('clientInterface', clientInterface)
        ]

    elif clientInterface == 'local-batch':
        ci_config = [
            ('batchSize', batchSize),
            ('clientInterface', clientInterface)
        ]

    elif clientInterface == 'runner':
        ci_config = [
            ('mods', mods),
            ('clientInterface', clientInterface)
        ]

        if usePillar == 'true':
            ci_config.append(('usePillar', usePillar))

            pillar_cfg = [
                ('pillarkey', data.get('pillarkey')),
                ('pillarvalue', data.get('pillarvalue'))
            ]

    for emt, value in ci_config:
        XML.SubElement(insertOrder, 'string').text = emt
        entry = XML.SubElement(ordered_map, 'entry')
        XML.SubElement(entry, 'string').text = emt

        # Special handling when usePillar == true, requires additional
        # structure in the builder XML
        if emt != 'usePillar':
            XML.SubElement(entry, 'string').text = value
        else:
            jsonobj = XML.SubElement(entry, 'net.sf.json.JSONObject')
            XML.SubElement(jsonobj, 'nullObject').text = 'false'

            pillarProps = XML.SubElement(jsonobj, 'properties', ci_attrib)
            XML.SubElement(pillarProps, 'unserializable-parents')

            pillarLom = XML.SubElement(pillarProps, lomElement)

            pillarDefault = XML.SubElement(pillarLom, 'default')
            pillarMap = XML.SubElement(pillarLom, 'map')
            pillarInsertOrder = XML.SubElement(pillarDefault, 'insertOrder')

            for pemt, value in pillar_cfg:
                XML.SubElement(pillarInsertOrder, 'string').text = pemt
                pillarEntry = XML.SubElement(pillarMap, 'entry')
                XML.SubElement(pillarEntry, 'string').text = pemt
                XML.SubElement(pillarEntry, 'string').text = value


class Builders(jenkins_jobs.modules.base.Base):
    sequence = 60

    component_type = 'builder'
    component_list_type = 'builders'

    def gen_xml(self, xml_parent, data):

        for alias in ['prebuilders', 'builders', 'postbuilders']:
            if alias in data:
                builders = XML.SubElement(xml_parent, alias)
                for builder in data[alias]:
                    self.registry.dispatch('builder', builders, builder)

        # Make sure freestyle projects always have a <builders> entry
        # or Jenkins v1.472 (at least) will NPE.
        project_type = data.get('project-type', 'freestyle')
        if project_type in ('freestyle', 'matrix') and 'builders' not in data:
            XML.SubElement(xml_parent, 'builders')


def shining_panda(registry, xml_parent, data):
    """yaml: shining-panda
    Execute a command inside various python environments. Requires the Jenkins
    :jenkins-wiki:`ShiningPanda plugin <ShiningPanda+Plugin>`.

    :arg str build-environment: Building environment to set up (required).

        :build-environment values:
            * **python**: Use a python installation configured in Jenkins.
            * **custom**: Use a manually installed python.
            * **virtualenv**: Create a virtualenv

    For the **python** environment

    :arg str python-version: Name of the python installation to use.
        Must match one of the configured installations on server
        configuration (default 'System-CPython-2.7')

    For the **custom** environment:

    :arg str home: path to the home folder of the custom installation
        (required)

    For the **virtualenv** environment:

    :arg str python-version: Name of the python installation to use.
        Must match one of the configured installations on server
        configuration (default 'System-CPython-2.7')
    :arg str name: Name of this virtualenv. Two virtualenv builders with
        the same name will use the same virtualenv installation (optional)
    :arg bool clear: If true, delete and recreate virtualenv on each build.
        (default false)
    :arg bool use-distribute: if true use distribute, if false use
        setuptools. (default true)
    :arg bool system-site-packages: if true, give access to the global
        site-packages directory to the virtualenv. (default false)

    Common to all environments:

    :arg str nature: Nature of the command field. (default shell)

        :nature values:
            * **shell**: execute the Command contents with default shell
            * **xshell**: like **shell** but performs platform conversion
              first
            * **python**: execute the Command contents with the Python
              executable

    :arg str command: The command to execute
    :arg bool ignore-exit-code: mark the build as failure if any of the
        commands exits with a non-zero exit code. (default false)

    Examples:

    .. literalinclude::
        /../../tests/builders/fixtures/shining-panda-pythonenv.yaml
       :language: yaml

    .. literalinclude::
        /../../tests/builders/fixtures/shining-panda-customenv.yaml
       :language: yaml

    .. literalinclude::
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


def tox(registry, xml_parent, data):
    """yaml: tox
    Use tox to build a multi-configuration project. Requires the Jenkins
    :jenkins-wiki:`ShiningPanda plugin <ShiningPanda+Plugin>`.

    :arg str ini: The TOX configuration file path (default tox.ini)
    :arg bool recreate: If true, create a new environment each time (default
        false)
    :arg str toxenv-pattern: The pattern used to build the TOXENV environment
        variable. (optional)

    Example:

    .. literalinclude:: /../../tests/builders/fixtures/tox001.yaml
       :language: yaml
    """
    pluginelement = 'jenkins.plugins.shiningpanda.builders.ToxBuilder'
    t = XML.SubElement(xml_parent, pluginelement)
    XML.SubElement(t, 'toxIni').text = data.get('ini', 'tox.ini')
    XML.SubElement(t, 'recreate').text = str(
        data.get('recreate', False)).lower()
    pattern = data.get('toxenv-pattern')
    if pattern:
        XML.SubElement(t, 'toxenvPattern').text = pattern


def managed_script(registry, xml_parent, data):
    """yaml: managed-script
    This step allows to reference and execute a centrally managed
    script within your build. Requires the Jenkins
    :jenkins-wiki:`Managed Script Plugin <Managed+Script+Plugin>`.

    :arg str script-id: Id of script to execute (required)
    :arg str type: Type of managed file (default script)

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


def cmake(registry, xml_parent, data):
    """yaml: cmake
    Execute a CMake target. Requires the Jenkins :jenkins-wiki:`CMake Plugin
    <CMake+Plugin>`.

    This builder is compatible with both versions 2.x and 1.x of the
    plugin. When specifying paramenters from both versions only the ones from
    the installed version in Jenkins will be used, and the rest will be
    ignored.

    :arg str source-dir: the source code directory relative to the workspace
        directory. (required)
    :arg str build-type: Sets the "build type" option for CMake (default
        "Debug").
    :arg str preload-script: Path to a CMake preload script file. (optional)
    :arg str other-arguments: Other arguments to be added to the CMake
        call. (optional)
    :arg bool clean-build-dir: If true, delete the build directory before each
        build (default false).

    :arg list generator: The makefile generator (default "Unix Makefiles").

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

    :Version 2.x: Parameters that available only to versions 2.x of the plugin

        * **working-dir** (`str`): The directory where the project will be
          built in. Relative to the workspace directory. (optional)
        * **installation-name** (`str`): The CMake installation to be used on
          this builder. Use one defined in your Jenkins global configuration
          page (default "InSearchPath").
        * **build-tool-invocations** (`list`): list of build tool invocations
          that will happen during the build:

            :Build tool invocations:
                * **use-cmake** (`str`) -- Whether to run the actual build tool
                    directly (by expanding ``$CMAKE_BUILD_TOOL``) or to have
                    cmake run the build tool (by invoking ``cmake --build
                    <dir>``) (default false).
                * **arguments** (`str`) -- Specify arguments to pass to the
                    build tool or cmake (separated by spaces). Arguments may
                    contain spaces if they are enclosed in double
                    quotes. (optional)
                * **environment-variables** (`str`) -- Specify extra
                    environment variables to pass to the build tool as
                    key-value pairs here. Each entry must be on its own line,
                    for example:

                      ``DESTDIR=${WORKSPACE}/artifacts/dir``

                      ``KEY=VALUE``

    :Version 1.x: Parameters available only to versions 1.x of the plugin

        * **build-dir** (`str`): The directory where the project will be built
          in.  Relative to the workspace directory. (optional)
        * **install-dir** (`str`): The directory where the project will be
          installed in, relative to the workspace directory. (optional)
        * **build-type** (`list`): Sets the "build type" option. A custom type
          different than the default ones specified on the CMake plugin can
          also be set, which will be automatically used in the "Other Build
          Type" option of the plugin. (default "Debug")

            :Default types present in the CMake plugin:
                * **Debug**
                * **Release**
                * **RelWithDebInfo**
                * **MinSizeRel**

        * **make-command** (`str`): The make command (default "make").
        * **install-command** (`arg`): The install command (default "make
          install").
        * **custom-cmake-path** (`str`): Path to cmake executable. (optional)
        * **clean-install-dir** (`bool`): If true, delete the install dir
          before each build (default false).

    Example (Versions 2.x):

    .. literalinclude::
        ../../tests/builders/fixtures/cmake/version-2.0/complete-2.x.yaml
       :language: yaml

    Example (Versions 1.x):

    .. literalinclude::
        ../../tests/builders/fixtures/cmake/version-1.10/complete-1.x.yaml
       :language: yaml
    """

    BUILD_TYPES = ['Debug', 'Release', 'RelWithDebInfo', 'MinSizeRel']

    cmake = XML.SubElement(xml_parent, 'hudson.plugins.cmake.CmakeBuilder')

    source_dir = XML.SubElement(cmake, 'sourceDir')
    try:
        source_dir.text = data['source-dir']
    except KeyError:
        raise MissingAttributeError('source-dir')

    XML.SubElement(cmake, 'generator').text = str(
        data.get('generator', "Unix Makefiles"))

    XML.SubElement(cmake, 'preloadScript').text = str(
        data.get('preload-script', ''))

    XML.SubElement(cmake, 'cleanBuild').text = str(
        data.get('clean-build-dir', False)).lower()

    plugin_info = registry.get_plugin_info("CMake plugin")
    version = pkg_resources.parse_version(plugin_info.get("version", "1.0"))

    # Version 2.x breaks compatibility. So parse the input data differently
    # based on it:
    if version >= pkg_resources.parse_version("2.0"):
        XML.SubElement(cmake, 'workingDir').text = str(
            data.get('working-dir', ''))

        XML.SubElement(cmake, 'buildType').text = str(
            data.get('build-type', 'Debug'))

        XML.SubElement(cmake, 'installationName').text = str(
            data.get('installation-name', 'InSearchPath'))

        XML.SubElement(cmake, 'toolArgs').text = str(
            data.get('other-arguments', ''))

        tool_steps = XML.SubElement(cmake, 'toolSteps')

        for step_data in data.get('build-tool-invocations', []):
            tagname = 'hudson.plugins.cmake.BuildToolStep'
            step = XML.SubElement(tool_steps, tagname)

            XML.SubElement(step, 'withCmake').text = str(
                step_data.get('use-cmake', False)).lower()

            XML.SubElement(step, 'args').text = str(
                step_data.get('arguments', ''))

            XML.SubElement(step, 'vars').text = str(
                step_data.get('environment-variables', ''))

    else:
        build_dir = XML.SubElement(cmake, 'buildDir')
        build_dir.text = data.get('build-dir', '')

        install_dir = XML.SubElement(cmake, 'installDir')
        install_dir.text = data.get('install-dir', '')

        # The options buildType and otherBuildType work together on the CMake
        # plugin:
        #  * If the passed value is one of the predefined values, set buildType
        #    to it and otherBuildType to blank;
        #  * Otherwise, set otherBuildType to the value, and buildType to
        #    "Debug". The CMake plugin will ignore the buildType option.
        #
        # It is strange and confusing that the plugin author chose to do
        # something like that instead of simply passing a string "buildType"
        # option, so this was done to simplify it for the JJB user.
        build_type = XML.SubElement(cmake, 'buildType')
        build_type.text = data.get('build-type', BUILD_TYPES[0])

        other_build_type = XML.SubElement(cmake, 'otherBuildType')

        if(build_type.text not in BUILD_TYPES):
            other_build_type.text = build_type.text
            build_type.text = BUILD_TYPES[0]
        else:
            other_build_type.text = ''

        make_command = XML.SubElement(cmake, 'makeCommand')
        make_command.text = data.get('make-command', 'make')

        install_command = XML.SubElement(cmake, 'installCommand')
        install_command.text = data.get('install-command', 'make install')

        other_cmake_args = XML.SubElement(cmake, 'cmakeArgs')
        other_cmake_args.text = data.get('other-arguments', '')

        custom_cmake_path = XML.SubElement(cmake, 'projectCmakePath')
        custom_cmake_path.text = data.get('custom-cmake-path', '')

        clean_install_dir = XML.SubElement(cmake, 'cleanInstallDir')
        clean_install_dir.text = str(data.get('clean-install-dir',
                                              False)).lower()

        # The plugin generates this tag, but there doesn't seem to be anything
        # that can be configurable by it. Let's keep it to maintain
        # compatibility:
        XML.SubElement(cmake, 'builderImpl')


def dsl(registry, xml_parent, data):
    """yaml: dsl
    Process Job DSL

    Requires the Jenkins :jenkins-wiki:`Job DSL plugin <Job+DSL+Plugin>`.

    :arg str script-text: dsl script which is Groovy code (Required if targets
        is not specified)
    :arg str targets: Newline separated list of DSL scripts, located in the
        Workspace. Can use wildcards like 'jobs/\*/\*/\*.groovy' (Required
        if script-text is not specified)
    :arg str ignore-existing: Ignore previously generated jobs and views
    :arg str removed-job-action: Specifies what to do when a previously
        generated job is not referenced anymore, can be 'IGNORE', 'DISABLE',
        or 'DELETE' (default 'IGNORE')
    :arg str removed-view-action: Specifies what to do when a previously
        generated view is not referenced anymore, can be 'IGNORE' or 'DELETE'.
        (default 'IGNORE')
    :arg str lookup-strategy: Determines how relative job names in DSL
        scripts are interpreted, can be 'JENKINS_ROOT' or 'SEED_JOB'.
        (default 'JENKINS_ROOT')
    :arg str additional-classpath: Newline separated list of additional
        classpath entries for the Job DSL scripts. All entries must be
        relative to the workspace root, e.g. build/classes/main. (optional)

    Example:

    .. literalinclude:: /../../tests/builders/fixtures/dsl001.yaml
       :language: yaml
    .. literalinclude:: /../../tests/builders/fixtures/dsl002.yaml
       :language: yaml

    """

    dsl = XML.SubElement(xml_parent,
                         'javaposse.jobdsl.plugin.ExecuteDslScripts')

    if 'target' in data:
        if 'targets' not in data:
            logger.warning("Converting from old format of 'target' to new "
                           "name 'targets', please update your job "
                           "definitions.")
            data['targets'] = data['target']
        else:
            logger.warning("Ignoring old argument 'target' in favour of new "
                           "format argument 'targets', please remove old "
                           "format.")

    if data.get('script-text'):
        XML.SubElement(dsl, 'scriptText').text = data.get('script-text')
        XML.SubElement(dsl, 'usingScriptText').text = 'true'
    elif data.get('targets'):
        XML.SubElement(dsl, 'targets').text = data.get('targets')
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


def github_notifier(registry, xml_parent, data):
    """yaml: github-notifier
    Set pending build status on Github commit.
    Requires the Jenkins :jenkins-wiki:`Github Plugin <GitHub+Plugin>`.

    Example:

    .. literalinclude:: /../../tests/builders/fixtures/github-notifier.yaml
       :language: yaml
    """
    XML.SubElement(xml_parent,
                   'com.cloudbees.jenkins.GitHubSetCommitStatusBuilder')


def scan_build(registry, xml_parent, data):
    """yaml: scan-build
    This plugin allows you configure a build step that will execute the Clang
    scan-build static analysis tool against an XCode project.

    The scan-build report has to be generated in the directory
    ``${WORKSPACE}/clangScanBuildReports`` for the publisher to find it.

    Requires the Jenkins :jenkins-wiki:`Clang Scan-Build Plugin
    <Clang+Scan-Build+Plugin>`.

    :arg str target: Provide the exact name of the XCode target you wish to
        have compiled and analyzed (required)
    :arg str target-sdk: Set the simulator version of a currently installed SDK
        (default iphonesimulator)
    :arg str config: Provide the XCode config you wish to execute scan-build
        against (default Debug)
    :arg str clang-install-name: Name of clang static analyzer to use (default
        '')
    :arg str xcode-sub-path: Path of XCode project relative to the workspace
        (default '')
    :arg str workspace: Name of workspace (default '')
    :arg str scheme: Name of scheme (default '')
    :arg str scan-build-args: Additional arguments to clang scan-build
        (default --use-analyzer Xcode)
    :arg str xcode-build-args: Additional arguments to XCode (default
        -derivedDataPath $WORKSPACE/build)
    :arg str report-folder: Folder where generated reports are located
        (>=1.7) (default clangScanBuildReports)

    Full Example:

    .. literalinclude:: /../../tests/builders/fixtures/scan-build-full.yaml
       :language: yaml

    Minimal Example:

    .. literalinclude::
       /../../tests/builders/fixtures/scan-build-minimal.yaml
       :language: yaml
    """
    p = XML.SubElement(
        xml_parent,
        'jenkins.plugins.clangscanbuild.ClangScanBuildBuilder')
    p.set('plugin', 'clang-scanbuild')

    mappings = [
        ('target', 'target', None),
        ('target-sdk', 'targetSdk', 'iphonesimulator'),
        ('config', 'config', 'Debug'),
        ('clang-install-name', 'clangInstallationName', ''),
        ('xcode-sub-path', 'xcodeProjectSubPath', 'myProj/subfolder'),
        ('workspace', 'workspace', ''),
        ('scheme', 'scheme', ''),
        ('scan-build-args', 'scanbuildargs', '--use-analyzer Xcode'),
        ('xcode-build-args',
         'xcodebuildargs',
         '-derivedDataPath $WORKSPACE/build'),
        ('report-folder', 'outputFolderName', 'clangScanBuildReports'),
    ]
    convert_mapping_to_xml(p, data, mappings, fail_required=True)


def ssh_builder(registry, xml_parent, data):
    """yaml: ssh-builder
    Executes command on remote host
    Requires the Jenkins :jenkins-wiki:`SSH plugin <SSH+plugin>`.

    :arg str ssh-user-ip: user@ip:ssh_port of machine that was defined
        in jenkins according to SSH plugin instructions
    :arg str command: command to run on remote server

    Example:

    .. literalinclude:: /../../tests/builders/fixtures/ssh-builder.yaml
       :language: yaml
    """
    builder = XML.SubElement(
        xml_parent, 'org.jvnet.hudson.plugins.SSHBuilder')
    try:
        XML.SubElement(builder, 'siteName').text = str(data['ssh-user-ip'])
        XML.SubElement(builder, 'command').text = str(data['command'])
    except KeyError as e:
        raise MissingAttributeError("'%s'" % e.args[0])


def sonar(registry, xml_parent, data):
    """yaml: sonar
    Invoke standalone Sonar analysis.
    Requires the Jenkins `Sonar Plugin.
    <http://docs.sonarqube.org/display/SCAN/\
        Analyzing+with+SonarQube+Scanner+for+Jenkins\
        #AnalyzingwithSonarQubeScannerforJenkins-\
        AnalyzingwiththeSonarQubeScanner>`_

    :arg str sonar-name: Name of the Sonar installation.
    :arg str task: Task to run. (default '')
    :arg str project: Path to Sonar project properties file. (default '')
    :arg str properties: Sonar configuration properties. (default '')
    :arg str java-opts: Java options for Sonnar Runner. (default '')
    :arg str additional-arguments: additional command line arguments
        (default '')
    :arg str jdk: JDK to use (inherited from the job if omitted). (optional)

    Example:

    .. literalinclude:: /../../tests/builders/fixtures/sonar.yaml
       :language: yaml
    """
    sonar = XML.SubElement(xml_parent,
                           'hudson.plugins.sonar.SonarRunnerBuilder')
    sonar.set('plugin', 'sonar')
    XML.SubElement(sonar, 'installationName').text = data['sonar-name']
    mappings = [
        ('task', 'task', ''),
        ('project', 'project', ''),
        ('properties', 'properties', ''),
        ('java-opts', 'javaOpts', ''),
        ('additional-arguments', 'additionalArguments', ''),
    ]
    convert_mapping_to_xml(sonar, data, mappings, fail_required=True)
    if 'jdk' in data:
        XML.SubElement(sonar, 'jdk').text = data['jdk']


def xcode(registry, xml_parent, data):
    """yaml: xcode
    This step allows to execute an xcode build step. Requires the Jenkins
    :jenkins-wiki:`Xcode Plugin <Xcode+Plugin>`.

    :arg str developer-profile: the jenkins credential id for a
        ios developer profile. (optional)
    :arg bool clean-build: if true will delete the build directories
        before invoking the build. (default false)
    :arg bool clean-test-reports: UNKNOWN. (default false)
    :arg bool archive: if true will generate an xcarchive of the specified
        scheme. A workspace and scheme are are also needed for archives.
        (default false)
    :arg str configuration: This is the name of the configuration
        as defined in the Xcode project. (default 'Release')
    :arg str configuration-directory: The value to use for
        CONFIGURATION_BUILD_DIR setting. (default '')
    :arg str target: Leave empty for all targets. (default '')
    :arg str sdk: Leave empty for default SDK. (default '')
    :arg str symroot: Leave empty for default SYMROOT. (default '')
    :arg str project-path: Relative path within the workspace
        that contains the xcode project file(s). (default '')
    :arg str project-file: Only needed if there is more than one
        project file in the Xcode Project Directory. (default '')
    :arg str build-arguments: Extra commandline arguments provided
        to the xcode builder. (default '')
    :arg str schema: Only needed if you want to compile for a
        specific schema instead of a target. (default '')
    :arg str workspace: Only needed if you want to compile a
        workspace instead of a project. (default '')
    :arg str profile: The relative path to the mobileprovision to embed,
        leave blank for no embedded profile. (default '')
    :arg str codesign-id: Override the code signing identity specified
        in the project. (default '')
    :arg bool allow-failing: if true will prevent this build step from
        failing if xcodebuild exits with a non-zero return code. (default
        false)
    :arg str version-technical: The value to use for CFBundleVersion.
        Leave blank to use project's technical number. (default '')
    :arg str version-marketing: The value to use for
        CFBundleShortVersionString. Leave blank to use project's
        marketing number. (default '')
    :arg str ipa-version: A pattern for the ipa file name. You may use
        ${VERSION} and ${BUILD_DATE} (yyyy.MM.dd) in this string.
        (default '')
    :arg str ipa-output: The output directory for the .ipa file,
        relative to the build directory. (default '')
    :arg str keychain-name: The globally configured keychain to unlock for
        this build. (default '')
    :arg str keychain-path: The path of the keychain to use to sign the IPA.
        (default '')
    :arg str keychain-password: The password to use to unlock the keychain.
        (default '')
    :arg str keychain-unlock: Unlocks the keychain during use.
        (default false)

    Example:

    .. literalinclude:: /../../tests/builders/fixtures/xcode.yaml
       :language: yaml
    """

    if data.get('developer-profile'):
        profile = XML.SubElement(xml_parent, 'au.com.rayh.'
                                 'DeveloperProfileLoader')
        XML.SubElement(profile, 'id').text = str(
            data['developer-profile'])

    xcode = XML.SubElement(xml_parent, 'au.com.rayh.XCodeBuilder')

    XML.SubElement(xcode, 'cleanBeforeBuild').text = str(
        data.get('clean-build', False)).lower()
    XML.SubElement(xcode, 'cleanTestReports').text = str(
        data.get('clean-test-reports', False)).lower()
    XML.SubElement(xcode, 'generateArchive').text = str(
        data.get('archive', False)).lower()

    XML.SubElement(xcode, 'configuration').text = str(
        data.get('configuration', 'Release'))
    XML.SubElement(xcode, 'configurationBuildDir').text = str(
        data.get('configuration-directory', ''))
    XML.SubElement(xcode, 'target').text = str(data.get('target', ''))
    XML.SubElement(xcode, 'sdk').text = str(data.get('sdk', ''))
    XML.SubElement(xcode, 'symRoot').text = str(data.get('symroot', ''))

    XML.SubElement(xcode, 'xcodeProjectPath').text = str(
        data.get('project-path', ''))
    XML.SubElement(xcode, 'xcodeProjectFile').text = str(
        data.get('project-file', ''))
    XML.SubElement(xcode, 'xcodebuildArguments').text = str(
        data.get('build-arguments', ''))
    XML.SubElement(xcode, 'xcodeSchema').text = str(data.get('schema', ''))
    XML.SubElement(xcode, 'xcodeWorkspaceFile').text = str(
        data.get('workspace', ''))
    XML.SubElement(xcode, 'embeddedProfileFile').text = str(
        data.get('profile', ''))

    XML.SubElement(xcode, 'codeSigningIdentity').text = str(
        data.get('codesign-id', ''))
    XML.SubElement(xcode, 'allowFailingBuildResults').text = str(
        data.get('allow-failing', False)).lower()

    version = XML.SubElement(xcode, 'provideApplicationVersion')
    version_technical = XML.SubElement(xcode,
                                       'cfBundleVersionValue')
    version_marketing = XML.SubElement(xcode,
                                       'cfBundleShortVersionStringValue')
    if data.get('version-technical') or data.get('version-marketing'):
        version.text = 'true'
        version_technical.text = data.get('version-technical', '')
        version_marketing.text = data.get('version-marketing', '')
    else:
        version.text = 'false'

    XML.SubElement(xcode, 'buildIpa').text = str(
        bool(data.get('ipa-version')) or False).lower()
    XML.SubElement(xcode, 'ipaName').text = data.get('ipa-version', '')
    XML.SubElement(xcode, 'ipaOutputDirectory').text = str(
        data.get('ipa-output', ''))

    XML.SubElement(xcode, 'keychainName').text = str(
        data.get('keychain-name', ''))
    XML.SubElement(xcode, 'keychainPath').text = str(
        data.get('keychain-path', ''))
    XML.SubElement(xcode, 'keychainPwd').text = str(
        data.get('keychain-password', ''))
    XML.SubElement(xcode, 'unlockKeychain').text = str(
        data.get('keychain-unlock', False)).lower()


def sonatype_clm(registry, xml_parent, data):
    """yaml: sonatype-clm
    Requires the Jenkins :jenkins-wiki:`Sonatype CLM Plugin
    <Sonatype+CLM+%28formerly+Insight+for+CI%29>`.

    :arg str value: Select CLM application from a list of available CLM
        applications or specify CLM Application ID (default list)
    :arg str application-name: Determines the policy elements to associate
        with this build. (required)
    :arg str username: Username on the Sonatype CLM server. Leave empty to
        use the username configured at global level. (default '')
    :arg str password: Password on the Sonatype CLM server. Leave empty to
        use the password configured at global level. (default '')
    :arg bool fail-on-clm-server-failure: Controls the build outcome if there
        is a failure in communicating with the CLM server. (default false)
    :arg str stage: Controls the stage the policy evaluation will be run
        against on the CLM server. Valid stages: build, stage-release, release,
        operate. (default 'build')
    :arg str scan-targets: Pattern of files to include for scanning.
        (default '')
    :arg str module-excludes: Pattern of files to exclude. (default '')
    :arg str advanced-options: Options to be set on a case-by-case basis as
        advised by Sonatype Support. (default '')

    Minimal Example:

    .. literalinclude::
        /../../tests/builders/fixtures/sonatype-clm-minimal.yaml
       :language: yaml

    Full Example:

    .. literalinclude::
        /../../tests/builders/fixtures/sonatype-clm-complete.yaml
       :language: yaml
    """
    clm = XML.SubElement(xml_parent,
                         'com.sonatype.insight.ci.hudson.PreBuildScan')
    clm.set('plugin', 'sonatype-clm-ci')
    SUPPORTED_VALUES = ['list', 'manual']
    SUPPORTED_STAGES = ['build', 'stage-release', 'release', 'operate']

    application_select = XML.SubElement(clm,
                                        'applicationSelectType')
    application_mappings = [
        ('value', 'value', 'list', SUPPORTED_VALUES),
        ('application-name', 'applicationId', None),
    ]
    convert_mapping_to_xml(
        application_select, data, application_mappings, fail_required=True)

    path = XML.SubElement(clm, 'pathConfig')
    path_mappings = [
        ('scan-targets', 'scanTargets', ''),
        ('module-excludes', 'moduleExcludes', ''),
        ('advanced-options', 'scanProperties', ''),
    ]
    convert_mapping_to_xml(path, data, path_mappings, fail_required=True)

    mappings = [
        ('fail-on-clm-server-failure', 'failOnClmServerFailures', False),
        ('stage', 'stageId', 'build', SUPPORTED_STAGES),
        ('username', 'username', ''),
        ('password', 'password', ''),
    ]
    convert_mapping_to_xml(clm, data, mappings, fail_required=True)


def beaker(registry, xml_parent, data):
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


def cloudformation(registry, xml_parent, data):
    """yaml: cloudformation
    Create cloudformation stacks before running a build and optionally
    delete them at the end.  Requires the Jenkins :jenkins-wiki:`AWS
    Cloudformation Plugin <AWS+Cloudformation+Plugin>`.

    :arg list name: The names of the stacks to create (required)
    :arg str description: Description of the stack (optional)
    :arg str recipe: The cloudformation recipe file (required)
    :arg list parameters: List of key/value pairs to pass
        into the recipe, will be joined together into a comma separated
        string (optional)
    :arg int timeout: Number of seconds to wait before giving up creating
        a stack (default 0)
    :arg str access-key: The Amazon API Access Key (required)
    :arg str secret-key: The Amazon API Secret Key (required)
    :arg int sleep: Number of seconds to wait before continuing to the
        next step (default 0)
    :arg array region: The region to run cloudformation in (required)

        :region values:
            * **us-east-1**
            * **us-west-1**
            * **us-west-2**
            * **eu-central-1**
            * **eu-west-1**
            * **ap-southeast-1**
            * **ap-southeast-2**
            * **ap-northeast-1**
            * **sa-east-1**

    Example:

    .. literalinclude:: ../../tests/builders/fixtures/cloudformation.yaml
       :language: yaml
    """
    region_dict = cloudformation_region_dict()
    stacks = cloudformation_init(xml_parent, data, 'CloudFormationBuildStep')
    for stack in data:
        cloudformation_stack(xml_parent, stack, 'PostBuildStackBean', stacks,
                             region_dict)


def openshift_build_verify(registry, xml_parent, data):
    """yaml: openshift-build-verify
    Performs the equivalent of an 'oc get builds` command invocation for the
    provided buildConfig key provided; once the list of builds are obtained,
    the state of the latest build is inspected for up to a minute to see if
    it has completed successfully.
    Requires the Jenkins :jenkins-wiki:`OpenShift
    Pipeline Plugin <OpenShift+Pipeline+Plugin>`.

    :arg str api-url: this would be the value you specify if you leverage the
        --server option on the OpenShift `oc` command.
        (default '\https://openshift.default.svc.cluster.local')
    :arg str bld-cfg: The value here should be whatever was the output
        form `oc project` when you created the BuildConfig you
        want to run a Build on (default 'frontend')
    :arg str namespace: If you run `oc get bc` for the project listed in
        "namespace", that is the value you want to put here. (default 'test')
    :arg str auth-token: The value here is what you supply with the --token
        option when invoking the OpenShift `oc` command. (default '')
    :arg bool verbose: This flag is the toggle for
        turning on or off detailed logging in this plug-in. (default false)

    Full Example:

    .. literalinclude::
        ../../tests/builders/fixtures/openshift-build-verify001.yaml
       :language: yaml

    Minimal Example:

    .. literalinclude::
        ../../tests/builders/fixtures/openshift-build-verify002.yaml
       :language: yaml
    """
    osb = XML.SubElement(xml_parent,
                         'com.openshift.jenkins.plugins.pipeline.'
                         'OpenShiftBuildVerifier')

    mapping = [
        # option, xml name, default value
        ("api-url", 'apiURL', 'https://openshift.default.svc.cluster.local'),
        ("bld-cfg", 'bldCfg', 'frontend'),
        ("namespace", 'namespace', 'test'),
        ("auth-token", 'authToken', ''),
        ("verbose", 'verbose', False),
    ]
    convert_mapping_to_xml(osb, data, mapping, fail_required=True)


def openshift_builder(registry, xml_parent, data):
    """yaml: openshift-builder
    Perform builds in OpenShift for the job.
    Requires the Jenkins :jenkins-wiki:`OpenShift
    Pipeline Plugin <OpenShift+Pipeline+Plugin>`.

    :arg str api-url: this would be the value you specify if you leverage the
        --server option on the OpenShift `oc` command.
        (default '\https://openshift.default.svc.cluster.local')
    :arg str bld-cfg: The value here should be whatever was the output
        form `oc project` when you created the BuildConfig you want to run a
        Build on (default 'frontend')
    :arg str namespace: If you run `oc get bc` for the project listed in
        "namespace", that is the value you want to put here. (default 'test')
    :arg str auth-token: The value here is what you supply with the --token
        option when invoking the OpenShift `oc` command. (default '')
    :arg str commit-ID: The value here is what you supply with the
        --commit option when invoking the
        OpenShift `oc start-build` command. (default '')
    :arg bool verbose: This flag is the toggle for
        turning on or off detailed logging in this plug-in. (default false)
    :arg str build-name: TThe value here is what you supply with the
        --from-build option when invoking the
        OpenShift `oc start-build` command. (default '')
    :arg bool show-build-logs: Indicates whether the build logs get dumped
        to the console of the Jenkins build. (default false)


    Full Example:

    .. literalinclude:: ../../tests/builders/fixtures/openshift-builder001.yaml
       :language: yaml

    Minimal Example:

    .. literalinclude:: ../../tests/builders/fixtures/openshift-builder002.yaml
       :language: yaml
    """
    osb = XML.SubElement(xml_parent,
                         'com.openshift.jenkins.plugins.pipeline.'
                         'OpenShiftBuilder')

    mapping = [
        # option, xml name, default value
        ("api-url", 'apiURL', 'https://openshift.default.svc.cluster.local'),
        ("bld-cfg", 'bldCfg', 'frontend'),
        ("namespace", 'namespace', 'test'),
        ("auth-token", 'authToken', ''),
        ("commit-ID", 'commitID', ''),
        ("verbose", 'verbose', False),
        ("build-name", 'buildName', ''),
        ("show-build-logs", 'showBuildLogs', False),
    ]
    convert_mapping_to_xml(osb, data, mapping, fail_required=True)


def openshift_creator(registry, xml_parent, data):
    """yaml: openshift-creator
    Performs the equivalent of an oc create command invocation;
    this build step takes in the provided JSON or YAML text, and if it
    conforms to OpenShift schema, creates whichever
    OpenShift resources are specified.
    Requires the Jenkins :jenkins-wiki:`OpenShift
    Pipeline Plugin <OpenShift+Pipeline+Plugin>`.

    :arg str api-url: this would be the value you specify if you leverage the
        --server option on the OpenShift `oc` command.
        (default '\https://openshift.default.svc.cluster.local')
    :arg str jsonyaml: The JSON or YAML formatted text that conforms to
        the schema for defining the various OpenShift resources. (default '')
    :arg str namespace: If you run `oc get bc` for the project listed in
        "namespace", that is the value you want to put here. (default 'test')
    :arg str auth-token: The value here is what you supply with the --token
        option when invoking the OpenShift `oc` command. (default '')
    :arg bool verbose: This flag is the toggle for
        turning on or off detailed logging in this plug-in. (default false)

    Full Example:

    .. literalinclude::
        ../../tests/builders/fixtures/openshift-creator001.yaml
       :language: yaml

    Minimal Example:

    .. literalinclude::
        ../../tests/builders/fixtures/openshift-creator002.yaml
       :language: yaml
    """
    osb = XML.SubElement(xml_parent,
                         'com.openshift.jenkins.plugins.pipeline.'
                         'OpenShiftCreator')

    mapping = [
        # option, xml name, default value
        ("api-url", 'apiURL', 'https://openshift.default.svc.cluster.local'),
        ("jsonyaml", 'jsonyaml', ''),
        ("namespace", 'namespace', 'test'),
        ("auth-token", 'authToken', ''),
        ("verbose", 'verbose', False),
    ]
    convert_mapping_to_xml(osb, data, mapping, fail_required=True)


def openshift_dep_verify(registry, xml_parent, data):
    """yaml: openshift-dep-verify
    Determines whether the expected set of DeploymentConfig's,
    ReplicationController's, and active replicas are present based on prior
    use of the scaler (2) and deployer (3) steps
    Requires the Jenkins :jenkins-wiki:`OpenShift
    Pipeline Plugin <OpenShift+Pipeline+Plugin>`._

    :arg str api-url: this would be the value you specify if you leverage the
        --server option on the OpenShift `oc` command.
        (default \https://openshift.default.svc.cluster.local\)
    :arg str dep-cfg: The value here should be whatever was the output
        form `oc project` when you created the BuildConfig you want to run a
        Build on (default frontend)
    :arg str namespace: If you run `oc get bc` for the project listed in
        "namespace", that is the value you want to put here. (default test)
    :arg int replica-count: The value here should be whatever the number
        of pods you want started for the deployment. (default 0)
    :arg str auth-token: The value here is what you supply with the --token
        option when invoking the OpenShift `oc` command. (default '')
    :arg bool verbose: This flag is the toggle for
        turning on or off detailed logging in this plug-in. (default false)

    Full Example:

    .. literalinclude::
        ../../tests/builders/fixtures/openshift-dep-verify001.yaml
       :language: yaml

    Minimal Example:

    .. literalinclude::
        ../../tests/builders/fixtures/openshift-dep-verify002.yaml
       :language: yaml
    """
    osb = XML.SubElement(xml_parent,
                         'com.openshift.jenkins.plugins.pipeline.'
                         'OpenShiftDeploymentVerifier')

    mapping = [
        # option, xml name, default value
        ("api-url", 'apiURL', 'https://openshift.default.svc.cluster.local'),
        ("dep-cfg", 'depCfg', 'frontend'),
        ("namespace", 'namespace', 'test'),
        ("replica-count", 'replicaCount', 0),
        ("auth-token", 'authToken', ''),
        ("verbose", 'verbose', False),
    ]
    convert_mapping_to_xml(osb, data, mapping, fail_required=True)


def openshift_deployer(registry, xml_parent, data):
    """yaml: openshift-deployer
    Start a deployment in OpenShift for the job.
    Requires the Jenkins :jenkins-wiki:`OpenShift
    Pipeline Plugin <OpenShift+Pipeline+Plugin>`.

    :arg str api-url: this would be the value you specify if you leverage the
        --server option on the OpenShift `oc` command.
        (default '\https://openshift.default.svc.cluster.local')
    :arg str dep-cfg: The value here should be whatever was the output
        form `oc project` when you created the BuildConfig you want to run a
        Build on (default 'frontend')
    :arg str namespace: If you run `oc get bc` for the project listed in
        "namespace", that is the value you want to put here. (default 'test')
    :arg str auth-token: The value here is what you supply with the --token
        option when invoking the OpenShift `oc` command. (default '')
    :arg bool verbose: This flag is the toggle for
        turning on or off detailed logging in this plug-in. (default false)

    Full Example:

    .. literalinclude::
        ../../tests/builders/fixtures/openshift-deployer001.yaml
       :language: yaml

    Minimal Example:

    .. literalinclude::
        ../../tests/builders/fixtures/openshift-deployer002.yaml
       :language: yaml
    """
    osb = XML.SubElement(xml_parent,
                         'com.openshift.jenkins.plugins.pipeline.'
                         'OpenShiftDeployer')

    mapping = [
        # option, xml name, default value
        ("api-url", 'apiURL', 'https://openshift.default.svc.cluster.local'),
        ("dep-cfg", 'depCfg', 'frontend'),
        ("namespace", 'namespace', 'test'),
        ("auth-token", 'authToken', ''),
        ("verbose", 'verbose', False),
    ]
    convert_mapping_to_xml(osb, data, mapping, fail_required=True)


def openshift_img_tagger(registry, xml_parent, data):
    """yaml: openshift-img-tagger
    Performs the equivalent of an oc tag command invocation in order to
    manipulate tags for images in OpenShift ImageStream's
    Requires the Jenkins :jenkins-wiki:`OpenShift
    Pipeline Plugin <OpenShift+Pipeline+Plugin>`.

    :arg str api-url: this would be the value you specify if you leverage the
        --server option on the OpenShift `oc` command.
        (default '\https://openshift.default.svc.cluster.local')
    :arg str test-tag: The equivalent to the name supplied to a
        `oc get service` command line invocation.
        (default 'origin-nodejs-sample:latest')
    :arg str prod-tag: The equivalent to the name supplied to a
        `oc get service` command line invocation.
        (default 'origin-nodejs-sample:prod')
    :arg str namespace: If you run `oc get bc` for the project listed in
        "namespace", that is the value you want to put here. (default 'test')
    :arg str auth-token: The value here is what you supply with the --token
        option when invoking the OpenShift `oc` command. (default '')
    :arg bool verbose: This flag is the toggle for
        turning on or off detailed logging in this plug-in. (default false)

    Full Example:

    .. literalinclude::
        ../../tests/builders/fixtures/openshift-img-tagger001.yaml
       :language: yaml

    Minimal Example:

    .. literalinclude::
        ../../tests/builders/fixtures/openshift-img-tagger002.yaml
       :language: yaml
    """
    osb = XML.SubElement(xml_parent,
                         'com.openshift.jenkins.plugins.pipeline.'
                         'OpenShiftImageTagger')

    mapping = [
        # option, xml name, default value
        ("api-url", 'apiURL', 'https://openshift.default.svc.cluster.local'),
        ("test-tag", 'testTag', 'origin-nodejs-sample:latest'),
        ("prod-tag", 'prodTag', 'origin-nodejs-sample:prod'),
        ("namespace", 'namespace', 'test'),
        ("auth-token", 'authToken', ''),
        ("verbose", 'verbose', False),
    ]
    convert_mapping_to_xml(osb, data, mapping, fail_required=True)


def openshift_scaler(registry, xml_parent, data):
    """yaml: openshift-scaler
    Scale deployments in OpenShift for the job.
    Requires the Jenkins :jenkins-wiki:`OpenShift
    Pipeline Plugin <OpenShift+Pipeline+Plugin>`.

    :arg str api-url: this would be the value you specify if you leverage the
        --server option on the OpenShift `oc` command.
        (default '\https://openshift.default.svc.cluster.local')
    :arg str dep-cfg: The value here should be whatever was the output
        form `oc project` when you created the BuildConfig you want to run a
        Build on (default 'frontend')
    :arg str namespace: If you run `oc get bc` for the project listed in
        "namespace", that is the value you want to put here. (default 'test')
    :arg int replica-count: The value here should be whatever the number
        of pods you want started for the deployment. (default 0)
    :arg str auth-token: The value here is what you supply with the --token
        option when invoking the OpenShift `oc` command. (default '')
    :arg bool verbose: This flag is the toggle for
        turning on or off detailed logging in this plug-in. (default false)

    Full Example:

    .. literalinclude:: ../../tests/builders/fixtures/openshift-scaler001.yaml
       :language: yaml

    Minimal Example:

    .. literalinclude:: ../../tests/builders/fixtures/openshift-scaler002.yaml
       :language: yaml
    """
    osb = XML.SubElement(xml_parent,
                         'com.openshift.jenkins.plugins.pipeline.'
                         'OpenShiftScaler')

    mapping = [
        # option, xml name, default value
        ("api-url", 'apiURL', 'https://openshift.default.svc.cluster.local'),
        ("dep-cfg", 'depCfg', 'frontend'),
        ("namespace", 'namespace', 'test'),
        ("replica-count", 'replicaCount', 0),
        ("auth-token", 'authToken', ''),
        ("verbose", 'verbose', False),
    ]
    convert_mapping_to_xml(osb, data, mapping, fail_required=True)


def openshift_svc_verify(registry, xml_parent, data):
    """yaml: openshift-svc-verify
    Verify a service is up in OpenShift for the job.
    Requires the Jenkins :jenkins-wiki:`OpenShift
    Pipeline Plugin <OpenShift+Pipeline+Plugin>`.

    :arg str api-url: this would be the value you specify if you leverage the
        --server option on the OpenShift `oc` command.
        (default '\https://openshift.default.svc.cluster.local')
    :arg str svc-name: The equivalent to the name supplied to a
        `oc get service` command line invocation. (default 'frontend')
    :arg str namespace: If you run `oc get bc` for the project listed in
        "namespace", that is the value you want to put here. (default 'test')
    :arg str auth-token: The value here is what you supply with the --token
        option when invoking the OpenShift `oc` command. (default '')
    :arg bool verbose: This flag is the toggle for
        turning on or off detailed logging in this plug-in. (default false)

    Full Example:

    .. literalinclude::
        ../../tests/builders/fixtures/openshift-svc-verify001.yaml
       :language: yaml

    Minimal Example:

    .. literalinclude::
        ../../tests/builders/fixtures/openshift-svc-verify002.yaml
       :language: yaml
    """
    osb = XML.SubElement(xml_parent,
                         'com.openshift.jenkins.plugins.pipeline.'
                         'OpenShiftServiceVerifier')

    mapping = [
        # option, xml name, default value
        ("api-url", 'apiURL', 'https://openshift.default.svc.cluster.local'),
        ("svc-name", 'svcName', 'frontend'),
        ("namespace", 'namespace', 'test'),
        ("auth-token", 'authToken', ''),
        ("verbose", 'verbose', False),
    ]
    convert_mapping_to_xml(osb, data, mapping, fail_required=True)


def runscope(registry, xml_parent, data):
    """yaml: runscope
    Execute a Runscope test.
    Requires the Jenkins :jenkins-wiki:`Runscope Plugin <Runscope+Plugin>`.

    :arg str test-trigger-url: Trigger URL for test. (required)
    :arg str access-token: OAuth Personal Access token. (required)
    :arg int timeout: Timeout for test duration in seconds. (default 60)

    Minimal Example:

    .. literalinclude:: /../../tests/builders/fixtures/runscope-minimal.yaml
       :language: yaml

    Full Example:

    .. literalinclude:: /../../tests/builders/fixtures/runscope-full.yaml
       :language: yaml
    """
    runscope = XML.SubElement(xml_parent,
                              'com.runscope.jenkins.Runscope.RunscopeBuilder')
    runscope.set('plugin', 'runscope')

    mapping = [
        ('test-trigger-url', 'triggerEndPoint', None),
        ('access-token', 'accessToken', None),
        ('timeout', 'timeout', 60),
    ]
    convert_mapping_to_xml(runscope, data, mapping, fail_required=True)


def description_setter(registry, xml_parent, data):
    """yaml: description-setter
    This plugin sets the description for each build,
    based upon a RegEx test of the build log file.

    Requires the Jenkins :jenkins-wiki:`Description Setter Plugin
    <Description+Setter+Plugin>`.

    :arg str regexp: A RegEx which is used to scan the build log file
        (default '')
    :arg str description: The description to set on the build (optional)

    Example:

    .. literalinclude::
        /../../tests/builders/fixtures/description-setter001.yaml
       :language: yaml
    """

    descriptionsetter = XML.SubElement(
        xml_parent,
        'hudson.plugins.descriptionsetter.DescriptionSetterBuilder')
    XML.SubElement(descriptionsetter, 'regexp').text = data.get('regexp', '')
    if 'description' in data:
        XML.SubElement(descriptionsetter, 'description').text = data[
            'description']


def docker_build_publish(parse, xml_parent, data):
    """yaml: docker-build-publish
    Requires the Jenkins :jenkins-wiki`Docker build publish Plugin
    <Docker+build+publish+Plugin>`.

    :arg str repo-name: Name of repository to push to.
    :arg str repo-tag: Tag for image. (default '')
    :arg bool no-cache: If build should be cached. (default false)
    :arg bool no-force-pull: Don't update the source image before building when
        it exists locally. (default false)
    :arg bool skip-build: Do not build the image. (default false)
    :arg bool skip-decorate: Do not decorate the build name. (default false)
    :arg bool skip-tag-latest: Do not tag this build as latest. (default false)
    :arg bool skip-push: Do not push. (default false)
    :arg str file-path: Path of the Dockerfile. (default '')
    :arg str build-context: Project root path for the build, defaults to the
        workspace if not specified. (default '')

    Example:

    .. literalinclude:: /../../tests/builders/fixtures/docker-builder001.yaml
    """
    db = XML.SubElement(xml_parent,
                        'com.cloudbees.dockerpublish.DockerBuilder')
    db.set('plugin', 'docker-build-publish')

    mapping = [
        ('repo-name', 'repoName', None),
        ('repo-tag', 'repoTag', ''),
        ('no-cache', 'noCache', False),
        ('no-force-pull', 'noForcePull', False),
        ('skip-build', 'skipBuild', False),
        ('skip-decorate', 'skipDecorate', False),
        ('skip-tag-latest', 'skipTagLatest', False),
        ('skip-push', 'skipPush', False),
        ('file-path', 'dockerfilePath', ''),
        ('build-context', 'buildContext', ''),
    ]
    convert_mapping_to_xml(db, data, mapping, fail_required=True)


def build_name_setter(registry, xml_parent, data):
    """yaml: build-name-setter
    Define Build Name Setter options which allows your build name to be
    updated during the build process.
    Requires the Jenkins :jenkins-wiki:`Build Name Setter Plugin
    <Build+Name+Setter+Plugin>`.

    :arg str name: Filename to use for Build Name Setter, only used if
        file bool is true. (default 'version.txt')
    :arg str template: Macro Template string, only used if macro
        bool is true. (default '#${BUILD_NUMBER}')
    :arg bool file: Read from named file (default false)
    :arg bool macro: Read from macro template (default false)
    :arg bool macro-first: Insert macro first (default false)

    File Example:

    .. literalinclude::
        /../../tests/builders/fixtures/build-name-setter001.yaml
       :language: yaml

    Macro Example:

    .. literalinclude::
        /../../tests/builders/fixtures/build-name-setter002.yaml
       :language: yaml
    """
    build_name_setter = XML.SubElement(
        xml_parent,
        'org.jenkinsci.plugins.buildnameupdater.BuildNameUpdater')
    mapping = [
        ('name', 'buildName', 'version.txt'),
        ('template', 'macroTemplate', '#${BUILD_NUMBER}'),
        ('file', 'fromFile', False),
        ('macro', 'fromMacro', False),
        ('macro-first', 'macroFirst', False),
    ]
    convert_mapping_to_xml(
        build_name_setter, data, mapping, fail_required=True)


def nexus_artifact_uploader(registry, xml_parent, data):
    """yaml: nexus-artifact-uploader
    To upload result of a build as an artifact in Nexus without the need of
    Maven. Requires the Jenkins :nexus-artifact-uploader:
    `Nexus Artifact Uploader Plugin <Nexus+Artifact+Uploader>`.

    :arg str protocol: Protocol to use to connect to Nexus (default https)
    :arg str nexus_url: Nexus url (without protocol) (default '')
    :arg str nexus_user: Username to upload artifact to Nexus (default '')
    :arg str nexus_password: Password to upload artifact to Nexus
        (default '')
    :arg str group_id: GroupId to set for the artifact to upload
        (default '')
    :arg str artifact_id: ArtifactId to set for the artifact to upload
        (default '')
    :arg str version: Version to set for the artifact to upload
        (default '')
    :arg str packaging: Packaging to set for the artifact to upload
        (default '')
    :arg str type: Type to set for the artifact to upload (default '')
    :arg str classifier: Classifier to set for the artifact to upload
        (default '')
    :arg str repository: In which repository to upload the artifact
        (default '')
    :arg str file: File which will be the uploaded artifact (default '')
    :arg str credentials_id: Credentials to use (instead of password)
        (default '')

    File Example:

    .. literalinclude::
        /../../tests/builders/fixtures/nexus-artifact-uploader.yaml
       :language: yaml
    """
    nexus_artifact_uploader = XML.SubElement(
        xml_parent,
        'sp.sd.nexusartifactuploader.NexusArtifactUploader')
    mapping = [
        ('protocol', 'protocol', 'https'),
        ('nexus_url', 'nexusUrl', ''),
        ('nexus_user', 'nexusUser', ''),
        ('nexus_password', 'nexusPassword', ''),
        ('group_id', 'groupId', ''),
        ('artifact_id', 'artifactId', ''),
        ('version', 'version', ''),
        ('packaging', 'packaging', ''),
        ('type', 'type', ''),
        ('classifier', 'classifier', ''),
        ('repository', 'repository', ''),
        ('file', 'file', ''),
        ('credentials_id', 'credentialsId', ''),
    ]
    convert_mapping_to_xml(
        nexus_artifact_uploader, data, mapping, fail_required=True)
