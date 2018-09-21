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
import sys
import xml.etree.ElementTree as XML

import six

from jenkins_jobs.errors import is_sequence
from jenkins_jobs.errors import InvalidAttributeError
from jenkins_jobs.errors import JenkinsJobsException
from jenkins_jobs.errors import MissingAttributeError
import jenkins_jobs.modules.base
import jenkins_jobs.modules.helpers as helpers
import pkg_resources
from jenkins_jobs.modules import hudson_model
from jenkins_jobs.modules.publishers import ssh

logger = logging.getLogger(__name__)


def shell(registry, xml_parent, data):
    """yaml: shell
    Execute a shell command.

    There are two ways of configuring the builder, with a plain string to
    execute:

    :arg str parameter: the shell command to execute

    Or with a mapping that allows other parameters to be passed:

    :arg str command: the shell command to execute
    :arg int unstable-return:
        the shell exit code to interpret as an unstable build result

    Example:

    .. literalinclude:: /../../tests/builders/fixtures/shell.yaml
       :language: yaml

    .. literalinclude::
        /../../tests/builders/fixtures/shell-unstable-return.yaml
       :language: yaml
    """
    shell = XML.SubElement(xml_parent, 'hudson.tasks.Shell')
    if isinstance(data, six.string_types):
        XML.SubElement(shell, 'command').text = data
    else:
        mappings = [
            ('command', 'command', None),
            ('unstable-return', 'unstableReturn', 0),
        ]
        helpers.convert_mapping_to_xml(
            shell, data, mappings, fail_required=True)


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
    :arg string exclude: Specify paths or patterns of artifacts to
        exclude, even if specified in "Artifacts to copy". (default '')
    :arg string result-var-suffix: The build number of the selected build
        will be recorded into the variable named
        COPYARTIFACT_BUILD_NUMBER_(SUFFIX)
        for later build steps to reference. (default '')

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
        ('parameter-filters', 'parameters', ''),
        ('exclude', 'exclude', ''),
        ('result-var-suffix', 'resultVariableSuffix', ''),
    ]
    helpers.convert_mapping_to_xml(t, data, mappings, fail_required=True)
    helpers.copyartifact_build_selector(t, data)


def change_assembly_version(registry, xml_parent, data):
    """yaml: change-assembly-version
    Change the assembly version.
    Requires the Jenkins :jenkins-wiki:`Change Assembly Version
    <Change+Assembly+Version>`.

    :arg str version: Set the new version number for replace (default 1.0.0)
    :arg str assemblyFile: The file name to search (default AssemblyInfo.cs)

    Minimal Example:

    .. literalinclude::
        /../../tests/builders/fixtures/changeassemblyversion-minimal.yaml
       :language: yaml

    Full Example:

    .. literalinclude::
        /../../tests/builders/fixtures/changeassemblyversion-full.yaml
       :language: yaml
    """

    cav_builder_tag = ('org.jenkinsci.plugins.changeassemblyversion.'
                       'ChangeAssemblyVersion')
    cav = XML.SubElement(xml_parent, cav_builder_tag)
    mappings = [
        ('version', 'task', '1.0.0'),
        ('assembly-file', 'assemblyFile', 'AssemblyInfo.cs'),
    ]
    helpers.convert_mapping_to_xml(cav, data, mappings, fail_required=True)


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

    mapping = [
        ('targets', 'targets', ''),
    ]
    helpers.convert_mapping_to_xml(
        fingerprint, data, mapping, fail_required=True)


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

    mapping = [
        ('targets', 'targets', None),
        ('buildfile', 'buildFile', None),
        ('ant-name', 'antName', 'default'),
    ]
    helpers.convert_mapping_to_xml(ant, data, mapping, fail_required=False)

    mapping = []
    for setting, value in sorted(data.items()):
        if setting == 'properties':
            properties = value
            prop_string = ''
            for prop, val in properties.items():
                prop_string += "%s=%s\n" % (prop, val)
            mapping.append(('', 'properties', prop_string))
        if setting == 'java-opts':
            jopt_string = '\n'.join(value)
            mapping.append(('', 'antOpts', jopt_string))

    helpers.convert_mapping_to_xml(ant, data, mapping, fail_required=True)


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
    :arg bool enhanced-logging: if this option is enabled,
        the console output of the remote job is also logged. (default false)
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

    mappings = [
        ('remote-jenkins-name', 'remoteJenkinsName', None),
        ('token', 'token', ''),
        ('job', 'job', None),
        ('should-not-fail-build', 'shouldNotFailBuild', False),
        ('poll-interval', 'pollInterval', 10),
        ('connection-retry-limit', 'connectionRetryLimit', 5),
        ('enhanced-logging', 'enhancedLogging', False),
        ('prevent-remote-build-queue', 'preventRemoteBuildQueue', False),
        ('block', 'blockBuildUntilComplete', True),
    ]
    helpers.convert_mapping_to_xml(
        triggerr, data, mappings, fail_required=True)

    mappings = []
    if 'predefined-parameters' in data:
        parameters = data.get('predefined-parameters', '')
        XML.SubElement(triggerr, 'parameters').text = parameters
        params_list = parameters.split("\n")

        parameter_list = XML.SubElement(triggerr, 'parameterList')
        for param in params_list:
            if param == '':
                continue
            tmp = XML.SubElement(parameter_list, 'string')
            tmp.text = param

    if 'property-file' in data and data['property-file'] != '':
        mappings.append(('', 'loadParamsFromFile', 'true'))
        mappings.append(('property-file', 'parameterFile', None))
    else:
        mappings.append(('', 'loadParamsFromFile', 'false'))

    mappings.append(('', 'overrideAuth', 'false'))

    helpers.convert_mapping_to_xml(
        triggerr, data, mappings, fail_required=True)


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
            helpers.append_git_revision_config(
                tconfigs, project_def['git-revision'])

        if(project_def.get('same-node')):
            XML.SubElement(tconfigs,
                           'hudson.plugins.parameterizedtrigger.'
                           'NodeParameters')
        if 'property-file' in project_def:
            params = XML.SubElement(tconfigs,
                                    'hudson.plugins.parameterizedtrigger.'
                                    'FileBuildParameters')
            mapping = [
                ('property-file', 'propertiesFile', None),
                ('property-file-fail-on-missing',
                    'failTriggerOnMissing', True),
            ]
            helpers.convert_mapping_to_xml(params,
                project_def, mapping, fail_required=True)

        if 'predefined-parameters' in project_def:
            params = XML.SubElement(tconfigs,
                                    'hudson.plugins.parameterizedtrigger.'
                                    'PredefinedBuildParameters')
            mapping = [
                ('predefined-parameters', 'properties', None),
            ]
            helpers.convert_mapping_to_xml(params,
                project_def, mapping, fail_required=True)

        if 'bool-parameters' in project_def:
            params = XML.SubElement(tconfigs,
                                    'hudson.plugins.parameterizedtrigger.'
                                    'BooleanParameters')
            configs = XML.SubElement(params, 'configs')
            for bool_param in project_def['bool-parameters']:
                param = XML.SubElement(configs,
                                       'hudson.plugins.parameterizedtrigger.'
                                       'BooleanParameterConfig')
                mapping = [
                    ('name', 'name', None),
                    ('value', 'value', False),
                ]
                helpers.convert_mapping_to_xml(param,
                    bool_param, mapping, fail_required=True)

        if 'node-label-name' in project_def and 'node-label' in project_def:
            node = XML.SubElement(tconfigs, 'org.jvnet.jenkins.plugins.'
                                  'nodelabelparameter.parameterizedtrigger.'
                                  'NodeLabelBuildParameter')
            mapping = [
                ('node-label-name', 'name', None),
                ('node-label', 'nodeLabel', None),
            ]
            helpers.convert_mapping_to_xml(node,
                project_def, mapping, fail_required=True)

        if 'restrict-matrix-project' in project_def:
            params = XML.SubElement(tconfigs,
                                    'hudson.plugins.parameterizedtrigger.'
                                    'matrix.MatrixSubsetBuildParameters')
            mapping = [
                ('restrict-matrix-project', 'filter', None),
            ]
            helpers.convert_mapping_to_xml(params,
                project_def, mapping, fail_required=True)

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
                    mapping = [
                        ('parameter-name', 'parameterName', None),
                    ]
                    helpers.convert_mapping_to_xml(params,
                        factory, mapping, fail_required=True)

                if (factory['factory'] == 'filebuild' or
                        factory['factory'] == 'binaryfile'):
                    mapping = [
                        ('file-pattern', 'filePattern', None),
                        ('no-files-found-action',
                            'noFilesFoundAction', 'SKIP', supported_actions),
                    ]
                    helpers.convert_mapping_to_xml(params,
                        factory, mapping, fail_required=True)

                if factory['factory'] == 'counterbuild':
                    params = XML.SubElement(
                        fconfigs,
                        'hudson.plugins.parameterizedtrigger.'
                        'CounterBuildParameterFactory')
                    mapping = [
                        ('from', 'from', None),
                        ('to', 'to', None),
                        ('step', 'step', None),
                        ('parameters', 'paramExpr', ''),
                        ('validation-fail',
                         'validationFail',
                         'FAIL', supported_actions),
                    ]
                    helpers.convert_mapping_to_xml(params,
                        factory, mapping, fail_required=True)

                if factory['factory'] == 'allnodesforlabel':
                    params = XML.SubElement(
                        fconfigs,
                        'org.jvnet.jenkins.plugins.nodelabelparameter.'
                        'parameterizedtrigger.'
                        'AllNodesForLabelBuildParameterFactory')
                    mapping = [
                        ('name', 'name', ''),
                        ('node-label', 'nodeLabel', None),
                        ('ignore-offline-nodes',
                         'ignoreOfflineNodes', True),
                    ]
                    helpers.convert_mapping_to_xml(params,
                        factory, mapping, fail_required=True)

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

        mapping = [
            ('', 'condition', 'ALWAYS'),
            ('', 'triggerWithNoParameters', False),
            ('', 'buildAllNodesWithLabel', False),
        ]
        helpers.convert_mapping_to_xml(
            tconfig, {}, mapping, fail_required=True)

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
                mapping = [
                    ('name', 'name', None),
                    ('ordinal', 'ordinal', None),
                    ('color', 'color', None),
                    ('', 'completeBuild', True),
                ]
                helpers.convert_mapping_to_xml(th,
                        hudson_model.THRESHOLDS[tvalue.upper()],
                mapping, fail_required=True)

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
    mapping = [
        ('', 'projectName', data),
    ]
    helpers.convert_mapping_to_xml(pbs, {}, mapping, fail_required=True)


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
        or multiple codes separated by comma(',') e.g. "200,404,500"
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
       ../../tests/builders/fixtures/http-request-full.yaml
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
        ('valid-response-content', 'validResponseContent', ''),
    ]
    helpers.convert_mapping_to_xml(
        http_request, data, mappings, fail_required=True)

    if 'authentication-key' in data:
        XML.SubElement(
            http_request, 'authentication').text = data['authentication-key']

    if 'custom-headers' in data:
        customHeader = XML.SubElement(http_request, 'customHeaders')
        header_mappings = [
            ('name', 'name', None),
            ('value', 'value', None),
        ]
        for customhead in data['custom-headers']:
            pair = XML.SubElement(customHeader, 'pair')
            helpers.convert_mapping_to_xml(pair,
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
    mapping = [
        ('properties-file', 'propertiesFilePath', None),
        ('properties-content', 'propertiesContent', None),
        ('script-file', 'scriptFilePath', None),
        ('script-content', 'scriptContent', None),
    ]
    helpers.convert_mapping_to_xml(info, data, mapping, fail_required=False)


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
    helpers.convert_mapping_to_xml(kmap, data, mapping, fail_required=True)

    if publish is True:
        publish_optional = XML.SubElement(kmap, 'publishOptional')
        publish_mapping = [
            ('groups', 'teams', ''),
            ('users', 'users', ''),
            ('notify-users', 'sendNotifications', False),
        ]
        helpers.convert_mapping_to_xml(
            publish_optional, data, publish_mapping, fail_required=True)


def artifact_resolver(registry, xml_parent, data):
    """yaml: artifact-resolver
    Allows one to resolve artifacts from a maven repository like nexus
    (without having maven installed)
    Requires the Jenkins :jenkins-wiki:`Repository Connector Plugin
    <Repository+Connector+Plugin>`.

    :arg bool fail-on-error: Whether to fail the build on error (default false)
    :arg bool repository-logging: Enable repository logging (default false)
    :arg str target-directory: Where to resolve artifacts to (required)
    :arg list artifacts: list of artifacts to resolve

        :Artifact:
            * **group-id** (`str`) -- Group ID of the artifact (required)
            * **artifact-id** (`str`) -- Artifact ID of the artifact (required)
            * **version** (`str`) -- Version of the artifact (required)
            * **classifier** (`str`) -- Classifier of the artifact (default '')
            * **extension** (`str`) -- Extension of the artifact
              (default 'jar')
            * **target-file-name** (`str`) -- What to name the artifact
              (default '')

    Minimal Example:

    .. literalinclude::
        ../../tests/builders/fixtures/artifact-resolver-minimal.yaml
       :language: yaml

    Full Example:

    .. literalinclude::
        ../../tests/builders/fixtures/artifact-resolver-full.yaml
       :language: yaml
    """
    ar = XML.SubElement(
        xml_parent,
        'org.jvnet.hudson.plugins.repositoryconnector.ArtifactResolver')
    mapping = [
        ('target-directory', 'targetDirectory', None),
        ('fail-on-error', 'failOnError', False),
        ('repository-logging', 'enableRepoLogging', False),
        ('', 'snapshotUpdatePolicy', 'never'),
        ('', 'releaseUpdatePolicy', 'never'),
        ('', 'snapshotChecksumPolicy', 'warn'),
        ('', 'releaseChecksumPolicy', 'warn'),
    ]
    helpers.convert_mapping_to_xml(ar, data, mapping, fail_required=True)

    artifact_top = XML.SubElement(ar, 'artifacts')
    artifacts = data['artifacts']
    artifacts_mapping = [
        ('group-id', 'groupId', None),
        ('artifact-id', 'artifactId', None),
        ('version', 'version', None),
        ('classifier', 'classifier', ''),
        ('extension', 'extension', 'jar'),
        ('target-file-name', 'targetFileName', ''),
    ]
    for artifact in artifacts:
        rcartifact = XML.SubElement(
            artifact_top,
            'org.jvnet.hudson.plugins.repositoryconnector.Artifact')
        helpers.convert_mapping_to_xml(
            rcartifact, artifact, artifacts_mapping, fail_required=True)


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
        ('unstable-warning', 'unstableIfWarnings', False),
    ]
    helpers.convert_mapping_to_xml(doxygen, data, mappings, fail_required=True)


def gradle(registry, xml_parent, data):
    """yaml: gradle
    Execute gradle tasks. Requires the Jenkins :jenkins-wiki:`Gradle Plugin
    <Gradle+Plugin>`.

    :arg str tasks: List of tasks to execute
    :arg str gradle-name: Use a custom gradle name (default '')
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
    :arg str build-file: name of gradle build script (default 'build.gradle')

    Example:

    .. literalinclude:: ../../tests/builders/fixtures/gradle.yaml
       :language: yaml
    """
    gradle = XML.SubElement(xml_parent, 'hudson.plugins.gradle.Gradle')

    XML.SubElement(gradle, 'description').text = ''

    mappings = [
        ('build-file', 'buildFile', 'build.gradle'),
        ('tasks', 'tasks', None),
        ('root-build-script-dir', 'rootBuildScriptDir', ''),
        ('gradle-name', 'gradleName', ''),
        ('wrapper', 'useWrapper', False),
        ('executable', 'makeExecutable', False),
        ('use-root-dir', 'fromRootBuildScriptDir', False),
    ]
    helpers.convert_mapping_to_xml(gradle, data, mappings, fail_required=True)

    XML.SubElement(gradle, 'switches').text = '\n'.join(
        data.get('switches', []))


def _groovy_common_scriptSource(data):
    """Helper function to generate the XML element common to groovy builders
    """

    scriptSource = XML.Element("scriptSource")
    if 'command' in data and 'file' in data:
        raise JenkinsJobsException("Use just one of 'command' or 'file'")

    if 'command' in data:
        mapping = [
            ('command', 'command', None),
        ]
        helpers.convert_mapping_to_xml(
            scriptSource, data, mapping, fail_required=True)
        scriptSource.set('class', 'hudson.plugins.groovy.StringScriptSource')
    elif 'file' in data:
        mapping = [
            ('file', 'scriptFile', None),
        ]
        helpers.convert_mapping_to_xml(
            scriptSource, data, mapping, fail_required=True)
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
    :arg str parameters: Parameters for the Groovy executable. (default '')
    :arg str script-parameters: These parameters will be passed to the script.
        (default '')
    :arg str properties: Instead of passing properties using the -D parameter
        you can define them here. (default '')
    :arg str java-opts: Direct access to JAVA_OPTS. Properties allows only
        -D properties, while sometimes also other properties like -XX need to
        be setup. It can be done here. This line is appended at the end of
        JAVA_OPTS string. (default '')
    :arg str class-path: Specify script classpath here. Each line is one
        class path item. (default '')

    Minimal Example:

    .. literalinclude:: ../../tests/builders/fixtures/groovy-minimal.yaml
       :language: yaml


    Full Example:

    .. literalinclude:: ../../tests/builders/fixtures/groovy-full.yaml
       :language: yaml
    """

    root_tag = 'hudson.plugins.groovy.Groovy'
    groovy = XML.SubElement(xml_parent, root_tag)
    groovy.append(_groovy_common_scriptSource(data))

    mappings = [
        ('version', 'groovyName', '(Default)'),
        ('parameters', 'parameters', ''),
        ('script-parameters', 'scriptParameters', ''),
        ('properties', 'properties', ''),
        ('java-opts', 'javaOpts', ''),
        ('class-path', 'classPath', ''),
    ]
    helpers.convert_mapping_to_xml(groovy, data, mappings, fail_required=True)


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

    mapping = [
        ('bindings', 'bindings', ''),
        ('class-path', 'classpath', ''),
    ]
    helpers.convert_mapping_to_xml(
        sysgroovy, data, mapping, fail_required=True)


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
        ('unstable-if-warnings', 'unstableIfWarnings', False),
    ]
    helpers.convert_mapping_to_xml(
        msbuilder, data, mapping, fail_required=True)


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
                             result of another job (BuildResultTrigger Plugin)
                         :exclusive-cause: (bool) There might by multiple
                           causes causing a build to be triggered, with
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

    Examples:

    .. literalinclude::
        /../../tests/builders/fixtures/conditional-step-multiple-steps.yaml
       :language: yaml
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
    def build_condition(cdata, cond_root_tag, condition_tag):
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
            mapping = [
                ('condition-expression', 'token', None),
            ]
            helpers.convert_mapping_to_xml(
                ctag, cdata, mapping, fail_required=True)
        elif kind == "build-cause":
            ctag.set('class', core_prefix + 'CauseCondition')
            cause_list = ('USER_CAUSE', 'SCM_CAUSE', 'TIMER_CAUSE',
                          'CLI_CAUSE', 'REMOTE_CAUSE', 'UPSTREAM_CAUSE',
                          'FS_CAUSE', 'URL_CAUSE', 'IVY_CAUSE',
                          'SCRIPT_CAUSE', 'BUILDRESULT_CAUSE')
            mapping = [
                ('cause', 'buildCause', 'USER_CAUSE', cause_list),
                ('exclusive-cause', "exclusiveCause", False),
            ]
            helpers.convert_mapping_to_xml(
                ctag, cdata, mapping, fail_required=True)
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
                    mapping = [
                        ('', 'day', day_no),
                        (day, "selected", False),
                    ]
                    helpers.convert_mapping_to_xml(day_tag,
                        inp_days, mapping, fail_required=True)
            mapping = [
                ('use-build-time', "useBuildTime", False),
            ]
            helpers.convert_mapping_to_xml(
                ctag, cdata, mapping, fail_required=True)
        elif kind == "execution-node":
            ctag.set('class', core_prefix + 'NodeCondition')
            allowed_nodes_tag = XML.SubElement(ctag, "allowedNodes")
            for node in cdata['nodes']:
                mapping = [
                    ('', "string", node),
                ]
                helpers.convert_mapping_to_xml(allowed_nodes_tag,
                    cdata, mapping, fail_required=True)
        elif kind == "strings-match":
            ctag.set('class', core_prefix + 'StringsMatchCondition')
            mapping = [
                ('condition-string1', "arg1", ''),
                ('condition-string2', "arg2", ''),
                ('condition-case-insensitive', "ignoreCase", False),
            ]
            helpers.convert_mapping_to_xml(
                ctag, cdata, mapping, fail_required=True)
        elif kind == "current-status":
            ctag.set('class', core_prefix + 'StatusCondition')
            wr = XML.SubElement(ctag, 'worstResult')
            wr_name = cdata.get('condition-worst', 'SUCCESS')
            if wr_name not in hudson_model.THRESHOLDS:
                raise InvalidAttributeError('condition-worst', wr_name,
                                            hudson_model.THRESHOLDS.keys())
            wr_threshold = hudson_model.THRESHOLDS[wr_name]
            mapping = [
                ('name', 'name', None),
                ('ordinal', 'ordinal', None),
                ('color', 'color', 'color'),
                ('complete', 'completeBuild', None),
            ]
            helpers.convert_mapping_to_xml(wr,
                wr_threshold, mapping, fail_required=True)
            br = XML.SubElement(ctag, 'bestResult')
            br_name = cdata.get('condition-best', 'SUCCESS')
            if br_name not in hudson_model.THRESHOLDS:
                raise InvalidAttributeError('condition-best', br_name,
                                            hudson_model.THRESHOLDS.keys())
            br_threshold = hudson_model.THRESHOLDS[br_name]
            mapping = [
                ('name', 'name', None),
                ('ordinal', 'ordinal', None),
                ('color', 'color', 'color'),
                ('complete', 'completeBuild', None),
            ]
            helpers.convert_mapping_to_xml(br,
                br_threshold, mapping, fail_required=True)
        elif kind == "shell":
            ctag.set('class',
                     'org.jenkins_ci.plugins.run_condition.contributed.'
                     'ShellCondition')
            mapping = [
                ('condition-command', 'command', ''),
            ]
            helpers.convert_mapping_to_xml(
                ctag, cdata, mapping, fail_required=True)
        elif kind == "windows-shell":
            ctag.set('class',
                     'org.jenkins_ci.plugins.run_condition.contributed.'
                     'BatchFileCondition')
            mapping = [
                ('condition-command', 'command', ''),
            ]
            helpers.convert_mapping_to_xml(
                ctag, cdata, mapping, fail_required=True)
        elif kind == "file-exists" or kind == "files-match":
            if kind == "file-exists":
                ctag.set('class', core_prefix + 'FileExistsCondition')
                mapping = [
                    ('condition-filename', 'file', None),
                ]
                helpers.convert_mapping_to_xml(ctag, cdata, mapping,
                    fail_required=True)
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
            mapping = [
                ('lhs', 'lhs', None),
                ('rhs', 'rhs', None),
            ]
            helpers.convert_mapping_to_xml(
                ctag, cdata, mapping, fail_required=True)
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
            mapping = [
                ('regex', 'expression', ''),
                ('label', 'label', ''),
            ]
            helpers.convert_mapping_to_xml(
                ctag, cdata, mapping, fail_required=True)
        elif kind == "time":
            ctag.set('class', core_prefix + 'TimeCondition')
            mapping = [
                ('earliest-hour', 'earliestHours', '09'),
                ('earliest-min', 'earliestMinutes', '00'),
                ('latest-hour', 'latestHours', '17'),
                ('latest-min', 'latestMinutes', '30'),
                ('use-build-time', 'useBuildTime', False),
            ]
            helpers.convert_mapping_to_xml(
                ctag, cdata, mapping, fail_required=True)
        elif kind == "not":
            ctag.set('class', logic_prefix + 'Not')
            try:
                notcondition = cdata['condition-operand']
            except KeyError:
                raise MissingAttributeError('condition-operand')
            build_condition(notcondition, ctag, "condition")
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
                build_condition(condition, conditions_container_tag,
                                "condition")

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

    build_condition(data, root_tag, condition_tag)
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
    helpers.convert_mapping_to_xml(maven, data, mapping, fail_required=True)


def jira_issue_updater(registry, xml_parent, data):
    """yaml: jenkins-jira-issue-updater
    Updates issues in Atlassian JIRA as part of a Jenkins job.

    Requires the Jenkins :jenkins-wiki:`Jira Issue Updater Plugin
    <Jira+Issue+Updater+Plugin>`.

    :arg str base-url: The base url of the rest API. (default '')
    :arg str username: The Jira username (required)
    :arg str password: The Jira password (required)
    :arg str jql: The JQL used to select the issues to update. (required)
    :arg str workflow: The Name of the workflow action to be executed.
        (default '')
    :arg str comment: The Jira comment to be added. (default '')
    :arg str custom-Id: The Jira custom field to be edited. (default '')
    :arg str custom-value: Jira custom field value. (default '')
    :arg bool fail-if-error: Fail this build if JQL returns error.
        ((default false)
    :arg bool fail-if-no-match: Fail this build if no issues are matched.
        (default false)
    :arg bool fail-if-no-connection: Fail this build if can't connect to Jira.
        (default false)

    Minimal Example:

    .. literalinclude::
        /../../tests/builders/fixtures/jenkins-jira-issue-updater-minimal.yaml
        :language: yaml

    Full Example:

    .. literalinclude::
        /../../tests/builders/fixtures/jenkins-jira-issue-updater-full.yaml
        :language: yaml
    """
    issue_updater = XML.SubElement(xml_parent, 'info.bluefloyd.jenkins.'
                                               'IssueUpdatesBuilder')
    issue_updater.set('plugin', 'jenkins-jira-issue-updater')

    mapping = [
        ('base-url', 'restAPIUrl', ''),
        ('username', 'userName', None),
        ('password', 'password', None),
        ('jql', 'jql', None),
        ('workflow', 'workflowActionName', ''),
        ('comment', 'comment', ''),
        ('custom-Id', 'customFieldId', ''),
        ('custom-value', 'customFieldValue', ''),
        ('fail-if-error', 'failIfJqlFails', False),
        ('fail-if-no-match', 'failIfNoIssuesReturned', False),
        ('fail-if-no-connection', 'failIfNoJiraConnection', False),
    ]
    helpers.convert_mapping_to_xml(
        issue_updater, data, mapping, fail_required=True)


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

    mapping = [
        ('maven-version', 'mavenName', None),
        ('pom', 'pom', None),
        ('private-repository', 'usePrivateRepository', False),
    ]
    helpers.convert_mapping_to_xml(maven, data, mapping, fail_required=False)
    if 'java-opts' in data:
        javaoptions = ' '.join(data.get('java-opts', []))
        XML.SubElement(maven, 'jvmOptions').text = javaoptions
    helpers.config_file_provider_settings(maven, data)


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
    :arg str execution-type: Define how to run jobs in a phase:
        sequentially or parallel.
        Can be: 'PARALLEL', 'SEQUENTIALLY'
        (default 'PARALLEL')

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
            * **aggregate-results** (`bool`) -- Aggregate test results.
              (default false)
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
    conditions_available = ('SUCCESSFUL', 'UNSTABLE', 'COMPLETED', 'FAILURE',
                            'ALWAYS')
    job_execution_type_available = ('PARALLEL', 'SEQUENTIALLY')
    mapping = [
        ('name', 'phaseName', None),
        ('condition', 'continuationCondition',
            'SUCCESSFUL', conditions_available),
        ('execution-type', 'executionType',
            'PARALLEL', job_execution_type_available),
    ]
    helpers.convert_mapping_to_xml(builder, data, mapping, fail_required=True)

    phaseJobs = XML.SubElement(builder, 'phaseJobs')

    kill_status_list = ('FAILURE', 'UNSTABLE', 'NEVER')

    for project in data.get('projects', []):
        phaseJob = XML.SubElement(phaseJobs, 'com.tikal.jenkins.plugins.'
                                             'multijob.PhaseJobsConfig')
        mapping = [
            ('name', 'jobName', None),
            # Pass through the current build params
            ('current-parameters', 'currParams', False),
        ]
        helpers.convert_mapping_to_xml(
            phaseJob, project, mapping, fail_required=True)
        # Pass through other params
        configs = XML.SubElement(phaseJob, 'configs')

        nodeLabelName = project.get('node-label-name')
        nodeLabel = project.get('node-label')
        if nodeLabelName and nodeLabel:
            node = XML.SubElement(
                configs, 'org.jvnet.jenkins.plugins.nodelabelparameter.'
                         'parameterizedtrigger.NodeLabelBuildParameter')
            mapping = [
                ('', 'name', nodeLabelName),
                ('', 'nodeLabel', nodeLabel),
            ]
            helpers.convert_mapping_to_xml(
                node, project, mapping, fail_required=True)

        # Node parameter
        if project.get('node-parameters', False):
            XML.SubElement(configs, 'hudson.plugins.parameterizedtrigger.'
                                    'NodeParameters')

        # Git Revision
        if project.get('git-revision', False):
            param = XML.SubElement(configs,
                                   'hudson.plugins.git.'
                                   'GitRevisionBuildParameters')
            mapping = [
                ('', 'combineQueuedCommits', False),
            ]
            helpers.convert_mapping_to_xml(
                param, project, mapping, fail_required=True)

        # Properties File
        properties_file = project.get('property-file', False)
        if properties_file:
            param = XML.SubElement(configs,
                                   'hudson.plugins.parameterizedtrigger.'
                                   'FileBuildParameters')
            mapping = [
                ('', 'propertiesFile', properties_file),
                ('', 'failTriggerOnMissing', True),
            ]
            helpers.convert_mapping_to_xml(
                param, project, mapping, fail_required=True)

        # Predefined Parameters
        predefined_parameters = project.get('predefined-parameters', False)
        if predefined_parameters:
            param = XML.SubElement(configs,
                                   'hudson.plugins.parameterizedtrigger.'
                                   'PredefinedBuildParameters')
            mapping = [
                ('', 'properties', predefined_parameters),
            ]
            helpers.convert_mapping_to_xml(
                param, project, mapping, fail_required=True)

        mapping = [
            ('abort-all-job', 'abortAllJob', False),
            ('aggregate-results', 'aggregatedTestResults', False),
        ]
        helpers.convert_mapping_to_xml(
            phaseJob, project, mapping, fail_required=True)

        # Retry job
        retry = project.get('retry', False)
        if retry:
            max_retry = retry.get('max-retry', 0)
            mapping = [
                ('strategy-path', 'parsingRulesPath', None),
                ('', 'maxRetries', int(max_retry)),
                ('', 'enableRetryStrategy', True),
            ]
            helpers.convert_mapping_to_xml(phaseJob,
                retry, mapping, fail_required=True)
        else:
            XML.SubElement(phaseJob, 'enableRetryStrategy').text = 'false'

        # Restrict matrix jobs to a subset
        if project.get('restrict-matrix-project') is not None:
            subset = XML.SubElement(
                configs, 'hudson.plugins.parameterizedtrigger.'
                         'matrix.MatrixSubsetBuildParameters')
            mapping = [
                ('restrict-matrix-project', 'filter', None),
            ]
            helpers.convert_mapping_to_xml(subset,
                project, mapping, fail_required=True)

        # Enable Condition
        enable_condition = project.get('enable-condition')
        if enable_condition is not None:
            mapping = [
                ('', 'enableCondition', True),
                ('', 'condition', enable_condition),
            ]
            helpers.convert_mapping_to_xml(phaseJob,
                project, mapping, fail_required=True)

        # Kill phase on job status
        kill_status = project.get('kill-phase-on')
        if kill_status is not None:
            kill_status = kill_status.upper()
            mapping = [
                ('', 'killPhaseOnJobResultCondition',
                kill_status, kill_status_list),
            ]
            helpers.convert_mapping_to_xml(phaseJob,
                project, mapping, fail_required=True)


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
            * **replace-tokens** (`bool`) -- Replace tokens in config file. For
              example "password: ${PYPI_JENKINS_PASS}" will be replaced with
              the global variable configured in Jenkins.

    Full Example:

    .. literalinclude::
        ../../tests/builders/fixtures/config-file-provider-full.yaml
       :language: yaml

    Minimal Example:

    .. literalinclude::
        ../../tests/builders/fixtures/config-file-provider-minimal.yaml
       :language: yaml
    """
    cfp = XML.SubElement(xml_parent,
                         'org.jenkinsci.plugins.configfiles.builder.'
                         'ConfigFileBuildStep')
    cfp.set('plugin', 'config-file-provider')
    helpers.config_file_provider_builder(cfp, data)


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
    helpers.convert_mapping_to_xml(grails, data, mappings, fail_required=True)


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
    helpers.convert_mapping_to_xml(sbt, data, mappings, fail_required=True)


def critical_block_start(registry, xml_parent, data):
    """yaml: critical-block-start
    Designate the start of a critical block. Must be used in conjunction with
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
    Designate the end of a critical block. Must be used in conjunction with
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
        ('saveoutput', 'saveEnvVar', False),
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
        python_mapping = [
            ('python-version', 'pythonName', 'System-CPython-2.7'),
        ]
        helpers.convert_mapping_to_xml(
            t, data, python_mapping, fail_required=True)

    if buildenv in 'custom':
        custom_mapping = [
            ('home', 'home', None),
        ]
        helpers.convert_mapping_to_xml(
            t, data, custom_mapping, fail_required=True)
    if buildenv in 'virtualenv':
        virtualenv_mapping = [
            ('name', 'home', ''),
            ('clear', 'clear', False),
            ('use-distribute', 'useDistribute', False),
            ('system-site-packages', 'systemSitePackages', False),
        ]
        helpers.convert_mapping_to_xml(
            t, data, virtualenv_mapping, fail_required=True)

    # Common arguments
    naturelist = ['shell', 'xshell', 'python']
    mapping = [
        ('nature', 'nature', 'shell', naturelist),
        ('command', 'command', ""),
        ('ignore-exit-code', 'ignoreExitCode', False),
    ]
    helpers.convert_mapping_to_xml(t, data, mapping, fail_required=True)


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
    mappings = [
        ('ini', 'toxIni', 'tox.ini'),
        ('recreate', 'recreate', False),
    ]
    helpers.convert_mapping_to_xml(t, data, mappings, fail_required=True)
    pattern = data.get('toxenv-pattern')
    if pattern:
        XML.SubElement(t, 'toxenvPattern').text = pattern


def managed_script(registry, xml_parent, data):
    """yaml: managed-script
    This step allows you to reference and execute a centrally managed
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
    mapping = [
        ('script-id', script_tag, None),
    ]
    helpers.convert_mapping_to_xml(ms, data, mapping, fail_required=True)
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

    mapping = [
        ('source-dir', 'sourceDir', None),  # Required parameter
        ('generator', 'generator', "Unix Makefiles"),
        ('clean-build-dir', 'cleanBuild', False),
    ]
    helpers.convert_mapping_to_xml(
        cmake, data, mapping, fail_required=True)

    info = registry.get_plugin_info("CMake plugin")
    # Note: Assume latest version of plugin is preferred config format
    version = pkg_resources.parse_version(
        info.get("version", str(sys.maxsize)))

    if version >= pkg_resources.parse_version("2.0"):
        mapping_20 = [
            ('preload-script', 'preloadScript', None),  # Optional parameter
            ('working-dir', 'workingDir', ''),
            ('build-type', 'buildType', 'Debug'),
            ('installation-name', 'installationName', 'InSearchPath'),
            ('other-arguments', 'toolArgs', ''),
        ]
        helpers.convert_mapping_to_xml(
            cmake, data, mapping_20, fail_required=False)

        tool_steps = XML.SubElement(cmake, 'toolSteps')

        for step_data in data.get('build-tool-invocations', []):
            step = XML.SubElement(
                tool_steps, 'hudson.plugins.cmake.BuildToolStep')
            step_mapping = [
                ('use-cmake', 'withCmake', False),
                ('arguments', 'args', ''),
                ('environment-variables', 'vars', ''),
            ]
            helpers.convert_mapping_to_xml(
                step, step_data, step_mapping, fail_required=True)

    else:
        mapping_10 = [
            ('preload-script', 'preloadScript', ''),
            ('build-dir', 'buildDir', ''),
            ('install-dir', 'installDir', ''),
            ('make-command', 'makeCommand', 'make'),
            ('install-command', 'installCommand', 'make install'),
            ('other-arguments', 'cmakeArgs', ''),
            ('custom-cmake-path', 'projectCmakePath', ''),
            ('clean-install-dir', 'cleanInstallDir', False),
        ]
        helpers.convert_mapping_to_xml(
            cmake, data, mapping_10, fail_required=True)

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

        if build_type.text not in BUILD_TYPES:
            other_build_type.text = build_type.text
            build_type.text = BUILD_TYPES[0]
        else:
            other_build_type.text = ''

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
    helpers.convert_mapping_to_xml(p, data, mappings, fail_required=True)


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

    mapping = [
        ('ssh-user-ip', 'siteName', None),
        ('command', 'command', None),
    ]
    helpers.convert_mapping_to_xml(builder, data, mapping, fail_required=True)


def sonar(registry, xml_parent, data):
    """yaml: sonar
    Invoke standalone Sonar analysis.
    Requires the Jenkins `Sonar Plugin.
    <http://docs.sonarqube.org/display/SCAN/\
        Analyzing+with+SonarQube+Scanner+for+Jenkins\
        #AnalyzingwithSonarQubeScannerforJenkins-\
        AnalyzingwiththeSonarQubeScanner>`_

    :arg str sonar-name: Name of the Sonar installation.
    :arg str sonar-scanner: Name of the Sonar Scanner.
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
        ('scanner-name', 'sonarScannerName', ''),
        ('task', 'task', ''),
        ('project', 'project', ''),
        ('properties', 'properties', ''),
        ('java-opts', 'javaOpts', ''),
        ('additional-arguments', 'additionalArguments', ''),
    ]
    helpers.convert_mapping_to_xml(sonar, data, mappings, fail_required=True)
    if 'jdk' in data:
        XML.SubElement(sonar, 'jdk').text = data['jdk']


def xcode(registry, xml_parent, data):
    """yaml: xcode
    This step allows you to execute an xcode build step. Requires the Jenkins
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
    :arg str ipa-export-method: The export method of the .app to generate the
        .ipa file.  Should be one in 'development', 'ad-hoc', 'enterprise',
        or 'app-store'. (default '')
    :arg str ipa-version: A pattern for the ipa file name. You may use
        ${VERSION} and ${BUILD_DATE} (yyyy.MM.dd) in this string.
        (default '')
    :arg str ipa-output: The output directory for the .ipa file,
        relative to the build directory. (default '')
    :arg bool compile-bitcode: recompile from Bitcode when exporting the
        application to IPA. (default true)
    :arg bool upload-bitcode: include Bitcode when exporting applications to
        IPA. (default true)
    :arg bool upload-symbols: include symbols when exporting applications to
        IPA. (default true)
    :arg development-team-id: The ID of the Apple development team to use to
        sign the IPA (default '')
    :arg str keychain-name: The globally configured keychain to unlock for
        this build. (default '')
    :arg str keychain-path: The path of the keychain to use to sign the IPA.
        (default '')
    :arg str keychain-password: The password to use to unlock the keychain.
        (default '')
    :arg str keychain-unlock: Unlocks the keychain during use.
        (default false)
    :arg str bundle-id: The bundle identifier (App ID) for this provisioning
        profile (default '')
    :arg str provisioning-profile-uuid: The UUID of the provisioning profile
        associated to this bundle identifier. (default '')

    Example:

    .. literalinclude:: /../../tests/builders/fixtures/xcode.yaml
       :language: yaml
    """

    if data.get('developer-profile'):
        profile = XML.SubElement(xml_parent, 'au.com.rayh.'
                                 'DeveloperProfileLoader')
        mapping = [
            ('developer-profile', 'id', None),
        ]
        helpers.convert_mapping_to_xml(
            profile, data, mapping, fail_required=False)

    xcode = XML.SubElement(xml_parent, 'au.com.rayh.XCodeBuilder')

    mappings = [
        ('clean-build', 'cleanBeforeBuild', False),
        ('clean-test-reports', 'cleanTestReports', False),
        ('archive', 'generateArchive', False),
        ('configuration', 'configuration', 'Release'),
        ('configuration-directory', 'configurationBuildDir', ''),
        ('target', 'target', ''),
        ('sdk', 'sdk', ''),
        ('symroot', 'symRoot', ''),
        ('project-path', 'xcodeProjectPath', ''),
        ('project-file', 'xcodeProjectFile', ''),
        ('build-arguments', 'xcodebuildArguments', ''),
        ('schema', 'xcodeSchema', ''),
        ('workspace', 'xcodeWorkspaceFile', ''),
        ('profile', 'embeddedProfileFile', ''),
        ('codesign-id', 'codeSigningIdentity', ''),
        ('allow-failing', 'allowFailingBuildResults', False),
    ]
    helpers.convert_mapping_to_xml(xcode, data, mappings, fail_required=True)

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

    valid_ipa_export_methods = ['', 'ad-hoc', 'app-store', 'development']
    mapping = [
        ('ipa-export-method', 'ipaExportMethod', '',
            valid_ipa_export_methods),
        ('ipa-version', 'ipaName', ''),
        ('ipa-output', 'ipaOutputDirectory', ''),
        ('development-team-id', 'developmentTeamID', ''),
        ('keychain-name', 'keychainName', ''),
        ('keychain-path', 'keychainPath', ''),
        ('keychain-password', 'keychainPwd', ''),
        ('keychain-unlock', 'unlockKeychain', False),
        ('compile-bitcode', 'compileBitcode', True),
        ('upload-bitcode', 'uploadBitcode', True),
        ('upload-symbols', 'uploadSymbols', True)
    ]
    helpers.convert_mapping_to_xml(xcode, data, mapping, fail_required=True)

    has_provisioning_profiles = bool(data.get('provisioning-profiles'))
    XML.SubElement(xcode, 'manualSigning').text = str(
        has_provisioning_profiles or False).lower()
    if has_provisioning_profiles:
        provisioning_profiles_xml = XML.SubElement(
            xcode, 'provisioningProfiles')
        mapping = [
            ('bundle-id', 'provisioningProfileAppId', ''),
            ('provisioning-profile-uuid', 'provisioningProfileUUID', ''),
        ]
        for provisioning_profile in data.get('provisioning-profiles'):
            provisioning_profile_xml = XML.SubElement(
                provisioning_profiles_xml, 'au.com.rayh.ProvisioningProfile')
            helpers.convert_mapping_to_xml(provisioning_profile_xml,
                provisioning_profile, mapping, fail_required=True)


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
        /../../tests/builders/fixtures/sonatype-clm-full.yaml
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
    helpers.convert_mapping_to_xml(
        application_select, data, application_mappings, fail_required=True)

    path = XML.SubElement(clm, 'pathConfig')
    path_mappings = [
        ('scan-targets', 'scanTargets', ''),
        ('module-excludes', 'moduleExcludes', ''),
        ('advanced-options', 'scanProperties', ''),
    ]
    helpers.convert_mapping_to_xml(
        path, data, path_mappings, fail_required=True)

    mappings = [
        ('fail-on-clm-server-failure', 'failOnClmServerFailures', False),
        ('stage', 'stageId', 'build', SUPPORTED_STAGES),
        ('username', 'username', ''),
        ('password', 'password', ''),
    ]
    helpers.convert_mapping_to_xml(clm, data, mappings, fail_required=True)


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
    region_dict = helpers.cloudformation_region_dict()
    stacks = helpers.cloudformation_init(
        xml_parent, data, 'CloudFormationBuildStep')
    for stack in data:
        helpers.cloudformation_stack(
            xml_parent, stack, 'PostBuildStackBean', stacks, region_dict)


def jms_messaging(registry, xml_parent, data):
    """yaml: jms-messaging
    The JMS Messaging Plugin provides the following functionality:
     - A build trigger to submit jenkins jobs upon receipt
       of a matching message.
     - A builder that may be used to submit a message to the topic
       upon the completion of a job
     - A post-build action that may be used to submit a message to the topic
       upon the completion of a job


    JMS Messaging provider types supported:
        - ActiveMQ
        - FedMsg

    Requires the Jenkins :jenkins-wiki:`JMS Messaging Plugin
    Pipeline Plugin <JMS+Messaging+Plugin>`.

    :arg str override-topic: If you need to override the default topic.
        (default '')
    :arg str provider-name: Name of message provider setup in the
        global config. (default '')
    :arg str msg-type: A message type
        (default 'CodeQualityChecksDone')
    :arg str msg-props: Message header to publish. (default '')
    :arg str msg-content: Message body to publish. (default '')


    Full Example:

    .. literalinclude::
        ../../tests/builders/fixtures/jms-messaging-full.yaml
       :language: yaml

    Minimal Example:

    .. literalinclude::
        ../../tests/builders/fixtures/jms-messaging-minimal.yaml
       :language: yaml
    """
    helpers.jms_messaging_common(xml_parent, 'com.redhat.jenkins.plugins.ci.'
                                             'CIMessageBuilder', data)


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
    helpers.convert_mapping_to_xml(osb, data, mapping, fail_required=True)


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
    helpers.convert_mapping_to_xml(osb, data, mapping, fail_required=True)


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
    helpers.convert_mapping_to_xml(osb, data, mapping, fail_required=True)


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
    helpers.convert_mapping_to_xml(osb, data, mapping, fail_required=True)


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
    helpers.convert_mapping_to_xml(osb, data, mapping, fail_required=True)


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
    helpers.convert_mapping_to_xml(osb, data, mapping, fail_required=True)


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
    helpers.convert_mapping_to_xml(osb, data, mapping, fail_required=True)


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
    helpers.convert_mapping_to_xml(osb, data, mapping, fail_required=True)


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
    helpers.convert_mapping_to_xml(runscope, data, mapping, fail_required=True)


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
    mapping = [
        ('regexp', 'regexp', ''),
    ]
    if 'description' in data:
        mapping.append(('description', 'description', None))
    helpers.convert_mapping_to_xml(
        descriptionsetter, data, mapping, fail_required=True)


def docker_build_publish(parse, xml_parent, data):
    """yaml: docker-build-publish
    Requires the Jenkins :jenkins-wiki:`Docker build publish Plugin
    <Docker+build+publish+Plugin>`.

    :arg str repo-name: Name of repository to push to.
    :arg str repo-tag: Tag for image. (default '')
    :arg dict server: The docker daemon (optional)

        * **uri** (str): Define the docker server to use. (optional)
        * **credentials-id** (str): ID of credentials to use to connect
          (optional)
    :arg dict registry: Registry to push to

        * **url** (str) repository url to use (optional)
        * **credentials-id** (str): ID of credentials to use to connect
          (optional)
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
    :arg bool create-fingerprint: If enabled, the plugin will create
        fingerprints after the build of each image. (default false)
    :arg str build-args: Additional build arguments passed to
        docker build (default '')
    :arg bool force-tag: Force tag replacement when tag already
        exists (default false)

    Minimal example:

    .. literalinclude:: /../../tests/builders/fixtures/docker-builder001.yaml

    Full example:

    .. literalinclude:: /../../tests/builders/fixtures/docker-builder002.yaml
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
        ('create-fingerprint', 'createFingerprint', False),
        ('build-args', 'buildAdditionalArgs', ''),
        ('force-tag', 'forceTag', False),
    ]
    helpers.convert_mapping_to_xml(db, data, mapping, fail_required=True)

    mapping = []
    if 'server' in data:
        server = XML.SubElement(db, 'server')
        server.set('plugin', 'docker-commons')
        server_data = data['server']
        if 'credentials-id' in server_data:
            mapping.append(('credentials-id', 'credentialsId', None))

        if 'uri' in server_data:
            mapping.append(('uri', 'uri', None))
        helpers.convert_mapping_to_xml(
            server, server_data, mapping, fail_required=True)

    mappings = []
    if 'registry' in data:
        registry = XML.SubElement(db, 'registry')
        registry.set('plugin', 'docker-commons')
        registry_data = data['registry']
        if 'credentials-id' in registry_data:
            mappings.append(('credentials-id', 'credentialsId', None))

        if 'url' in registry_data:
            mappings.append(('url', 'url', None))
        helpers.convert_mapping_to_xml(
            registry, registry_data, mappings, fail_required=True)


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
    helpers.convert_mapping_to_xml(
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
        /../../tests/builders/fixtures/nexus_artifact_uploader001.yaml
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
    helpers.convert_mapping_to_xml(
        nexus_artifact_uploader, data, mapping, fail_required=True)


def nexus_iq_policy_evaluator(registry, xml_parent, data):
    """yaml: nexus-iq-policy-evaluator
    Integrates the Nexus Lifecycle into a Jenkins job.
    This function triggers 'Invokes Nexus Policy Evaluation'.
    Requires the Jenkins :jenkins-wiki:`Nexus
    Platform Plugin <Nexus+Platform+Plugin>`.

    :arg str stage: Controls the stage the policy evaluation will be
        run against on the Nexus IQ Server (required)

        :stage values:
            * **build**
            * **stage-release**
            * **operate**
    :arg dict application-type: Specifies an IQ Application (default manual)

        :application-type values:
            * **manual**
            * **selected**
    :arg str application-id: Specify the IQ Application ID (required)
    :arg list scan-patterns: List of Ant-style patterns relative to the
        workspace root that denote files/archives to be scanned (default [])
    :arg bool fail-build-network-error: Controls the build outcome if there
        is a failure in communicating with the Nexus IQ Server (default false)

    Minimal Example:

    .. literalinclude::
        /../../tests/builders/fixtures/nexus-iq-policy-evaluator-minimal.yaml
       :language: yaml

    Full Example:

    .. literalinclude::
        /../../tests/builders/fixtures/nexus-iq-policy-evaluator-full.yaml
       :language: yaml
    """
    nexus_iq_policy_evaluator = XML.SubElement(
        xml_parent,
        'org.sonatype.nexus.ci.iq.IqPolicyEvaluatorBuildStep')

    format_dict = {
        'stage': 'com__sonatype__nexus__ci__iq__IqPolicyEvaluator____iqStage',
        'fone': 'com__sonatype__nexus__ci__iq__IqPolicyEvaluator'
                '____failBuildOnNetworkError',
    }

    valid_stages = ['build', 'stage-release', 'operate']
    mapping = [
        ('stage', format_dict.get('stage'), None, valid_stages),
        ('fail-build-network-error', format_dict.get('fone'), False),
    ]
    helpers.convert_mapping_to_xml(
        nexus_iq_policy_evaluator, data, mapping, fail_required=True)

    application_type_label = data.get('application-type', 'manual').lower()
    application_type_label_dict = {
        'manual': 'org.sonatype.nexus.ci.iq.ManualApplication',
        'selected': 'org.sonatype.nexus.ci.iq.SelectedApplication',
    }
    if application_type_label not in application_type_label_dict:
        raise InvalidAttributeError(application_type_label,
                                    application_type_label,
                                    application_type_label_dict.keys())

    application_type_tag = XML.SubElement(
        nexus_iq_policy_evaluator,
        'com__sonatype__nexus__ci__iq__IqPolicyEvaluator____iqApplication')
    application_type_tag.set(
        "class", application_type_label_dict[application_type_label]
    )

    mapping = [
        ('application-id', 'applicationId', None),
    ]
    helpers.convert_mapping_to_xml(application_type_tag, data,
        mapping, fail_required=True)

    scan_pattern_list = data.get('scan-patterns', [])
    iq_scan_pattern_tag = XML.SubElement(nexus_iq_policy_evaluator,
                                  'com__sonatype__nexus__ci__iq'
                                  '__IqPolicyEvaluator____iqScanPatterns')

    for scan_pattern in scan_pattern_list:
        scan_pattern_tag = XML.SubElement(
            iq_scan_pattern_tag, 'org.sonatype.nexus.ci.iq.ScanPattern')
        XML.SubElement(scan_pattern_tag, 'scanPattern').text = scan_pattern


def nexus_repo_manager(registry, xml_parent, data):
    """yaml: nexus-repo-manager
    Allows for artifacts selected in Jenkins packages to be
    available in Nexus Repository Manager.
    Requires the Jenkins :jenkins-wiki:`Nexus
    Platform Plugin <Nexus+Platform+Plugin>`.

    :arg str instance-id: The ID of the Nexus Instance (required)
    :arg str repo-id: The ID of the Nexus Repository (required)

    Minimal Example:

    .. literalinclude::
        /../../tests/builders/fixtures/nexus-repo-manager-minimal.yaml
       :language: yaml
    """
    nexus_repo_manager = XML.SubElement(xml_parent,
                                        'org.sonatype.nexus.ci.'
                                        'nxrm.NexusPublisherBuildStep')
    mapping = [
        ('instance-id', 'nexusInstanceId', None),
        ('repo-id', 'nexusRepositoryId', None),
    ]
    helpers.convert_mapping_to_xml(nexus_repo_manager,
                                   data, mapping, fail_required=True)


def ansible_playbook(parser, xml_parent, data):
    """yaml: ansible-playbook
    This plugin allows you to execute Ansible tasks as a job build step.
    Requires the Jenkins :jenkins-wiki:`Ansible Plugin <Ansible+Plugin>`.

    :arg str playbook: Path to the ansible playbook file. The path can be
        absolute or relative to the job workspace. (required)
    :arg str inventory-type: The inventory file form (default `path`)

        :inventory-type values:
            * **path**
            * **content**
            * **do-not-specify**

    :arg dict inventory: Inventory data, depends on inventory-type

        :inventory-type == path:
            * **path** (`str`) -- Path to inventory file.

        :inventory-type == content:
            * **content** (`str`) -- Content of inventory file.
            * **dynamic** (`bool`) -- Dynamic inventory is used (default false)

    :arg str hosts: Further limit selected hosts to an additional pattern
        (default '')
    :arg str tags-to-run: Only run plays and tasks tagged with these values
        (default '')
    :arg str tags-to-skip: Only run plays and tasks whose tags do not match
        these values (default '')
    :arg str task-to-start-at: Start the playbook at the task matching this
        name (default '')
    :arg int workers: Specify number of parallel processes to use (default 5)
    :arg str credentials-id: The ID of credentials for the SSH connections.
        Only private key authentication is supported (default '')
    :arg bool sudo: Run operations with sudo. It works only when the remote
        user is sudoer with nopasswd option (default false)
    :arg str sudo-user: Desired sudo user. "root" is used when this field is
        empty. (default '')
    :arg bool unbuffered-output: Skip standard output buffering for the ansible
        process. The ansible output is directly rendered into the Jenkins
        console. This option can be useful for long running operations.
        (default true)
    :arg bool colorized-output: Check this box to allow ansible to render ANSI
        color codes in the Jenkins console. (default false)
    :arg bool host-key-checking: Check this box to enforce the validation of
        the hosts SSH server keys. (default false)
    :arg str additional-parameters: Any additional parameters to pass to the
        ansible command. (default '')
    :arg list variables: List of extra variables to be passed to ansible.
        (optional)

        :variable item:
            * **name** (`str`) -- Name of variable (required)
            * **value** (`str`) -- Desired value (default '')
            * **hidden** (`bool`) -- Hide variable in build log (default false)

    Example:

    .. literalinclude::
        /../../tests/builders/fixtures/ansible-playbook001.yaml
       :language: yaml

    OR

    .. literalinclude::
        /../../tests/builders/fixtures/ansible-playbook002.yaml
       :language: yaml
    """
    plugin = XML.SubElement(
        xml_parent,
        'org.jenkinsci.plugins.ansible.AnsiblePlaybookBuilder')
    try:
        XML.SubElement(plugin, 'playbook').text = str(data['playbook'])
    except KeyError as ex:
        raise MissingAttributeError(ex)

    inventory_types = ('path', 'content', 'do-not-specify')
    inventory_type = str(
        data.get('inventory-type', inventory_types[0])).lower()

    inventory = XML.SubElement(plugin, 'inventory')
    inv_data = data.get('inventory', {})
    if inventory_type == 'path':
        inventory.set(
            'class', 'org.jenkinsci.plugins.ansible.InventoryPath')
        try:
            path = inv_data['path']
        except KeyError:
            raise MissingAttributeError('inventory[\'path\']')
        XML.SubElement(inventory, 'path').text = path
    elif inventory_type == 'content':
        inventory.set(
            'class', 'org.jenkinsci.plugins.ansible.InventoryContent')
        try:
            content = inv_data['content']
        except KeyError:
            raise MissingAttributeError('inventory[\'content\']')
        XML.SubElement(inventory, 'content').text = content
        XML.SubElement(inventory, 'dynamic').text = str(
            inv_data.get('dynamic', False)).lower()
    elif inventory_type == 'do-not-specify':
        inventory.set(
            'class', 'org.jenkinsci.plugins.ansible.InventoryDoNotSpecify')
    else:
        raise InvalidAttributeError(
            'inventory-type', inventory_type, inventory_types)
    XML.SubElement(plugin, 'limit').text = data.get('hosts', '')
    XML.SubElement(plugin, 'tags').text = data.get('tags-to-run', '')
    XML.SubElement(plugin, 'skippedTags').text = data.get('tags-to-skip', '')
    XML.SubElement(plugin, 'startAtTask').text = data.get(
        'task-to-start-at', '')
    XML.SubElement(plugin, 'credentialsId').text = data.get(
        'credentials-id', '')
    if data.get('sudo', False):
        XML.SubElement(plugin, 'sudo').text = 'true'
        XML.SubElement(plugin, 'sudoUser').text = data.get('sudo-user', '')
    else:
        XML.SubElement(plugin, 'sudo').text = 'false'
    XML.SubElement(plugin, 'forks').text = str(data.get('workers', '5'))
    XML.SubElement(plugin, 'unbufferedOutput').text = str(
        data.get('unbuffered-output', True)).lower()
    XML.SubElement(plugin, 'colorizedOutput').text = str(
        data.get('colorized-output', False)).lower()
    XML.SubElement(plugin, 'hostKeyChecking').text = str(
        data.get('host-key-checking', False)).lower()
    XML.SubElement(plugin, 'additionalParameters').text = str(
        data.get('additional-parameters', ''))
    # Following option is not available from UI
    XML.SubElement(plugin, 'copyCredentialsInWorkspace').text = 'false'
    variables = data.get('variables', [])
    if variables:
        if not is_sequence(variables):
            raise InvalidAttributeError(
                'variables', variables, 'list(dict(name, value, hidden))')
        variables_elm = XML.SubElement(plugin, 'extraVars')
        for idx, values in enumerate(variables):
            if not hasattr(values, 'keys'):
                raise InvalidAttributeError(
                    'variables[%s]' % idx, values, 'dict(name, value, hidden)')
            try:
                var_name = values['name']
            except KeyError:
                raise MissingAttributeError('variables[%s][\'name\']' % idx)
            value_elm = XML.SubElement(
                variables_elm, 'org.jenkinsci.plugins.ansible.ExtraVar')
            XML.SubElement(value_elm, 'key').text = var_name
            XML.SubElement(value_elm, 'value').text = values.get('value', '')
            XML.SubElement(value_elm, 'hidden').text = str(
                values.get('hidden', False)).lower()


def nodejs(parser, xml_parent, data):
    """yaml: nodejs
    This plugin allows you to execute NodeJS scripts as a job build step.
    Requires the Jenkins :jenkins-wiki:`NodeJS Plugin <NodeJS+Plugin>`.

    :arg str name: NodeJS installation name
    :arg str script: NodeJS script (required)
    :arg str config-id: ID of npmrc config file, which is the
        last field (a 32-digit hexadecimal code) of the path of URL visible
        after you clicked the file under Jenkins Managed Files.

    Minimal Example:

    .. literalinclude::
        ../../tests/builders/fixtures/nodejs-minimal.yaml
       :language: yaml

    Full Example:

    .. literalinclude::
        ../../tests/builders/fixtures/nodejs-full.yaml
       :language: yaml
    """
    nodejs = XML.SubElement(xml_parent,
                            'jenkins.plugins.nodejs.NodeJSCommandInterpreter')
    mapping = [
        ('script', 'command', None),
    ]

    mapping_opt = [
        ('name', 'nodeJSInstallationName', None),
        ('config-id', 'configId', None),
    ]

    helpers.convert_mapping_to_xml(nodejs, data, mapping, fail_required=True)
    helpers.convert_mapping_to_xml(
        nodejs, data, mapping_opt, fail_required=False)


def xunit(registry, xml_parent, data):
    """yaml: xunit
    Process tests results. Requires the Jenkins :jenkins-wiki:`xUnit Plugin
    <xUnit+Plugin>`.

    :arg str thresholdmode: Whether thresholds represents an absolute number
        of tests or a percentage. Either 'number' or 'percent'. (default
        'number')
    :arg list thresholds: Thresholds for both 'failed' and 'skipped' tests.

        :threshold (`dict`): Threshold values to set, where missing, xUnit
            should default to an internal value of 0. Each test threshold
            should contain the following:

            * **unstable** (`int`)
            * **unstablenew** (`int`)
            * **failure** (`int`)
            * **failurenew** (`int`)

    :arg int test-time-margin: Give the report time margin value in ms, before
        to fail if not new unless the option **requireupdate** is set for the
        configured framework. (default 3000)
    :arg list types: Frameworks to configure, and options. Supports the
        following: ``aunit``, ``boosttest``, ``checktype``, ``cpptest``,
        ``cppunit``, ``ctest``, ``dotnettest``, ``embunit``, ``fpcunit``,
        ``gtest``, ``junit``, ``mstest``, ``nunit``, ``phpunit``, ``tusar``,
        ``unittest``, and ``valgrind``.

        The 'custom' type is not supported.

        :type (`dict`): each type can be configured using the following:

            * **pattern** (`str`): An Ant pattern to look for Junit result
              files, relative to the workspace root (default '')
            * **requireupdate** (`bool`): fail the build whenever fresh tests
              results have not been found (default true).
            * **deleteoutput** (`bool`): delete temporary JUnit files
              (default true).
            * **skip-if-no-test-files** (`bool`): Skip parsing this xUnit type
              report if there are no test reports files (default false).
            * **stoponerror** (`bool`): Fail the build whenever an error occur
              during a result file processing (default true).

    Minimal Example:

    .. literalinclude::
        /../../tests/builders/fixtures/xunit-minimal.yaml
       :language: yaml

    Full Example:

    .. literalinclude::
        /../../tests/builders/fixtures/xunit-full.yaml
       :language: yaml

    """
    logger = logging.getLogger(__name__)
    xunit = XML.SubElement(xml_parent,
                           'org.jenkinsci.plugins.xunit.XUnitBuilder')
    xunit.set('plugin', 'xunit')

    # Map our internal types to the XML element names used by Jenkins plugin
    types_to_plugin_types = {
        'aunit': 'AUnitJunitHudsonTestType',
        'boosttest': 'BoostTestJunitHudsonTestType',
        'checktype': 'CheckType',
        'cpptest': 'CppTestJunitHudsonTestType',
        'cppunit': 'CppUnitJunitHudsonTestType',
        'ctest': 'CTestType',
        'dotnettest': 'XUnitDotNetTestType',  # since plugin v1.93
        'embunit': 'EmbUnitType',  # since plugin v1.84
        'fpcunit': 'FPCUnitJunitHudsonTestType',
        'gtest': 'GoogleTestType',
        'junit': 'JUnitType',
        'mstest': 'MSTestJunitHudsonTestType',
        'nunit': 'NUnitJunitHudsonTestType',
        'phpunit': 'PHPUnitJunitHudsonTestType',
        'tusar': 'TUSARJunitHudsonTestType',
        'unittest': 'UnitTestJunitHudsonTestType',
        'valgrind': 'ValgrindJunitHudsonTestType',
        # FIXME should implement the 'custom' type
    }
    implemented_types = types_to_plugin_types.keys()  # shortcut

    # Unit framework we are going to generate xml for
    supported_types = []

    for configured_type in data['types']:
        type_name = next(iter(configured_type.keys()))
        if type_name not in implemented_types:
            logger.warning("Requested xUnit type '%s' is not yet supported",
                           type_name)
        else:
            # Append for generation
            supported_types.append(configured_type)

    # Generate XML for each of the supported framework types
    xmltypes = XML.SubElement(xunit, 'types')
    mappings = [
        ('pattern', 'pattern', ''),
        ('requireupdate', 'failIfNotNew', True),
        ('deleteoutput', 'deleteOutputFiles', True),
        ('skip-if-no-test-files', 'skipNoTestFiles', False),
        ('stoponerror', 'stopProcessingIfError', True),
    ]
    for supported_type in supported_types:
        framework_name = next(iter(supported_type.keys()))
        xmlframework = XML.SubElement(xmltypes,
                                      types_to_plugin_types[framework_name])

        helpers.convert_mapping_to_xml(xmlframework,
                                       supported_type[framework_name],
                                       mappings,
                                       fail_required=True)

    xmlthresholds = XML.SubElement(xunit, 'thresholds')
    for t in data.get('thresholds', []):
        if not ('failed' in t or 'skipped' in t):
            logger.warning(
                "Unrecognized threshold, should be 'failed' or 'skipped'")
            continue
        elname = ("org.jenkinsci.plugins.xunit.threshold.%sThreshold" %
                  next(iter(t.keys())).title())
        el = XML.SubElement(xmlthresholds, elname)
        for threshold_name, threshold_value in next(iter(t.values())).items():
            # Normalize and craft the element name for this threshold
            elname = "%sThreshold" % threshold_name.lower().replace(
                'new', 'New')
            XML.SubElement(el, elname).text = str(threshold_value)

    # Whether to use percent of exact number of tests.
    # Thresholdmode is either:
    # - 1 : absolute (number of tests), default.
    # - 2 : relative (percentage of tests)
    thresholdmode = '1'
    if 'percent' == data.get('thresholdmode', 'number'):
        thresholdmode = '2'
    XML.SubElement(xunit, 'thresholdMode').text = thresholdmode

    extra_config = XML.SubElement(xunit, 'extraConfiguration')
    XML.SubElement(extra_config, 'testTimeMargin').text = str(
        data.get('test-time-margin', '3000'))
