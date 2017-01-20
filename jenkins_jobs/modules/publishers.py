# Copyright 2012 Hewlett-Packard Development Company, L.P.
# Copyright 2012 Varnish Software AS
# Copyright 2013-2014 Antoine "hashar" Musso
# Copyright 2013-2014 Wikimedia Foundation Inc.
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
Publishers define actions that the Jenkins job should perform after
the build is complete.

**Component**: publishers
  :Macro: publisher
  :Entry Point: jenkins_jobs.publishers
"""

import logging
import pkg_resources
import random
import xml.etree.ElementTree as XML

import six

from jenkins_jobs.errors import InvalidAttributeError
from jenkins_jobs.errors import JenkinsJobsException
from jenkins_jobs.errors import MissingAttributeError
import jenkins_jobs.modules.base
from jenkins_jobs.modules import hudson_model
import jenkins_jobs.modules.helpers as helpers


def archive(registry, xml_parent, data):
    """yaml: archive
    Archive build artifacts

    :arg str artifacts: path specifier for artifacts to archive
    :arg str excludes: path specifier for artifacts to exclude (optional)
    :arg bool latest-only: only keep the artifacts from the latest
        successful build
    :arg bool allow-empty:  pass the build if no artifacts are
        found (default false)
    :arg bool only-if-success: archive artifacts only if build is successful
        (default false)
    :arg bool fingerprint: fingerprint all archived artifacts (default false)
    :arg bool default-excludes: This option allows to enable or disable the
        default Ant exclusions. (default true)

    Example:

    .. literalinclude::  /../../tests/publishers/fixtures/archive001.yaml
       :language: yaml
    """
    logger = logging.getLogger("%s:archive" % __name__)
    archiver = XML.SubElement(xml_parent, 'hudson.tasks.ArtifactArchiver')
    artifacts = XML.SubElement(archiver, 'artifacts')
    artifacts.text = data['artifacts']
    if 'excludes' in data:
        excludes = XML.SubElement(archiver, 'excludes')
        excludes.text = data['excludes']
    latest = XML.SubElement(archiver, 'latestOnly')
    # backward compatibility
    latest_only = data.get('latest_only', False)
    if 'latest_only' in data:
        logger.warning('latest_only is deprecated please use latest-only')
    if 'latest-only' in data:
        latest_only = data['latest-only']
    if latest_only:
        latest.text = 'true'
    else:
        latest.text = 'false'

    if 'allow-empty' in data:
        empty = XML.SubElement(archiver, 'allowEmptyArchive')
        # Default behavior is to fail the build.
        empty.text = str(data.get('allow-empty', False)).lower()

    if 'only-if-success' in data:
        success = XML.SubElement(archiver, 'onlyIfSuccessful')
        success.text = str(data.get('only-if-success', False)).lower()

    if 'fingerprint' in data:
        fingerprint = XML.SubElement(archiver, 'fingerprint')
        fingerprint.text = str(data.get('fingerprint', False)).lower()

    default_excludes = XML.SubElement(archiver, 'defaultExcludes')
    default_excludes.text = str(data.get('default-excludes', True)).lower()


def blame_upstream(registry, xml_parent, data):
    """yaml: blame-upstream
    Notify upstream commiters when build fails
    Requires the Jenkins :jenkins-wiki:`Blame upstream commiters Plugin
    <Blame+Upstream+Committers+Plugin>`.

    Example:

    .. literalinclude::  /../../tests/publishers/fixtures/blame001.yaml
       :language: yaml
    """

    XML.SubElement(xml_parent,
                   'hudson.plugins.blame__upstream__commiters.'
                   'BlameUpstreamCommitersPublisher')


def jclouds(registry, xml_parent, data):
    """yaml: jclouds
    JClouds Cloud Storage Settings provides a way to store artifacts on
    JClouds supported storage providers. Requires the Jenkins
    :jenkins-wiki:`JClouds Plugin <JClouds+Plugin>`.

    JClouds Cloud Storage Settings must be configured for the Jenkins instance.

    :arg str profile: preconfigured storage profile (required)
    :arg str files: files to upload (regex) (required)
    :arg str basedir: the source file path (relative to workspace, Optional)
    :arg str container: the destination container name (required)
    :arg bool hierarchy: keep hierarchy (default false)

    Example:

    .. literalinclude::  /../../tests/publishers/fixtures/jclouds001.yaml

    """

    deployer = XML.SubElement(xml_parent,
                              'jenkins.plugins.jclouds.blobstore.'
                              'BlobStorePublisher')

    if 'profile' not in data:
        raise JenkinsJobsException('profile parameter is missing')
    XML.SubElement(deployer, 'profileName').text = data.get('profile')

    entries = XML.SubElement(deployer, 'entries')

    deployer_entry = XML.SubElement(entries,
                                    'jenkins.plugins.jclouds.blobstore.'
                                    'BlobStoreEntry')

    try:
        XML.SubElement(deployer_entry, 'container').text = data['container']
        XML.SubElement(deployer_entry, 'path').text = data.get('basedir', '')
        XML.SubElement(deployer_entry, 'sourceFile').text = data['files']
    except KeyError as e:
        raise JenkinsJobsException("blobstore requires '%s' to be set"
                                   % e.args[0])

    XML.SubElement(deployer_entry, 'keepHierarchy').text = str(
        data.get('hierarchy', False)).lower()


def javadoc(registry, xml_parent, data):
    """yaml: javadoc
    Publish Javadoc
    Requires the Jenkins :jenkins-wiki:`Javadoc Plugin <Javadoc+Plugin>`.

    :arg str directory: Directory relative to the root of the workspace,
      such as 'myproject/build/javadoc' (optional)
    :arg bool keep-all-successful: When true, it will retain Javadoc for each
      successful build. This allows you to browse Javadoc for older builds,
      at the expense of additional disk space requirement. If false, it will
      only keep the latest Javadoc, so older Javadoc will be overwritten as
      new builds succeed. (default false)

    Example:

    .. literalinclude::  /../../tests/publishers/fixtures/javadoc001.yaml
       :language: yaml
    """

    root = XML.SubElement(xml_parent, 'hudson.tasks.JavadocArchiver')
    if 'directory' in data:
        XML.SubElement(root, 'javadocDir').text = data.get('directory', '')
    XML.SubElement(root, 'keepAll').text = str(data.get(
        'keep-all-successful', False)).lower()


def jdepend(registry, xml_parent, data):
    """yaml: jdepend
    Publish jdepend report
    Requires the :jenkins-wiki:`JDepend Plugin <JDepend+Plugin>`.

    :arg str file: path to jdepend file (required)

    Example:

    .. literalinclude::  /../../tests/publishers/fixtures/jdepend001.yaml
       :language: yaml
    """
    jdepend = XML.SubElement(
        xml_parent,
        'hudson.plugins.jdepend.JDependRecorder')
    mapping = [('file', 'configuredJDependFile', None)]
    helpers.convert_mapping_to_xml(jdepend, data, mapping, fail_required=True)


def hue_light(registry, xml_parent, data):
    """yaml: hue-light
    This plugin shows the state of your builds using the awesome Philips hue
    lights.

    Requires the Jenkins :jenkins-wiki:`hue-light Plugin
    <hue-light+Plugin>`.

    :arg int light-id: ID of light. Define multiple lights by a comma as a
        separator (required)
    :arg string pre-build: Colour of building state (default 'blue')
    :arg string good-build: Colour of succesful state (default 'green')
    :arg string unstable-build: Colour of unstable state (default 'yellow')
    :arg string bad-build: Colour of unsuccessful state (default 'red')

    Full Example:

    .. literalinclude:: /../../tests/publishers/fixtures/hue-light-full.yaml
       :language: yaml

    Minimal Example:

    .. literalinclude:: /../../tests/publishers/fixtures/hue-light-minimal.yaml
       :language: yaml
    """

    hue_light = XML.SubElement(
        xml_parent, 'org.jenkinsci.plugins.hue__light.LightNotifier')
    hue_light.set('plugin', 'hue-light')
    lightId = XML.SubElement(hue_light, 'lightId')

    id_mapping = [('light-id', 'string', None)]
    helpers.convert_mapping_to_xml(
        lightId, data, id_mapping, fail_required=True)

    build_mapping = [
        ('pre-build', 'preBuild', 'blue'),
        ('good-build', 'goodBuild', 'green'),
        ('unstable-build', 'unstableBuild', 'yellow'),
        ('bad-build', 'badBuild', 'red'),
    ]
    helpers.convert_mapping_to_xml(
        hue_light, data, build_mapping, fail_required=True)


def campfire(registry, xml_parent, data):
    """yaml: campfire
    Send build notifications to Campfire rooms.
    Requires the Jenkins :jenkins-wiki:`Campfire Plugin <Campfire+Plugin>`.

    Campfire notifications global default values must be configured for
    the Jenkins instance. Default values will be used if no specific
    values are specified for each job, so all config params are optional.

    :arg str subdomain: override the default campfire subdomain
    :arg str token: override the default API token
    :arg bool ssl: override the default 'use SSL'
    :arg str room: override the default room name

    Example:

    .. literalinclude::  /../../tests/publishers/fixtures/campfire001.yaml
       :language: yaml
    """

    root = XML.SubElement(xml_parent,
                          'hudson.plugins.campfire.'
                          'CampfireNotifier')

    campfire = XML.SubElement(root, 'campfire')

    if ('subdomain' in data and data['subdomain']):
        subdomain = XML.SubElement(campfire, 'subdomain')
        subdomain.text = data['subdomain']
    if ('token' in data and data['token']):
        token = XML.SubElement(campfire, 'token')
        token.text = data['token']
    if ('ssl' in data):
        ssl = XML.SubElement(campfire, 'ssl')
        ssl.text = str(data['ssl']).lower()

    if ('room' in data and data['room']):
        room = XML.SubElement(root, 'room')
        name = XML.SubElement(room, 'name')
        name.text = data['room']

        XML.SubElement(room, 'campfire reference="../../campfire"')


def codecover(registry, xml_parent, data):
    """yaml: codecover
    This plugin allows you to capture code coverage report from CodeCover.
    Jenkins will generate the trend report of coverage.
    Requires the Jenkins :jenkins-wiki:`CodeCover Plugin <CodeCover+Plugin>`.

    :arg str include: Specify the path to the CodeCover HTML report file,
        relative to the workspace root (default '')
    :arg int min-statement: Minimum statement threshold (default 0)
    :arg int max-statement: Maximum statement threshold (default 90)
    :arg int min-branch: Minimum branch threshold (default 0)
    :arg int max-branch: Maximum branch threshold (default 80)
    :arg int min-loop: Minimum loop threshold (default 0)
    :arg int max-loop: Maximum loop threshold (default 50)
    :arg int min-condition: Minimum condition threshold (default 0)
    :arg int max-condition: Maximum conditon threshold (default 50)

    Minimal Example:

    .. literalinclude:: /../../tests/publishers/fixtures/codecover-minimal.yaml
       :language: yaml

    Full Example:

    .. literalinclude:: /../../tests/publishers/fixtures/codecover-full.yaml
       :language: yaml
    """

    codecover = XML.SubElement(
        xml_parent, 'hudson.plugins.codecover.CodeCoverPublisher')
    codecover.set('plugin', 'codecover')

    XML.SubElement(codecover, 'includes').text = str(data.get('include', ''))

    health_report = XML.SubElement(codecover, 'healthReports')
    mapping = [
        ('min-statement', 'minStatement', 0),
        ('max-statement', 'maxStatement', 90),
        ('min-branch', 'minBranch', 0),
        ('max-branch', 'maxBranch', 80),
        ('min-loop', 'minLoop', 0),
        ('max-loop', 'maxLoop', 50),
        ('min-condition', 'minCondition', 0),
        ('max-condition', 'maxCondition', 50),
    ]
    helpers.convert_mapping_to_xml(
        health_report, data, mapping, fail_required=True)


def emotional_jenkins(registry, xml_parent, data):
    """yaml: emotional-jenkins
    Emotional Jenkins. This funny plugin changes the expression of Mr. Jenkins
    in the background when your builds fail.

    Requires the Jenkins :jenkins-wiki:`Emotional Jenkins Plugin
    <Emotional+Jenkins+Plugin>`.

    Example:

    .. literalinclude:: /../../tests/publishers/fixtures/emotional-jenkins.yaml
       :language: yaml
    """
    XML.SubElement(xml_parent,
                   'org.jenkinsci.plugins.emotional__jenkins.'
                   'EmotionalJenkinsPublisher')


def trigger_parameterized_builds(registry, xml_parent, data):
    """yaml: trigger-parameterized-builds
    Trigger parameterized builds of other jobs.
    Requires the Jenkins :jenkins-wiki:`Parameterized Trigger Plugin
    <Parameterized+Trigger+Plugin>`.

    Use of the `node-label-name` or `node-label` parameters
    requires the Jenkins :jenkins-wiki:`NodeLabel Parameter Plugin
    <NodeLabel+Parameter+Plugin>`.
    Note: 'node-parameters' overrides the Node that the triggered
    project is tied to.

    :arg list project: list the jobs to trigger, will generate comma-separated
      string containing the named jobs.
    :arg str predefined-parameters: parameters to pass to the other
      job (optional)
    :arg bool current-parameters: Whether to include the parameters passed
      to the current build to the triggered job (optional)
    :arg bool node-parameters: Use the same Node for the triggered builds
      that was used for this build. (optional)
    :arg bool svn-revision: Pass svn revision to the triggered job (optional)
    :arg bool include-upstream: Include/pass through Upstream SVN Revisons.
        Only valid when 'svn-revision' is true. (default false)
    :arg dict git-revision: Passes git revision to the triggered job
        (optional).

        * **combine-queued-commits** (bool): Whether to combine queued git
          hashes or not (default false)

    :arg bool combine-queued-commits: Combine Queued git hashes. Only valid
        when 'git-revision' is true. (default false)

        .. deprecated:: 1.5.0 Please use `combine-queued-commits` under the
            `git-revision` argument instead.

    :arg dict boolean-parameters: Pass boolean parameters to the downstream
        jobs. Specify the name and boolean value mapping of the parameters.
        (optional)
    :arg str condition: when to trigger the other job. Can be: 'SUCCESS',
      'UNSTABLE', 'FAILED_OR_BETTER', 'UNSTABLE_OR_BETTER',
      'UNSTABLE_OR_WORSE', 'FAILED', 'ALWAYS'. (default 'ALWAYS')
    :arg str property-file: Use properties from file (optional)
    :arg bool fail-on-missing: Blocks the triggering of the downstream jobs
        if any of the property files are not found in the workspace.
        Only valid when 'property-file' is specified.
        (default 'False')
    :arg bool use-matrix-child-files: Use files in workspaces of child
        builds (default 'False')
    :arg str matrix-child-combination-filter: A Groovy expression to filter
        the child builds to look in for files
    :arg bool only-exact-matrix-child-runs: Use only child builds triggered
        exactly by the parent.
    :arg str file-encoding: Encoding of contents of the files. If not
        specified, default encoding of the platform is used. Only valid when
        'property-file' is specified. (optional)
    :arg bool trigger-with-no-params: Trigger a build even when there are
      currently no parameters defined (default 'False')
    :arg str restrict-matrix-project: Filter that restricts the subset
        of the combinations that the downstream project will run (optional)
    :arg str node-label-name: Specify the Name for the NodeLabel parameter.
      (optional)
    :arg str node-label: Specify the Node for the NodeLabel parameter.
      (optional)

    Example:

    .. literalinclude::
        /../../tests/publishers/fixtures/trigger_parameterized_builds001.yaml
       :language: yaml
    .. literalinclude::
        /../../tests/publishers/fixtures/trigger_parameterized_builds003.yaml
       :language: yaml
    """
    logger = logging.getLogger("%s:trigger-parameterized-builds" % __name__)
    pt_prefix = 'hudson.plugins.parameterizedtrigger.'
    tbuilder = XML.SubElement(xml_parent, pt_prefix + 'BuildTrigger')
    configs = XML.SubElement(tbuilder, 'configs')

    # original order
    orig_order = [
        'predefined-parameters',
        'git-revision',
        'property-file',
        'current-parameters',
        'node-parameters',
        'svn-revision',
        'restrict-matrix-project',
        'node-label-name',
        'node-label',
        'boolean-parameters',
    ]

    try:
        if registry.jjb_config.config_parser.getboolean(
                '__future__', 'param_order_from_yaml'):
            orig_order = None
    except six.moves.configparser.NoSectionError:
        pass

    if orig_order:
        logger.warning(
            "Using deprecated order for parameter sets in "
            "triggered-parameterized-builds. This will be changed in a future "
            "release to inherit the order from the user defined yaml. To "
            "enable this behaviour immediately, set the config option "
            "'__future__.param_order_from_yaml' to 'true' and change the "
            "input job configuration to use the desired order")

    for project_def in data:
        tconfig = XML.SubElement(configs, pt_prefix + 'BuildTriggerConfig')
        tconfigs = XML.SubElement(tconfig, 'configs')

        if orig_order:
            parameters = orig_order
        else:
            parameters = project_def.keys()

        for param_type in parameters:
            param_value = project_def.get(param_type)
            if param_value is None:
                continue

            if param_type == 'predefined-parameters':
                params = XML.SubElement(tconfigs, pt_prefix +
                                        'PredefinedBuildParameters')
                properties = XML.SubElement(params, 'properties')
                properties.text = param_value
            elif param_type == 'git-revision' and param_value:
                if 'combine-queued-commits' in project_def:
                    logger.warning(
                        "'combine-queued-commit' has moved to reside under "
                        "'git-revision' configuration, please update your "
                        "configs as support for this will be removed."
                    )
                    git_revision = {
                        'combine-queued-commits':
                        project_def['combine-queued-commits']
                    }
                else:
                    git_revision = project_def['git-revision']
                helpers.append_git_revision_config(tconfigs, git_revision)
            elif param_type == 'property-file':
                params = XML.SubElement(tconfigs,
                                        pt_prefix + 'FileBuildParameters')
                properties = XML.SubElement(params, 'propertiesFile')
                properties.text = project_def['property-file']
                failOnMissing = XML.SubElement(params, 'failTriggerOnMissing')
                failOnMissing.text = str(project_def.get('fail-on-missing',
                                                         False)).lower()
                if 'file-encoding' in project_def:
                    XML.SubElement(params, 'encoding'
                                   ).text = project_def['file-encoding']
                if 'use-matrix-child-files' in project_def:
                    # TODO: These parameters only affect execution in
                    # publishers of matrix projects; we should warn if they are
                    # used in other contexts.
                    XML.SubElement(params, "useMatrixChild").text = (
                        str(project_def['use-matrix-child-files']).lower())
                    XML.SubElement(params, "combinationFilter").text = (
                        project_def.get('matrix-child-combination-filter', ''))
                    XML.SubElement(params, "onlyExactRuns").text = (
                        str(project_def.get('only-exact-matrix-child-runs',
                                            False)).lower())
            elif param_type == 'current-parameters' and param_value:
                XML.SubElement(tconfigs, pt_prefix + 'CurrentBuildParameters')
            elif param_type == 'node-parameters' and param_value:
                XML.SubElement(tconfigs, pt_prefix + 'NodeParameters')
            elif param_type == 'svn-revision' and param_value:
                param = XML.SubElement(tconfigs, pt_prefix +
                                       'SubversionRevisionBuildParameters')
                XML.SubElement(param, 'includeUpstreamParameters').text = str(
                    project_def.get('include-upstream', False)).lower()
            elif param_type == 'restrict-matrix-project' and param_value:
                subset = XML.SubElement(tconfigs, pt_prefix +
                                        'matrix.MatrixSubsetBuildParameters')
                XML.SubElement(subset, 'filter').text = \
                    project_def['restrict-matrix-project']
            elif (param_type == 'node-label-name' or
                    param_type == 'node-label'):
                tag_name = ('org.jvnet.jenkins.plugins.nodelabelparameter.'
                            'parameterizedtrigger.NodeLabelBuildParameter')
                if tconfigs.find(tag_name) is not None:
                    # already processed and can only have one
                    continue
                params = XML.SubElement(tconfigs, tag_name)
                name = XML.SubElement(params, 'name')
                if 'node-label-name' in project_def:
                    name.text = project_def['node-label-name']
                label = XML.SubElement(params, 'nodeLabel')
                if 'node-label' in project_def:
                    label.text = project_def['node-label']
            elif param_type == 'boolean-parameters' and param_value:
                params = XML.SubElement(tconfigs,
                                        pt_prefix + 'BooleanParameters')
                config_tag = XML.SubElement(params, 'configs')
                param_tag_text = pt_prefix + 'BooleanParameterConfig'
                params_list = param_value
                for name, value in params_list.items():
                    param_tag = XML.SubElement(config_tag, param_tag_text)
                    XML.SubElement(param_tag, 'name').text = name
                    XML.SubElement(param_tag, 'value').text = str(
                        value or False).lower()

        if not list(tconfigs):
            # not child parameter tags added
            tconfigs.set('class', 'java.util.Collections$EmptyList')

        projects = XML.SubElement(tconfig, 'projects')

        if isinstance(project_def['project'], list):
            projects.text = ",".join(project_def['project'])
        else:
            projects.text = project_def['project']

        condition = XML.SubElement(tconfig, 'condition')
        condition.text = project_def.get('condition', 'ALWAYS')
        trigger_with_no_params = XML.SubElement(tconfig,
                                                'triggerWithNoParameters')
        trigger_with_no_params.text = str(
            project_def.get('trigger-with-no-params', False)).lower()


def trigger(registry, xml_parent, data):
    """yaml: trigger
    Trigger non-parametrised builds of other jobs.

    :arg str project: name of the job to trigger
    :arg str threshold: when to trigger the other job (default 'SUCCESS'),
      alternatives: SUCCESS, UNSTABLE, FAILURE

    Example:

    .. literalinclude:: /../../tests/publishers/fixtures/trigger_success.yaml
       :language: yaml
    """
    tconfig = XML.SubElement(xml_parent, 'hudson.tasks.BuildTrigger')
    childProjects = XML.SubElement(tconfig, 'childProjects')
    childProjects.text = data['project']
    tthreshold = XML.SubElement(tconfig, 'threshold')

    threshold = data.get('threshold', 'SUCCESS')
    supported_thresholds = ['SUCCESS', 'UNSTABLE', 'FAILURE']
    if threshold not in supported_thresholds:
        raise JenkinsJobsException("threshold must be one of %s" %
                                   ", ".join(supported_thresholds))
    tname = XML.SubElement(tthreshold, 'name')
    tname.text = hudson_model.THRESHOLDS[threshold]['name']
    tordinal = XML.SubElement(tthreshold, 'ordinal')
    tordinal.text = hudson_model.THRESHOLDS[threshold]['ordinal']
    tcolor = XML.SubElement(tthreshold, 'color')
    tcolor.text = hudson_model.THRESHOLDS[threshold]['color']


def clone_workspace(registry, xml_parent, data):
    """yaml: clone-workspace
    Archive the workspace from builds of one project and reuse them as the SCM
    source for another project.
    Requires the Jenkins :jenkins-wiki:`Clone Workspace SCM Plugin
    <Clone+Workspace+SCM+Plugin>`.

    :arg str workspace-glob: Files to include in cloned workspace (default '')
    :arg str workspace-exclude-glob: Files to exclude from cloned workspace
    :arg str criteria: Criteria for build to be archived.  Can be 'any',
        'not failed', or 'successful'. (default 'any')
    :arg str archive-method: Choose the method to use for archiving the
        workspace.  Can be 'tar' or 'zip'.  (default 'tar')
    :arg bool override-default-excludes: Override default ant excludes.
        (default false)

    Minimal example:

    .. literalinclude::
        /../../tests/publishers/fixtures/clone-workspace001.yaml
       :language: yaml

    Full example:

    .. literalinclude::
        /../../tests/publishers/fixtures/clone-workspace002.yaml
       :language: yaml
    """

    cloneworkspace = XML.SubElement(
        xml_parent,
        'hudson.plugins.cloneworkspace.CloneWorkspacePublisher')
    cloneworkspace.set('plugin', 'clone-workspace-scm')

    mappings = [
        ('workspace-glob', 'workspaceGlob', ''),
        ('override-default-excludes', 'overrideDefaultExcludes', False),
    ]
    helpers.convert_mapping_to_xml(
        cloneworkspace, data, mappings, fail_required=True)

    if 'workspace-exclude-glob' in data:
        XML.SubElement(
            cloneworkspace,
            'workspaceExcludeGlob').text = data['workspace-exclude-glob']

    criteria_list = ['Any', 'Not Failed', 'Successful']

    criteria = data.get('criteria', 'Any').title()

    if 'criteria' in data and criteria not in criteria_list:
        raise JenkinsJobsException(
            'clone-workspace criteria must be one of: '
            + ', '.join(criteria_list))
    else:
        XML.SubElement(cloneworkspace, 'criteria').text = criteria

    archive_list = ['TAR', 'ZIP']

    archive_method = data.get('archive-method', 'TAR').upper()

    if 'archive-method' in data and archive_method not in archive_list:
        raise JenkinsJobsException(
            'clone-workspace archive-method must be one of: '
            + ', '.join(archive_list))
    else:
        XML.SubElement(cloneworkspace, 'archiveMethod').text = archive_method


def cloverphp(registry, xml_parent, data):
    """yaml: cloverphp
    Capture code coverage reports from PHPUnit
    Requires the Jenkins :jenkins-wiki:`Clover PHP Plugin <Clover+PHP+Plugin>`.

    Your job definition should pass to PHPUnit the --coverage-clover option
    pointing to a file in the workspace (ex: clover-coverage.xml). The filename
    has to be filled in the `xml-location` field.

    :arg str xml-location: Path to the coverage XML file generated by PHPUnit
        using --coverage-clover. Relative to workspace. (required)
    :arg dict html: When existent, whether the plugin should generate a HTML
        report.  Note that PHPUnit already provide a HTML report via its
        --cover-html option which can be set in your builder (optional):

        * **dir** (str): Directory where HTML report will be generated relative
                         to workspace. (required in `html` dict).
        * **archive** (bool): Whether to archive HTML reports (default true).

    :arg list metric-targets: List of metric targets to reach, must be one of
        **healthy**, **unhealthy** and **failing**. Each metric target can
        takes two parameters:

        * **method**  Target for method coverage
        * **statement** Target for statements coverage

        Whenever a metric target is not filled in, the Jenkins plugin can fill
        in defaults for you (as of v0.3.3 of the plugin the healthy target will
        have method: 70 and statement: 80 if both are left empty). Jenkins Job
        Builder will mimic that feature to ensure clean configuration diff.

    Minimal example:

    .. literalinclude:: /../../tests/publishers/fixtures/cloverphp001.yaml
       :language: yaml

    Full example:

    .. literalinclude:: /../../tests/publishers/fixtures/cloverphp002.yaml
       :language: yaml
    """
    cloverphp = XML.SubElement(
        xml_parent,
        'org.jenkinsci.plugins.cloverphp.CloverPHPPublisher')
    cloverphp.set('plugin', 'cloverphp')

    # The plugin requires clover XML file to parse
    if 'xml-location' not in data:
        raise JenkinsJobsException('xml-location must be set')

    # Whether HTML publishing has been checked
    html_publish = False
    # By default, disableArchiving = false. Note that we use
    # reversed logic.
    html_archive = True

    if 'html' in data:
        html_publish = True
        html_dir = data['html'].get('dir', None)
        html_archive = data['html'].get('archive', html_archive)
        if html_dir is None:
            # No point in going further, the plugin would not work
            raise JenkinsJobsException('htmldir is required in a html block')

    XML.SubElement(cloverphp, 'publishHtmlReport').text = str(
        html_publish).lower()
    if html_publish:
        XML.SubElement(cloverphp, 'reportDir').text = html_dir
    XML.SubElement(cloverphp, 'xmlLocation').text = data.get('xml-location')
    XML.SubElement(cloverphp, 'disableArchiving').text = str(
        not html_archive).lower()

    # Handle targets

    # Plugin v0.3.3 will fill defaults for us whenever healthy targets are both
    # blanks.
    default_metrics = {
        'healthy': {'method': 70, 'statement': 80}
    }
    allowed_metrics = ['healthy', 'unhealthy', 'failing']

    metrics = data.get('metric-targets', [])
    # list of dicts to dict
    metrics = dict(kv for m in metrics for kv in m.items())

    # Populate defaults whenever nothing has been filled by user.
    for default in default_metrics.keys():
        if metrics.get(default, None) is None:
            metrics[default] = default_metrics[default]

    # The plugin would at least define empty targets so make sure
    # we output them all in the XML regardless of what the user
    # has or has not entered.
    for target in allowed_metrics:
        cur_target = XML.SubElement(cloverphp, target + 'Target')

        for t_type in ['method', 'statement']:
            val = metrics.get(target, {}).get(t_type)
            if val is None or type(val) != int:
                continue
            if val < 0 or val > 100:
                raise JenkinsJobsException(
                    "Publisher cloverphp metric target %s:%s = %s "
                    "is not in valid range 0-100." % (target, t_type, val))
            XML.SubElement(cur_target, t_type + 'Coverage').text = str(val)


def coverage(registry, xml_parent, data):
    """yaml: coverage
    WARNING: The coverage function is deprecated. Instead, use the
    cobertura function to generate a cobertura coverage report.
    Requires the Jenkins :jenkins-wiki:`Cobertura Coverage Plugin
    <Cobertura+Plugin>`.

    Example:

    .. literalinclude:: /../../tests/publishers/fixtures/coverage001.yaml
       :language: yaml
    """
    logger = logging.getLogger(__name__)
    logger.warning("Coverage function is deprecated. Switch to cobertura.")

    cobertura = XML.SubElement(xml_parent,
                               'hudson.plugins.cobertura.CoberturaPublisher')
    XML.SubElement(cobertura, 'coberturaReportFile').text = '**/coverage.xml'
    XML.SubElement(cobertura, 'onlyStable').text = 'false'
    healthy = XML.SubElement(cobertura, 'healthyTarget')
    targets = XML.SubElement(healthy, 'targets', {
        'class': 'enum-map',
        'enum-type': 'hudson.plugins.cobertura.targets.CoverageMetric'})
    entry = XML.SubElement(targets, 'entry')
    XML.SubElement(entry, 'hudson.plugins.cobertura.targets.CoverageMetric'
                   ).text = 'CONDITIONAL'
    XML.SubElement(entry, 'int').text = '70'
    entry = XML.SubElement(targets, 'entry')
    XML.SubElement(entry, 'hudson.plugins.cobertura.targets.CoverageMetric'
                   ).text = 'LINE'
    XML.SubElement(entry, 'int').text = '80'
    entry = XML.SubElement(targets, 'entry')
    XML.SubElement(entry, 'hudson.plugins.cobertura.targets.CoverageMetric'
                   ).text = 'METHOD'
    XML.SubElement(entry, 'int').text = '80'
    unhealthy = XML.SubElement(cobertura, 'unhealthyTarget')
    targets = XML.SubElement(unhealthy, 'targets', {
        'class': 'enum-map',
        'enum-type': 'hudson.plugins.cobertura.targets.CoverageMetric'})
    entry = XML.SubElement(targets, 'entry')
    XML.SubElement(entry, 'hudson.plugins.cobertura.targets.CoverageMetric'
                   ).text = 'CONDITIONAL'
    XML.SubElement(entry, 'int').text = '0'
    entry = XML.SubElement(targets, 'entry')
    XML.SubElement(entry, 'hudson.plugins.cobertura.targets.CoverageMetric'
                   ).text = 'LINE'
    XML.SubElement(entry, 'int').text = '0'
    entry = XML.SubElement(targets, 'entry')
    XML.SubElement(entry, 'hudson.plugins.cobertura.targets.CoverageMetric'
                   ).text = 'METHOD'
    XML.SubElement(entry, 'int').text = '0'
    failing = XML.SubElement(cobertura, 'failingTarget')
    targets = XML.SubElement(failing, 'targets', {
        'class': 'enum-map',
        'enum-type': 'hudson.plugins.cobertura.targets.CoverageMetric'})
    entry = XML.SubElement(targets, 'entry')
    XML.SubElement(entry, 'hudson.plugins.cobertura.targets.CoverageMetric'
                   ).text = 'CONDITIONAL'
    XML.SubElement(entry, 'int').text = '0'
    entry = XML.SubElement(targets, 'entry')
    XML.SubElement(entry, 'hudson.plugins.cobertura.targets.CoverageMetric'
                   ).text = 'LINE'
    XML.SubElement(entry, 'int').text = '0'
    entry = XML.SubElement(targets, 'entry')
    XML.SubElement(entry, 'hudson.plugins.cobertura.targets.CoverageMetric'
                   ).text = 'METHOD'
    XML.SubElement(entry, 'int').text = '0'
    XML.SubElement(cobertura, 'sourceEncoding').text = 'ASCII'


def cobertura(registry, xml_parent, data):
    """yaml: cobertura
    Generate a cobertura coverage report.
    Requires the Jenkins :jenkins-wiki:`Cobertura Coverage Plugin
    <Cobertura+Plugin>`.

    :arg str report-file: This is a file name pattern that can be used
        to locate the cobertura xml report files (optional)
    :arg bool only-stable: Include only stable builds (default false)
    :arg bool fail-no-reports: fail builds if no coverage reports are found
        (default false)
    :arg bool fail-unhealthy: Unhealthy projects will be failed (default false)
    :arg bool fail-unstable: Unstable projects will be failed (default false)
    :arg bool health-auto-update: Auto update threshold for health on
        successful build (default false)
    :arg bool stability-auto-update: Auto update threshold for stability on
        successful build (default false)
    :arg bool zoom-coverage-chart: Zoom the coverage chart and crop area below
        the minimum and above the maximum coverage of the past reports
        (default false)
    :arg str source-encoding: Override the source encoding (default ASCII)
    :arg dict targets:

           :targets: (packages, files, classes, method, line, conditional)

                * **healthy** (`int`): Healthy threshold (default 0)
                * **unhealthy** (`int`): Unhealthy threshold (default 0)
                * **failing** (`int`): Failing threshold (default 0)

    Example:

    .. literalinclude:: /../../tests/publishers/fixtures/cobertura001.yaml
       :language: yaml
    """
    cobertura = XML.SubElement(xml_parent,
                               'hudson.plugins.cobertura.CoberturaPublisher')
    mapping = [
        ('report-file', 'coberturaReportFile', '**/coverage.xml'),
        ('only-stable', 'onlyStable', False),
        ('fail-unhealthy', 'failUnhealthy', False),
        ('fail-unstable', 'failUnstable', False),
        ('health-auto-update', 'autoUpdateHealth', False),
        ('stability-auto-update', 'autoUpdateStability', False),
        ('zoom-coverage-chart', 'zoomCoverageChart', False),
        ('fail-no-reports', 'failNoReports', False),
    ]
    helpers.convert_mapping_to_xml(
        cobertura, data, mapping, fail_required=True)

    healthy = XML.SubElement(cobertura, 'healthyTarget')
    targets = XML.SubElement(healthy, 'targets', {
        'class': 'enum-map',
        'enum-type': 'hudson.plugins.cobertura.targets.CoverageMetric'})
    for item in data['targets']:
        item_name = next(iter(item.keys()))
        item_values = item.get(item_name, 0)
        entry = XML.SubElement(targets, 'entry')
        XML.SubElement(entry,
                       'hudson.plugins.cobertura.targets.'
                       'CoverageMetric').text = str(item_name).upper()
        XML.SubElement(entry, 'int').text = str(item_values.get('healthy', 0))
    unhealthy = XML.SubElement(cobertura, 'unhealthyTarget')
    targets = XML.SubElement(unhealthy, 'targets', {
        'class': 'enum-map',
        'enum-type': 'hudson.plugins.cobertura.targets.CoverageMetric'})
    for item in data['targets']:
        item_name = next(iter(item.keys()))
        item_values = item.get(item_name, 0)
        entry = XML.SubElement(targets, 'entry')
        XML.SubElement(entry, 'hudson.plugins.cobertura.targets.'
                              'CoverageMetric').text = str(item_name).upper()
        XML.SubElement(entry, 'int').text = str(item_values.get('unhealthy',
                                                                0))
    failing = XML.SubElement(cobertura, 'failingTarget')
    targets = XML.SubElement(failing, 'targets', {
        'class': 'enum-map',
        'enum-type': 'hudson.plugins.cobertura.targets.CoverageMetric'})
    for item in data['targets']:
        item_name = next(iter(item.keys()))
        item_values = item.get(item_name, 0)
        entry = XML.SubElement(targets, 'entry')
        XML.SubElement(entry, 'hudson.plugins.cobertura.targets.'
                              'CoverageMetric').text = str(item_name).upper()
        XML.SubElement(entry, 'int').text = str(item_values.get('failing', 0))
    XML.SubElement(cobertura, 'sourceEncoding').text = data.get(
        'source-encoding', 'ASCII')


def jacoco(registry, xml_parent, data):
    """yaml: jacoco
    Generate a JaCoCo coverage report.
    Requires the Jenkins :jenkins-wiki:`JaCoCo Plugin <JaCoCo+Plugin>`.

    :arg str exec-pattern: This is a file name pattern that can be used to
                          locate the jacoco report files (default
                          ``**/**.exec``)
    :arg str class-pattern: This is a file name pattern that can be used
                          to locate class files (default ``**/classes``)
    :arg str source-pattern: This is a file name pattern that can be used
                          to locate source files (default ``**/src/main/java``)
    :arg bool update-build-status: Update the build according to the results
                          (default false)
    :arg str inclusion-pattern: This is a file name pattern that can be used
                          to include certain class files (optional)
    :arg str exclusion-pattern: This is a file name pattern that can be used
                          to exclude certain class files (optional)
    :arg dict targets:

           :targets: (instruction, branch, complexity, line, method, class)

                * **healthy** (`int`): Healthy threshold (default 0)
                * **unhealthy** (`int`): Unhealthy threshold (default 0)

    Example:

    .. literalinclude:: /../../tests/publishers/fixtures/jacoco001.yaml
       :language: yaml
    """

    jacoco = XML.SubElement(xml_parent,
                            'hudson.plugins.jacoco.JacocoPublisher')
    XML.SubElement(jacoco, 'execPattern').text = data.get(
        'exec-pattern', '**/**.exec')
    XML.SubElement(jacoco, 'classPattern').text = data.get(
        'class-pattern', '**/classes')
    XML.SubElement(jacoco, 'sourcePattern').text = data.get(
        'source-pattern', '**/src/main/java')
    XML.SubElement(jacoco, 'changeBuildStatus').text = data.get(
        'update-build-status', False)
    XML.SubElement(jacoco, 'inclusionPattern').text = data.get(
        'inclusion-pattern', '')
    XML.SubElement(jacoco, 'exclusionPattern').text = data.get(
        'exclusion-pattern', '')

    itemsList = ['instruction',
                 'branch',
                 'complexity',
                 'line',
                 'method',
                 'class']

    for item in data['targets']:
        item_name = next(iter(item.keys()))
        if item_name not in itemsList:
            raise JenkinsJobsException("item entered is not valid must be "
                                       "one of: %s" % ",".join(itemsList))
        item_values = item.get(item_name, 0)

        XML.SubElement(jacoco,
                       'maximum' +
                       item_name.capitalize() +
                       'Coverage').text = str(item_values.get('healthy', 0))
        XML.SubElement(jacoco,
                       'minimum' +
                       item_name.capitalize() +
                       'Coverage').text = str(item_values.get('unhealthy', 0))


def ftp(registry, xml_parent, data):
    """yaml: ftp
    Upload files via FTP.
    Requires the Jenkins :jenkins-wiki:`Publish over FTP Plugin
    <Publish+Over+FTP+Plugin>`.

    :arg str site: name of the ftp site
    :arg str target: destination directory
    :arg bool target-is-date-format: whether target is a date format. If true,
      raw text should be quoted (default false)
    :arg bool clean-remote: should the remote directory be deleted before
      transferring files (default false)
    :arg str source: source path specifier
    :arg str excludes: excluded file pattern (optional)
    :arg str remove-prefix: prefix to remove from uploaded file paths
      (optional)
    :arg bool fail-on-error: fail the build if an error occurs (default false).
    :arg bool flatten: only create files on the server, don't create
      directories (default false).

    Example:

    .. literalinclude::  /../../tests/publishers/fixtures/ftp001.yaml
       :language: yaml

    """
    console_prefix = 'FTP: '
    plugin_tag = 'jenkins.plugins.publish__over__ftp.BapFtpPublisherPlugin'
    publisher_tag = 'jenkins.plugins.publish__over__ftp.BapFtpPublisher'
    transfer_tag = 'jenkins.plugins.publish__over__ftp.BapFtpTransfer'
    plugin_reference_tag = 'jenkins.plugins.publish_over_ftp.'    \
        'BapFtpPublisherPlugin'
    (_, transfer_node) = base_publish_over(xml_parent,
                                           data,
                                           console_prefix,
                                           plugin_tag,
                                           publisher_tag,
                                           transfer_tag,
                                           plugin_reference_tag)
    XML.SubElement(transfer_node, 'asciiMode').text = 'false'


def ftp_publisher(registry, xml_parent, data):
    """yaml: ftp-publisher
    This plugin can be used to upload project artifacts and whole directories
    to an ftp server.
    Requires the Jenkins :jenkins-wiki:`FTP-Publisher Plugin
    <FTP-Publisher+Plugin>`.

    :arg list uploads: List of files to upload

        :uploads:
            * **file-path** ('str') -- Destination folder. It will be created
                if doesn't exists. Created relative to ftp root directory.
                (default '')
            * **source-file** ('str') -- Source files which will be uploaded
                (default '')
    :arg str site-name: Name of FTP server to upload to (required)
    :arg bool use-timestamps: Use timestamps in the FTP directory path (default
        false)
    :arg bool flatten-files: Flatten files on the FTP host (default false)
    :arg bool skip-publishing: Skip publishing (default false)

    Minimal Example:

    .. literalinclude::
       /../../tests/publishers/fixtures/ftp-publisher-minimal.yaml
       :language: yaml

    Full Example:

    .. literalinclude::
       /../../tests/publishers/fixtures/ftp-publisher-full.yaml
       :language: yaml
    """
    ftp = XML.SubElement(xml_parent, 'com.zanox.hudson.plugins.FTPPublisher')
    ftp.set('plugin', 'ftppublisher')

    entries = XML.SubElement(ftp, 'entries')
    if 'uploads' in data:
        upload_mapping = [
            ('file-path', 'filePath', ''),
            ('source-file', 'sourceFile', ''),
        ]
        for upload in data['uploads']:
            entry = XML.SubElement(entries, 'com.zanox.hudson.plugins.Entry')
            helpers.convert_mapping_to_xml(
                entry, upload, upload_mapping, fail_required=True)

    mapping = [
        ('site-name', 'siteName', None),
        ('use-timestamps', 'useTimestamps', False),
        ('flatten-files', 'flatten', False),
        ('skip-publishing', 'skip', False),
    ]
    helpers.convert_mapping_to_xml(ftp, data, mapping, fail_required=True)


def junit(registry, xml_parent, data):
    """yaml: junit
    Publish JUnit test results.

    :arg str results: results filename (required)
    :arg bool keep-long-stdio: Retain long standard output/error in test
        results (default true).
    :arg float health-scale-factor: Amplification factor to apply to test
        failures when computing the test result contribution to the build
        health score. (default 1.0)
    :arg bool allow-empty-results: Do not fail the build on empty test results
        (default false)
    :arg bool test-stability: Add historical information about test
        results stability (default false).
        Requires the Jenkins :jenkins-wiki:`Test stability Plugin
        <Test+stability+plugin>`.
    :arg bool claim-build: Allow claiming of failed tests (default false)
        Requires the Jenkins :jenkins-wiki:`Claim Plugin <Claim+plugin>`.
    :arg bool measurement-plots: Create measurement plots (default false)
        Requires the Jenkins :jenkins-wiki:`Measurement Plots Plugin
        <Measurement+Plots+Plugin>`.
    :arg bool flaky-test-reports: Publish flaky test reports (default false).
        Requires the Jenkins :jenkins-wiki:`Flaky Test Handler Plugin
        <Flaky+Test+Handler+Plugin>`.

    Minimal example using defaults:

    .. literalinclude::  /../../tests/publishers/fixtures/junit001.yaml
       :language: yaml

    Full example:

    .. literalinclude::  /../../tests/publishers/fixtures/junit002.yaml
       :language: yaml
    """
    junitresult = XML.SubElement(xml_parent,
                                 'hudson.tasks.junit.JUnitResultArchiver')
    junitresult.set('plugin', 'junit')
    mapping = [
        ('results', 'testResults', None),
        ('keep-long-stdio', 'keepLongStdio', True),
        ('health-scale-factor', 'healthScaleFactor', '1.0'),
        ('allow-empty-results', 'allowEmptyResults', False),
    ]
    helpers.convert_mapping_to_xml(
        junitresult, data, mapping, fail_required=True)

    datapublisher = XML.SubElement(junitresult, 'testDataPublishers')
    if str(data.get('test-stability', False)).lower() == 'true':
        XML.SubElement(datapublisher,
                       'de.esailors.jenkins.teststability'
                       '.StabilityTestDataPublisher')
    if str(data.get('claim-build', False)).lower() == 'true':
        XML.SubElement(datapublisher,
                       'hudson.plugins.claim.ClaimTestDataPublisher')
    if str(data.get('measurement-plots', False)).lower() == 'true':
        XML.SubElement(datapublisher,
                       'hudson.plugins.measurement__plots.TestDataPublisher')
    if str(data.get('flaky-test-reports', False)).lower() == 'true':
        XML.SubElement(datapublisher,
                       'com.google.jenkins.flakyTestHandler.plugin'
                       '.JUnitFlakyTestDataPublisher')


def cucumber_reports(registry, xml_parent, data):
    """yaml: cucumber-reports
    This plugin creates pretty cucumber-jvm html reports on jenkins.

    Requires the Jenkins :jenkins-wiki:`cucumber reports
    <Cucumber+Reports+Plugin>`.

    :arg str json-reports-path: The path relative to the workspace of
        the json reports generated by cucumber-jvm e.g. target - leave
        empty to scan the whole workspace (default '')
    :arg str file-include-pattern: Include pattern (default '')
    :arg str file-exclude-pattern: Exclude pattern (default '')
    :arg str plugin-url-path: The path to the jenkins user content url
        e.g. :samp:`http://host:port[/jenkins/]plugin` - leave empty if jenkins
        url root is host:port (default '')
    :arg bool skipped-fails: Skipped steps to cause the build to fail
        (default false)
    :arg bool pending-fails: Pending steps to cause the build to fail
        (default false)
    :arg bool undefined-fails: Undefined steps to cause the build to fail
        (default false)
    :arg bool missing-fails: Missing steps to cause the build to fail
        (default false)
    :arg bool no-flash-charts: Use javascript charts instead of flash charts
        (default false)
    :arg bool ignore-failed-tests: Entire build to fail when these tests fail
        (default false)
    :arg bool parallel-testing: Run same test in parallel for multiple devices
        (default false)

    Full example:

    .. literalinclude::
       /../../tests/publishers/fixtures/cucumber-reports-complete.yaml
       :language: yaml

    Minimal Example:

    .. literalinclude::
       /../../tests/publishers/fixtures/cucumber-reports-minimal.yaml
       :language: yaml
    """
    cucumber_reports = XML.SubElement(xml_parent,
                                      'net.masterthought.jenkins.'
                                      'CucumberReportPublisher')
    cucumber_reports.set('plugin', 'cucumber-reports')

    mappings = [
        ('json-reports-path', 'jsonReportDirectory', ''),
        ('plugin-url-path', 'pluginUrlPath', ''),
        ('file-include-pattern', 'fileIncludePattern', ''),
        ('file-exclude-pattern', 'fileExcludePattern', ''),
        ('skipped-fails', 'skippedFails', False),
        ('pending-fails', 'pendingFails', False),
        ('undefined-fails', 'undefinedFails', False),
        ('missing-fails', 'missingFails', False),
        ('no-flash-charts', 'noFlashCharts', False),
        ('ignore-failed-tests', 'ignoreFailedTests', False),
        ('parallel-testing', 'parallelTesting', False)
    ]
    helpers.convert_mapping_to_xml(
        cucumber_reports, data, mappings, fail_required=True)


def cucumber_testresult(registry, xml_parent, data):
    """yaml: cucumber-testresult
    Publish cucumber test results.
    Requires the Jenkins :jenkins-wiki:`cucumber testresult
    <Cucumber+Test+Result+Plugin>`.

    :arg str results: Results filename (required)
    :arg bool ignore-bad-steps: Ignore not existed step results (default false)

    Minimal example:

    .. literalinclude::
       /../../tests/publishers/fixtures/cucumber-testresult-minimal.yaml
       :language: yaml

    Full Example:

    .. literalinclude::
       /../../tests/publishers/fixtures/cucumber-testresult-complete.yaml
       :language: yaml
    """
    cucumber_result = XML.SubElement(xml_parent,
                                     'org.jenkinsci.plugins.cucumber.'
                                     'jsontestsupport.'
                                     'CucumberTestResultArchiver')
    cucumber_result.set('plugin', 'cucumber-testresult-plugin')

    mappings = [
        ('results', 'testResults', None),
        ('ignore-bad-steps', 'ignoreBadSteps', False)
    ]
    helpers.convert_mapping_to_xml(
        cucumber_result, data, mappings, fail_required=True)


def xunit(registry, xml_parent, data):
    """yaml: xunit
    Publish tests results. Requires the Jenkins :jenkins-wiki:`xUnit Plugin
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

    Example:

    .. literalinclude::  /../../tests/publishers/fixtures/xunit001.yaml
       :language: yaml

    """
    logger = logging.getLogger(__name__)
    xunit = XML.SubElement(xml_parent, 'xunit')
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
    for supported_type in supported_types:
        framework_name = next(iter(supported_type.keys()))
        xmlframework = XML.SubElement(xmltypes,
                                      types_to_plugin_types[framework_name])

        mappings = [
            ('pattern', 'pattern', ''),
            ('requireupdate', 'failIfNotNew', True),
            ('deleteoutput', 'deleteOutputFiles', True),
            ('skip-if-no-test-files', 'skipNoTestFiles', False),
            ('stoponerror', 'stopProcessingIfError', True),
        ]
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


def _violations_add_entry(xml_parent, name, data):
    vmin = data.get('min', 10)
    vmax = data.get('max', 999)
    vunstable = data.get('unstable', 999)
    pattern = data.get('pattern', None)

    entry = XML.SubElement(xml_parent, 'entry')
    XML.SubElement(entry, 'string').text = name
    tconfig = XML.SubElement(entry, 'hudson.plugins.violations.TypeConfig')
    XML.SubElement(tconfig, 'type').text = name
    XML.SubElement(tconfig, 'min').text = str(vmin)
    XML.SubElement(tconfig, 'max').text = str(vmax)
    XML.SubElement(tconfig, 'unstable').text = str(vunstable)
    XML.SubElement(tconfig, 'usePattern').text = 'false'
    if pattern:
        XML.SubElement(tconfig, 'pattern').text = pattern
    else:
        XML.SubElement(tconfig, 'pattern')


def violations(registry, xml_parent, data):
    """yaml: violations
    Publish code style violations.
    Requires the Jenkins :jenkins-wiki:`Violations Plugin <Violations>`.

    The violations component accepts any number of dictionaries keyed
    by the name of the violations system.  The dictionary has the
    following values:

    :arg int min: sunny threshold
    :arg int max: stormy threshold
    :arg int unstable: unstable threshold
    :arg str pattern: report filename pattern

    Any system without a dictionary provided will use default values.

    Valid systems are:

      checkstyle, codenarc, cpd, cpplint, csslint, findbugs, fxcop,
      gendarme, jcreport, jslint, pep8, perlcritic, pmd, pylint,
      simian, stylecop

    Example:

    .. literalinclude::  /../../tests/publishers/fixtures/violations001.yaml
       :language: yaml
    """
    violations = XML.SubElement(xml_parent,
                                'hudson.plugins.violations.'
                                'ViolationsPublisher')
    config = XML.SubElement(violations, 'config')
    suppressions = XML.SubElement(config, 'suppressions',
                                  {'class': 'tree-set'})
    XML.SubElement(suppressions, 'no-comparator')
    configs = XML.SubElement(config, 'typeConfigs')
    XML.SubElement(configs, 'no-comparator')

    for name in ['checkstyle',
                 'codenarc',
                 'cpd',
                 'cpplint',
                 'csslint',
                 'findbugs',
                 'fxcop',
                 'gendarme',
                 'jcreport',
                 'jslint',
                 'pep8',
                 'perlcritic',
                 'pmd',
                 'pylint',
                 'simian',
                 'stylecop']:
        _violations_add_entry(configs, name, data.get(name, {}))

    XML.SubElement(config, 'limit').text = '100'
    XML.SubElement(config, 'sourcePathPattern')
    XML.SubElement(config, 'fauxProjectPath')
    XML.SubElement(config, 'encoding').text = 'default'


def findbugs(registry, xml_parent, data):
    """yaml: findbugs
    FindBugs reporting for builds

    Requires the Jenkins :jenkins-wiki:`FindBugs Plugin
    <FindBugs+Plugin>`.

    :arg str pattern: specifies the generated raw FindBugs XML report files,
        such as \*\*/findbugs.xml or \*\*/findbugsXml.xml. (default '')
    :arg bool rank-priority: Use rank as priority (default false)
    :arg str include-files: Comma separated list of files to include.
        (default '')
    :arg str exclude-files: Comma separated list of files to exclude.
        (default '')
    :arg bool can-run-on-failed: Weather or not to run plug-in on failed builds
        (default false)
    :arg bool should-detect-modules: Determines if Ant or Maven modules should
        be detected for all files that contain warnings. (default false)
    :arg int healthy: Sunny threshold (default '')
    :arg int unhealthy: Stormy threshold (default '')
    :arg str health-threshold: Threshold priority for health status
        ('low', 'normal' or 'high', defaulted to 'low')
    :arg bool dont-compute-new: If set to false, computes new warnings based on
        the reference build (default true)
    :arg bool use-delta-values: Use delta for new warnings. (default false)
    :arg bool use-previous-build-as-reference:  If set then the number of new
        warnings will always be calculated based on the previous build.
        Otherwise the reference build. (default false)
    :arg bool use-stable-build-as-reference: The number of new warnings will be
        calculated based on the last stable build, allowing reverts of unstable
        builds where the number of warnings was decreased. (default false)
    :arg dict thresholds:
        :thresholds:
            * **unstable** (`dict`)
                :unstable: * **total-all** (`int`)
                           * **total-high** (`int`)
                           * **total-normal** (`int`)
                           * **total-low** (`int`)
                           * **new-all** (`int`)
                           * **new-high** (`int`)
                           * **new-normal** (`int`)
                           * **new-low** (`int`)

            * **failed** (`dict`)
                :failed: * **total-all** (`int`)
                         * **total-high** (`int`)
                         * **total-normal** (`int`)
                         * **total-low** (`int`)
                         * **new-all** (`int`)
                         * **new-high** (`int`)
                         * **new-normal** (`int`)
                         * **new-low** (`int`)

    Minimal Example:

    .. literalinclude:: /../../tests/publishers/fixtures/findbugs-minimal.yaml

    Full Example:

    .. literalinclude:: /../../tests/publishers/fixtures/findbugs-full.yaml
    """
    findbugs = XML.SubElement(xml_parent,
                              'hudson.plugins.findbugs.FindBugsPublisher')
    findbugs.set('plugin', 'findbugs')

    helpers.findbugs_settings(findbugs, data)
    helpers.build_trends_publisher('[FINDBUGS] ', findbugs, data)


def checkstyle(registry, xml_parent, data):
    """yaml: checkstyle
    Publish trend reports with Checkstyle.
    Requires the Jenkins :jenkins-wiki:`Checkstyle Plugin <Checkstyle+Plugin>`.

    The checkstyle component accepts a dictionary with the
    following values:

    :arg str pattern: Report filename pattern (default '')
    :arg bool can-run-on-failed: Also runs for failed builds, instead of just
        stable or unstable builds (default false)
    :arg bool should-detect-modules: Determines if Ant or Maven modules should
        be detected for all files that contain warnings (default false)
    :arg int healthy: Sunny threshold (default '')
    :arg int unhealthy: Stormy threshold (default '')
    :arg str health-threshold: Threshold priority for health status
        ('low', 'normal' or 'high') (default 'low')
    :arg dict thresholds: Mark build as failed or unstable if the number of
        errors exceeds a threshold. (optional)

        :thresholds:
            * **unstable** (`dict`)
                :unstable: * **total-all** (`int`)
                           * **total-high** (`int`)
                           * **total-normal** (`int`)
                           * **total-low** (`int`)
                           * **new-all** (`int`)
                           * **new-high** (`int`)
                           * **new-normal** (`int`)
                           * **new-low** (`int`)

            * **failed** (`dict`)
                :failed: * **total-all** (`int`)
                         * **total-high** (`int`)
                         * **total-normal** (`int`)
                         * **total-low** (`int`)
                         * **new-all** (`int`)
                         * **new-high** (`int`)
                         * **new-normal** (`int`)
                         * **new-low** (`int`)
    :arg str default-encoding: Encoding for parsing or showing files
        (default '')
    :arg bool do-not-resolve-relative-paths: (default false)
    :arg bool dont-compute-new: If set to false, computes new warnings based on
        the reference build (default true)
    :arg bool use-previous-build-as-reference: determines whether to always
        use the previous build as the reference build (default false)
    :arg bool use-stable-build-as-reference: The number of new warnings will be
        calculated based on the last stable build, allowing reverts of unstable
        builds where the number of warnings was decreased. (default false)
    :arg bool use-delta-values: If set then the number of new warnings is
        calculated by subtracting the total number of warnings of the current
        build from the reference build. (default false)

    Example:

    .. literalinclude::  /../../tests/publishers/fixtures/checkstyle004.yaml
       :language: yaml

    Full example:

    .. literalinclude::  /../../tests/publishers/fixtures/checkstyle006.yaml
       :language: yaml
    """
    def convert_settings(lookup, data):
        """Helper to convert settings from one key to another
        """

        for old_key in list(data.keys()):
            if old_key in lookup:
                data.setdefault(lookup[old_key], data[old_key])
                del data[old_key]

    checkstyle = XML.SubElement(xml_parent,
                                'hudson.plugins.checkstyle.'
                                'CheckStylePublisher')
    checkstyle.set('plugin', 'checkstyle')

    # Convert old style yaml to new style
    convert_settings({
        'unHealthy': 'unhealthy',
        'healthThreshold': 'health-threshold',
        'defaultEncoding': 'default-encoding',
        'canRunOnFailed': 'can-run-on-failed',
        'shouldDetectModules': 'should-detect-modules'
    }, data)

    threshold_data = data.get('thresholds', {})
    for threshold in ['unstable', 'failed']:
        convert_settings({
            'totalAll': 'total-all',
            'totalHigh': 'total-high',
            'totalNormal': 'total-normal',
            'totalLow': 'total-low'
        }, threshold_data.get(threshold, {}))

    helpers.build_trends_publisher('[CHECKSTYLE] ', checkstyle, data)


def scp(registry, xml_parent, data):
    """yaml: scp
    Upload files via SCP
    Requires the Jenkins :jenkins-wiki:`SCP Plugin <SCP+plugin>`.

    When writing a publisher macro, it is important to keep in mind that
    Jenkins uses Ant's `SCP Task
    <https://ant.apache.org/manual/Tasks/scp.html>`_ via the Jenkins
    :jenkins-wiki:`SCP Plugin <SCP+plugin>` which relies on `FileSet
    <https://ant.apache.org/manual/Types/fileset.html>`_
    and `DirSet <https://ant.apache.org/manual/Types/dirset.html>`_ patterns.
    The relevant piece of documentation is excerpted below:

        Source points to files which will be uploaded. You can use ant
        includes syntax, eg. ``folder/dist/*.jar``. Path is constructed from
        workspace root. Note that you cannot point files outside the workspace
        directory.  For example providing: ``../myfile.txt`` won't work...
        Destination points to destination folder on remote site. It will be
        created if doesn't exists and relative to root repository path. You
        can define multiple blocks of source/destination pairs.

    This means that absolute paths, e.g., ``/var/log/**`` will not work and
    will fail to compile. All paths need to be relative to the directory that
    the publisher runs and the paths have to be contained inside of that
    directory. The relative working directory is usually::

        /home/jenkins/workspace/${JOB_NAME}

    :arg str site: name of the scp site (required)
    :arg str target: destination directory (required)
    :arg str source: source path specifier (default '')
    :arg bool keep-hierarchy: keep the file hierarchy when uploading
      (default false)
    :arg bool copy-after-failure: copy files even if the job fails
      (default false)
    :arg bool copy-console: copy the console log (default false); if
      specified, omit 'source'

    Example:

    .. literalinclude:: /../../tests/publishers/fixtures/scp001.yaml
       :language: yaml
    """
    scp = XML.SubElement(xml_parent,
                         'be.certipost.hudson.plugin.SCPRepositoryPublisher')
    scp.set('plugin', 'scp')

    mappings = [
        ('site', 'siteName', None),
    ]
    helpers.convert_mapping_to_xml(scp, data, mappings, fail_required=True)

    entries = XML.SubElement(scp, 'entries')
    for entry in data['files']:
        entry_e = XML.SubElement(entries, 'be.certipost.hudson.plugin.Entry')
        mappings = [
            ('target', 'filePath', None),
            ('source', 'sourceFile', ''),
            ('keep-hierarchy', 'keepHierarchy', False),
            ('copy-console', 'copyConsoleLog', False),
            ('copy-after-failure', 'copyAfterFailure', False),
        ]
        helpers.convert_mapping_to_xml(
            entry_e, entry, mappings, fail_required=True)


def ssh(registry, xml_parent, data):
    """yaml: ssh
    Upload files via SCP.
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
    :arg bool fail-on-error: fail the build if an error occurs (default false).
    :arg bool always-publish-from-master: transfer the files through the master
      before being sent to the remote server (defaults false)
    :arg bool flatten: only create files on the server, don't create
      directories (default false).

    Example:

    .. literalinclude::  /../../tests/publishers/fixtures/ssh001.yaml
       :language: yaml
    """
    console_prefix = 'SSH: '
    tag_prefix = 'jenkins.plugins.publish'
    publisher_tag = '%s__over__ssh.BapSshPublisher' % tag_prefix
    transfer_tag = '%s__over__ssh.BapSshTransfer' % tag_prefix
    reference_tag = '%s_over_ssh.BapSshPublisherPlugin' % tag_prefix

    if xml_parent.tag == 'publishers':
        plugin_tag = '%s__over__ssh.BapSshPublisherPlugin' % tag_prefix
    else:
        plugin_tag = '%s__over__ssh.BapSshBuilderPlugin' % tag_prefix

    base_publish_over(xml_parent, data, console_prefix, plugin_tag,
                      publisher_tag, transfer_tag, reference_tag)


def pipeline(registry, xml_parent, data):
    """yaml: pipeline
    Specify a downstream project in a pipeline.
    Requires the Jenkins :jenkins-wiki:`Build Pipeline Plugin
    <Build+Pipeline+Plugin>`.

    :arg str project: the name of the downstream project
    :arg str predefined-parameters: parameters to pass to the other
      job (optional)
    :arg bool current-parameters: Whether to include the parameters passed
      to the current build to the triggered job (optional)
    :arg str property-file: Use properties from file (optional)
    :arg bool fail-on-missing: Blocks the triggering of the downstream jobs
        if any of the property files are not found in the workspace.
        Only valid when 'property-file' is specified.
        (default false)
    :arg str file-encoding: Encoding of contents of the files. If not
        specified, default encoding of the platform is used. Only valid when
        'property-file' is specified. (optional)

    Example:

    .. literalinclude:: /../../tests/publishers/fixtures/pipeline002.yaml
       :language: yaml

    .. literalinclude:: /../../tests/publishers/fixtures/pipeline003.yaml
       :language: yaml


    You can build pipeline jobs that are re-usable in different pipelines by
    using a :ref:`job-template` to define the pipeline jobs,
    and variable substitution to specify the name of
    the downstream job in the pipeline.
    Job-specific substitutions are useful here (see :ref:`project`).

    See 'samples/pipeline.yaml' for an example pipeline implementation.
    """
    if 'project' in data and data['project'] != '':
        pippub = XML.SubElement(xml_parent,
                                'au.com.centrumsystems.hudson.plugin.'
                                'buildpipeline.trigger.BuildPipelineTrigger')

        configs = XML.SubElement(pippub, 'configs')

        if 'predefined-parameters' in data:
            params = XML.SubElement(configs,
                                    'hudson.plugins.parameterizedtrigger.'
                                    'PredefinedBuildParameters')
            properties = XML.SubElement(params, 'properties')
            properties.text = data['predefined-parameters']

        if ('current-parameters' in data
                and data['current-parameters']):
            XML.SubElement(configs,
                           'hudson.plugins.parameterizedtrigger.'
                           'CurrentBuildParameters')

        if 'property-file' in data and data['property-file']:
            params = XML.SubElement(configs,
                                    'hudson.plugins.parameterizedtrigger.'
                                    'FileBuildParameters')
            properties = XML.SubElement(params, 'propertiesFile')
            properties.text = data['property-file']
            failOnMissing = XML.SubElement(params, 'failTriggerOnMissing')
            failOnMissing.text = str(
                data.get('fail-on-missing', False)).lower()
            if 'file-encoding' in data:
                XML.SubElement(params, 'encoding'
                               ).text = data['file-encoding']

        XML.SubElement(pippub, 'downstreamProjectNames').text = data['project']


def email(registry, xml_parent, data):
    """yaml: email
    Email notifications on build failure.
    Requires the Jenkins :jenkins-wiki:`Mailer Plugin
    <Mailer>`.


    :arg str recipients: Space separated list of recipient email addresses
        (required)
    :arg bool notify-every-unstable-build: Send an email for every
        unstable build (default true)
    :arg bool send-to-individuals: Send an email to the individual
        who broke the build (default false)

    Example:

    .. literalinclude::
       /../../tests/publishers/fixtures/email-minimal.yaml
       :language: yaml

    .. literalinclude::  /../../tests/publishers/fixtures/email-complete.yaml
       :language: yaml
    """

    # TODO: raise exception if this is applied to a maven job
    mailer = XML.SubElement(xml_parent,
                            'hudson.tasks.Mailer')
    mailer.set('plugin', 'mailer')
    mapping = [
        ('recipients', 'recipients', None)
    ]
    helpers.convert_mapping_to_xml(mailer, data, mapping, fail_required=True)

    # Note the logic reversal (included here to match the GUI
    if data.get('notify-every-unstable-build', True):
        XML.SubElement(mailer, 'dontNotifyEveryUnstableBuild').text = 'false'
    else:
        XML.SubElement(mailer, 'dontNotifyEveryUnstableBuild').text = 'true'
    XML.SubElement(mailer, 'sendToIndividuals').text = str(
        data.get('send-to-individuals', False)).lower()


def claim_build(registry, xml_parent, data):
    """yaml: claim-build
    Claim build failures
    Requires the Jenkins :jenkins-wiki:`Claim Plugin <Claim+plugin>`.

    Example:

    .. literalinclude::  /../../tests/publishers/fixtures/claim-build001.yaml
       :language: yaml
    """

    XML.SubElement(xml_parent, 'hudson.plugins.claim.ClaimPublisher')


def base_email_ext(registry, xml_parent, data, ttype):
    trigger = XML.SubElement(xml_parent,
                             'hudson.plugins.emailext.plugins.trigger.'
                             + ttype)
    email = XML.SubElement(trigger, 'email')
    XML.SubElement(email, 'recipientList').text = ''
    XML.SubElement(email, 'subject').text = '$PROJECT_DEFAULT_SUBJECT'
    XML.SubElement(email, 'body').text = '$PROJECT_DEFAULT_CONTENT'
    if 'send-to' in data:
        XML.SubElement(email, 'sendToDevelopers').text = str(
            'developers' in data['send-to']).lower()
        XML.SubElement(email, 'sendToRequester').text = str(
            'requester' in data['send-to']).lower()
        XML.SubElement(email, 'includeCulprits').text = str(
            'culprits' in data['send-to']).lower()
        XML.SubElement(email, 'sendToRecipientList').text = str(
            'recipients' in data['send-to']).lower()
    else:
        XML.SubElement(email, 'sendToRequester').text = 'false'
        XML.SubElement(email, 'sendToDevelopers').text = 'false'
        XML.SubElement(email, 'includeCulprits').text = 'false'
        XML.SubElement(email, 'sendToRecipientList').text = 'true'
    if ttype == 'ScriptTrigger':
        XML.SubElement(trigger, 'triggerScript').text = data['trigger-script']


def email_ext(registry, xml_parent, data):
    """yaml: email-ext
    Extend Jenkin's built in email notification
    Requires the Jenkins :jenkins-wiki:`Email-ext Plugin
    <Email-ext+plugin>`.

    :arg bool disable-publisher: Disable the publisher, while maintaining the
        settings. The usage model for this is when you want to test things out
        in the build, not send out e-mails during the testing. A message will
        be printed to the build log saying that the publisher is disabled.
        (default false)
    :arg str recipients: Comma separated list of recipient email addresses
        (default '$DEFAULT_RECIPIENTS')
    :arg str reply-to: Comma separated list of email addresses that should be
        in the Reply-To header for this project (default '$DEFAULT_REPLYTO')
    :arg str content-type: The content type of the emails sent. If not set, the
        Jenkins plugin uses the value set on the main configuration page.
        Possible values: 'html', 'text', 'both-html-text' or 'default'
        (default 'default')
    :arg str subject: Subject for the email, can include variables like
        ${BUILD_NUMBER} or even groovy or javascript code
        (default '$DEFAULT_SUBJECT')
    :arg str body: Content for the body of the email, can include variables
        like ${BUILD_NUMBER}, but the real magic is using groovy or
        javascript to hook into the Jenkins API itself
        (default '$DEFAULT_CONTENT')
    :arg bool attach-build-log: Include build log in the email (default false)
    :arg bool compress-log: Compress build log in the email (default false)
    :arg str attachments: pattern of files to include as attachment
         (default '')
    :arg bool always: Send an email for every result (default false)
    :arg bool unstable: Send an email for an unstable result (default false)
    :arg bool first-failure: Send an email for just the first failure
        (default false)
    :arg bool not-built: Send an email if not built (default false)
    :arg bool aborted: Send an email if the build is aborted (default false)
    :arg bool regression: Send an email if there is a regression
        (default false)
    :arg bool failure: Send an email if the build fails (default true)
    :arg bool second-failure: Send an email for the second failure
        (default false)
    :arg bool improvement: Send an email if the build improves (default false)
    :arg bool still-failing: Send an email if the build is still failing
        (default false)
    :arg bool success: Send an email for a successful build (default false)
    :arg bool fixed: Send an email if the build is fixed (default false)
    :arg bool still-unstable: Send an email if the build is still unstable
        (default false)
    :arg bool pre-build: Send an email before the build (default false)
    :arg str trigger-script: A Groovy script used to determine if an email
        should be sent.
    :arg str presend-script: A Groovy script executed prior sending the mail.
        (default '')
    :arg str postsend-script: A Goovy script executed after sending the email.
        (default '')
    :arg bool save-output: Save email content to workspace (default false)
    :arg str matrix-trigger: If using matrix projects, when to trigger

        :matrix-trigger values:
            * **both**
            * **only-parent**
            * **only-configurations**
    :arg list send-to: list of recipients from the predefined groups

        :send-to values:
            * **developers** (disabled by default)
            * **requester** (disabled by default)
            * **culprits** (disabled by default)
            * **recipients** (enabled by default)

    Example:

    .. literalinclude:: /../../tests/publishers/fixtures/email-ext001.yaml
       :language: yaml
    """

    emailext = XML.SubElement(xml_parent,
                              'hudson.plugins.emailext.ExtendedEmailPublisher')
    if 'recipients' in data:
        XML.SubElement(emailext, 'recipientList').text = data['recipients']
    else:
        XML.SubElement(emailext, 'recipientList').text = '$DEFAULT_RECIPIENTS'
    ctrigger = XML.SubElement(emailext, 'configuredTriggers')
    if data.get('always', False):
        base_email_ext(registry, ctrigger, data, 'AlwaysTrigger')
    if data.get('unstable', False):
        base_email_ext(registry, ctrigger, data, 'UnstableTrigger')
    if data.get('first-failure', False):
        base_email_ext(registry, ctrigger, data, 'FirstFailureTrigger')
    if data.get('not-built', False):
        base_email_ext(registry, ctrigger, data, 'NotBuiltTrigger')
    if data.get('aborted', False):
        base_email_ext(registry, ctrigger, data, 'AbortedTrigger')
    if data.get('regression', False):
        base_email_ext(registry, ctrigger, data, 'RegressionTrigger')
    if data.get('failure', True):
        base_email_ext(registry, ctrigger, data, 'FailureTrigger')
    if data.get('second-failure', False):
        base_email_ext(registry, ctrigger, data, 'SecondFailureTrigger')
    if data.get('improvement', False):
        base_email_ext(registry, ctrigger, data, 'ImprovementTrigger')
    if data.get('still-failing', False):
        base_email_ext(registry, ctrigger, data, 'StillFailingTrigger')
    if data.get('success', False):
        base_email_ext(registry, ctrigger, data, 'SuccessTrigger')
    if data.get('fixed', False):
        base_email_ext(registry, ctrigger, data, 'FixedTrigger')
    if data.get('still-unstable', False):
        base_email_ext(registry, ctrigger, data, 'StillUnstableTrigger')
    if data.get('pre-build', False):
        base_email_ext(registry, ctrigger, data, 'PreBuildTrigger')
    if data.get('trigger-script', False):
        base_email_ext(registry, ctrigger, data, 'ScriptTrigger')

    content_type_mime = {
        'text': 'text/plain',
        'html': 'text/html',
        'default': 'default',
        'both-html-text': 'both',
    }
    ctype = data.get('content-type', 'default')
    if ctype not in content_type_mime:
        raise JenkinsJobsException('email-ext content type must be one of: %s'
                                   % ', '.join(content_type_mime.keys()))
    XML.SubElement(emailext, 'contentType').text = content_type_mime[ctype]

    mappings = [
        ('subject', 'defaultSubject', '$DEFAULT_SUBJECT'),
        ('body', 'defaultContent', '$DEFAULT_CONTENT'),
        ('attachments', 'attachmentsPattern', ''),
        ('presend-script', 'presendScript', ''),
        ('postsend-script', 'postsendScript', ''),
        ('attach-build-log', 'attachBuildLog', False),
        ('compress-log', 'compressBuildLog', False),
        ('save-output', 'saveOutput', False),
        ('disable-publisher', 'disabled', False),
        ('reply-to', 'replyTo', '$DEFAULT_REPLYTO'),
    ]
    helpers.convert_mapping_to_xml(
        emailext, data, mappings, fail_required=True)

    matrix_dict = {'both': 'BOTH',
                   'only-configurations': 'ONLY_CONFIGURATIONS',
                   'only-parent': 'ONLY_PARENT'}
    matrix_trigger = data.get('matrix-trigger', None)
    # If none defined, then do not create entry
    if matrix_trigger is not None:
        if matrix_trigger not in matrix_dict:
            raise JenkinsJobsException("matrix-trigger entered is not valid, "
                                       "must be one of: %s" %
                                       ", ".join(matrix_dict.keys()))
        XML.SubElement(emailext, 'matrixTriggerMode').text = matrix_dict.get(
            matrix_trigger)


def fingerprint(registry, xml_parent, data):
    """yaml: fingerprint
    Fingerprint files to track them across builds. Requires the
    Jenkins :jenkins-wiki:`Fingerprint Plugin <Fingerprint+Plugin>`.

    :arg str files: files to fingerprint, follows the @includes of Ant fileset
        (default '')
    :arg bool record-artifacts: fingerprint all archived artifacts
        (default false)

    Example:

    .. literalinclude::  /../../tests/publishers/fixtures/fingerprint001.yaml
       :language: yaml
    """
    finger = XML.SubElement(xml_parent, 'hudson.tasks.Fingerprinter')
    mappings = [
        ('files', 'targets', ''),
        ('record-artifacts', 'recordBuildArtifacts', False)
    ]
    helpers.convert_mapping_to_xml(finger, data, mappings, fail_required=True)


def aggregate_tests(registry, xml_parent, data):
    """yaml: aggregate-tests
    Aggregate downstream test results

    :arg bool include-failed-builds: whether to include failed builds

    Example:

    .. literalinclude::
        /../../tests/publishers/fixtures/aggregate-tests001.yaml
       :language: yaml
    """
    agg = XML.SubElement(xml_parent,
                         'hudson.tasks.test.AggregatedTestResultPublisher')
    XML.SubElement(agg, 'includeFailedBuilds').text = str(data.get(
        'include-failed-builds', False)).lower()


def aggregate_flow_tests(registry, xml_parent, data):
    """yaml: aggregate-flow-tests
    Aggregate downstream test results in a Build Flow job.
    Requires the Jenkins :jenkins-wiki:`Build Flow Test Aggregator Plugin
    <Build+Flow+Test+Aggregator+Plugin>`.

    :arg bool show-test-results-trend: whether to show test results
        trend graph (default true)

    Example:

    .. literalinclude::
        /../../tests/publishers/fixtures/aggregate-flow-tests002.yaml
       :language: yaml

    """
    agg_flow = XML.SubElement(xml_parent, 'org.zeroturnaround.jenkins.'
                              'flowbuildtestaggregator.FlowTestAggregator')
    XML.SubElement(agg_flow, 'showTestResultTrend').text = str(
        data.get('show-test-results-trend', True)).lower()


def cppcheck(registry, xml_parent, data):
    """yaml: cppcheck
    Cppcheck result publisher
    Requires the Jenkins :jenkins-wiki:`Cppcheck Plugin <Cppcheck+Plugin>`.

    :arg str pattern: File pattern for cppcheck xml report (required)
    :arg bool ignoreblankfiles: Ignore blank files (default false)
    :arg bool allow-no-report: Do not fail the build if the Cppcheck report
        is not found (default false)
    :arg dict thresholds:
        :thresholds: Configure the build status and health. A build is
            considered as unstable or failure if the new or total number
            of issues exceeds the specified thresholds. The build health
            is also determined by thresholds. If the actual number of issues
            is between the provided thresholds, then the build health is
            interpolated.
        * **unstable** (`str`): Total number unstable threshold (default '')
        * **new-unstable** (`str`): New number unstable threshold (default '')
        * **failure** (`str`): Total number failure threshold (default '')
        * **new-failure** (`str`): New number failure threshold (default '')
        * **healthy** (`str`): Healthy threshold (default '')
        * **unhealthy** (`str`): Unhealthy threshold (default '')
    :arg dict severity:
        :severity: Determines which severity of issues should be considered
            when evaluating the build status and health, default all true
        * **error** (`bool`): Severity error (default true)
        * **warning** (`bool`): Severity warning (default true)
        * **style** (`bool`): Severity style (default true)
        * **performance** (`bool`): Severity performance (default true)
        * **information** (`bool`): Severity information (default true)
        * **nocategory** (`bool`): Severity nocategory (default true)
        * **portability** (`bool`): Severity portability (default true)
    :arg dict graph:
        :graph: Graph configuration
        * **xysize** (`array`): Chart width and height (default [500, 200])
        * **num-builds-in-graph** (`int`): Builds number in graph (default 0)
    :arg dict display
        :display: which errors to display, default only sum
        * **sum** (`bool`): Display sum of all issues (default true)
        * **error** (`bool`): Display errors (default false)
        * **warning** (`bool`): Display warnings (default false)
        * **style** (`bool`): Display style (default false)
        * **performance** (`bool`): Display performance (default false)
        * **information** (`bool`): Display information (default false)
        * **nocategory** (`bool`): Display no category (default false)
        * **portability** (`bool`): Display portability (default false)

    Minimal Example:

    .. literalinclude::
        /../../tests/publishers/fixtures/cppcheck-minimal.yaml
       :language: yaml

    Full Example:
    .. literalinclude::
        /../../tests/publishers/fixtures/cppcheck-complete.yaml
       :language: yaml
    """

    cppextbase = XML.SubElement(xml_parent,
                                'org.jenkinsci.plugins.cppcheck.'
                                'CppcheckPublisher')
    cppextbase.set('plugin', 'cppcheck')
    cppext = XML.SubElement(cppextbase, 'cppcheckConfig')
    mappings = [
        ('pattern', 'pattern', None),
        ('ignoreblankfiles', 'ignoreBlankFiles', False),
        ('allow-no-report', 'allowNoReport', False)
    ]
    helpers.convert_mapping_to_xml(cppext, data, mappings, fail_required=True)

    csev = XML.SubElement(cppext, 'configSeverityEvaluation')
    thrsh = data.get('thresholds', {})
    thrsh_mappings = [
        ('unstable', 'threshold', ''),
        ('new-unstable', 'newThreshold', ''),
        ('failure', 'failureThreshold', ''),
        ('new-failure', 'newFailureThreshold', ''),
        ('healthy', 'healthy', ''),
        ('unhealthy', 'unHealthy', '')
    ]
    helpers.convert_mapping_to_xml(
        csev, thrsh, thrsh_mappings, fail_required=True)

    sev = thrsh.get('severity', {})
    sev_mappings = [
        ('error', 'severityError', True),
        ('warning', 'severityWarning', True),
        ('style', 'severityStyle', True),
        ('performance', 'severityPerformance', True),
        ('information', 'severityInformation', True),
        ('nocategory', 'severityNoCategory', True),
        ('portability', 'severityPortability', True)
    ]
    helpers.convert_mapping_to_xml(
        csev, sev, sev_mappings, fail_required=True)

    graph = data.get('graph', {})
    cgraph = XML.SubElement(cppext, 'configGraph')
    x, y = graph.get('xysize', [500, 200])
    XML.SubElement(cgraph, 'xSize').text = str(x)
    XML.SubElement(cgraph, 'ySize').text = str(y)
    graph_mapping = [
        ('num-builds-in-graph', 'numBuildsInGraph', 0)
    ]
    helpers.convert_mapping_to_xml(
        cgraph, graph, graph_mapping, fail_required=True)

    gdisplay = graph.get('display', {})
    gdisplay_mappings = [
        ('sum', 'displayAllErrors', True),
        ('error', 'displayErrorSeverity', False),
        ('warning', 'displayWarningSeverity', False),
        ('style', 'displayStyleSeverity', False),
        ('performance', 'displayPerformanceSeverity', False),
        ('information', 'displayInformationSeverity', False),
        ('nocategory', 'displayNoCategorySeverity', False),
        ('portability', 'displayPortabilitySeverity', False)
    ]
    helpers.convert_mapping_to_xml(
        cgraph, gdisplay, gdisplay_mappings, fail_required=True)


def logparser(registry, xml_parent, data):
    """yaml: logparser
    Requires the Jenkins :jenkins-wiki:`Log Parser Plugin <Log+Parser+Plugin>`.

    :arg str parse-rules: full path to parse rules (default '')
    :arg bool unstable-on-warning: mark build unstable on warning
        (default false)
    :arg bool fail-on-error: mark build failed on error (default false)

    Example:

    .. literalinclude::  /../../tests/publishers/fixtures/logparser001.yaml
       :language: yaml
    """

    clog = XML.SubElement(xml_parent,
                          'hudson.plugins.logparser.LogParserPublisher')
    clog.set('plugin', 'log-parser')
    mappings = [
        ('unstable-on-warning', 'unstableOnWarning', False),
        ('fail-on-error', 'failBuildOnError', False),
        ('parse-rules', 'parsingRulesPath', '')
    ]
    helpers.convert_mapping_to_xml(clog, data, mappings, fail_required=True)


def copy_to_master(registry, xml_parent, data):
    """yaml: copy-to-master
    Copy files to master from slave
    Requires the Jenkins :jenkins-wiki:`Copy To Slave Plugin
    <Copy+To+Slave+Plugin>`.

    :arg list includes: list of file patterns to copy
    :arg list excludes: list of file patterns to exclude
    :arg string destination: absolute path into which the files will be copied.
        If left blank they will be copied into the workspace of the current job
        (default '')
    :arg bool run-after-result: If this is checked then copying files back to
        master will not run until the build result is finalized.(default true)

    Example:

    .. literalinclude::
        /../../tests/publishers/fixtures/copy-to-master001.yaml
       :language: yaml
    """
    cm = XML.SubElement(xml_parent, 'com.michelin.'
                        'cio.hudson.plugins.copytoslave.CopyToMasterNotifier')
    cm.set('plugin', 'copy-to-slave')

    XML.SubElement(cm, 'includes').text = ','.join(data.get('includes', ['']))
    XML.SubElement(cm, 'excludes').text = ','.join(data.get('excludes', ['']))
    mappings = [
        ('run-after-result', 'runAfterResultFinalised', True),
        ('destination', 'destinationFolder', '')
    ]
    helpers.convert_mapping_to_xml(cm, data, mappings, fail_required=True)

    if data.get('destination', ''):
        XML.SubElement(cm, 'overrideDestinationFolder').text = 'true'


def jira(registry, xml_parent, data):
    """yaml: jira
    Update relevant JIRA issues
    Requires the Jenkins :jenkins-wiki:`JIRA Plugin <JIRA+Plugin>`.

    Example:

    .. literalinclude:: /../../tests/publishers/fixtures/jira001.yaml
       :language: yaml
    """
    XML.SubElement(xml_parent, 'hudson.plugins.jira.JiraIssueUpdater')


def growl(registry, xml_parent, data):
    """yaml: growl
    Push notifications to growl client.
    Requires the Jenkins :jenkins-wiki:`Growl Plugin <Growl+Plugin>`.

    :arg str ip: IP address to send growl notifications to (required)
    :arg bool notify-only-on-fail-or-recovery: send a growl only when build
        fails or recovers from a failure (default false)

    Minimal Example:

    .. literalinclude:: /../../tests/publishers/fixtures/growl-minimal.yaml
       :language: yaml

    Full Example:

    .. literalinclude:: /../../tests/publishers/fixtures/growl-full.yaml
       :language: yaml
    """
    growl = XML.SubElement(xml_parent, 'hudson.plugins.growl.GrowlPublisher')
    growl.set('plugin', 'growl')

    mapping = [
        ('ip', 'IP', None),
        ('notify-only-on-fail-or-recovery', 'onlyOnFailureOrRecovery', False),
    ]
    helpers.convert_mapping_to_xml(growl, data, mapping, fail_required=True)


def groovy_postbuild(registry, xml_parent, data):
    """yaml: groovy-postbuild
    Execute a groovy script.
    Requires the Jenkins :jenkins-wiki:`Groovy Postbuild Plugin
    <Groovy+Postbuild+Plugin>`.

    Please pay attention on version of plugin you have installed.
    There were incompatible changes between 1.x and 2.x. Please see
    :jenkins-wiki:`home page <Groovy+Postbuild+Plugin>` of this plugin
    for full information including migration process.

    :arg str script: The groovy script to execute
    :arg list classpath: List of additional classpaths (>=1.6)
    :arg str on-failure: In case of script failure leave build as it is
        for "nothing" option, mark build as unstable
        for "unstable" and mark job as failure for "failed"
        (default 'nothing')
    :arg bool matrix-parent: Run script for matrix parent only (>=1.9)
        (default false)
    :arg bool sandbox: Execute script inside of groovy sandbox (>=2.0)
        (default false)

    Example:

    .. literalinclude::
        /../../tests/publishers/fixtures/groovy-postbuild001.yaml
       :language: yaml
    """
    logger = logging.getLogger("%s:groovy-postbuild" % __name__)
    # Backward compatibility with old format
    if isinstance(data, six.string_types):
        logger.warning(
            "You use depricated configuration, please follow documentation "
            "to change configuration. It is not going to be supported in "
            "future releases!"
        )
        data = {
            'script': data,
        }
    # There are incompatible changes, we need to know version
    info = registry.get_plugin_info('groovy-postbuild')
    version = pkg_resources.parse_version(info.get('version', "0"))
    # Version specific predicates
    matrix_parent_support = version >= pkg_resources.parse_version("1.9")
    security_plugin_support = version >= pkg_resources.parse_version("2.0")
    extra_classpath_support = version >= pkg_resources.parse_version("1.6")

    root_tag = (
        'org.jvnet.hudson.plugins.groovypostbuild.GroovyPostbuildRecorder'
    )
    groovy = XML.SubElement(xml_parent, root_tag)

    behavior = data.get('on-failure')
    XML.SubElement(groovy, 'behavior').text = {
        'unstable': '1',
        'failed': '2',
    }.get(behavior, '0')

    if matrix_parent_support:
        XML.SubElement(
            groovy,
            'runForMatrixParent',
        ).text = str(data.get('matrix-parent', False)).lower()

    classpaths = data.get('classpath', list())
    if security_plugin_support:
        script = XML.SubElement(groovy, 'script')
        XML.SubElement(script, 'script').text = data.get('script')
        XML.SubElement(script, 'sandbox').text = str(
            data.get('sandbox', False)
        ).lower()
        if classpaths:
            classpath = XML.SubElement(script, 'classpath')
            for path in classpaths:
                script_path = XML.SubElement(classpath, 'entry')
                XML.SubElement(script_path, 'url').text = path
    else:
        XML.SubElement(groovy, 'groovyScript').text = data.get('script')
        if extra_classpath_support and classpaths:
            classpath = XML.SubElement(groovy, 'classpath')
            for path in classpaths:
                script_path = XML.SubElement(
                    classpath,
                    'org.jvnet.hudson.plugins.groovypostbuild.'
                    'GroovyScriptPath',
                )
                XML.SubElement(script_path, 'path').text = path


def base_publish_over(xml_parent, data, console_prefix,
                      plugin_tag, publisher_tag,
                      transferset_tag, reference_plugin_tag):
    outer = XML.SubElement(xml_parent, plugin_tag)
    # 'Publish over SSH' builder has an extra top delegate element
    if xml_parent.tag == 'builders':
        outer = XML.SubElement(outer, 'delegate')

    XML.SubElement(outer, 'consolePrefix').text = console_prefix
    delegate = XML.SubElement(outer, 'delegate')
    publishers = XML.SubElement(delegate, 'publishers')

    inner = XML.SubElement(publishers, publisher_tag)
    XML.SubElement(inner, 'configName').text = data['site']
    XML.SubElement(inner, 'verbose').text = 'true'

    transfers = XML.SubElement(inner, 'transfers')
    transfersset = XML.SubElement(transfers, transferset_tag)

    XML.SubElement(transfersset, 'remoteDirectory').text = data['target']
    XML.SubElement(transfersset, 'sourceFiles').text = data['source']
    XML.SubElement(transfersset, 'excludes').text = data.get('excludes', '')
    XML.SubElement(transfersset, 'removePrefix').text = data.get(
        'remove-prefix', '')
    XML.SubElement(transfersset, 'remoteDirectorySDF').text = str(
        data.get('target-is-date-format', False)).lower()
    XML.SubElement(transfersset, 'flatten').text = str(
        data.get('flatten', False)).lower()
    XML.SubElement(transfersset, 'cleanRemote').text = str(
        data.get('clean-remote', False)).lower()

    if 'command' in data:
        XML.SubElement(transfersset, 'execCommand').text = data['command']
    if 'timeout' in data:
        XML.SubElement(transfersset, 'execTimeout').text = str(data['timeout'])
    if 'use-pty' in data:
        XML.SubElement(transfersset, 'usePty').text = str(
            data.get('use-pty', False)).lower()

    XML.SubElement(inner, 'useWorkspaceInPromotion').text = 'false'
    XML.SubElement(inner, 'usePromotionTimestamp').text = 'false'

    XML.SubElement(delegate, 'continueOnError').text = 'false'
    XML.SubElement(delegate, 'failOnError').text = str(
        data.get('fail-on-error', False)).lower()
    XML.SubElement(delegate, 'alwaysPublishFromMaster').text = str(
        data.get('always-publish-from-master', False)).lower()
    XML.SubElement(delegate, 'hostConfigurationAccess',
                   {'class': reference_plugin_tag, 'reference': '../..'})

    return (outer, transfersset)


def cifs(registry, xml_parent, data):
    """yaml: cifs
    Upload files via CIFS.
    Requires the Jenkins :jenkins-wiki:`Publish over CIFS Plugin
    <Publish+Over+CIFS+Plugin>`.

    :arg str site: name of the cifs site/share (required)
    :arg str target: destination directory (required)
    :arg bool target-is-date-format: whether target is a date format. If true,
        raw text should be quoted (default false)
    :arg bool clean-remote: should the remote directory be deleted before
        transferring files (default false)
    :arg str source: source path specifier (required)
    :arg str excludes: excluded file pattern (default '')
    :arg str remove-prefix: prefix to remove from uploaded file paths
        (default '')
    :arg bool fail-on-error: fail the build if an error occurs (default false).
    :arg bool flatten: only create files on the server, don't create
        directories (default false).

    Example:

    .. literalinclude::  /../../tests/publishers/fixtures/cifs001.yaml
       :language: yaml

    """
    console_prefix = 'CIFS: '
    plugin_tag = 'jenkins.plugins.publish__over__cifs.CifsPublisherPlugin'
    publisher_tag = 'jenkins.plugins.publish__over__cifs.CifsPublisher'
    transfer_tag = 'jenkins.plugins.publish__over__cifs.CifsTransfer'
    plugin_reference_tag = ('jenkins.plugins.publish_over_cifs.'
                            'CifsPublisherPlugin')
    base_publish_over(xml_parent,
                      data,
                      console_prefix,
                      plugin_tag,
                      publisher_tag,
                      transfer_tag,
                      plugin_reference_tag)


def cigame(registry, xml_parent, data):
    """yaml: cigame
    This plugin introduces a game where users get points
    for improving the builds.
    Requires the Jenkins :jenkins-wiki:`The Continuous Integration Game plugin
    <The+Continuous+Integration+Game+plugin>`.

    Example:

    .. literalinclude:: /../../tests/publishers/fixtures/cigame.yaml
       :language: yaml
    """
    XML.SubElement(xml_parent, 'hudson.plugins.cigame.GamePublisher')


def sonar(registry, xml_parent, data):
    """yaml: sonar
    Sonar plugin support.
    Requires the Jenkins `Sonar Plugin.
    <http://docs.sonarqube.org/display/SONAR/\
        Analyzing+with+SonarQube+Scanner+for+Jenkins>`_

    :arg str jdk: JDK to use (inherited from the job if omitted). (optional)
    :arg str branch: branch onto which the analysis will be posted (default '')
    :arg str language: source code language (default '')
    :arg str root-pom: Root POM (default 'pom.xml')
    :arg bool private-maven-repo: If true, use private Maven repository.
        (default false)
    :arg str maven-opts: options given to maven (default '')
    :arg str additional-properties: sonar analysis parameters (default '')
    :arg dict skip-global-triggers:
        :Triggers: * **skip-when-scm-change** (`bool`): skip analysis when
                     build triggered by scm (default false)
                   * **skip-when-upstream-build** (`bool`): skip analysis when
                     build triggered by an upstream build (default false)
                   * **skip-when-envvar-defined** (`str`): skip analysis when
                     the specified environment variable is set to true
                     (default '')
    :arg str settings: Path to use as user settings.xml. It is possible to
        provide a ConfigFileProvider settings file, see Example below.
        (optional)
    :arg str global-settings: Path to use as global settings.xml. It is
        possible to provide a ConfigFileProvider settings file, see Example
        below. (optional)

    Requires the Jenkins :jenkins-wiki:`Config File Provider Plugin
    <Config+File+Provider+Plugin>`
    for the Config File Provider "settings" and "global-settings" config.

    This publisher supports the post-build action exposed by the Jenkins
    Sonar Plugin, which is triggering a Sonar Analysis with Maven.

    Minimal Example:

    .. literalinclude:: /../../tests/publishers/fixtures/sonar-minimal.yaml
       :language: yaml

    Full Example:
    .. literalinclude:: /../../tests/publishers/fixtures/sonar-complete.yaml
       :language: yaml
    """

    sonar = XML.SubElement(xml_parent, 'hudson.plugins.sonar.SonarPublisher')
    sonar.set('plugin', 'sonar')

    if 'jdk' in data:
        XML.SubElement(sonar, 'jdk').text = data['jdk']

    mappings = [
        ('branch', 'branch', ''),
        ('language', 'language', ''),
        ('root-pom', 'rootPom', 'pom.xml'),
        ('private-maven-repo', 'usePrivateRepository', False),
        ('maven-opts', 'mavenOpts', ''),
        ('additional-properties', 'jobAdditionalProperties', '')
    ]
    helpers.convert_mapping_to_xml(sonar, data, mappings, fail_required=True)

    if 'skip-global-triggers' in data:
        data_triggers = data['skip-global-triggers']
        triggers = XML.SubElement(sonar, 'triggers')
        triggers_mappings = [
            ('skip-when-scm-change', 'skipScmCause', False),
            ('skip-when-upstream-build', 'skipUpstreamCause', False),
            ('skip-when-envvar-defined', 'envVar', '')
        ]
        helpers.convert_mapping_to_xml(
            triggers, data_triggers, triggers_mappings, fail_required=True)

    helpers.config_file_provider_settings(sonar, data)


def performance(registry, xml_parent, data):
    """yaml: performance
    Publish performance test results from jmeter and junit.
    Requires the Jenkins :jenkins-wiki:`Performance Plugin
    <Performance+Plugin>`.

    :arg int failed-threshold: Specify the error percentage threshold that
        set the build failed. A negative value means don't use this threshold
        (default 0)
    :arg int unstable-threshold: Specify the error percentage threshold that
        set the build unstable. A negative value means don't use this threshold
        (default 0)
    :arg str unstable-response-time-threshold: Average response time threshold
        (default '')
    :arg float failed-threshold-positive: Maximum failed percentage for build
        comparison (default 0.0)
    :arg float failed-threshold-negative: Minimum failed percentage for build
        comparison (default 0.0)
    :arg float unstable-threshold-positive: Maximum unstable percentage for
        build comparison (default 0.0)
    :arg float unstable-threshold-negative: Minimum unstable percentage for
        build comparison (default 0.0)
    :arg int nth-build-number: Build number for build comparison (default 0)
    :arg bool mode-relative-thresholds: Relative threshold mode (default false)
    :arg str config-type: Compare based on (default 'ART')

        :config-type values:
          * **ART** -- Average Response Time
          * **MRT** -- Median Response Time
          * **PRT** -- Percentile Response Time

    :arg bool mode-of-threshold: Mode of threshold, true for relative threshold
        and false for error threshold (default false)
    :arg bool fail-build: Fail build when result files are not present
        (default false)
    :arg bool compare-build-previous: Compare with previous build
        (default false)
    :arg bool mode-performance-per-test-case: Performance Per Test Case Mode
        (default true)
    :arg bool mode-thoughput: Show Throughput Chart (default false)

    :arg dict report:

        :(jmeter or junit): (`dict` or `str`): Specify a custom report file
         (optional; jmeter default \**/*.jtl, junit default **/TEST-\*.xml)

    Minimal Example:

    .. literalinclude::
       /../../tests/publishers/fixtures/performance-minimal.yaml
       :language: yaml

    Full Example:

    .. literalinclude::
       /../../tests/publishers/fixtures/performance-complete.yaml
       :language: yaml
    """
    perf = XML.SubElement(xml_parent, 'hudson.plugins.performance.'
                                      'PerformancePublisher')
    perf.set('plugin', 'performance')
    types = ['ART', 'MRT', 'PRT']
    mappings = [
        ('failed-threshold', 'errorFailedThreshold', 0),
        ('unstable-threshold', 'errorUnstableThreshold', 0),
        ('unstable-response-time-threshold',
         'errorUnstableResponseTimeThreshold',
         ''),
        ('failed-threshold-positive',
         'relativeFailedThresholdPositive',
         '0.0'),
        ('failed-threshold-negative',
         'relativeFailedThresholdNegative',
         '0.0'),
        ('unstable-threshold-positive',
         'relativeUnstableThresholdPositive',
         '0.0'),
        ('unstable-threshold-negative',
         'relativeUnstableThresholdNegative',
         '0.0'),
        ('nth-build-number', 'nthBuildNumber', 0),
        ('mode-relative-thresholds', 'modeRelativeThresholds', False),
        ('config-type', 'configType', 'ART', types),
        ('mode-of-threshold', 'modeOfThreshold', False),
        ('fail-build', 'failBuildIfNoResultFile', False),
        ('compare-build-previous', 'compareBuildPrevious', False),
        ('mode-performance-per-test-case', 'modePerformancePerTestCase', True),
        ('mode-thoughput', 'modeThroughput', False)
    ]
    helpers.convert_mapping_to_xml(perf, data, mappings, fail_required=True)

    parsers = XML.SubElement(perf, 'parsers')
    if 'report' in data:
        for item in data['report']:
            if isinstance(item, dict):
                item_name = next(iter(item.keys()))
                item_values = item.get(item_name, None)
                if item_name == 'jmeter':
                    jmhold = XML.SubElement(parsers, 'hudson.plugins.'
                                                     'performance.'
                                                     'JMeterParser')
                    XML.SubElement(jmhold, 'glob').text = str(item_values)
                elif item_name == 'junit':
                    juhold = XML.SubElement(parsers, 'hudson.plugins.'
                                                     'performance.'
                                                     'JUnitParser')
                    XML.SubElement(juhold, 'glob').text = str(item_values)
                else:
                    raise JenkinsJobsException("You have not specified jmeter "
                                               "or junit, or you have "
                                               "incorrectly assigned the key "
                                               "value.")
            elif isinstance(item, str):
                if item == 'jmeter':
                    jmhold = XML.SubElement(parsers, 'hudson.plugins.'
                                                     'performance.'
                                                     'JMeterParser')
                    XML.SubElement(jmhold, 'glob').text = '**/*.jtl'
                elif item == 'junit':
                    juhold = XML.SubElement(parsers, 'hudson.plugins.'
                                                     'performance.'
                                                     'JUnitParser')
                    XML.SubElement(juhold, 'glob').text = '**/TEST-*.xml'
                else:
                    raise JenkinsJobsException("You have not specified jmeter "
                                               "or junit, or you have "
                                               "incorrectly assigned the key "
                                               "value.")


def join_trigger(registry, xml_parent, data):
    """yaml: join-trigger
    Trigger a job after all the immediate downstream jobs have completed.
    Requires the Jenkins :jenkins-wiki:`Join Plugin <Join+Plugin>`.

    :arg bool even-if-unstable: if true jobs will trigger even if some
        downstream jobs are marked as unstable (default false)
    :arg list projects: list of projects to trigger
    :arg list publishers: list of triggers from publishers module that
        defines projects that need to be triggered

    Example:

    .. literalinclude:: /../../tests/publishers/fixtures/join-trigger001.yaml
       :language: yaml
    """
    jointrigger = XML.SubElement(xml_parent, 'join.JoinTrigger')

    joinProjectsText = ','.join(data.get('projects', ['']))
    XML.SubElement(jointrigger, 'joinProjects').text = joinProjectsText

    publishers = XML.SubElement(jointrigger, 'joinPublishers')
    for pub in data.get('publishers', []):
        for edited_node in create_publishers(registry, pub):
            publishers.append(edited_node)

    unstable = str(data.get('even-if-unstable', 'false')).lower()
    XML.SubElement(jointrigger, 'evenIfDownstreamUnstable').text = unstable


def jabber(registry, xml_parent, data):
    """yaml: jabber
    Integrates Jenkins with the Jabber/XMPP instant messaging protocol
    Requires the Jenkins :jenkins-wiki:`Jabber Plugin <Jabber+Plugin>`.

    :arg bool notify-on-build-start: Whether to send notifications
        to channels when a build starts (default false)
    :arg bool notify-scm-committers: Whether to send notifications
        to the users that are suspected of having broken this build
        (default false)
    :arg bool notify-scm-culprits: Also send notifications to 'culprits'
        from previous unstable/failed builds (default false)
    :arg bool notify-upstream-committers: Whether to send notifications to
        upstream committers if no committers were found for a broken build
        (default false)
    :arg bool notify-scm-fixers: Whether to send notifications to the users
        that have fixed a broken build (default false)
    :arg list group-targets: List of group targets to notify
    :arg list individual-targets: List of individual targets to notify
    :arg dict strategy: When to send notifications (default all)

        :strategy values:
          * **all** -- Always
          * **failure** -- On any failure
          * **failure-fixed** -- On failure and fixes
          * **new-failure-fixed** -- On new failure and fixes
          * **change** -- Only on state change
    :arg dict message: Channel notification message (default summary-scm)

        :message  values:
          * **summary-scm** -- Summary + SCM changes
          * **summary** -- Just summary
          * **summary-build** -- Summary and build parameters
          * **summary-scm-fail** -- Summary, SCM changes, and failed tests

    Minimal Example:

    .. literalinclude:: /../../tests/publishers/fixtures/jabber-minimal.yaml
       :language: yaml

    Full Example:

    .. literalinclude:: /../../tests/publishers/fixtures/jabber-complete.yaml
       :language: yaml
    """
    j = XML.SubElement(xml_parent, 'hudson.plugins.jabber.im.transport.'
                       'JabberPublisher')
    j.set('plugin', 'jabber')

    t = XML.SubElement(j, 'targets')
    if 'group-targets' in data:
        for group in data['group-targets']:
            gcimt = XML.SubElement(t, 'hudson.plugins.im.'
                                   'GroupChatIMMessageTarget')
            gcimt.set('plugin', 'instant-messaging')
            XML.SubElement(gcimt, 'name').text = group
            XML.SubElement(gcimt, 'notificationOnly').text = 'false'
    if 'individual-targets' in data:
        for individual in data['individual-targets']:
            dimt = XML.SubElement(t, 'hudson.plugins.im.'
                                  'DefaultIMMessageTarget')
            dimt.set('plugin', 'instant-messaging')
            XML.SubElement(dimt, 'value').text = individual
    strategy = data.get('strategy', 'all')
    strategydict = {'all': 'ALL',
                    'failure': 'ANY_FAILURE',
                    'failure-fixed': 'FAILURE_AND_FIXED',
                    'new-failure-fixed': 'NEW_FAILURE_AND_FIXED',
                    'change': 'STATECHANGE_ONLY'}
    if strategy not in strategydict:
        raise JenkinsJobsException("Strategy entered is not valid, must be " +
                                   "one of: all, failure, failure-fixed, or "
                                   "change")
    XML.SubElement(j, 'strategy').text = strategydict[strategy]

    mappings = [
        ('notify-on-build-start', 'notifyOnBuildStart', False),
        ('notify-scm-committers', 'notifySuspects', False),
        ('notify-scm-culprits', 'notifyCulprits', False),
        ('notify-scm-fixers', 'notifyFixers', False),
        ('notify-upstream-committers', 'notifyUpstreamCommitters', False)
    ]
    helpers.convert_mapping_to_xml(j, data, mappings, fail_required=True)

    message = data.get('message', 'summary-scm')
    messagedict = {'summary-scm': 'DefaultBuildToChatNotifier',
                   'summary': 'SummaryOnlyBuildToChatNotifier',
                   'summary-build': 'BuildParametersBuildToChatNotifier',
                   'summary-scm-fail': 'PrintFailingTestsBuildToChatNotifier'}
    if message not in messagedict:
        raise JenkinsJobsException("Message entered is not valid, must be one "
                                   "of: summary-scm, summary, summary-build "
                                   "or summary-scm-fail")
    XML.SubElement(j, 'buildToChatNotifier', {
        'class': 'hudson.plugins.im.build_notify.' + messagedict[message]})
    XML.SubElement(j, 'matrixMultiplier').text = 'ONLY_CONFIGURATIONS'


def workspace_cleanup(registry, xml_parent, data):
    """yaml: workspace-cleanup (post-build)

    Requires the Jenkins :jenkins-wiki:`Workspace Cleanup Plugin
    <Workspace+Cleanup+Plugin>`.

    The pre-build workspace-cleanup is available as a wrapper.

    :arg list include: list of files to be included
    :arg list exclude: list of files to be excluded
    :arg bool dirmatch: Apply pattern to directories too (default false)
    :arg list clean-if: clean depending on build status

        :clean-if values:
            * **success** (`bool`) (default true)
            * **unstable** (`bool`) (default true)
            * **failure** (`bool`) (default true)
            * **aborted** (`bool`) (default true)
            * **not-built** (`bool`)  (default true)
    :arg bool fail-build: Fail the build if the cleanup fails (default true)
    :arg bool clean-parent: Cleanup matrix parent workspace (default false)
    :arg str external-deletion-command: external deletion command to run
        against files and directories

    Minimal Example:

    .. literalinclude::
        /../../tests/publishers/fixtures/workspace-cleanup-minimal.yaml
       :language: yaml

    Full Example:

    .. literalinclude::
        /../../tests/publishers/fixtures/workspace-cleanup-complete.yaml
       :language: yaml
    """

    p = XML.SubElement(xml_parent,
                       'hudson.plugins.ws__cleanup.WsCleanup')
    p.set("plugin", "ws-cleanup")
    if "include" in data or "exclude" in data:
        patterns = XML.SubElement(p, 'patterns')

    for inc in data.get("include", []):
        ptrn = XML.SubElement(patterns, 'hudson.plugins.ws__cleanup.Pattern')
        XML.SubElement(ptrn, 'pattern').text = inc
        XML.SubElement(ptrn, 'type').text = "INCLUDE"

    for exc in data.get("exclude", []):
        ptrn = XML.SubElement(patterns, 'hudson.plugins.ws__cleanup.Pattern')
        XML.SubElement(ptrn, 'pattern').text = exc
        XML.SubElement(ptrn, 'type').text = "EXCLUDE"

    mappings = [
        ('dirmatch', 'deleteDirs', False),
        ('clean-parent', 'cleanupMatrixParent', False),
        ('external-deletion-command', 'externalDelete', '')
    ]
    helpers.convert_mapping_to_xml(p, data, mappings, fail_required=True)

    mask = [('success', 'cleanWhenSuccess'),
            ('unstable', 'cleanWhenUnstable'),
            ('failure', 'cleanWhenFailure'),
            ('not-built', 'cleanWhenNotBuilt'),
            ('aborted', 'cleanWhenAborted')]
    clean = data.get('clean-if', [])
    cdict = dict()
    for d in clean:
        cdict.update(d)
    for k, v in mask:
        XML.SubElement(p, v).text = str(cdict.pop(k, True)).lower()

    if len(cdict) > 0:
        raise ValueError('clean-if must be one of: %r' % list(mask.keys()))

    if str(data.get("fail-build", False)).lower() == 'false':
        XML.SubElement(p, 'notFailBuild').text = 'true'
    else:
        XML.SubElement(p, 'notFailBuild').text = 'false'


def maven_deploy(registry, xml_parent, data):
    """yaml: maven-deploy
    Deploy artifacts to Maven repository.

    :arg str id: Repository ID
    :arg str url: Repository URL (optional)
    :arg bool unique-version: Assign unique versions to snapshots
      (default true)
    :arg bool deploy-unstable: Deploy even if the build is unstable
      (default false)
    :arg str release-env-var: If the given variable name is set to "true",
      the deploy steps are skipped. (optional)


    Example:

    .. literalinclude:: /../../tests/publishers/fixtures/maven-deploy001.yaml
       :language: yaml
    """

    p = XML.SubElement(xml_parent, 'hudson.maven.RedeployPublisher')
    if 'id' in data:
        XML.SubElement(p, 'id').text = data['id']
    if 'url' in data:
        XML.SubElement(p, 'url').text = data['url']
    XML.SubElement(p, 'uniqueVersion').text = str(
        data.get('unique-version', True)).lower()
    XML.SubElement(p, 'evenIfUnstable').text = str(
        data.get('deploy-unstable', False)).lower()
    if 'release-env-var' in data:
        XML.SubElement(p, 'releaseEnvVar').text = data['release-env-var']


def artifactory(registry, xml_parent, data):
    """yaml: artifactory
    Uses/requires the Artifactory plugin to deploy artifacts to
    Artifactory Server.

    Requires the Jenkins :jenkins-wiki:`Artifactory Plugin
    <Artifactory+Plugin>`.

    :arg str url: Artifactory server url (default '')
    :arg str name: Artifactory user with permissions use for
        connected to the selected Artifactory Server (default '')
    :arg str release-repo-key: Release repository name (default '')
    :arg str snapshot-repo-key: Snapshots repository name (default '')
    :arg bool publish-build-info: Push build metadata with artifacts
        (default false)
    :arg bool discard-old-builds:
        Remove older build info from Artifactory (default false)
    :arg bool discard-build-artifacts:
        Remove older build artifacts from Artifactory (default false)
    :arg bool even-if-unstable: Deploy artifacts even when the build
        is unstable (default false)
    :arg bool run-checks: Run automatic license scanning check after the
        build is complete (default false)
    :arg bool include-publish-artifacts: Include the build's published
        module artifacts in the license violation checks if they are
        also used as dependencies for other modules in this build
        (default false)
    :arg bool pass-identified-downstream: When true, a build parameter
        named ARTIFACTORY_BUILD_ROOT with a value of
        ${JOB_NAME}-${BUILD_NUMBER} will be sent to downstream builds
        (default false)
    :arg bool license-auto-discovery: Tells Artifactory not to try
        and automatically analyze and tag the build's dependencies
        with license information upon deployment (default true)
    :arg bool enable-issue-tracker-integration: When the Jenkins
        JIRA plugin is enabled, synchronize information about JIRA
        issues to Artifactory and attach issue information to build
        artifacts (default false)
    :arg bool aggregate-build-issues: When the Jenkins JIRA plugin
        is enabled, include all issues from previous builds up to the
        latest build status defined in "Aggregation Build Status"
        (default false)
    :arg bool allow-promotion-of-non-staged-builds: The build
        promotion operation will be available to all successful builds
        instead of only staged ones (default false)
    :arg bool filter-excluded-artifacts-from-build: Add the excluded
        files to the excludedArtifacts list and remove them from the
        artifacts list in the build info (default false)
    :arg str scopes:  A list of dependency scopes/configurations to run
        license violation checks on. If left empty all dependencies from
        all scopes will be checked (default '')
    :arg str violation-recipients: Recipients that need to be notified
        of license violations in the build info (default '')
    :arg list matrix-params: Semicolon-separated list of properties to
        attach to all deployed artifacts in addition to the default ones:
        build.name, build.number, and vcs.revision (default [])
    :arg str black-duck-app-name: The existing Black Duck Code Center
        application name (default '')
    :arg str black-duck-app-version: The existing Black Duck Code Center
        application version (default '')
    :arg str black-duck-report-recipients: Recipients that will be emailed
        a report after the automatic Black Duck Code Center compliance checks
        finished (default '')
    :arg str black-duck-scopes: A list of dependency scopes/configurations
        to run Black Duck Code Center compliance checks on. If left empty
        all dependencies from all scopes will be checked (default '')
    :arg bool black-duck-run-checks: Automatic Black Duck Code Center
        compliance checks will occur after the build completes
        (default false)
    :arg bool black-duck-include-published-artifacts: Include the build's
        published module artifacts in the license violation checks if they
        are also used as dependencies for other modules in this build
        (default false)
    :arg bool auto-create-missing-component-requests: Auto create
        missing components in Black Duck Code Center application after
        the build is completed and deployed in Artifactory
        (default true)
    :arg bool auto-discard-stale-component-requests: Auto discard
        stale components in Black Duck Code Center application after
        the build is completed and deployed in Artifactory
        (default true)
    :arg bool deploy-artifacts: Push artifacts to the Artifactory
        Server. Use deployment-include-patterns and
        deployment-exclude-patterns to filter deploy artifacts. (default true)
    :arg list deployment-include-patterns: New line or comma separated mappings
        of build artifacts to published artifacts. Supports Ant-style wildcards
        mapping to target directories. E.g.: */*.zip=>dir (default [])
    :arg list deployment-exclude-patterns: New line or comma separated patterns
        for excluding artifacts from deployment to Artifactory (default [])
    :arg bool env-vars-include: Include all environment variables
        accessible by the build process. Jenkins-specific env variables
        are always included. Use env-vars-include-patterns and
        env-vars-exclude-patterns to filter variables to publish,
        (default false)
    :arg list env-vars-include-patterns: Comma or space-separated list of
        environment variables that will be included as part of the published
        build info. Environment variables may contain the * and the ? wildcards
        (default [])
    :arg list env-vars-exclude-patterns: Comma or space-separated list of
        environment variables that will be excluded from the published
        build info (default [])

    Example:

    .. literalinclude:: /../../tests/publishers/fixtures/artifactory01.yaml

    .. literalinclude:: /../../tests/publishers/fixtures/artifactory02.yaml

    """

    artifactory = XML.SubElement(
        xml_parent, 'org.jfrog.hudson.ArtifactoryRedeployPublisher')

    # optional_props
    helpers.artifactory_optional_props(artifactory, data, 'publishers')

    XML.SubElement(artifactory, 'matrixParams').text = ','.join(
        data.get('matrix-params', []))

    # details
    details = XML.SubElement(artifactory, 'details')
    helpers.artifactory_common_details(details, data)

    XML.SubElement(details, 'repositoryKey').text = data.get(
        'release-repo-key', '')
    XML.SubElement(details, 'snapshotsRepositoryKey').text = data.get(
        'snapshot-repo-key', '')

    plugin = XML.SubElement(details, 'stagingPlugin')
    XML.SubElement(plugin, 'pluginName').text = 'None'

    # artifactDeploymentPatterns
    helpers.artifactory_deployment_patterns(artifactory, data)

    # envVarsPatterns
    helpers.artifactory_env_vars_patterns(artifactory, data)


def test_fairy(registry, xml_parent, data):
    """yaml: test-fairy
    This plugin helps you to upload Android APKs or iOS IPA files to
    www.testfairy.com.

    Requires the Jenkins :jenkins-wiki:`Test Fairy Plugin
    <TestFairy+Plugin>`.

    :arg str platform: Select platform to upload to, **android** or **ios**
        (required)

    Android Only:

    :arg str proguard-file: Path to Proguard file. Path of mapping.txt from
        your proguard output directory. (default '')
    :arg str storepass: Password for the keystore (default android)
    :arg str alias: alias for key (default androiddebugkey)
    :arg str keypass: password for the key (default '')
    :arg str keystorepath: Path to Keystore file (required)

    IOS Only:

    :arg str dSYM-file: Path to .dSYM.zip file (default '')

    All:

    :arg str apikey: TestFairy API_KEY. Find it in your TestFairy account
        settings (required)
    :arg str appfile: Path to App file (.apk) or (.ipa). For example:
        $WORKSPACE/[YOUR_FILE_NAME].apk or full path to the apk file.
        (required)
    :arg str tester-groups: Tester groups to notify (default '')
    :arg bool notify-testers: Send email with changelogs to testers
        (default false)
    :arg bool autoupdate: Automatic update (default false)
    :arg str max-duration: Duration of the session (default 10m)

        :max-duration values:
            * **10m**
            * **60m**
            * **300m**
            * **1440m**
    :arg bool record-on-background: Record on background (default false)
    :arg bool data-only-wifi: Record data only in wifi (default false)
    :arg bool video-enabled: Record video (default true)
    :arg int screenshot-interval: Time interval between screenshots
        (default 1)

        :screenshot-interval values:
            * **1**
            * **2**
            * **5**
    :arg str video-quality: Video quality (default high)

        :video-quality values:
            * **high**
            * **medium**
            * **low**
    :arg bool cpu: Enable CPU metrics (default true)
    :arg bool memory: Enable memory metrics (default true)
    :arg bool logs: Enable logs metrics (default true)
    :arg bool network: Enable network metrics (default false)
    :arg bool phone-signal: Enable phone signal metrics (default false)
    :arg bool wifi: Enable wifi metrics (default false)
    :arg bool gps: Enable gps metrics (default false)
    :arg bool battery: Enable battery metrics (default false)
    :arg bool opengl: Enable opengl metrics (default false)

    Example:

    .. literalinclude::
       /../../tests/publishers/fixtures/test-fairy-android-minimal.yaml
       :language: yaml

    .. literalinclude::
       /../../tests/publishers/fixtures/test-fairy-android001.yaml
       :language: yaml

    .. literalinclude::
       /../../tests/publishers/fixtures/test-fairy-ios-minimal.yaml
       :language: yaml

    .. literalinclude::
       /../../tests/publishers/fixtures/test-fairy-ios001.yaml
       :language: yaml
    """
    platform = data.get('platform')
    valid_platforms = ['android', 'ios']

    if 'platform' not in data:
        raise MissingAttributeError('platform')
    if platform == 'android':
        root = XML.SubElement(
            xml_parent,
            'org.jenkinsci.plugins.testfairy.TestFairyAndroidRecorder')
        helpers.test_fairy_common(root, data)

        mappings = [
            ('proguard-file', 'mappingFile', ''),
            ('keystorepath', 'keystorePath', None),
            ('storepass', 'storepass', 'android'),
            ('alias', 'alias', 'androiddebugkey'),
            ('keypass', 'keypass', '')]
        helpers.convert_mapping_to_xml(
            root, data, mappings, fail_required=True)
    elif platform == 'ios':
        root = XML.SubElement(
            xml_parent, 'org.jenkinsci.plugins.testfairy.TestFairyIosRecorder')
        helpers.test_fairy_common(root, data)

        mappings = [('dSYM-file', 'mappingFile', '')]
        helpers.convert_mapping_to_xml(
            root, data, mappings, fail_required=True)
    else:
        raise InvalidAttributeError('platform', platform, valid_platforms)


def text_finder(registry, xml_parent, data):
    """yaml: text-finder
    This plugin lets you search keywords in the files you specified and
    additionally check build status

    Requires the Jenkins :jenkins-wiki:`Text-finder Plugin
    <Text-finder+Plugin>`.

    :arg str regexp: Specify a regular expression
    :arg str fileset: Specify the path to search
    :arg bool also-check-console-output:
              Search the console output (default false)
    :arg bool succeed-if-found:
              Force a build to succeed if a string was found (default false)
    :arg bool unstable-if-found:
              Set build unstable instead of failing the build (default false)


    Example:

    .. literalinclude:: /../../tests/publishers/fixtures/text-finder001.yaml
       :language: yaml
    """

    finder = XML.SubElement(xml_parent,
                            'hudson.plugins.textfinder.TextFinderPublisher')
    if ('fileset' in data):
        XML.SubElement(finder, 'fileSet').text = data['fileset']
    XML.SubElement(finder, 'regexp').text = data['regexp']
    check_output = str(data.get('also-check-console-output', False)).lower()
    XML.SubElement(finder, 'alsoCheckConsoleOutput').text = check_output
    succeed_if_found = str(data.get('succeed-if-found', False)).lower()
    XML.SubElement(finder, 'succeedIfFound').text = succeed_if_found
    unstable_if_found = str(data.get('unstable-if-found', False)).lower()
    XML.SubElement(finder, 'unstableIfFound').text = unstable_if_found


def html_publisher(registry, xml_parent, data):
    """yaml: html-publisher
    This plugin publishes HTML reports.

    Requires the Jenkins :jenkins-wiki:`HTML Publisher Plugin
    <HTML+Publisher+Plugin>`.

    :arg str name: Report name (required)
    :arg str dir: HTML directory to archive (required)
    :arg str files: Specify the pages to display (required)
    :arg bool keep-all: keep HTML reports for each past build (default false)
    :arg bool allow-missing: Allow missing HTML reports (default false)
    :arg bool link-to-last-build: If this and 'keep-all' both are true, it
        publishes the link on project level even if build failed.
        (default false)


    Example:

    .. literalinclude:: /../../tests/publishers/fixtures/html-publisher001.yaml
       :language: yaml
    """

    reporter = XML.SubElement(xml_parent, 'htmlpublisher.HtmlPublisher')
    targets = XML.SubElement(reporter, 'reportTargets')
    ptarget = XML.SubElement(targets, 'htmlpublisher.HtmlPublisherTarget')

    mapping = [
        ('name', 'reportName', None),
        ('dir', 'reportDir', None),
        ('files', 'reportFiles', None),
        ('link-to-last-build', 'alwaysLinkToLastBuild', False),
        ('keep-all', 'keepAll', False),
        ('allow-missing', 'allowMissing', False),
    ]
    helpers.convert_mapping_to_xml(ptarget, data, mapping, fail_required=True)
    XML.SubElement(ptarget, 'wrapperName').text = "htmlpublisher-wrapper.html"


def rich_text_publisher(registry, xml_parent, data):
    """yaml: rich-text-publisher
    This plugin puts custom rich text message to the Build pages and Job main
    page.

    Requires the Jenkins :jenkins-wiki:`Rich Text Publisher Plugin
    <Rich+Text+Publisher+Plugin>`.

    :arg str stable-text: The stable text (required)
    :arg str unstable-text: The unstable text if different from stable
        (default '')
    :arg bool unstable-as-stable: The same text block is used for stable and
         unstable builds (default true)
    :arg str failed-text: The failed text if different from stable (default '')
    :arg bool failed-as-stable: The same text block is used for stable and
         failed builds (default true)
    :arg str parser-name: HTML, Confluence or WikiText (default 'WikiText')


    Minimal Example:

    .. literalinclude::  /../../tests/publishers/fixtures/richtext-minimal.yaml
       :language: yaml

    Full Example:

    .. literalinclude::
       /../../tests/publishers/fixtures/richtext-complete.yaml
       :language: yaml
    """

    parsers = ['HTML', 'Confluence', 'WikiText']
    reporter = XML.SubElement(
        xml_parent,
        'org.korosoft.jenkins.plugin.rtp.RichTextPublisher')
    reporter.set('plugin', 'rich-text-publisher-plugin')

    mappings = [
        ('stable-text', 'stableText', None),
        ('unstable-text', 'unstableText', ''),
        ('failed-text', 'failedText', ''),
        ('unstable-as-stable', 'unstableAsStable', True),
        ('failed-as-stable', 'failedAsStable', True),
        ('parser-name', 'parserName', 'WikiText', parsers)
    ]
    helpers.convert_mapping_to_xml(
        reporter, data, mappings, fail_required=True)


def tap(registry, xml_parent, data):
    """yaml: tap
    Adds support to TAP test result files

    Requires the Jenkins :jenkins-wiki:`TAP Plugin <TAP+Plugin>`.

    :arg str results: TAP test result files (required)
    :arg bool fail-if-no-results: Fail if no result (default false)
    :arg bool failed-tests-mark-build-as-failure:
                Mark build as failure if test fails (default false)
    :arg bool output-tap-to-console: Output tap to console (default true)
    :arg bool enable-subtests: Enable subtests (default true)
    :arg bool discard-old-reports: Discard old reports (default false)
    :arg bool todo-is-failure: Handle TODO's as failures (default true)
    :arg bool include-comment-diagnostics: Include comment diagnostics (#) in
        the results table (>=1.12) (default false)
    :arg bool validate-tests: Validate number of tests (>=1.13) (default false)
    :arg bool plan-required: TAP plan required? (>=1.17) (default true)
    :arg bool verbose: Print a message for each TAP stream file (>=1.17)
        (default true)
    :arg bool show-only-failures: show only test failures (>=1.17)
        (default false)

    Full Example:

    .. literalinclude:: /../../tests/publishers/fixtures/tap-full.yaml
       :language: yaml

    Minimal Example:

    .. literalinclude:: /../../tests/publishers/fixtures/tap-minimal.yaml
       :language: yaml
    """

    tap = XML.SubElement(xml_parent, 'org.tap4j.plugin.TapPublisher')
    tap.set('plugin', 'tap')

    mappings = [
        ('results', 'testResults', None),
        ('fail-if-no-results', 'failIfNoResults', False),
        ('failed-tests-mark-build-as-failure',
         'failedTestsMarkBuildAsFailure',
         False),
        ('output-tap-to-console', 'outputTapToConsole', True),
        ('enable-subtests', 'enableSubtests', True),
        ('discard-old-reports', 'discardOldReports', False),
        ('todo-is-failure', 'todoIsFailure', True),
        ('include-comment-diagnostics', 'includeCommentDiagnostics', False),
        ('validate-tests', 'validateNumberOfTests', False),
        ('plan-required', 'planRequired', True),
        ('verbose', 'verbose', True),
        ('show-only-failures', 'showOnlyFailures', False),
    ]
    helpers.convert_mapping_to_xml(tap, data, mappings, fail_required=True)


def post_tasks(registry, xml_parent, data):
    """yaml: post-tasks
    Adds support to post build task plugin

    Requires the Jenkins :jenkins-wiki:`Post Build Task plugin
    <Post+build+task>`.

    :arg dict task: Post build task definition
    :arg list task[matches]: list of matches when to run the task
    :arg dict task[matches][*]: match definition
    :arg str task[matches][*][log-text]: text to match against the log
    :arg str task[matches][*][operator]: operator to apply with the next match

        :task[matches][*][operator] values (default 'AND'):
            * **AND**
            * **OR**

    :arg bool task[escalate-status]: Escalate the task status to the job
        (default 'false')
    :arg bool task[run-if-job-successful]: Run only if the job was successful
        (default 'false')
    :arg str task[script]: Shell script to run (default '')

    Example:

    .. literalinclude:: /../../tests/publishers/fixtures/post-tasks001.yaml
       :language: yaml
    """

    pb_xml = XML.SubElement(xml_parent,
                            'hudson.plugins.postbuildtask.PostbuildTask')
    tasks_xml = XML.SubElement(pb_xml, 'tasks')
    for task in data:
        task_xml = XML.SubElement(
            tasks_xml,
            'hudson.plugins.postbuildtask.TaskProperties')
        matches_xml = XML.SubElement(task_xml, 'logTexts')
        for match in task.get('matches', []):
            lt_xml = XML.SubElement(
                matches_xml,
                'hudson.plugins.postbuildtask.LogProperties')
            XML.SubElement(lt_xml, 'logText').text = str(
                match.get('log-text', False) or '')
            XML.SubElement(lt_xml, 'operator').text = str(
                match.get('operator', 'AND')).upper()
        XML.SubElement(task_xml, 'EscalateStatus').text = str(
            task.get('escalate-status', False)).lower()
        XML.SubElement(task_xml, 'RunIfJobSuccessful').text = str(
            task.get('run-if-job-successful', False)).lower()
        XML.SubElement(task_xml, 'script').text = str(
            task.get('script', ''))


def postbuildscript(registry, xml_parent, data):
    """yaml: postbuildscript
    Executes additional builders, script or Groovy after the build is
    complete.

    Requires the Jenkins :jenkins-wiki:`Post Build Script plugin
    <PostBuildScript+Plugin>`.

    :arg list generic-script: Paths to Batch/Shell scripts
    :arg list groovy-script: Paths to Groovy scripts
    :arg list groovy: Inline Groovy
    :arg list builders: Any supported builders, see :doc:`builders`.
    :arg bool onsuccess: Deprecated, replaced with script-only-if-succeeded
    :arg bool script-only-if-succeeded: Scripts and builders are run only if
                                        the build succeeded (default true)
    :arg bool onfailure: Deprecated, replaced with script-only-if-failed
    :arg bool script-only-if-failed: Scripts and builders are run only if the
                                     build failed (default false)
    :arg bool mark-unstable-if-failed: Build will be marked unstable
                                       if job will be successfully completed
                                       but publishing script will return
                                       non zero exit code (default false)
    :arg str execute-on: For matrix projects, scripts can be run after each
                         axis is built (`axes`), after all axis of the matrix
                         are built (`matrix`) or after each axis AND the matrix
                         are built (`both`).

    The `script-only-if-succeeded` and `bool script-only-if-failed` options are
    confusing. If you want the post build to always run regardless of the build
    status, you should set them both to `false`.

    Example:

    .. literalinclude::
        /../../tests/publishers/fixtures/postbuildscript001.yaml
       :language: yaml

    You can also execute :doc:`builders </builders>`:

    .. literalinclude::
        /../../tests/publishers/fixtures/postbuildscript002.yaml
       :language: yaml

    Run once after the whole matrix (all axes) is built:

    .. literalinclude::
        /../../tests/publishers/fixtures/postbuildscript003.yaml
       :language: yaml
    """

    pbs_xml = XML.SubElement(
        xml_parent,
        'org.jenkinsci.plugins.postbuildscript.PostBuildScript')

    # Shell/Groovy in a file
    script_types = {
        'generic-script': 'GenericScript',
        'groovy-script': 'GroovyScriptFile',
    }

    # Assuming yaml preserves order of input data make sure
    # corresponding XML steps are generated in the same order
    build_scripts = [(k, v) for k, v in data.items()
                     if k in script_types or k in ['groovy', 'builders']]

    for step, script_data in build_scripts:
        if step in script_types:
            scripts_xml = XML.SubElement(pbs_xml, step[:-len('-script')] +
                                         'ScriptFileList')
            for shell_script in script_data:
                script_xml = XML.SubElement(
                    scripts_xml,
                    'org.jenkinsci.plugins.postbuildscript.'
                    + script_types[step])
                file_path_xml = XML.SubElement(script_xml, 'filePath')
                file_path_xml.text = shell_script

        # Inlined Groovy
        if step == 'groovy':
            groovy_inline_xml = XML.SubElement(pbs_xml,
                                               'groovyScriptContentList')
            for groovy in script_data:
                groovy_xml = XML.SubElement(
                    groovy_inline_xml,
                    'org.jenkinsci.plugins.postbuildscript.GroovyScriptContent'
                )
                groovy_content = XML.SubElement(groovy_xml, 'content')
                groovy_content.text = groovy

        # Inject builders
        if step == 'builders':
            build_steps_xml = XML.SubElement(pbs_xml, 'buildSteps')
            for builder in script_data:
                registry.dispatch('builder', build_steps_xml, builder)

    # When to run the build? Note the plugin let one specify both options
    # although they are antinomic
    # onsuccess and onfailure parameters are deprecated, this is to keep
    # backwards compatability
    success_xml = XML.SubElement(pbs_xml, 'scriptOnlyIfSuccess')
    if 'script-only-if-succeeded' in data:
        success_xml.text = str(data.get('script-only-if-succeeded',
                                        True)).lower()
    else:
        success_xml.text = str(data.get('onsuccess', True)).lower()

    failure_xml = XML.SubElement(pbs_xml, 'scriptOnlyIfFailure')
    if 'script-only-if-failed' in data:
        failure_xml.text = str(data.get('script-only-if-failed',
                                        False)).lower()
    else:
        failure_xml.text = str(data.get('onfailure', False)).lower()

    # Mark build unstable if publisher script return non zero exit code
    XML.SubElement(pbs_xml, 'markBuildUnstable').text = str(
        data.get('mark-unstable-if-failed', False)).lower()
    # TODO: we may want to avoid setting "execute-on" on non-matrix jobs,
    # either by skipping this part or by raising an error to let the user know
    # an attempt was made to set execute-on on a non-matrix job. There are
    # currently no easy ways to check for this though.
    if 'execute-on' in data:
        valid_values = ('matrix', 'axes', 'both')
        execute_on = data['execute-on'].lower()
        if execute_on not in valid_values:
            raise JenkinsJobsException(
                'execute-on must be one of %s, got %s' %
                valid_values, execute_on
            )
        execute_on_xml = XML.SubElement(pbs_xml, 'executeOn')
        execute_on_xml.text = execute_on.upper()


def xml_summary(registry, xml_parent, data):
    """yaml: xml-summary
    Adds support for the Summary Display Plugin

    Requires the Jenkins :jenkins-wiki:`Summary Display Plugin
    <Summary+Display+Plugin>`.

    :arg str files: Files to parse (required)
    :arg bool shown-on-project-page: Display summary on project page
        (default false)

    Minimal Example:

    .. literalinclude::
       /../../tests/publishers/fixtures/xml-summary-minimal.yaml
       :language: yaml

    Full Example:

    .. literalinclude:: /../../tests/publishers/fixtures/xml-summary-full.yaml
       :language: yaml
    """

    summary = XML.SubElement(
        xml_parent, 'hudson.plugins.summary__report.ACIPluginPublisher')
    summary.set('plugin', 'summary_report')

    mapping = [
        ('files', 'name', None),
        ('shown-on-project-page', 'shownOnProjectPage', False),
    ]
    helpers.convert_mapping_to_xml(summary, data, mapping, fail_required=True)


def robot(registry, xml_parent, data):
    """yaml: robot
    Adds support for the Robot Framework Plugin

    Requires the Jenkins :jenkins-wiki:`Robot Framework Plugin
    <Robot+Framework+Plugin>`.

    :arg str output-path: Path to directory containing robot xml and html files
        relative to build workspace. (required)
    :arg str log-file-link: Name of log or report file to be linked on jobs
        front page (default '')
    :arg str report-html: Name of the html file containing robot test report
        (default 'report.html')
    :arg str log-html: Name of the html file containing detailed robot test log
        (default 'log.html')
    :arg str output-xml: Name of the xml file containing robot output
        (default 'output.xml')
    :arg str pass-threshold: Minimum percentage of passed tests to consider
        the build successful (default 0.0)
    :arg str unstable-threshold: Minimum percentage of passed test to
        consider the build as not failed (default 0.0)
    :arg bool only-critical: Take only critical tests into account when
        checking the thresholds (default true)
    :arg list other-files: list other files to archive (default '')
    :arg bool archive-output-xml: Archive output xml file to server
        (default true)
    :arg bool enable-cache: Enable cache for test results (default true)

    Minimal Example:

    .. literalinclude:: /../../tests/publishers/fixtures/robot-minimal.yaml
       :language: yaml

    Full Example:

    .. literalinclude:: /../../tests/publishers/fixtures/robot-complete.yaml
       :language: yaml
    """
    parent = XML.SubElement(xml_parent, 'hudson.plugins.robot.RobotPublisher')
    parent.set('plugin', 'robot')
    mappings = [
        ('output-path', 'outputPath', None),
        ('log-file-link', 'logFileLink', ''),
        ('report-html', 'reportFileName', 'report.html'),
        ('log-html', 'logFileName', 'log.html'),
        ('output-xml', 'outputFileName', 'output.xml'),
        ('pass-threshold', 'passThreshold', '0.0'),
        ('unstable-threshold', 'unstableThreshold', '0.0'),
        ('only-critical', 'onlyCritical', True),
        ('enable-cache', 'enableCache', True)
    ]
    helpers.convert_mapping_to_xml(parent, data, mappings, fail_required=True)

    other_files = XML.SubElement(parent, 'otherFiles')
    for other_file in data.get('other-files', []):
        XML.SubElement(other_files, 'string').text = str(other_file)
    XML.SubElement(parent, 'disableArchiveOutput').text = str(
        not data.get('archive-output-xml', True)).lower()


def warnings(registry, xml_parent, data):
    """yaml: warnings
    Generate trend report for compiler warnings in the console log or
    in log files. Requires the Jenkins :jenkins-wiki:`Warnings Plugin
    <Warnings+Plugin>`.

    :arg list console-log-parsers: The parser to use to scan the console
        log (default '')
    :arg dict workspace-file-scanners:

        :workspace-file-scanners:
            * **file-pattern** (`str`) -- Fileset 'includes' setting that
                specifies the files to scan for warnings (required)
            * **scanner** (`str`) -- The parser to use to scan the files
                provided in workspace-file-pattern (default '')
    :arg str files-to-include: Comma separated list of regular
        expressions that specifies the files to include in the report
        (based on their absolute filename). By default all files are
        included
    :arg str files-to-ignore: Comma separated list of regular expressions
        that specifies the files to exclude from the report (based on their
        absolute filename). (default '')
    :arg bool run-always: By default, this plug-in runs only for stable or
        unstable builds, but not for failed builds.  Set to true if the
        plug-in should run even for failed builds.  (default false)
    :arg bool detect-modules: Determines if Ant or Maven modules should be
        detected for all files that contain warnings.  Activating this
        option may increase your build time since the detector scans
        the whole workspace for 'build.xml' or 'pom.xml' files in order
        to assign the correct module names. (default false)
    :arg bool resolve-relative-paths: Determines if relative paths in
        warnings should be resolved using a time expensive operation that
        scans the whole workspace for matching files.  Deactivate this
        option if you encounter performance problems.  (default false)
    :arg int health-threshold-high: The upper threshold for the build
        health.  If left empty then no health report is created.  If
        the actual number of warnings is between the provided
        thresholds then the build health is interpolated (default '')
    :arg int health-threshold-low: The lower threshold for the build
        health.  See health-threshold-high.  (default '')
    :arg dict health-priorities: Determines which warning priorities
        should be considered when evaluating the build health (default
        all-priorities)

        :health-priorities values:
          * **priority-high** -- Only priority high
          * **high-and-normal** -- Priorities high and normal
          * **all-priorities** -- All priorities
    :arg dict total-thresholds: If the number of total warnings is greater
        than one of these thresholds then a build is considered as unstable
        or failed, respectively. (default '')

        :total-thresholds:
            * **unstable** (`dict`)
                :unstable: * **total-all** (`int`)
                           * **total-high** (`int`)
                           * **total-normal** (`int`)
                           * **total-low** (`int`)
            * **failed** (`dict`)
                :failed: * **total-all** (`int`)
                         * **total-high** (`int`)
                         * **total-normal** (`int`)
                         * **total-low** (`int`)
    :arg dict new-thresholds: If the specified number of new warnings exceeds
        one of these thresholds then a build is considered as unstable or
        failed, respectively.  (default '')

        :new-thresholds:
            * **unstable** (`dict`)
                :unstable: * **new-all** (`int`)
                           * **new-high** (`int`)
                           * **new-normal** (`int`)
                           * **new-low** (`int`)
            * **failed** (`dict`)
                :failed: * **new-all** (`int`)
                         * **new-high** (`int`)
                         * **new-normal** (`int`)
                         * **new-high** (`int`)
    :arg bool use-delta-for-new-warnings:  If set then the number of new
        warnings is calculated by subtracting the total number of warnings
        of the current build from the reference build. This may lead to wrong
        results if you have both fixed and new warnings in a build. If not set,
        then the number of new warnings is calculated by an asymmetric set
        difference of the warnings in the current and reference build. This
        will find all new warnings even if the number of total warnings is
        decreasing. However, sometimes false positives will be reported due
        to minor changes in a warning (refactoring of variable of method
        names, etc.) (default false)
    :arg bool use-previous-build-as-reference: If set the number of new
        warnings will always be computed based on the previous build, even if
        that build is unstable (due to a violated warning threshold).
        Otherwise the last build that did not violate any given threshold will
        be used as
        reference. It is recommended to uncheck this option if the plug-in
        should ensure that all new warnings will be finally fixed in subsequent
        builds. (default false)
    :arg bool only-use-stable-builds-as-reference: The number of new warnings
        will be calculated based on the last stable build, allowing reverts
        of unstable builds where the number of warnings was decreased.
        (default false)
    :arg str default-encoding: Default encoding when parsing or showing files
        Leave empty to use default encoding of platform (default '')

    Minimal Example:

    .. literalinclude:: /../../tests/publishers/fixtures/warnings-minimal.yaml
       :language: yaml

    Full Example:

    .. literalinclude:: /../../tests/publishers/fixtures/warnings-complete.yaml
       :language: yaml
    """

    warnings = XML.SubElement(xml_parent,
                              'hudson.plugins.warnings.'
                              'WarningsPublisher')
    warnings.set('plugin', 'warnings')
    console = XML.SubElement(warnings, 'consoleParsers')
    for parser in data.get('console-log-parsers', []):
        console_parser = XML.SubElement(console,
                                        'hudson.plugins.warnings.'
                                        'ConsoleParser')
        XML.SubElement(console_parser, 'parserName').text = parser
    workspace = XML.SubElement(warnings, 'parserConfigurations')
    for wfs in data.get('workspace-file-scanners', []):
        workspace_pattern = XML.SubElement(workspace,
                                           'hudson.plugins.warnings.'
                                           'ParserConfiguration')
        workspace_pattern_mappings = [
            ('file-pattern', 'pattern', None),
            ('scanner', 'parserName', '')
        ]
        helpers.convert_mapping_to_xml(workspace_pattern,
                                       wfs,
                                       workspace_pattern_mappings,
                                       fail_required=True)
    prioritiesDict = {'priority-high': 'high',
                      'high-and-normal': 'normal',
                      'all-priorities': 'low'}
    warnings_mappings = [
        ('files-to-include', 'includePattern', ''),
        ('files-to-ignore', 'excludePattern', ''),
        ('plugin-name', 'pluginName', '[WARNINGS]'),
        ('run-always', 'canRunOnFailed', False),
        ('detect-modules', 'shouldDetectModules', False),
        ('health-threshold-high', 'healthy', ''),
        ('health-threshold-low', 'unHealthy', ''),
        ('health-priorities',
         'thresholdLimit',
         'all-priorities',
         prioritiesDict),
        ('default-encoding', 'defaultEncoding', '')
    ]
    helpers.convert_mapping_to_xml(
        warnings, data, warnings_mappings, fail_required=True)
    # Note the logic reversal (included here to match the GUI)
    XML.SubElement(warnings, 'doNotResolveRelativePaths').text = str(
        not data.get('resolve-relative-paths', False)).lower()
    td = XML.SubElement(warnings, 'thresholds')
    for base in ["total", "new"]:
        thresholds = data.get("%s-thresholds" % base, {})
        for status in ["unstable", "failed"]:
            bystatus = thresholds.get(status, {})
            for level in ["all", "high", "normal", "low"]:
                val = str(bystatus.get("%s-%s" % (base, level), ''))
                XML.SubElement(td, "%s%s%s" % (status,
                               base.capitalize(), level.capitalize())
                               ).text = val
    if data.get('new-thresholds'):
        XML.SubElement(warnings, 'dontComputeNew').text = 'false'
        delta = data.get('use-delta-for-new-warnings', False)
        XML.SubElement(warnings, 'useDeltaValues').text = str(delta).lower()
        use_previous_build = data.get('use-previous-build-as-reference', False)
        XML.SubElement(warnings, 'usePreviousBuildAsReference').text = str(
            use_previous_build).lower()
        use_stable_builds = data.get('only-use-stable-builds-as-reference',
                                     False)
        XML.SubElement(warnings, 'useStableBuildAsReference').text = str(
            use_stable_builds).lower()
    else:
        XML.SubElement(warnings, 'dontComputeNew').text = 'true'
        XML.SubElement(warnings, 'useDeltaValues').text = 'false'
        XML.SubElement(warnings, 'usePreviousBuildAsReference').text = 'false'
        XML.SubElement(warnings, 'useStableBuildAsReference').text = 'false'


def sloccount(registry, xml_parent, data):
    """yaml: sloccount
    Generates the trend report for SLOCCount

    Requires the Jenkins :jenkins-wiki:`SLOCCount Plugin <SLOCCount+Plugin>`.

    :arg str report-files: Setting that specifies the generated raw
        SLOCCount report files. Be sure not to include any non-report files
        into this pattern. The report files must have been generated by
        sloccount using the "--wide --details" options.
        (default '\*\*/sloccount.sc')
    :arg str charset: The character encoding to be used to read the SLOCCount
        result files. (default 'UTF-8')
    :arg int builds-in-graph: Maximal number of last successful builds, that
        are displayed in the trend graphs. (default 0)
    :arg bool comment-is-code: This option is considered only in the cloc
        report parser and is ignored in the SLOCCount one. (default false)
    :arg bool ignore-build-failure: Try to process the report files even if
        the build is not successful. (default false)

    Minimal Example:

    .. literalinclude:: /../../tests/publishers/fixtures/sloccount-minimal.yaml
       :language: yaml

    Full Example:

    .. literalinclude::
       /../../tests/publishers/fixtures/sloccount-complete.yaml
       :language: yaml
    """
    top = XML.SubElement(xml_parent,
                         'hudson.plugins.sloccount.SloccountPublisher')
    top.set('plugin', 'sloccount')
    mappings = [
        ('report-files', 'pattern', '**/sloccount.sc'),
        ('charset', 'encoding', 'UTF-8'),
        ('builds-in-graph', 'numBuildsInGraph', 0),
        ('comment-is-code', 'commentIsCode', False),
        ('ignore-build-failure', 'ignoreBuildFailure', False)
    ]
    helpers.convert_mapping_to_xml(top, data, mappings, fail_required=True)


def ircbot(registry, xml_parent, data):
    """yaml: ircbot
    ircbot enables Jenkins to send build notifications via IRC and lets you
    interact with Jenkins via an IRC bot.

    Requires the Jenkins :jenkins-wiki:`IRC Plugin <IRC+Plugin>`.

    :arg string strategy: When to send notifications

        :strategy values:
            * **all** always (default)
            * **any-failure** on any failure
            * **failure-and-fixed** on failure and fixes
            * **new-failure-and-fixed** on new failure and fixes
            * **statechange-only** only on state change
    :arg bool notify-start: Whether to send notifications to channels when a
                           build starts
                           (default false)
    :arg bool notify-committers: Whether to send notifications to the users
                                that are suspected of having broken this build
                                (default false)
    :arg bool notify-culprits: Also send notifications to 'culprits' from
                              previous unstable/failed builds
                              (default false)
    :arg bool notify-upstream: Whether to send notifications to upstream
                              committers if no committers were found for a
                              broken build
                              (default false)
    :arg bool notify-fixers: Whether to send notifications to the users that
                            have fixed a broken build
                            (default false)
    :arg string message-type: Channel Notification Message.

        :message-type values:
            * **summary-scm** for summary and SCM changes (default)
            * **summary** for summary only
            * **summary-params** for summary and build parameters
            * **summary-scm-fail** for summary, SCM changes, failures)
    :arg list channels: list channels definitions
                        If empty, it takes channel from Jenkins configuration.
                        (default empty)
                        WARNING: the IRC plugin requires the channel to be
                        configured in the system wide configuration or the jobs
                        will fail to emit notifications to the channel

        :Channel: * **name** (`str`) Channel name
                  * **password** (`str`) Channel password (optional)
                  * **notify-only** (`bool`) Set to true if you want to
                    disallow bot commands (default false)
    :arg string matrix-notifier: notify for matrix projects
                                 instant-messaging-plugin injects an additional
                                 field in the configuration form whenever the
                                 project is a multi-configuration project

        :matrix-notifier values:
            * **all**
            * **only-configurations** (default)
            * **only-parent**

    Example:

    .. literalinclude:: /../../tests/publishers/fixtures/ircbot001.yaml
       :language: yaml
    """
    top = XML.SubElement(xml_parent, 'hudson.plugins.ircbot.IrcPublisher')
    message_dict = {'summary-scm': 'DefaultBuildToChatNotifier',
                    'summary': 'SummaryOnlyBuildToChatNotifier',
                    'summary-params': 'BuildParametersBuildToChatNotifier',
                    'summary-scm-fail': 'PrintFailingTestsBuildToChatNotifier'}
    message = data.get('message-type', 'summary-scm')
    if message not in message_dict:
        raise JenkinsJobsException("message-type entered is not valid, must "
                                   "be one of: %s" %
                                   ", ".join(message_dict.keys()))
    message = "hudson.plugins.im.build_notify." + message_dict.get(message)
    XML.SubElement(top, 'buildToChatNotifier', attrib={'class': message})
    strategy_dict = {'all': 'ALL',
                     'any-failure': 'ANY_FAILURE',
                     'failure-and-fixed': 'FAILURE_AND_FIXED',
                     'new-failure-and-fixed': 'NEW_FAILURE_AND_FIXED',
                     'statechange-only': 'STATECHANGE_ONLY'}
    strategy = data.get('strategy', 'all')
    if strategy not in strategy_dict:
        raise JenkinsJobsException("strategy entered is not valid, must be "
                                   "one of: %s" %
                                   ", ".join(strategy_dict.keys()))
    XML.SubElement(top, 'strategy').text = strategy_dict.get(strategy)
    targets = XML.SubElement(top, 'targets')
    channels = data.get('channels', [])
    for channel in channels:
        sub = XML.SubElement(targets,
                             'hudson.plugins.im.GroupChatIMMessageTarget')
        XML.SubElement(sub, 'name').text = channel.get('name')
        XML.SubElement(sub, 'password').text = channel.get('password')
        XML.SubElement(sub, 'notificationOnly').text = str(
            channel.get('notify-only', False)).lower()
    XML.SubElement(top, 'notifyOnBuildStart').text = str(
        data.get('notify-start', False)).lower()
    XML.SubElement(top, 'notifySuspects').text = str(
        data.get('notify-committers', False)).lower()
    XML.SubElement(top, 'notifyCulprits').text = str(
        data.get('notify-culprits', False)).lower()
    XML.SubElement(top, 'notifyFixers').text = str(
        data.get('notify-fixers', False)).lower()
    XML.SubElement(top, 'notifyUpstreamCommitters').text = str(
        data.get('notify-upstream', False)).lower()
    matrix_dict = {'all': 'ALL',
                   'only-configurations': 'ONLY_CONFIGURATIONS',
                   'only-parent': 'ONLY_PARENT'}
    matrix = data.get('matrix-notifier', 'only-configurations')
    if matrix not in matrix_dict:
        raise JenkinsJobsException("matrix-notifier entered is not valid, "
                                   "must be one of: %s" %
                                   ", ".join(matrix_dict.keys()))
    XML.SubElement(top, 'matrixMultiplier').text = matrix_dict.get(matrix)


def plot(registry, xml_parent, data):
    """yaml: plot
    Plot provides generic plotting (or graphing).

    Requires the Jenkins :jenkins-wiki:`Plot Plugin <Plot+Plugin>`.

    :arg str title: title for the graph (default '')
    :arg str yaxis: title of Y axis (default '')
    :arg int width: the width of the plot in pixels (default 750)
    :arg int height: the height of the plot in pixels (default 450)
    :arg str group: name of the group to which the plot belongs (required)
    :arg int num-builds: number of builds to plot across
        (default plot all builds)
    :arg str style:  Specifies the graph style of the plot
        Can be: area, bar, bar3d, line, line3d, stackedArea, stackedbar,
        stackedbar3d, waterfall (default 'line')
    :arg bool use-description: When false, the X-axis labels are formed using
        build numbers and dates, and the corresponding tooltips contain the
        build descriptions. When enabled, the contents of the labels and
        tooltips are swapped, with the descriptions used as X-axis labels and
        the build number and date used for tooltips. (default false)
    :arg bool exclude-zero-yaxis: When false, Y-axis contains the value zero
        even if it is not included in the data series. When true, the value
        zero is not automatically included. (default false)
    :arg bool logarithmic-yaxis: When true, the Y-axis will use a logarithmic
        scale. By default, the Y-axis uses a linear scale. (default false)
    :arg bool keep-records: When true, show all builds up to 'Number of
        builds to include'. (default false)
    :arg str csv-file-name: Use for choosing the file name in which the data
        will be persisted. If none specified and random name is generated as
        done in the Jenkins Plot plugin. (default random generated .csv
        filename, same behaviour as the Jenkins Plot plugin)
    :arg list series: list data series definitions

      :Serie: * **file** (`str`) : files to include
              * **inclusion-flag** filtering mode for CSV files. Possible
                values are:

                  * **off** (default)
                  * **include-by-string**
                  * **exclude-by-string**
                  * **include-by-column**
                  * **exclude-by-column**

              * **exclude** (`str`) : exclude pattern for CSV file.
              * **url** (`str`) : for 'csv' and 'xml' file types
                used when you click on a point (default empty)
              * **display-table** (`bool`) : for 'csv' file type
                if true, original CSV will be shown above plot (default false)
              * **label** (`str`) : used by 'properties' file type
                Specifies the legend label for this data series.
                (default empty)
              * **format** (`str`) : Type of file where we get datas.
                Can be: properties, csv, xml
              * **xpath-type** (`str`) : The result type of the expression must
                be supplied due to limitations in the java.xml.xpath parsing.
                The result can be: node, nodeset, boolean, string, or number.
                Strings and numbers will be converted to double. Boolean will
                be converted to 1 for true, and 0 for false. (default 'node')
              * **xpath** (`str`) : used by 'xml' file type
                Xpath which selects the values that should be plotted.


    Example:

    .. literalinclude:: /../../tests/publishers/fixtures/plot004.yaml
       :language: yaml

    .. literalinclude:: /../../tests/publishers/fixtures/plot005.yaml
       :language: yaml
    """
    top = XML.SubElement(xml_parent, 'hudson.plugins.plot.PlotPublisher')
    plots = XML.SubElement(top, 'plots')
    format_dict = {'properties': 'hudson.plugins.plot.PropertiesSeries',
                   'csv': 'hudson.plugins.plot.CSVSeries',
                   'xml': 'hudson.plugins.plot.XMLSeries'}
    xpath_dict = {'nodeset': 'NODESET', 'node': 'NODE', 'string': 'STRING',
                  'boolean': 'BOOLEAN', 'number': 'NUMBER'}
    inclusion_dict = {'off': 'OFF',
                      'include-by-string': 'INCLUDE_BY_STRING',
                      'exclude-by-string': 'EXCLUDE_BY_STRING',
                      'include-by-column': 'INCLUDE_BY_COLUMN',
                      'exclude-by-column': 'EXCLUDE_BY_COLUMN'}
    for plot in data:
        plugin = XML.SubElement(plots, 'hudson.plugins.plot.Plot')
        XML.SubElement(plugin, 'title').text = plot.get('title', '')
        XML.SubElement(plugin, 'yaxis').text = plot['yaxis']
        XML.SubElement(plugin, 'width').text = str(plot.get('width', '750'))
        XML.SubElement(plugin, 'height').text = str(plot.get('height', '450'))
        XML.SubElement(plugin, 'csvFileName').text = \
            plot.get('csv-file-name', '%s.csv' % random.randrange(2 << 32))
        topseries = XML.SubElement(plugin, 'series')
        series = plot['series']
        for serie in series:
            format_data = serie.get('format')
            if format_data not in format_dict:
                raise JenkinsJobsException("format entered is not valid, must "
                                           "be one of: %s" %
                                           " , ".join(format_dict.keys()))
            subserie = XML.SubElement(topseries, format_dict.get(format_data))
            XML.SubElement(subserie, 'file').text = serie.get('file')
            if format_data == 'properties':
                XML.SubElement(subserie, 'label').text = serie.get('label', '')
            if format_data == 'csv':
                inclusion_flag = serie.get('inclusion-flag', 'off')
                if inclusion_flag not in inclusion_dict:
                    raise JenkinsJobsException("Inclusion flag result entered "
                                               "is not valid, must be one of: "
                                               "%s"
                                               % ", ".join(inclusion_dict))
                XML.SubElement(subserie, 'inclusionFlag').text = \
                    inclusion_dict.get(inclusion_flag)
                XML.SubElement(subserie, 'exclusionValues').text = \
                    serie.get('exclude', '')
                if serie.get('exclude', ''):
                    exclude_strings = serie.get('exclude', '').split(',')
                    exclusionset = XML.SubElement(subserie, 'strExclusionSet')
                    for exclude_string in exclude_strings:
                        XML.SubElement(exclusionset, 'string').text = \
                            exclude_string
                XML.SubElement(subserie, 'url').text = serie.get('url', '')
                XML.SubElement(subserie, 'displayTableFlag').text = \
                    str(serie.get('display-table', False)).lower()
            if format_data == 'xml':
                XML.SubElement(subserie, 'url').text = serie.get('url', '')
                XML.SubElement(subserie, 'xpathString').text = \
                    serie.get('xpath')
                xpathtype = serie.get('xpath-type', 'node')
                if xpathtype not in xpath_dict:
                    raise JenkinsJobsException("XPath result entered is not "
                                               "valid, must be one of: %s" %
                                               ", ".join(xpath_dict))
                XML.SubElement(subserie, 'nodeTypeString').text = \
                    xpath_dict.get(xpathtype)
            XML.SubElement(subserie, 'fileType').text = serie.get('format')

        mappings = [
            ('group', 'group', None),
            ('use-description', 'useDescr', False),
            ('exclude-zero-yaxis', 'exclZero', False),
            ('logarithmic-yaxis', 'logarithmic', False),
            ('keep-records', 'keepRecords', False),
            ('num-builds', 'numBuilds', '')]
        helpers.convert_mapping_to_xml(
            plugin, plot, mappings, fail_required=True)

        style_list = ['area', 'bar', 'bar3d', 'line', 'line3d', 'stackedArea',
                      'stackedbar', 'stackedbar3d', 'waterfall']
        style = plot.get('style', 'line')
        if style not in style_list:
            raise JenkinsJobsException("style entered is not valid, must be "
                                       "one of: %s" % ", ".join(style_list))
        XML.SubElement(plugin, 'style').text = style


def git(registry, xml_parent, data):
    """yaml: git
    This plugin will configure the Jenkins Git plugin to
    push merge results, tags, and/or branches to
    remote repositories after the job completes.

    Requires the Jenkins :jenkins-wiki:`Git Plugin <Git+Plugin>`.

    :arg bool push-merge: push merges back to the origin specified in the
                          pre-build merge options (default false)
    :arg bool push-only-if-success: Only push to remotes if the build succeeds
                                    - otherwise, nothing will be pushed.
                                    (default true)
    :arg bool force-push: Add force option to git push (default false)
    :arg list tags: tags to push at the completion of the build

        :tag: * **remote** (`str`) remote repo name to push to
                (default 'origin')
              * **name** (`str`) name of tag to push
              * **message** (`str`) message content of the tag
              * **create-tag** (`bool`) whether or not to create the tag
                after the build, if this is False then the tag needs to
                exist locally (default false)
              * **update-tag** (`bool`) whether to overwrite a remote tag
                or not (default false)

    :arg list branches: branches to push at the completion of the build

        :branch: * **remote** (`str`) remote repo name to push to
                   (default 'origin')
                 * **name** (`str`) name of remote branch to push to

    :arg list notes: notes to push at the completion of the build

        :note: * **remote** (`str`) remote repo name to push to
                 (default 'origin')
               * **message** (`str`) content of the note
               * **namespace** (`str`) namespace of the note
                 (default master)
               * **replace-note** (`bool`) whether to overwrite a note or not
                 (default false)


    Example:

    .. literalinclude:: /../../tests/publishers/fixtures/git001.yaml
       :language: yaml
    """
    mappings = [('push-merge', 'pushMerge', False),
                ('push-only-if-success', 'pushOnlyIfSuccess', True),
                ('force-push', 'forcePush', False)]

    tag_mappings = [('remote', 'targetRepoName', 'origin'),
                    ('name', 'tagName', None),
                    ('message', 'tagMessage', ''),
                    ('create-tag', 'createTag', False),
                    ('update-tag', 'updateTag', False)]

    branch_mappings = [('remote', 'targetRepoName', 'origin'),
                       ('name', 'branchName', None)]

    note_mappings = [('remote', 'targetRepoName', 'origin'),
                     ('message', 'noteMsg', None),
                     ('namespace', 'noteNamespace', 'master'),
                     ('replace-note', 'noteReplace', False)]

    top = XML.SubElement(xml_parent, 'hudson.plugins.git.GitPublisher')
    XML.SubElement(top, 'configVersion').text = '2'
    helpers.convert_mapping_to_xml(top, data, mappings, fail_required=True)

    tags = data.get('tags', [])
    if tags:
        xml_tags = XML.SubElement(top, 'tagsToPush')
        for tag in tags:
            xml_tag = XML.SubElement(
                xml_tags,
                'hudson.plugins.git.GitPublisher_-TagToPush')
            helpers.convert_mapping_to_xml(
                xml_tag, tag['tag'], tag_mappings, fail_required=True)

    branches = data.get('branches', [])
    if branches:
        xml_branches = XML.SubElement(top, 'branchesToPush')
        for branch in branches:
            xml_branch = XML.SubElement(
                xml_branches,
                'hudson.plugins.git.GitPublisher_-BranchToPush')
            helpers.convert_mapping_to_xml(xml_branch,
                                           branch['branch'],
                                           branch_mappings,
                                           fail_required=True)

    notes = data.get('notes', [])
    if notes:
        xml_notes = XML.SubElement(top, 'notesToPush')
        for note in notes:
            xml_note = XML.SubElement(
                xml_notes,
                'hudson.plugins.git.GitPublisher_-NoteToPush')
            helpers.convert_mapping_to_xml(
                xml_note, note['note'], note_mappings, fail_required=True)


def github_notifier(registry, xml_parent, data):
    """yaml: github-notifier
    Set build status on Github commit.
    Requires the Jenkins :jenkins-wiki:`Github Plugin <GitHub+Plugin>`.

    Example:

    .. literalinclude:: /../../tests/publishers/fixtures/github-notifier.yaml
       :language: yaml
    """
    XML.SubElement(xml_parent,
                   'com.cloudbees.jenkins.GitHubCommitNotifier')


def gitlab_notifier(registry, xml_parent, data):
    """yaml: gitlab-notifier
    Set build status on GitLab commit.
    Requires the Jenkins :jenkins-wiki:`GitLab Plugin <GitLab+Plugin>`.

    Example:

    .. literalinclude:: /../../tests/publishers/fixtures/gitlab-notifier.yaml
       :language: yaml
    """
    XML.SubElement(
        xml_parent,
        'com.dabsquared.gitlabjenkins.publisher.GitLabCommitStatusPublisher')


def zulip(registry, xml_parent, data):
    """yaml: zulip
    Set build status on zulip.
    Requires the Jenkins :jenkins-wiki:`Humbug Plugin <Humbug+Plugin>`.

    Example:

    .. literalinclude:: /../../tests/publishers/fixtures/zulip.yaml
       :language: yaml
    """
    XML.SubElement(xml_parent,
                   'hudson.plugins.humbug.HumbugNotifier')


def build_publisher(registry, xml_parent, data):
    """yaml: build-publisher
    This plugin allows records from one Jenkins to be published
    on another Jenkins.

    Requires the Jenkins :jenkins-wiki:`Build Publisher Plugin
    <Build+Publisher+Plugin>`.

    :arg bool publish-unstable-builds: publish unstable builds (default true)
    :arg bool publish-failed-builds: publish failed builds (default true)
    :arg int days-to-keep: days to keep when publishing results (optional)
    :arg int num-to-keep: number of jobs to keep in the published results
      (optional)

    Example:

    .. literalinclude::
        /../../tests/publishers/fixtures/build-publisher002.yaml
       :language: yaml
    """

    reporter = XML.SubElement(
        xml_parent,
        'hudson.plugins.build__publisher.BuildPublisher')

    XML.SubElement(reporter, 'publishUnstableBuilds').text = \
        str(data.get('publish-unstable-builds', True)).lower()
    XML.SubElement(reporter, 'publishFailedBuilds').text = \
        str(data.get('publish-failed-builds', True)).lower()

    if 'days-to-keep' in data or 'num-to-keep' in data:
        logrotator = XML.SubElement(reporter, 'logRotator')
        XML.SubElement(logrotator, 'daysToKeep').text = \
            str(data.get('days-to-keep', -1))
        XML.SubElement(logrotator, 'numToKeep').text = \
            str(data.get('num-to-keep', -1))
        # hardcoded to -1 to emulate what the build publisher
        # plugin seem to do.
        XML.SubElement(logrotator, 'artifactDaysToKeep').text = "-1"
        XML.SubElement(logrotator, 'artifactNumToKeep').text = "-1"


def stash(registry, xml_parent, data):
    """yaml: stash
    This plugin will configure the Jenkins Stash Notifier plugin to
    notify Atlassian Stash after job completes.

    Requires the Jenkins :jenkins-wiki:`StashNotifier Plugin
    <StashNotifier+Plugin>`.

    :arg string url: Base url of Stash Server (default "")
    :arg string username: Username of Stash Server (default "")
    :arg string password: Password of Stash Server (default "")
    :arg string credentials-id: Credentials of Stash Server (optional)
    :arg bool   ignore-ssl: Ignore unverified SSL certificate (default false)
    :arg string commit-sha1: Commit SHA1 to notify (default "")
    :arg bool   include-build-number: Include build number in key
                (default false)

    Example:

    .. literalinclude:: /../../tests/publishers/fixtures/stash001.yaml
       :language: yaml
    """
    top = XML.SubElement(xml_parent,
                         'org.jenkinsci.plugins.stashNotifier.StashNotifier')

    XML.SubElement(top, 'stashServerBaseUrl').text = data.get('url', '')
    if data.get('credentials-id') is not None:
        XML.SubElement(top, 'credentialsId').text = str(
            data.get('credentials-id'))
    else:
        XML.SubElement(top, 'stashUserName'
                       ).text = helpers.get_value_from_yaml_or_config_file(
                           'username', 'stash', data, registry.jjb_config)
        XML.SubElement(top, 'stashUserPassword'
                       ).text = helpers.get_value_from_yaml_or_config_file(
                           'password', 'stash', data, registry.jjb_config)

    XML.SubElement(top, 'ignoreUnverifiedSSLPeer').text = str(
        data.get('ignore-ssl', False)).lower()
    XML.SubElement(top, 'commitSha1').text = data.get('commit-sha1', '')
    XML.SubElement(top, 'includeBuildNumberInKey').text = str(
        data.get('include-build-number', False)).lower()


def dependency_check(registry, xml_parent, data):
    """yaml: dependency-check
    Dependency-Check is an open source utility that identifies project
    dependencies and checks if there are any known, publicly disclosed,
    vulnerabilities.

    Requires the Jenkins :jenkins-wiki:`OWASP Dependency-Check Plugin
    <OWASP+Dependency-Check+Plugin>`.

    :arg str pattern: Report filename pattern (optional)
    :arg bool can-run-on-failed: Also runs for failed builds, instead of just
      stable or unstable builds (default false)
    :arg bool should-detect-modules: Determines if Ant or Maven modules should
      be detected for all files that contain warnings (default false)
    :arg int healthy: Sunny threshold (optional)
    :arg int unhealthy: Stormy threshold (optional)
    :arg str health-threshold: Threshold priority for health status
      ('low', 'normal' or 'high', defaulted to 'low')
    :arg dict thresholds: Mark build as failed or unstable if the number of
      errors exceeds a threshold. (optional)

        :thresholds:
            * **unstable** (`dict`)
                :unstable: * **total-all** (`int`)
                           * **total-high** (`int`)
                           * **total-normal** (`int`)
                           * **total-low** (`int`)
                           * **new-all** (`int`)
                           * **new-high** (`int`)
                           * **new-normal** (`int`)
                           * **new-low** (`int`)

            * **failed** (`dict`)
                :failed: * **total-all** (`int`)
                         * **total-high** (`int`)
                         * **total-normal** (`int`)
                         * **total-low** (`int`)
                         * **new-all** (`int`)
                         * **new-high** (`int`)
                         * **new-normal** (`int`)
                         * **new-low** (`int`)
    :arg str default-encoding: Encoding for parsing or showing files (optional)
    :arg bool do-not-resolve-relative-paths: (default false)
    :arg bool dont-compute-new: If set to false, computes new warnings based on
      the reference build (default true)
    :arg bool use-previous-build-as-reference: determines whether to always
        use the previous build as the reference build (default false)
    :arg bool use-stable-build-as-reference: The number of new warnings will be
      calculated based on the last stable build, allowing reverts of unstable
      builds where the number of warnings was decreased. (default false)
    :arg bool use-delta-values: If set then the number of new warnings is
      calculated by subtracting the total number of warnings of the current
      build from the reference build.
      (default false)

    Example:

    .. literalinclude::
        /../../tests/publishers/fixtures/dependency-check001.yaml
       :language: yaml
    """

    dependency_check = XML.SubElement(
        xml_parent,
        'org.jenkinsci.plugins.DependencyCheck.DependencyCheckPublisher')

    # trends
    helpers.build_trends_publisher(
        '[DEPENDENCYCHECK] ', dependency_check, data)


def description_setter(registry, xml_parent, data):
    """yaml: description-setter
    This plugin sets the description for each build,
    based upon a RegEx test of the build log file.

    Requires the Jenkins :jenkins-wiki:`Description Setter Plugin
    <Description+Setter+Plugin>`.

    :arg str regexp: A RegEx which is used to scan the build log file
    :arg str regexp-for-failed: A RegEx which is used for failed builds
        (optional)
    :arg str description: The description to set on the build (optional)
    :arg str description-for-failed: The description to set on
        the failed builds (optional)
    :arg bool set-for-matrix: Also set the description on
        a multi-configuration build (default false)

    Example:

    .. literalinclude::
        /../../tests/publishers/fixtures/description-setter001.yaml
       :language: yaml
    """

    descriptionsetter = XML.SubElement(
        xml_parent,
        'hudson.plugins.descriptionsetter.DescriptionSetterPublisher')
    XML.SubElement(descriptionsetter, 'regexp').text = data.get('regexp', '')
    XML.SubElement(descriptionsetter, 'regexpForFailed').text = \
        data.get('regexp-for-failed', '')
    if 'description' in data:
        XML.SubElement(descriptionsetter, 'description').text = \
            data['description']
    if 'description-for-failed' in data:
        XML.SubElement(descriptionsetter, 'descriptionForFailed').text = \
            data['description-for-failed']
    for_matrix = str(data.get('set-for-matrix', False)).lower()
    XML.SubElement(descriptionsetter, 'setForMatrix').text = for_matrix


def doxygen(registry, xml_parent, data):
    """yaml: doxygen
    This plugin parses the Doxygen descriptor (Doxyfile) and provides a link to
    the generated Doxygen documentation.

    Requires the Jenkins :jenkins-wiki:`Doxygen Plugin <Doxygen+Plugin>`.

    :arg str doxyfile: The doxyfile path
    :arg str slave: The node or label to pull the doxygen HTML files from
    :arg bool keep-all: Retain doxygen generation for each successful build
        (default false)
    :arg str folder: Folder where you run doxygen (default '')

    Example:

    .. literalinclude:: /../../tests/publishers/fixtures/doxygen001.yaml
       :language: yaml
    """

    logger = logging.getLogger(__name__)
    p = XML.SubElement(xml_parent, 'hudson.plugins.doxygen.DoxygenArchiver')
    if not data.get('doxyfile'):
        raise JenkinsJobsException('The path to a doxyfile must be specified.')
    XML.SubElement(p, 'doxyfilePath').text = str(data.get('doxyfile'))
    XML.SubElement(p, 'runOnChild').text = str(data.get('slave', ''))
    # backward compatibility
    if 'keepall' in data:
        if 'keep-all' in data:
            XML.SubElement(p, 'keepAll').text = str(
                data.get('keep-all', False)).lower()
            logger.warning("The value of 'keepall' will be ignored "
                           "in preference to 'keep-all'.")
        else:
            XML.SubElement(p, 'keepAll').text = str(
                data.get('keepall', False)).lower()
            logger.warning("'keepall' is deprecated please use 'keep-all'")
    else:
        XML.SubElement(p, 'keepAll').text = str(
            data.get('keep-all', False)).lower()
    XML.SubElement(p, 'folderWhereYouRunDoxygen').text = str(
        data.get('folder', ''))


def sitemonitor(registry, xml_parent, data):
    """yaml: sitemonitor
    This plugin checks the availability of an url.

    It requires the :jenkins-wiki:`sitemonitor plugin <SiteMonitor+Plugin>`.

    :arg list sites: List of URLs to check

    Example:

    .. literalinclude:: /../../tests/publishers/fixtures/sitemonitor001.yaml
       :language: yaml
    """
    mon = XML.SubElement(xml_parent,
                         'hudson.plugins.sitemonitor.SiteMonitorRecorder')
    if data.get('sites'):
        sites = XML.SubElement(mon, 'mSites')
        for siteurl in data.get('sites'):
            site = XML.SubElement(sites,
                                  'hudson.plugins.sitemonitor.model.Site')
            XML.SubElement(site, 'mUrl').text = siteurl['url']


def testng(registry, xml_parent, data):
    """yaml: testng
    This plugin publishes TestNG test reports.

    Requires the Jenkins :jenkins-wiki:`TestNG Results Plugin <testng-plugin>`.

    :arg str pattern: filename pattern to locate the TestNG XML report files
        (required)
    :arg bool escape-test-description: escapes the description string
      associated with the test method while displaying test method details
      (default true)
    :arg bool escape-exception-msg: escapes the test method's exception
      messages. (default true)
    :arg bool fail-on-failed-test-config: Allows for a distinction between
        failing tests and failing configuration methods (>=1.10) (default
        false)
    :arg bool show-failed-builds: include results from failed builds in the
        trend graph (>=1.6) (default false)
    :arg int unstable-skips: Build is marked UNSTABLE if the number/percentage
        of skipped tests exceeds the specified threshold (>=1.11) (default 100)
    :arg int unstable-fails: Build is marked UNSTABLE if the number/percentage
        of failed tests exceeds the specified threshold (>=1.11) (default 0)
    :arg int failed-skips: Build is marked FAILURE if the number/percentage of
        skipped tests exceeds the specified threshold (>=1.11) (default 100)
    :arg int failed-fails: Build is marked FAILURE if the number/percentage of
        failed tests exceeds the specified threshold (>=1.11) (default 100)
    :arg str threshold-mode: Interpret threshold as number of tests or
        percentage of tests (>=1.11) (default percentage)

    Full Example:

    .. literalinclude:: /../../tests/publishers/fixtures/testng-full.yaml
       :language: yaml

    Minimal Example:

    .. literalinclude:: /../../tests/publishers/fixtures/testng-minimal.yaml
       :language: yaml
    """

    reporter = XML.SubElement(xml_parent, 'hudson.plugins.testng.Publisher')
    reporter.set('plugin', 'testng-plugin')
    threshold_modes = {
        'number': 1,
        'percentage': 2}

    mappings = [
        ('pattern', 'reportFilenamePattern', None),
        ('escape-test-description', 'escapeTestDescp', True),
        ('escape-exception-msg', 'escapeExceptionMsg', True),
        ('fail-on-failed-test-config', 'failureOnFailedTestConfig', False),
        ('show-failed-builds', 'showFailedBuilds', False),
        ('unstable-skips', 'unstableSkips', 100),
        ('unstable-fails', 'unstableFails', 0),
        ('failed-skips', 'failedSkips', 100),
        ('failed-fails', 'failedFails', 100),
        ('threshold-mode', 'thresholdMode', 'percentage', threshold_modes)
    ]
    helpers.convert_mapping_to_xml(
        reporter, data, mappings, fail_required=True)


def artifact_deployer(registry, xml_parent, data):
    """yaml: artifact-deployer
    This plugin makes it possible to copy artifacts to remote locations.

    Requires the Jenkins :jenkins-wiki:`ArtifactDeployer Plugin
    <ArtifactDeployer+Plugin>`.

    :arg list entries:
        :entries:
            * **files** (`str`) - files to deploy
            * **basedir** (`str`) - the dir from files are deployed
            * **excludes** (`str`) - the mask to exclude files
            * **remote** (`str`) - a remote output directory
            * **flatten** (`bool`) - ignore the source directory structure
              (default false)
            * **delete-remote** (`bool`) - clean-up remote directory
              before deployment (default false)
            * **delete-remote-artifacts** (`bool`) - delete remote artifacts
              when the build is deleted (default false)
            * **fail-no-files** (`bool`) - fail build if there are no files
              (default false)
            * **groovy-script** (`str`) - execute a Groovy script
              before a build is deleted

    :arg bool deploy-if-fail: Deploy if the build is failed (default false)

    Example:

    .. literalinclude:: /../../tests/publishers/fixtures/artifact-dep.yaml
       :language: yaml
    """

    deployer = XML.SubElement(xml_parent,
                              'org.jenkinsci.plugins.artifactdeployer.'
                              'ArtifactDeployerPublisher')
    if data is None or 'entries' not in data:
        raise Exception('entries field is missing')
    elif data.get('entries', None) is None:
        entries = XML.SubElement(deployer, 'entries', {'class': 'empty-list'})
    else:
        entries = XML.SubElement(deployer, 'entries')
        for entry in data.get('entries'):
            deployer_entry = XML.SubElement(
                entries,
                'org.jenkinsci.plugins.artifactdeployer.ArtifactDeployerEntry')
            XML.SubElement(deployer_entry, 'includes').text = \
                entry.get('files')
            XML.SubElement(deployer_entry, 'basedir').text = \
                entry.get('basedir')
            XML.SubElement(deployer_entry, 'excludes').text = \
                entry.get('excludes')
            XML.SubElement(deployer_entry, 'remote').text = entry.get('remote')
            XML.SubElement(deployer_entry, 'flatten').text = \
                str(entry.get('flatten', False)).lower()
            XML.SubElement(deployer_entry, 'deleteRemote').text = \
                str(entry.get('delete-remote', False)).lower()
            XML.SubElement(deployer_entry, 'deleteRemoteArtifacts').text = \
                str(entry.get('delete-remote-artifacts', False)).lower()
            XML.SubElement(deployer_entry, 'failNoFilesDeploy').text = \
                str(entry.get('fail-no-files', False)).lower()
            XML.SubElement(deployer_entry, 'groovyExpression').text = \
                entry.get('groovy-script')
    deploy_if_fail = str(data.get('deploy-if-fail', False)).lower()
    XML.SubElement(deployer, 'deployEvenBuildFail').text = deploy_if_fail


def s3(registry, xml_parent, data):
    """yaml: s3
    Upload build artifacts to Amazon S3.

    Requires the Jenkins :jenkins-wiki:`S3 plugin <S3+Plugin>`.

    :arg str s3-profile: Globally-defined S3 profile to use
    :arg list entries:
      :entries:
        * **destination-bucket** (`str`) - Destination S3 bucket
        * **source-files** (`str`) - Source files (Ant glob syntax)
        * **storage-class** (`str`) - S3 storage class; one of "STANDARD"
          or "REDUCED_REDUNDANCY"
        * **bucket-region** (`str`) - S3 bucket region (capitalized with
          underscores)
        * **upload-on-failure** (`bool`) - Upload files even if the build
          failed (default false)
        * **upload-from-slave** (`bool`) - Perform the upload directly from
          the Jenkins slave rather than the master node. (default false)
        * **managed-artifacts** (`bool`) - Let Jenkins fully manage the
          published artifacts, similar to when artifacts are published to
          the Jenkins master. (default false)
        * **s3-encryption** (`bool`) - Use S3 AES-256 server side encryption
          support. (default false)
        * **flatten** (`bool`) - Ignore the directory structure of the
          artifacts in the source project and copy all matching artifacts
          directly into the specified bucket. (default false)
    :arg list metadata-tags:
      :metadata-tags:
        * **key** Metadata key for files from this build. It will be
          prefixed by "x-amz-meta-" when uploaded to S3. Can contain macros
          (e.g. environment variables).
        * **value** Metadata value associated with the key. Can contain macros.

    Example:

    .. literalinclude:: /../../tests/publishers/fixtures/s3001.yaml
       :language: yaml
    """
    deployer = XML.SubElement(xml_parent,
                              'hudson.plugins.s3.S3BucketPublisher')
    if data is None or not data.get('entries'):
        raise JenkinsJobsException('No filesets defined.')

    XML.SubElement(deployer, 'profileName').text = data.get('s3-profile')

    entries = XML.SubElement(deployer, 'entries')

    for entry in data.get('entries'):
        fileset = XML.SubElement(entries, 'hudson.plugins.s3.Entry')

        # xml keys -> yaml keys
        settings = [('bucket', 'destination-bucket', ''),
                    ('sourceFile', 'source-files', ''),
                    ('storageClass', 'storage-class', ''),
                    ('selectedRegion', 'bucket-region', ''),
                    ('noUploadOnFailure', 'upload-on-failure', False),
                    ('uploadFromSlave', 'upload-from-slave', False),
                    ('managedArtifacts', 'managed-artifacts', False),
                    ('useServerSideEncryption', 's3-encryption', False),
                    ('flatten', 'flatten', False)]

        for xml_key, yaml_key, default in settings:
            xml_config = XML.SubElement(fileset, xml_key)
            config_value = entry.get(yaml_key, default)
            if xml_key == 'noUploadOnFailure':
                xml_config.text = str(not config_value).lower()
            elif isinstance(default, bool):
                xml_config.text = str(config_value).lower()
            else:
                xml_config.text = str(config_value)

    metadata = XML.SubElement(deployer, 'userMetadata')
    for tag in data.get('metadata-tags', []):
        pair = XML.SubElement(metadata, 'hudson.plugins.s3.MetadataPair')
        XML.SubElement(pair, 'key').text = tag.get('key')
        XML.SubElement(pair, 'value').text = tag.get('value')


def ruby_metrics(registry, xml_parent, data):
    """yaml: ruby-metrics
    Rcov plugin parses rcov html report files and
    shows it in Jenkins with a trend graph.

    Requires the Jenkins :jenkins-wiki:`Ruby metrics plugin
    <RubyMetrics+plugin>`.

    :arg str report-dir: Relative path to the coverage report directory
    :arg dict targets:

           :targets: (total-coverage, code-coverage)

                * **healthy** (`int`): Healthy threshold
                * **unhealthy** (`int`): Unhealthy threshold
                * **unstable** (`int`): Unstable threshold

    Example:

    .. literalinclude:: /../../tests/publishers/fixtures/ruby-metrics.yaml
       :language: yaml
    """

    metrics = XML.SubElement(
        xml_parent,
        'hudson.plugins.rubyMetrics.rcov.RcovPublisher')
    report_dir = data.get('report-dir', '')
    XML.SubElement(metrics, 'reportDir').text = report_dir
    targets = XML.SubElement(metrics, 'targets')
    if 'target' in data:
        for t in data['target']:
            if not ('code-coverage' in t or 'total-coverage' in t):
                raise JenkinsJobsException('Unrecognized target name')
            el = XML.SubElement(
                targets,
                'hudson.plugins.rubyMetrics.rcov.model.MetricTarget')
            if 'total-coverage' in t:
                XML.SubElement(el, 'metric').text = 'TOTAL_COVERAGE'
            else:
                XML.SubElement(el, 'metric').text = 'CODE_COVERAGE'
            for threshold_name, threshold_value in \
                    next(iter(t.values())).items():
                elname = threshold_name.lower()
                XML.SubElement(el, elname).text = str(threshold_value)
    else:
        raise JenkinsJobsException('Coverage metric targets must be set')


def fitnesse(registry, xml_parent, data):
    """yaml: fitnesse
    Publish Fitnesse test results

    Requires the Jenkins :jenkins-wiki:`Fitnesse plugin <Fitnesse+Plugin>`.

    :arg str results: path specifier for results files

    Example:

    .. literalinclude::  /../../tests/publishers/fixtures/fitnesse001.yaml
       :language: yaml
    """
    fitnesse = XML.SubElement(
        xml_parent,
        'hudson.plugins.fitnesse.FitnesseResultsRecorder')
    results = data.get('results', '')
    XML.SubElement(fitnesse, 'fitnessePathToXmlResultsIn').text = results


def valgrind(registry, xml_parent, data):
    """yaml: valgrind
    This plugin publishes Valgrind Memcheck XML results.

    Requires the Jenkins :jenkins-wiki:`Valgrind Plugin <Valgrind+Plugin>`.

    :arg str pattern: Filename pattern to locate the Valgrind XML report files
        (required)
    :arg dict thresholds: Mark build as failed or unstable if the number of
        errors exceeds a threshold. All threshold values are optional.

        :thresholds:
            * **unstable** (`dict`)
                :unstable: * **invalid-read-write** (`int`)
                           * **definitely-lost** (`int`)
                           * **total** (`int`)
            * **failed** (`dict`)
                :failed: * **invalid-read-write** (`int`)
                         * **definitely-lost** (`int`)
                         * **total** (`int`)
    :arg bool fail-no-reports: Fail build if no reports are found
      (default false)
    :arg bool fail-invalid-reports: Fail build if reports are malformed
      (default false)
    :arg bool publish-if-aborted: Publish results for aborted builds
      (default false)
    :arg bool publish-if-failed: Publish results for failed builds
      (default false)

    Example:

    .. literalinclude:: /../../tests/publishers/fixtures/valgrind001.yaml
       :language: yaml
    """
    p = XML.SubElement(xml_parent,
                       'org.jenkinsci.plugins.valgrind.ValgrindPublisher')
    p = XML.SubElement(p, 'valgrindPublisherConfig')

    if 'pattern' not in data:
        raise JenkinsJobsException("A filename pattern must be specified.")

    XML.SubElement(p, 'pattern').text = data['pattern']

    dthresholds = data.get('thresholds', {})

    for threshold in ['unstable', 'failed']:
        dthreshold = dthresholds.get(threshold, {})
        threshold = threshold.replace('failed', 'fail')
        XML.SubElement(p, '%sThresholdInvalidReadWrite' % threshold).text \
            = str(dthreshold.get('invalid-read-write', ''))
        XML.SubElement(p, '%sThresholdDefinitelyLost' % threshold).text \
            = str(dthreshold.get('definitely-lost', ''))
        XML.SubElement(p, '%sThresholdTotal' % threshold).text \
            = str(dthreshold.get('total', ''))

    XML.SubElement(p, 'failBuildOnMissingReports').text = str(
        data.get('fail-no-reports', False)).lower()
    XML.SubElement(p, 'failBuildOnInvalidReports').text = str(
        data.get('fail-invalid-reports', False)).lower()
    XML.SubElement(p, 'publishResultsForAbortedBuilds').text = str(
        data.get('publish-if-aborted', False)).lower()
    XML.SubElement(p, 'publishResultsForFailedBuilds').text = str(
        data.get('publish-if-failed', False)).lower()


def pmd(registry, xml_parent, data):
    """yaml: pmd
    Publish trend reports with PMD.
    Requires the Jenkins :jenkins-wiki:`PMD Plugin <PMD+Plugin>`.

    The PMD component accepts a dictionary with the following values:

    :arg str pattern: Report filename pattern (optional)
    :arg bool can-run-on-failed: Also runs for failed builds, instead of just
      stable or unstable builds (default false)
    :arg bool should-detect-modules: Determines if Ant or Maven modules should
      be detected for all files that contain warnings (default false)
    :arg int healthy: Sunny threshold (optional)
    :arg int unhealthy: Stormy threshold (optional)
    :arg str health-threshold: Threshold priority for health status
      ('low', 'normal' or 'high', defaulted to 'low')
    :arg dict thresholds: Mark build as failed or unstable if the number of
      errors exceeds a threshold. (optional)

        :thresholds:
            * **unstable** (`dict`)
                :unstable: * **total-all** (`int`)
                           * **total-high** (`int`)
                           * **total-normal** (`int`)
                           * **total-low** (`int`)
                           * **new-all** (`int`)
                           * **new-high** (`int`)
                           * **new-normal** (`int`)
                           * **new-low** (`int`)

            * **failed** (`dict`)
                :failed: * **total-all** (`int`)
                         * **total-high** (`int`)
                         * **total-normal** (`int`)
                         * **total-low** (`int`)
                         * **new-all** (`int`)
                         * **new-high** (`int`)
                         * **new-normal** (`int`)
                         * **new-low** (`int`)
    :arg str default-encoding: Encoding for parsing or showing files (optional)
    :arg bool do-not-resolve-relative-paths: (default false)
    :arg bool dont-compute-new: If set to false, computes new warnings based on
      the reference build (default true)
    :arg bool use-previous-build-as-reference: determines whether to always
        use the previous build as the reference build (default false)
    :arg bool use-stable-build-as-reference: The number of new warnings will be
      calculated based on the last stable build, allowing reverts of unstable
      builds where the number of warnings was decreased. (default false)
    :arg bool use-delta-values: If set then the number of new warnings is
      calculated by subtracting the total number of warnings of the current
      build from the reference build.
      (default false)

    Example:

    .. literalinclude::  /../../tests/publishers/fixtures/pmd001.yaml
       :language: yaml

    Full example:

    .. literalinclude::  /../../tests/publishers/fixtures/pmd002.yaml
       :language: yaml
    """

    xml_element = XML.SubElement(xml_parent, 'hudson.plugins.pmd.PmdPublisher')

    helpers.build_trends_publisher('[PMD] ', xml_element, data)


def scan_build(registry, xml_parent, data):
    """yaml: scan-build
    Publishes results from the Clang scan-build static analyzer.

    The scan-build report has to be generated in the directory
    ``${WORKSPACE}/clangScanBuildReports`` for the publisher to find it.

    Requires the Jenkins :jenkins-wiki:`Clang Scan-Build Plugin
    <Clang+Scan-Build+Plugin>`.

    :arg bool mark-unstable: Mark build as unstable if the number of bugs
        exceeds a threshold (default false)
    :arg int threshold: Threshold for marking builds as unstable (default 0)
    :arg string exclude-paths: Comma separated paths to exclude from reports
        (>=1.5) (default '')
    :arg string report-folder: Folder where generated reports are located
        (>=1.7) (default 'clangScanBuildReports')

    Full Example:

    .. literalinclude:: /../../tests/publishers/fixtures/scan-build-full.yaml
       :language: yaml

    Minimal Example:

    .. literalinclude::
       /../../tests/publishers/fixtures/scan-build-minimal.yaml
       :language: yaml
    """
    p = XML.SubElement(
        xml_parent,
        'jenkins.plugins.clangscanbuild.publisher.ClangScanBuildPublisher')
    p.set('plugin', 'clang-scanbuild')

    mappings = [
        ('mark-unstable', 'markBuildUnstableWhenThresholdIsExceeded', False),
        ('threshold', 'bugThreshold', 0),
        ('exclude-paths', 'clangexcludedpaths', ''),
        ('report-folder', 'reportFolderName', 'clangScanBuildReports'),
    ]
    helpers.convert_mapping_to_xml(p, data, mappings, fail_required=True)


def dry(registry, xml_parent, data):
    """yaml: dry
    Publish trend reports with DRY.
    Requires the Jenkins :jenkins-wiki:`DRY Plugin <DRY+Plugin>`.

    The DRY component accepts a dictionary with the following values:

    :arg str pattern: Report filename pattern (default '')
    :arg bool can-run-on-failed: Also runs for failed builds, instead of just
      stable or unstable builds (default false)
    :arg bool should-detect-modules: Determines if Ant or Maven modules should
      be detected for all files that contain warnings (default false)
    :arg int healthy: Sunny threshold (default '')
    :arg int unhealthy: Stormy threshold (default '')
    :arg str health-threshold: Threshold priority for health status
      ('low', 'normal' or 'high', defaulted to 'low')
    :arg int high-threshold: Minimum number of duplicated lines for high
      priority warnings. (default 50)
    :arg int normal-threshold: Minimum number of duplicated lines for normal
      priority warnings. (default 25)
    :arg dict thresholds: Mark build as failed or unstable if the number of
      errors exceeds a threshold. (default '')

        :thresholds:
            * **unstable** (`dict`)
                :unstable: * **total-all** (`int`)
                           * **total-high** (`int`)
                           * **total-normal** (`int`)
                           * **total-low** (`int`)
                           * **new-all** (`int`)
                           * **new-high** (`int`)
                           * **new-normal** (`int`)
                           * **new-low** (`int`)

            * **failed** (`dict`)
                :failed: * **total-all** (`int`)
                         * **total-high** (`int`)
                         * **total-normal** (`int`)
                         * **total-low** (`int`)
                         * **new-all** (`int`)
                         * **new-high** (`int`)
                         * **new-normal** (`int`)
                         * **new-low** (`int`)
    :arg str default-encoding: Encoding for parsing or showing files (optional)
    :arg bool do-not-resolve-relative-paths: (default false)
    :arg bool dont-compute-new: If set to false, computes new warnings based on
      the reference build (default true)
    :arg bool use-previous-build-as-reference: determines whether to always
        use the previous build as the reference build (default false)
    :arg bool use-stable-build-as-reference: The number of new warnings will be
      calculated based on the last stable build, allowing reverts of unstable
      builds where the number of warnings was decreased. (default false)
    :arg bool use-delta-values: If set then the number of new warnings is
      calculated by subtracting the total number of warnings of the current
      build from the reference build. (default false)

    Example:

    .. literalinclude::  /../../tests/publishers/fixtures/dry001.yaml
       :language: yaml

    Full example:

    .. literalinclude::  /../../tests/publishers/fixtures/dry004.yaml
       :language: yaml
    """

    xml_element = XML.SubElement(xml_parent, 'hudson.plugins.dry.DryPublisher')

    helpers.build_trends_publisher('[DRY] ', xml_element, data)

    # Add specific settings for this trends publisher
    settings = [
        ('high-threshold', 'highThreshold', 50),
        ('normal-threshold', 'normalThreshold', 25)]
    helpers.convert_mapping_to_xml(
        xml_element, data, settings, fail_required=True)


def shining_panda(registry, xml_parent, data):
    """yaml: shining-panda
    Publish coverage.py results. Requires the Jenkins
    :jenkins-wiki:`ShiningPanda Plugin <ShiningPanda+Plugin>`.

    :arg str html-reports-directory: path to coverage.py html results
                                    (optional)

    Example:

    .. literalinclude::  /../../tests/publishers/fixtures/shiningpanda001.yaml
       :language: yaml
    """
    shining_panda_plugin = XML.SubElement(
        xml_parent,
        'jenkins.plugins.shiningpanda.publishers.CoveragePublisher')
    if 'html-reports-directory' in data:
        XML.SubElement(shining_panda_plugin, 'htmlDir').text = str(
            data['html-reports-directory'])


def downstream_ext(registry, xml_parent, data):
    """yaml: downstream-ext
    Trigger multiple downstream jobs when a job is completed and
    condition is met.

    Requires the Jenkins :jenkins-wiki:`Downstream-Ext Plugin
    <Downstream-Ext+Plugin>`.

    :arg list projects: Projects to build (required)
    :arg string condition: comparison condition used for the criteria.
      One of 'equal-or-over', 'equal-or-under', 'equal'
      (default 'equal-or-over')
    :arg string criteria: Trigger downstream job if build results meets
      condition. One of 'success', 'unstable', 'failure' or
      'aborted' (default 'success')
    :arg bool only-on-scm-change: Trigger only if downstream project
      has SCM changes (default false)
    :arg bool only-on-local-scm-change: Trigger only if current project
      has SCM changes (default false)

    Example:

    .. literalinclude::
        /../../tests/publishers/fixtures/downstream-ext002.yaml
       :language: yaml
    """

    conditions = {
        "equal-or-over": "AND_HIGHER",
        "equal-or-under": "AND_LOWER",
        "equal": "EXACT"
    }

    p = XML.SubElement(xml_parent,
                       'hudson.plugins.downstream__ext.DownstreamTrigger')

    if 'projects' not in data:
        raise JenkinsJobsException("Missing list of downstream projects.")

    XML.SubElement(p, 'childProjects').text = ','.join(data['projects'])

    th = XML.SubElement(p, 'threshold')

    criteria = data.get('criteria', 'success').upper()

    if criteria not in hudson_model.THRESHOLDS:
        raise JenkinsJobsException("criteria must be one of %s" %
                                   ", ".join(hudson_model.THRESHOLDS.keys()))

    wr_threshold = hudson_model.THRESHOLDS[
        criteria]
    XML.SubElement(th, "name").text = wr_threshold['name']
    XML.SubElement(th, "ordinal").text = wr_threshold['ordinal']
    XML.SubElement(th, "color").text = wr_threshold['color']
    XML.SubElement(th, "completeBuild").text = str(
        wr_threshold['complete']).lower()

    condition = data.get('condition', 'equal-or-over')
    if condition not in conditions:
        raise JenkinsJobsException('condition must be one of: %s' %
                                   ", ".join(conditions))

    XML.SubElement(p, 'thresholdStrategy').text = conditions[
        condition]
    XML.SubElement(p, 'onlyIfSCMChanges').text = str(
        data.get('only-on-scm-change', False)).lower()
    XML.SubElement(p, 'onlyIfLocalSCMChanges').text = str(
        data.get('only-on-local-scm-change', False)).lower()


def rundeck(registry, xml_parent, data):
    """yaml: rundeck
    Trigger a rundeck job when the build is complete.

    Requires the Jenkins :jenkins-wiki:`RunDeck
    Plugin <RunDeck+Plugin>`.

    :arg str job-id: The RunDeck job identifier. (required)
        This could be:
        * ID example : "42"
        * UUID example : "2027ce89-7924-4ecf-a963-30090ada834f"
        * reference, in the format : "project:group/job"
    :arg str options: List of options for the Rundeck job, in Java-Properties
      format: key=value (default "")
    :arg str node-filters: List of filters to optionally filter the nodes
      included by the job. (default "")
    :arg str tag: Used for on-demand job scheduling on rundeck: if a tag is
      specified, the job will only execute if the given tag is present in the
      SCM changelog. (default "")
    :arg bool wait-for-rundeck: If true Jenkins will wait for the job to
      complete, if false the job will be started and Jenkins will move on.
      (default false)
    :arg bool fail-the-build: If true a RunDeck job failure will cause the
      Jenkins build to fail. (default false)

    Example:

    .. literalinclude:: /../../tests/publishers/fixtures/rundeck001.yaml
        :language: yaml

    Full example:

    .. literalinclude:: /../../tests/publishers/fixtures/rundeck002.yaml
        :language: yaml
    """

    p = XML.SubElement(
        xml_parent,
        'org.jenkinsci.plugins.rundeck.RundeckNotifier')

    mappings = [
        ('job-id', 'jobId', None),
        ('options', 'options', ''),
        ('node-filters', 'nodeFilters', ''),
        ('tag', 'tag', ''),
        ('wait-for-rundeck', 'shouldWaitForRundeckJob', False),
        ('fail-the-build', 'shouldFailTheBuild', False),
    ]
    helpers.convert_mapping_to_xml(p, data, mappings, fail_required=True)


def create_publishers(registry, action):
    dummy_parent = XML.Element("dummy")
    registry.dispatch('publisher', dummy_parent, action)
    return list(dummy_parent)


def conditional_publisher(registry, xml_parent, data):
    """yaml: conditional-publisher
    Conditionally execute some post-build steps. Requires the Jenkins
    :jenkins-wiki:`Flexible Publish Plugin <Flexible+Publish+Plugin>`.

    A Flexible Publish list of Conditional Actions is created in Jenkins.

    :arg str condition-kind: Condition kind that must be verified before the
      action is executed. Valid values and their additional attributes are
      described in the conditions_ table.
    :arg str on-evaluation-failure: What should be the outcome of the build
      if the evaluation of the condition fails. Possible values are `fail`,
      `mark-unstable`, `run-and-mark-unstable`, `run` and `dont-run`.
      Default is `fail`.
    :arg list action: Action to run if the condition is verified. Item
      can be any publisher known by Jenkins Job Builder and supported
      by the Flexible Publish Plugin.

    .. _conditions:

    ================== ====================================================
    Condition kind     Description
    ================== ====================================================
    always             Condition is always verified
    never              Condition is never verified
    boolean-expression Run the action if the expression expands to a
                       representation of true

                         :condition-expression: Expression to expand
    current-status     Run the action if the current build status is
                       within the configured range

                         :condition-worst: Accepted values are SUCCESS,
                           UNSTABLE, FAILURE, NOT_BUILD, ABORTED
                         :condition-best: Accepted values are SUCCESS,
                           UNSTABLE, FAILURE, NOT_BUILD, ABORTED

    shell              Run the action if the shell command succeeds

                         :condition-command: Shell command to execute
    windows-shell      Similar to shell, except that commands will be
                       executed by cmd, under Windows

                         :condition-command: Command to execute
    regexp             Run the action if a regular expression matches

                         :condition-expression: Regular Expression
                         :condition-searchtext: Text to match against
                           the regular expression
    file-exists        Run the action if a file exists

                         :condition-filename: Check existence of this file
                         :condition-basedir: If condition-filename is
                           relative, it will be considered relative to
                           either `workspace`, `artifact-directory`,
                           or `jenkins-home`. Default is `workspace`.
    ================== ====================================================

    Single Conditional Action Example:

    .. literalinclude:: \
    /../../tests/publishers/fixtures/conditional-publisher001.yaml
       :language: yaml

    Multiple Conditional Actions Example
    (includes example of multiple actions per condition which requires
    v0.13 or higher of the Flexible Publish plugin):

    .. literalinclude:: \
    /../../tests/publishers/fixtures/conditional-publisher003.yaml
       :language: yaml

    :download:`Multiple Conditional Actions Example for pre-v0.13 versions
    <../../tests/publishers/fixtures/conditional-publisher002.yaml>`

    """
    def publish_condition(cdata):
        kind = cdata['condition-kind']
        ctag = XML.SubElement(cond_publisher, condition_tag)
        class_pkg = 'org.jenkins_ci.plugins.run_condition'

        if kind == "always":
            ctag.set('class',
                     class_pkg + '.core.AlwaysRun')
        elif kind == "never":
            ctag.set('class',
                     class_pkg + '.core.NeverRun')
        elif kind == "boolean-expression":
            ctag.set('class',
                     class_pkg + '.core.BooleanCondition')
            XML.SubElement(ctag, "token").text = cdata['condition-expression']
        elif kind == "current-status":
            ctag.set('class',
                     class_pkg + '.core.StatusCondition')
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
                     class_pkg + '.contributed.ShellCondition')
            XML.SubElement(ctag, "command").text = cdata['condition-command']
        elif kind == "windows-shell":
            ctag.set('class',
                     class_pkg + '.contributed.BatchFileCondition')
            XML.SubElement(ctag, "command").text = cdata['condition-command']
        elif kind == "regexp":
            ctag.set('class',
                     class_pkg + '.core.ExpressionCondition')
            XML.SubElement(ctag,
                           "expression").text = cdata['condition-expression']
            XML.SubElement(ctag, "label").text = cdata['condition-searchtext']
        elif kind == "file-exists":
            ctag.set('class',
                     class_pkg + '.core.FileExistsCondition')
            XML.SubElement(ctag, "file").text = cdata['condition-filename']
            basedir = cdata.get('condition-basedir', 'workspace')
            basedir_tag = XML.SubElement(ctag, "baseDir")
            if "workspace" == basedir:
                basedir_tag.set('class',
                                class_pkg + '.common.BaseDirectory$Workspace')
            elif "artifact-directory" == basedir:
                basedir_tag.set('class',
                                class_pkg + '.common.'
                                'BaseDirectory$ArtifactsDir')
            elif "jenkins-home" == basedir:
                basedir_tag.set('class',
                                class_pkg + '.common.'
                                'BaseDirectory$JenkinsHome')
        else:
            raise JenkinsJobsException('%s is not a valid condition-kind '
                                       'value.' % kind)

    def publish_action(parent, action):
        for edited_node in create_publishers(registry, action):
            if not use_publisher_list:
                edited_node.set('class', edited_node.tag)
                edited_node.tag = 'publisher'
            parent.append(edited_node)

    flex_publisher_tag = 'org.jenkins__ci.plugins.flexible__publish.'    \
        'FlexiblePublisher'
    cond_publisher_tag = 'org.jenkins__ci.plugins.flexible__publish.'   \
        'ConditionalPublisher'

    root_tag = XML.SubElement(xml_parent, flex_publisher_tag)
    publishers_tag = XML.SubElement(root_tag, "publishers")
    condition_tag = "condition"

    evaluation_classes_pkg = 'org.jenkins_ci.plugins.run_condition'
    evaluation_classes = {
        'fail': evaluation_classes_pkg + '.BuildStepRunner$Fail',
        'mark-unstable': evaluation_classes_pkg +
        '.BuildStepRunner$Unstable',
        'run-and-mark-unstable': evaluation_classes_pkg +
        '.BuildStepRunner$RunUnstable',
        'run': evaluation_classes_pkg + '.BuildStepRunner$Run',
        'dont-run': evaluation_classes_pkg + '.BuildStepRunner$DontRun',
    }

    for cond_action in data:
        cond_publisher = XML.SubElement(publishers_tag, cond_publisher_tag)
        publish_condition(cond_action)
        evaluation_flag = cond_action.get('on-evaluation-failure', 'fail')
        if evaluation_flag not in evaluation_classes.keys():
            raise JenkinsJobsException('on-evaluation-failure value '
                                       'specified is not valid.  Must be one '
                                       'of: %s' % evaluation_classes.keys())

        evaluation_class = evaluation_classes[evaluation_flag]
        XML.SubElement(cond_publisher, "runner").set('class',
                                                     evaluation_class)

        if 'action' in cond_action:
            actions = cond_action['action']

            action_parent = cond_publisher

            plugin_info = \
                registry.get_plugin_info("Flexible Publish Plugin")
            version = pkg_resources.parse_version(plugin_info.get('version',
                                                                  '0'))
            # XML tag changed from publisher to publisherList in v0.13
            # check the plugin version to determine further operations
            use_publisher_list = version >= pkg_resources.parse_version("0.13")

            if use_publisher_list:
                action_parent = XML.SubElement(cond_publisher, 'publisherList')
            else:
                # Check the length of actions list for versions prior to 0.13.
                # Flexible Publish will overwrite action if more than one is
                # specified.  Limit the action list to one element.
                if len(actions) is not 1:
                    raise JenkinsJobsException("Only one action may be "
                                               "specified for each condition.")
            for action in actions:
                publish_action(action_parent, action)
        else:
            raise JenkinsJobsException('action must be set for each condition')


def scoverage(registry, xml_parent, data):
    """yaml: scoverage
    Publish scoverage results as a trend graph.
    Requires the Jenkins :jenkins-wiki:`Scoverage Plugin <Scoverage+Plugin>`.

    :arg str report-directory: This is a directory that specifies the locations
        where the xml scoverage report is generated (required)
    :arg str report-file: This is a file name that is given to the xml
        scoverage report (required)

    Example:

    .. literalinclude::  /../../tests/publishers/fixtures/scoverage001.yaml
       :language: yaml
    """
    scoverage = XML.SubElement(
        xml_parent,
        'org.jenkinsci.plugins.scoverage.ScoveragePublisher')
    scoverage.set('plugin', 'scoverage')

    mappings = [
        ('report-directory', 'reportDir', None),
        ('report-file', 'reportFile', None),
    ]
    helpers.convert_mapping_to_xml(
        scoverage, data, mappings, fail_required=True)


def display_upstream_changes(registry, xml_parent, data):
    """yaml: display-upstream-changes
    Display SCM changes of upstream jobs. Requires the Jenkins
    :jenkins-wiki:`Display Upstream Changes Plugin
    <Display+Upstream+Changes+Plugin>`.

    Example:

    .. literalinclude:: \
    /../../tests/publishers/fixtures/display-upstream-changes.yaml
    """
    XML.SubElement(
        xml_parent,
        'jenkins.plugins.displayupstreamchanges.'
        'DisplayUpstreamChangesRecorder')


def gatling(registry, xml_parent, data):
    """yaml: gatling
    Publish gatling results as a trend graph
    Requires the Jenkins :jenkins-wiki:`Gatling Plugin <Gatling+Plugin>`.

    Example:

    .. literalinclude:: /../../tests/publishers/fixtures/gatling001.yaml
       :language: yaml
    """
    gatling = XML.SubElement(
        xml_parent,
        'io.gatling.jenkins.GatlingPublisher')
    XML.SubElement(gatling, 'enabled').text = 'true'


def logstash(registry, xml_parent, data):
    """yaml: logstash
    Send job's console log to Logstash for processing and analyis of
    your job data. Also stores test metrics from Junit.
    Requires the Jenkins :jenkins-wiki:`Logstash Plugin <Logstash+Plugin>`.

    :arg int max-lines: The maximum number of log lines to send to Logstash.
        (default 1000)
    :arg bool fail-build: Mark build as failed if this step fails.
        (default false)

    Minimal Example:

    .. literalinclude::  /../../tests/publishers/fixtures/logstash-min.yaml
       :language: yaml

    Full Example:

    .. literalinclude::  /../../tests/publishers/fixtures/logstash-full.yaml
       :language: yaml
    """

    logstash = XML.SubElement(xml_parent,
                              'jenkins.plugins.logstash.LogstashNotifier')
    logstash.set('plugin', 'logstash')

    mapping = [
        ('max-lines', 'maxLines', 1000),
        ('fail-build', 'failBuild', False),
    ]
    helpers.convert_mapping_to_xml(logstash, data, mapping, fail_required=True)


def image_gallery(registry, xml_parent, data):
    """yaml: image-gallery
    Produce an image gallery using Javascript library. Requires the Jenkins
    :jenkins-wiki:`Image Gallery Plugin<Image+Gallery+Plugin>`.

    :arg str gallery-type:

        :gallery-type values:
            * **archived-images-gallery** (default)
            * **in-folder-comparative-gallery**
            * **multiple-folder-comparative-gallery**
    :arg str title: gallery title (optional)
    :arg int image-width: width of the image (optional)
    :arg bool unstable-if-no-artifacts: mark build as unstable
        if no archived artifacts were found (default false)
    :arg str includes: include pattern (valid for archived-images-gallery
        gallery)
    :arg str base-root-folder: base root dir (valid for comparative gallery)
    :arg int image-inner-width: width of the image displayed in the inner
        gallery popup (valid for comparative gallery, optional)

    Example:

    .. literalinclude:: /../../tests/publishers/fixtures/image-gallery001.yaml

    """
    def include_comparative_elements(gallery_parent_elem, gallery):
        XML.SubElement(gallery_parent_elem, 'baseRootFolder').text = str(
            gallery.get('base-root-folder', ''))
        image_inner_width = gallery.get('image-inner-width', '')
        if image_inner_width:
            XML.SubElement(gallery_parent_elem, 'imageInnerWidth').text = str(
                image_inner_width)

    package_prefix = 'org.jenkinsci.plugins.imagegallery.'
    builder = XML.SubElement(
        xml_parent, package_prefix + 'ImageGalleryRecorder'
    )
    image_galleries = XML.SubElement(builder, 'imageGalleries')
    galleries = {
        'archived-images-gallery': package_prefix + 'imagegallery.'
        'ArchivedImagesGallery',
        'in-folder-comparative-gallery': package_prefix + 'comparative.'
        'InFolderComparativeArchivedImagesGallery',
        'multiple-folder-comparative-gallery': package_prefix + 'comparative.'
        'MultipleFolderComparativeArchivedImagesGallery'
    }
    for gallery_def in data:
        gallery_type = gallery_def.get('gallery-type',
                                       'archived-images-gallery')
        if gallery_type not in galleries:
            raise InvalidAttributeError('gallery-type', gallery_type,
                                        galleries.keys())
        gallery_config = XML.SubElement(
            image_galleries, galleries[gallery_type])
        XML.SubElement(gallery_config, 'title').text = str(
            gallery_def.get('title', ''))
        image_width = str(gallery_def.get('image-width', ''))
        if image_width:
            XML.SubElement(gallery_config, 'imageWidth').text = str(
                image_width)
        XML.SubElement(
            gallery_config,
            'markBuildAsUnstableIfNoArchivesFound').text = str(gallery_def.get(
                'unstable-if-no-artifacts', False))
        if gallery_type == 'archived-images-gallery':
            XML.SubElement(gallery_config, 'includes').text = str(
                gallery_def.get('includes', ''))
        if gallery_type == 'in-folder-comparative-gallery':
            include_comparative_elements(gallery_config, gallery_def)
        if gallery_type == 'multiple-folder-comparative-gallery':
            include_comparative_elements(gallery_config, gallery_def)


def naginator(registry, xml_parent, data):
    """yaml: naginator
    Automatically reschedule a build after a build failure
    Requires the Jenkins :jenkins-wiki:`Naginator Plugin <Naginator+Plugin>`.

    :arg bool rerun-unstable-builds: Rerun build for unstable builds as well
        as failures (default false)
    :arg bool rerun-matrix-part: Rerun build only for failed parts on the
        matrix (>=1.12) (default false)
    :arg int fixed-delay: Fixed delay before retrying build (cannot be used
        with progressive-delay-increment or progressive-delay-maximum.
        This is the default delay type.  (default 0)
    :arg int progressive-delay-increment: Progressive delay before retrying
        build increment (cannot be used when fixed-delay is being used)
        (default 0)
    :arg int progressive-delay-maximum: Progressive delay before retrying
        maximum delay (cannot be used when fixed-delay is being used)
        (default 0)
    :arg int max-failed-builds: Maximum number of successive failed builds
        (default 0)
    :arg str regular-expression: Only rerun build if regular expression is
        found in output (default '')

    Example:

    .. literalinclude:: /../../tests/publishers/fixtures/naginator001.yaml
        :language: yaml
    """
    naginator = XML.SubElement(
        xml_parent,
        'com.chikli.hudson.plugin.naginator.NaginatorPublisher')
    XML.SubElement(naginator, 'regexpForRerun').text = str(
        data.get('regular-expression', ''))
    XML.SubElement(naginator, 'checkRegexp').text = str(
        'regular-expression' in data).lower()
    XML.SubElement(naginator, 'rerunIfUnstable').text = str(
        data.get('rerun-unstable-builds', False)).lower()
    XML.SubElement(naginator, 'rerunMatrixPart').text = str(
        data.get('rerun-matrix-part', False)).lower()
    progressive_delay = ('progressive-delay-increment' in data or
                         'progressive-delay-maximum' in data)
    if 'fixed-delay' in data and progressive_delay:
        raise JenkinsJobsException("You cannot specify both fixed "
                                   "and progressive delays")
    if not progressive_delay:
        delay = XML.SubElement(
            naginator,
            'delay',
            {'class': 'com.chikli.hudson.plugin.naginator.FixedDelay'})
        XML.SubElement(delay, 'delay').text = str(
            data.get('fixed-delay', '0'))
    else:
        delay = XML.SubElement(
            naginator,
            'delay',
            {'class': 'com.chikli.hudson.plugin.naginator.ProgressiveDelay'})
        XML.SubElement(delay, 'increment').text = str(
            data.get('progressive-delay-increment', '0'))
        XML.SubElement(delay, 'max').text = str(
            data.get('progressive-delay-maximum', '0'))
    XML.SubElement(naginator, 'maxSchedule').text = str(
        data.get('max-failed-builds', '0'))


def disable_failed_job(registry, xml_parent, data):
    """yaml: disable-failed-job
    Automatically disable failed jobs.

    Requires the Jenkins :jenkins-wiki:`Disable Failed Job Plugin
    <Disable+Failed+Job+Plugin>`.

    :arg str when-to-disable: The condition to disable the job. (required)
        Possible values are

        * **Only Failure**
        * **Failure and Unstable**
        * **Unstable**

    :arg int no-of-failures: Number of consecutive failures to disable the
        job. (optional)

    Example:

    .. literalinclude::
        /../../tests/publishers/fixtures/disable-failed-job001.yaml
       :language: yaml
    """

    xml_element = XML.SubElement(xml_parent, 'disableFailedJob.'
                                 'disableFailedJob.DisableFailedJob',
                                 {'plugin': 'disable-failed-job'})

    valid_conditions = ['Only Failure',
                        'Failure and Unstable',
                        'Only Unstable']
    mapping = [('when-to-disable', 'whenDisable', None, valid_conditions)]
    helpers.convert_mapping_to_xml(
        xml_element, data, mapping, fail_required=True)

    if 'no-of-failures' in data:
        XML.SubElement(xml_element, 'failureTimes').text = str(data.get(
            'no-of-failures'))
        XML.SubElement(xml_element, 'optionalBrockChecked').text = 'true'
    else:
        XML.SubElement(xml_element, 'optionalBrockChecked').text = 'false'


def google_cloud_storage(registry, xml_parent, data):
    """yaml: google-cloud-storage
    Upload build artifacts to Google Cloud Storage. Requires the
    Jenkins :jenkins-wiki:`Google Cloud Storage plugin
    <Google+Cloud+Storage+Plugin>`.

    Apart from the Google Cloud Storage Plugin itself, installation of Google
    OAuth Credentials and addition of required credentials to Jenkins is
    required.

    :arg str credentials-id: The set of Google credentials registered with
                             the Jenkins Credential Manager for authenticating
                             with your project. (required)
    :arg list uploads:
        :uploads:
            * **expiring-elements** (`dict`)
                :params:
                    * **bucket-name** (`str`) bucket name to upload artifacts
                      (required)
                    * **days-to-retain** (`int`) days to keep artifacts
                      (required)
            * **build-log** (`dict`)
                :params:
                    * **log-name** (`str`) name of the file that the Jenkins
                      console log to be named (required)
                    * **storage-location** (`str`) bucket name to upload
                      artifacts (required)
                    * **share-publicly** (`bool`) whether to share uploaded
                      share uploaded artifacts with everyone (default false)
                    * **upload-for-failed-jobs** (`bool`) whether to upload
                      artifacts even if the build fails (default false)
                    * **show-inline** (`bool`) whether to show uploaded build
                      log inline in web browsers, rather than forcing it to be
                      downloaded (default true)
                    * **strip-prefix** (`str`) strip this prefix off the
                      file names (default not set)

            * **classic** (`dict`)
                :params:
                    * **file-pattern** (`str`) ant style globs to match the
                      files to upload (required)
                    * **storage-location** (`str`) bucket name to upload
                      artifacts (required)
                    * **share-publicly** (`bool`) whether to share uploaded
                      share uploaded artifacts with everyone (default false)
                    * **upload-for-failed-jobs** (`bool`) whether to upload
                      artifacts even if the build fails (default false)
                    * **show-inline** (`bool`) whether to show uploaded
                      artifacts inline in web browsers, rather than forcing
                      them to be downloaded (default false)
                    * **strip-prefix** (`str`) strip this prefix off the
                      file names (default not set)

    Example:

    .. literalinclude::
        /../../tests/publishers/fixtures/google_cloud_storage001.yaml
       :language: yaml

    Full example:

    .. literalinclude::
        /../../tests/publishers/fixtures/google_cloud_storage002.yaml
       :language: yaml
    """

    def expiring_elements(properties, upload_element, types):
        """Handle expiring elements upload action
        """

        xml_element = XML.SubElement(upload_element, 'com.google.'
                                     'jenkins.plugins.storage.'
                                     'ExpiringBucketLifecycleManager')

        if 'bucket-name' not in properties:
            raise MissingAttributeError('bucket-name')
        XML.SubElement(xml_element, 'bucketNameWithVars').text = str(
            properties['bucket-name'])

        XML.SubElement(xml_element, 'sharedPublicly').text = 'false'
        XML.SubElement(xml_element, 'forFailedJobs').text = 'false'

        if types.count('expiring-elements') > 1:
            XML.SubElement(xml_element, 'module',
                           {'reference': '../../com.google.jenkins.plugins.'
                            'storage.ExpiringBucketLifecycleManager/module'})
        else:
            XML.SubElement(xml_element, 'module')

        if 'days-to-retain' not in properties:
            raise MissingAttributeError('days-to-retain')
        XML.SubElement(xml_element, 'bucketObjectTTL').text = str(
            properties['days-to-retain'])

    def build_log(properties, upload_element, types):
        """Handle build log upload action
        """

        xml_element = XML.SubElement(upload_element, 'com.google.jenkins.'
                                     'plugins.storage.StdoutUpload')

        if 'storage-location' not in properties:
            raise MissingAttributeError('storage-location')
        XML.SubElement(xml_element, 'bucketNameWithVars').text = str(
            properties['storage-location'])

        XML.SubElement(xml_element, 'sharedPublicly').text = str(
            properties.get('share-publicly', False)).lower()

        XML.SubElement(xml_element, 'forFailedJobs').text = str(
            properties.get('upload-for-failed-jobs', False)).lower()

        XML.SubElement(xml_element, 'showInline').text = str(
            properties.get('show-inline', True)).lower()

        XML.SubElement(xml_element, 'pathPrefix').text = str(
            properties.get('strip-prefix', ''))

        if types.count('build-log') > 1:
            XML.SubElement(xml_element, 'module',
                           {'reference': '../../com.google.jenkins.plugins.'
                            'storage.StdoutUpload/module'})
        else:
            XML.SubElement(xml_element, 'module')

        if 'log-name' not in properties:
            raise MissingAttributeError('log-name')
        XML.SubElement(xml_element, 'logName').text = str(
            properties['log-name'])

    def classic(properties, upload_element, types):
        """Handle classic upload action
        """

        xml_element = XML.SubElement(upload_element, 'com.google.jenkins.'
                                     'plugins.storage.ClassicUpload')

        if 'storage-location' not in properties:
            raise MissingAttributeError('storage-location')
        XML.SubElement(xml_element, 'bucketNameWithVars').text = str(
            properties['storage-location'])

        XML.SubElement(xml_element, 'sharedPublicly').text = str(
            properties.get('share-publicly', False)).lower()

        XML.SubElement(xml_element, 'forFailedJobs').text = str(
            properties.get('upload-for-failed-jobs', False)).lower()

        XML.SubElement(xml_element, 'showInline').text = str(
            properties.get('show-inline', False)).lower()

        XML.SubElement(xml_element, 'pathPrefix').text = str(
            properties.get('strip-prefix', ''))

        if types.count('classic') > 1:
            XML.SubElement(xml_element, 'module',
                           {'reference': '../../com.google.jenkins.plugins.'
                            'storage.ClassicUpload/module'})
        else:
            XML.SubElement(xml_element, 'module')

        if 'file-pattern' not in properties:
            raise MissingAttributeError('file-pattern')
        XML.SubElement(xml_element, 'sourceGlobWithVars').text = str(
            properties['file-pattern'])

    uploader = XML.SubElement(xml_parent,
                              'com.google.jenkins.plugins.storage.'
                              'GoogleCloudStorageUploader',
                              {'plugin': 'google-storage-plugin'})

    try:
        credentials_id = str(data['credentials-id'])
    except KeyError as e:
        raise MissingAttributeError(e.args[0])
    XML.SubElement(uploader, 'credentialsId').text = credentials_id

    valid_upload_types = ['expiring-elements',
                          'build-log',
                          'classic']

    types = []

    upload_element = XML.SubElement(uploader, 'uploads')

    uploads = data['uploads']
    for upload in uploads:
        for upload_type, properties in upload.items():
            types.append(upload_type)

            if upload_type not in valid_upload_types:
                raise InvalidAttributeError('uploads', upload_type,
                                            valid_upload_types)
            else:
                locals()[upload_type.replace('-', '_')](
                    properties, upload_element, types)


def flowdock(registry, xml_parent, data):
    """yaml: flowdock
    This plugin publishes job build results to a Flowdock flow.

    Requires the Jenkins :jenkins-wiki:`Flowdock Plugin
    <Flowdock+Plugin>`.

    :arg str token: API token for the targeted flow.
      (required)
    :arg str tags: Comma-separated list of tags to incude in message
      (default "")
    :arg bool chat-notification: Send chat notification when build fails
      (default true)
    :arg bool notify-success: Send notification on build success
      (default true)
    :arg bool notify-failure: Send notification on build failure
      (default true)
    :arg bool notify-fixed: Send notification when build is fixed
      (default true)
    :arg bool notify-unstable: Send notification when build is unstable
      (default false)
    :arg bool notify-aborted: Send notification when build was aborted
      (default false)
    :arg bool notify-notbuilt: Send notification when build did not occur
      (default false)

    Example:

    .. literalinclude:: /../../tests/publishers/fixtures/flowdock001.yaml
       :language: yaml

    Full example:

    .. literalinclude:: /../../tests/publishers/fixtures/flowdock002.yaml
       :language: yaml
    """

    def gen_notification_entry(data_item, default, text):
        e = XML.SubElement(nm, 'entry')
        XML.SubElement(e, 'com.flowdock.jenkins.BuildResult').text = text
        XML.SubElement(e, 'boolean').text = str(
            data.get(data_item, default)).lower()

    def gen_setting(item, default):
        XML.SubElement(parent, 'notify%s' % item).text = str(
            data.get('notify-%s' % item.lower(), default)).lower()

    # Raise exception if token was not specified
    if 'token' not in data:
        raise MissingAttributeError('token')

    parent = XML.SubElement(xml_parent,
                            'com.flowdock.jenkins.FlowdockNotifier')

    XML.SubElement(parent, 'flowToken').text = data['token']
    XML.SubElement(parent, 'notificationTags').text = data.get('tags', '')
    XML.SubElement(parent, 'chatNotification').text = str(
        data.get('chat-notification', True)).lower()

    nm = XML.SubElement(parent, 'notifyMap')

    # notification entries
    gen_notification_entry('notify-success', True, 'SUCCESS')
    gen_notification_entry('notify-failure', True, 'FAILURE')
    gen_notification_entry('notify-fixed', True, 'FIXED')
    gen_notification_entry('notify-unstable', False, 'UNSTABLE')
    gen_notification_entry('notify-aborted', False, 'ABORTED')
    gen_notification_entry('notify-notbuilt', False, 'NOT_BUILT')

    # notification settings
    gen_setting('Success', True)
    gen_setting('Failure', True)
    gen_setting('Fixed', True)
    gen_setting('Unstable', False)
    gen_setting('Aborted', False)
    gen_setting('NotBuilt', False)


def clamav(registry, xml_parent, data):
    """yaml: clamav
    Check files with ClamAV, an open source antivirus engine.
    Requires the Jenkins :jenkins-wiki:`ClamAV Plugin <ClamAV+Plugin>`.

    :arg str includes: Comma seperated list of files that should be scanned.
        Must be set for ClamAV to check for artifacts. (default '')
    :arg str excludes: Comma seperated list of files that should be ignored
        (default '')

    Full Example:

    .. literalinclude:: /../../tests/publishers/fixtures/clamav-full.yaml
       :language: yaml

    Minimal Example:

    .. literalinclude:: /../../tests/publishers/fixtures/clamav-minimal.yaml
       :language: yaml
    """
    clamav = XML.SubElement(
        xml_parent,
        'org.jenkinsci.plugins.clamav.ClamAvRecorder')
    clamav.set('plugin', 'clamav')

    mappings = [
        ('includes', 'includes', ''),
        ('excludes', 'excludes', ''),
    ]
    helpers.convert_mapping_to_xml(clamav, data, mappings, fail_required=True)


def testselector(registry, xml_parent, data):
    """yaml: testselector
    This plugin allows you to choose specific tests you want to run.

    Requires the Jenkins :jenkins-wiki:`Tests Selector Plugin
    <Tests+Selector+Plugin>`.

    :arg str name: Environment variable in which selected tests are saved
      (required)
    :arg str description: Description
      (default "")
    :arg str properties-file: Contain all your tests
      (required)
    :arg str enable-field: Imply if the test is enabled or not
      (default "")
    :arg str groupby: Plugin will group the tests by
      (default "")
    :arg str field-sperator: Separate between the fields in the tests tree
      (default "")
    :arg str show-fields: Shown in the tests tree
      (default "")
    :arg str multiplicity-field: Amount of times the test should run
      (default "")

    Example:

    .. literalinclude:: /../../tests/publishers/fixtures/testselector001.yaml
       :language: yaml
    """

    testselector = XML.SubElement(xml_parent, 'il.ac.technion.jenkins.plugins'
                                              'TestExecuter')
    try:
        name = str(data['name'])
    except KeyError as e:
        raise MissingAttributeError(e.args[0])
    try:
        propertiesfile = str(data['properties-file'])
    except KeyError as e:
        raise MissingAttributeError(e.args[0])
    XML.SubElement(testselector, 'name').text = name
    XML.SubElement(testselector, 'description').text = data.get(
        'description', '')
    XML.SubElement(testselector, 'propertiesFilePath').text = propertiesfile
    XML.SubElement(testselector, 'enableField').text = data.get(
        'enable-field', '')
    XML.SubElement(testselector, 'groupBy').text = data.get(
        'groupby', '')
    XML.SubElement(testselector, 'fieldSeparator').text = data.get(
        'field-separator', '')
    XML.SubElement(testselector, 'showFields').text = data.get(
        'show-fields', '')
    XML.SubElement(testselector, 'multiplicityField').text = data.get(
        'multiplicity-field', '')


def cloudformation(registry, xml_parent, data):
    """yaml: cloudformation
    Create cloudformation stacks before running a build and optionally
    delete them at the end.  Requires the Jenkins :jenkins-wiki:`AWS
    Cloudformation Plugin <AWS+Cloudformation+Plugin>`.

    :arg list create-stacks: List of stacks to create

        :create-stacks attributes:
            * **arg str name** - The name of the stack (Required)
            * **arg str description** - Description of the stack (Optional)
            * **arg str recipe** - The cloudformation recipe file (Required)
            * **arg list parameters** - A list of key/value pairs, will be
              joined together into a comma separated string (Optional)
            * **arg int timeout** - Number of seconds to wait before giving up
              creating a stack (default 0)
            * **arg str access-key** - The Amazon API Access Key (Required)
            * **arg str secret-key** - The Amazon API Secret Key (Required)
            * **arg int sleep** - Number of seconds to wait before continuing
              to the next step (default 0)
            * **arg array region** - The region to run cloudformation in.
              (Required)

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
    :arg list delete-stacks: List of stacks to delete

        :delete-stacks attributes:
            * **arg list name** - The names of the stacks to delete (Required)
            * **arg str access-key** - The Amazon API Access Key (Required)
            * **arg str secret-key** - The Amazon API Secret Key (Required)
            * **arg bool prefix** - If selected the tear down process will look
              for the stack that Starts with the stack name with the oldest
              creation date and will delete it.  (default false)
            * **arg array region** - The region to run cloudformation in.
              (Required)

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

    .. literalinclude:: /../../tests/publishers/fixtures/cloudformation.yaml
       :language: yaml
    """
    region_dict = helpers.cloudformation_region_dict()
    stacks = helpers.cloudformation_init(
        xml_parent, data, 'CloudFormationPostBuildNotifier')
    for stack in data.get('create-stacks', []):
        helpers.cloudformation_stack(xml_parent, stack, 'PostBuildStackBean',
                                     stacks, region_dict)
    delete_stacks = helpers.cloudformation_init(
        xml_parent, data, 'CloudFormationNotifier')
    for delete_stack in data.get('delete-stacks', []):
        helpers.cloudformation_stack(xml_parent, delete_stack,
                                     'SimpleStackBean', delete_stacks,
                                     region_dict)


def whitesource(registry, xml_parent, data):
    """yaml: whitesource
    This plugin brings automatic open source management to Jenkins users.

    Requires the Jenkins :jenkins-wiki:`Whitesource Plugin
    <Whitesource+Plugin>`.

    :arg str product-token: Product name or token to update (default '')
    :arg str version: Product version (default '')
    :arg str override-token: Override the api token from the global config
        (default '')
    :arg str project-token: Token uniquely identifying the project to update
        (default '')
    :arg list includes: list of libraries to include (default '[]')
    :arg list excludes: list of libraries to exclude (default '[]')
    :arg str policies: Whether to override the global settings.  Valid values:
        global, enable, disable (default 'global')
    :arg str requester-email: Email of the WhiteSource user that requests to
        update WhiteSource (>=1.5.1) (default '')

    Full Example:

    .. literalinclude:: /../../tests/publishers/fixtures/whitesource-full.yaml
       :language: yaml

    Minimal Example:

    .. literalinclude::
       /../../tests/publishers/fixtures/whitesource-minimal.yaml
       :language: yaml
    """
    whitesource = XML.SubElement(xml_parent, 'org.whitesource.jenkins.'
                                             'WhiteSourcePublisher')
    whitesource.set('plugin', 'whitesource')
    policies = ['global', 'enable', 'disable']

    mappings = [
        ('policies', 'jobCheckPolicies', 'global', policies),
        ('override-token', 'jobApiToken', ''),
        ('product-token', 'product', ''),
        ('version', 'productVersion', ''),
        ('project-token', 'projectToken', ''),
        ('requester-email', 'requesterEmail', ''),
    ]
    helpers.convert_mapping_to_xml(
        whitesource, data, mappings, fail_required=True)

    XML.SubElement(whitesource, 'libIncludes').text = ' '.join(
        data.get('includes', []))
    XML.SubElement(whitesource, 'libExcludes').text = ' '.join(
        data.get('excludes', []))
    XML.SubElement(whitesource, 'ignorePomModules').text = 'false'


def hipchat(registry, xml_parent, data):
    """yaml: hipchat
    Publisher that sends hipchat notifications on job events
    Requires the Jenkins :jenkins-wiki:`Hipchat Plugin
    <Hipchat+Plugin>` version >=1.9

    Please see documentation for older plugin version
    http://docs.openstack.org/infra/jenkins-job-builder/hipchat.html

    :arg str token: This will override the default auth token (optional)
    :arg list rooms: list of HipChat rooms to post messages to, overrides
        global default (optional)
    :arg bool notify-start: post messages about build start event
        (default false)
    :arg bool notify-success: post messages about successful build event
        (default false)
    :arg bool notify-aborted: post messages about aborted build event
        (default false)
    :arg bool notify-not-built: post messages about build set to NOT_BUILT.
        This status code is used in a multi-stage build where a problem in
        earlier stage prevented later stages from building. (default false)
    :arg bool notify-unstable: post messages about unstable build event
        (default false)
    :arg bool notify-failure:  post messages about build failure event
        (default false)
    :arg bool notify-back-to-normal: post messages about build being back to
        normal after being unstable or failed (default false)
    :arg str start-message: This will override the default start message
        (optional)
    :arg str complete-message: This will override the default complete message
        (optional)

    Example:

    .. literalinclude::  /../../tests/publishers/fixtures/hipchat001.yaml
       :language: yaml
    """
    hipchat = XML.SubElement(
        xml_parent,
        'jenkins.plugins.hipchat.HipChatNotifier')
    XML.SubElement(hipchat, 'token').text = str(
        data.get('token', ''))

    if 'rooms' in data:
        XML.SubElement(hipchat, 'room').text = str(
            ",".join(data['rooms']))

    mapping = [
        ('notify-start', 'startNotification', False),
        ('notify-success', 'notifySuccess', False),
        ('notify-aborted', 'notifyAborted', False),
        ('notify-not-built', 'notifyNotBuilt', False),
        ('notify-unstable', 'notifyUnstable', False),
        ('notify-failure', 'notifyFailure', False),
        ('notify-back-to-normal', 'notifyBackToNormal', False),
    ]
    helpers.convert_mapping_to_xml(hipchat, data, mapping, fail_required=True)

    # optional settings, so only add XML in if set.
    if 'start-message' in data:
        XML.SubElement(hipchat, 'startJobMessage').text = str(
            data['start-message'])
    if 'complete-message' in data:
        XML.SubElement(hipchat, 'completeJobMessage').text = str(
            data['complete-message'])


def slack(registry, xml_parent, data):
    """yaml: slack
    Publisher that sends slack notifications on job events.

    Requires the Jenkins :jenkins-wiki:`Slack Plugin <Slack+Plugin>`

    When using Slack Plugin version < 2.0, Slack Plugin itself requires a
    publisher aswell as properties please note that you have to create those
    too.  When using Slack Plugin version >= 2.0, you should only configure the
    publisher.

    :arg str team-domain: Your team's domain at slack. (default '')
    :arg str auth-token: The integration token to be used when sending
        notifications. (default '')
    :arg str build-server-url: Specify the URL for your server installation.
        (default '/')
    :arg str room: A comma seperated list of rooms / channels to post the
        notifications to. (default '')
    :arg bool notify-start: Send notification when the job starts (>=2.0).
        (default false)
    :arg bool notify-success: Send notification on success (>=2.0).
        (default false)
    :arg bool notify-aborted: Send notification when job is aborted (>=2.0).
        (default false)
    :arg bool notify-not-built: Send notification when job set to NOT_BUILT
        status (>=2.0). (default false)
    :arg bool notify-unstable: Send notification when job becomes unstable
        (>=2.0). (default false)
    :arg bool notify-failure: Send notification when job fails for the first
        time (previous build was a success) (>=2.0).  (default false)
    :arg bool notifiy-back-to-normal: Send notification when job is succeeding
        again after being unstable or failed (>=2.0). (default false)
    :arg bool notify-repeated-failure: Send notification when job fails
        successively (previous build was also a failure) (>=2.0).
        (default false)
    :arg bool include-test-summary: Include the test summary (>=2.0).
        (default false)
    :arg str commit-info-choice: What commit information to include into
        notification message, "NONE" includes nothing about commits, "AUTHORS"
        includes commit list with authors only, and "AUTHORS_AND_TITLES"
        includes commit list with authors and titles (>=2.0). (default "NONE")
    :arg bool include-custom-message: Include a custom message into the
        notification (>=2.0). (default false)
    :arg str custom-message: Custom message to be included (>=2.0).
        (default '')

    Example (version < 2.0):

    .. literalinclude::
        /../../tests/publishers/fixtures/slack001.yaml
        :language: yaml

    Minimal example (version >= 2.0):

    .. literalinclude::
        /../../tests/publishers/fixtures/slack003.yaml
        :language: yaml

    Full example (version >= 2.0):

    .. literalinclude::
        /../../tests/publishers/fixtures/slack004.yaml
        :language: yaml

    """
    def _add_xml(elem, name, value=''):
        if isinstance(value, bool):
            value = str(value).lower()
        XML.SubElement(elem, name).text = value

    logger = logging.getLogger(__name__)

    plugin_info = registry.get_plugin_info('Slack Notification Plugin')
    plugin_ver = pkg_resources.parse_version(plugin_info.get('version', "0"))

    mapping = (
        ('team-domain', 'teamDomain', ''),
        ('auth-token', 'authToken', ''),
        ('build-server-url', 'buildServerUrl', '/'),
        ('room', 'room', ''),
    )
    mapping_20 = (
        ('notify-start', 'startNotification', False),
        ('notify-success', 'notifySuccess', False),
        ('notify-aborted', 'notifyAborted', False),
        ('notify-not-built', 'notifyNotBuilt', False),
        ('notify-unstable', 'notifyUnstable', False),
        ('notify-failure', 'notifyFailure', False),
        ('notify-back-to-normal', 'notifyBackToNormal', False),
        ('notify-repeated-failure', 'notifyRepeatedFailure', False),
        ('include-test-summary', 'includeTestSummary', False),
        ('commit-info-choice', 'commitInfoChoice', 'NONE'),
        ('include-custom-message', 'includeCustomMessage', False),
        ('custom-message', 'customMessage', ''),
    )

    commit_info_choices = ['NONE', 'AUTHORS', 'AUTHORS_AND_TITLES']

    slack = XML.SubElement(
        xml_parent,
        'jenkins.plugins.slack.SlackNotifier',
    )

    if plugin_ver >= pkg_resources.parse_version("2.0"):
        mapping = mapping + mapping_20

    if plugin_ver < pkg_resources.parse_version("2.0"):
        for yaml_name, _, default_value in mapping:
            # All arguments that don't have a default value are mandatory for
            # the plugin to work as intended.
            if not data.get(yaml_name, default_value):
                raise MissingAttributeError(yaml_name)

        for yaml_name, _, _ in mapping_20:
            if yaml_name in data:
                logger.warning(
                    "'%s' is invalid with plugin version < 2.0, ignored",
                    yaml_name,
                )

    for yaml_name, xml_name, default_value in mapping:
        value = data.get(yaml_name, default_value)

        # 'commit-info-choice' is enumerated type
        if yaml_name == 'commit-info-choice':
            if value not in commit_info_choices:
                raise InvalidAttributeError(
                    yaml_name, value, commit_info_choices,
                )

        # Ensure that custom-message is set when include-custom-message is set
        # to true.
        if yaml_name == 'include-custom-message' and data is False:
            if not data.get('custom-message', ''):
                raise MissingAttributeError('custom-message')

        _add_xml(slack, xml_name, value)


def phabricator(registry, xml_parent, data):
    """yaml: phabricator
    Integrate with `Phabricator <http://phabricator.org/>`_

    Requires the Jenkins :jenkins-wiki:`Phabricator Plugin
    <Phabricator+Differential+Plugin>`.

    :arg bool comment-on-success: Post a *comment* when the build
      succeeds. (optional)
    :arg bool uberalls-enabled: Integrate with uberalls. (optional)
    :arg str comment-file: Include contents of given file if
      commenting is enabled. (optional)
    :arg int comment-size: Maximum comment character length. (optional)
    :arg bool comment-with-console-link-on-failure: Post a *comment*
      when the build fails. (optional)

    Example:

    .. literalinclude::
        /../../tests/publishers/fixtures/phabricator001.yaml
       :language: yaml
    """

    root = XML.SubElement(xml_parent,
                          'com.uber.jenkins.phabricator.PhabricatorNotifier')

    if 'comment-on-success' in data:
        XML.SubElement(root, 'commentOnSuccess').text = str(
            data.get('comment-on-success')).lower()
    if 'uberalls-enabled' in data:
        XML.SubElement(root, 'uberallsEnabled').text = str(
            data.get('uberalls-enabled')).lower()
    if 'comment-file' in data:
        XML.SubElement(root, 'commentFile').text = data.get('comment-file')
    if 'comment-size' in data:
        XML.SubElement(root, 'commentSize').text = str(
            data.get('comment-size'))
    if 'comment-with-console-link-on-failure' in data:
        XML.SubElement(root, 'commentWithConsoleLinkOnFailure').text = str(
            data.get('comment-with-console-link-on-failure')).lower()


def openshift_build_canceller(registry, xml_parent, data):
    """yaml: openshift-build-canceller
    This action is intended to provide cleanup for a Jenkins job which failed
    because a build is hung (instead of terminating with a failure code);
    this step will allow you to perform the equivalent of a oc cancel-build
    for the provided build config; any builds under that build config which
    are not previously terminated (either successfully or unsuccessfully)
    or cancelled will be cancelled.
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
        ../../tests/publishers/fixtures/openshift-build-canceller001.yaml
       :language: yaml

    Minimal Example:

    .. literalinclude::
        ../../tests/publishers/fixtures/openshift-build-canceller002.yaml
       :language: yaml
    """

    osb = XML.SubElement(xml_parent,
                         'com.openshift.jenkins.plugins.pipeline.'
                         'OpenShiftBuildCanceller')
    mapping = [
        # option, xml name, default value
        ("api-url", 'apiURL', 'https://openshift.default.svc.cluster.local'),
        ("bld-cfg", 'bldCfg', 'frontend'),
        ("namespace", 'namespace', 'test'),
        ("auth-token", 'authToken', ''),
        ("verbose", 'verbose', False),
    ]
    helpers.convert_mapping_to_xml(osb, data, mapping, fail_required=True)


def openshift_deploy_canceller(registry, xml_parent, data):
    """yaml: openshift-deploy-canceller
    This action is intended to provide cleanup for any OpenShift deployments
    left running when the Job completes; this step will allow you to perform
    the equivalent of a oc deploy --cancel for the provided deployment config.
    Requires the Jenkins :jenkins-wiki:`OpenShift
    Pipeline Plugin <OpenShift+Pipeline+Plugin>`.

    :arg str api-url: this would be the value you specify if you leverage the
        --server option on the OpenShift `oc` command.
        (default '\https://openshift.default.svc.cluster.local')
    :arg str dep-cfg: The value here should be whatever was the output
        form `oc project` when you created the BuildConfig you want to run a
        Build on (default frontend)
    :arg str namespace: If you run `oc get bc` for the project listed in
        "namespace", that is the value you want to put here. (default 'test')
    :arg str auth-token: The value here is what you supply with the --token
        option when invoking the OpenShift `oc` command. (default '')
    :arg bool verbose: This flag is the toggle for
        turning on or off detailed logging in this plug-in. (default false)

    Full Example:

    .. literalinclude::
        ../../tests/publishers/fixtures/openshift-deploy-canceller001.yaml
       :language: yaml

    Minimal Example:

    .. literalinclude::
        ../../tests/publishers/fixtures/openshift-deploy-canceller002.yaml
       :language: yaml
    """

    osb = XML.SubElement(xml_parent,
                         'com.openshift.jenkins.plugins.pipeline.'
                         'OpenShiftDeployCanceller')
    mapping = [
        # option, xml name, default value
        ("api-url", 'apiURL', 'https://openshift.default.svc.cluster.local'),
        ("dep-cfg", 'depCfg', 'frontend'),
        ("namespace", 'namespace', 'test'),
        ("auth-token", 'authToken', ''),
        ("verbose", 'verbose', False),
    ]
    helpers.convert_mapping_to_xml(osb, data, mapping, fail_required=True)


def github_pull_request_merge(registry, xml_parent, data):
    """yaml: github-pull-request-merge
    This action merges the pull request that triggered the build (see the
    github pull request trigger)
    Requires the Jenkins :jenkins-wiki:`GitHub pull request builder plugin
    <GitHub+pull+request+builder+plugin>`.


    :arg bool only-admins-merge: if `true` only administrators can merge the
        pull request, (default false)
    :arg bool disallow-own-code: if `true` will allow merging your own pull
        requests, in opposite to needing someone else to trigger the merge.
        (default false)
    :arg str merge-comment: Comment to set on the merge commit (default '')
    :arg bool fail-on-non-merge: fail the job if the merge was unsuccessful
        (default false)
    :arg bool delete-on-merge: Delete the branch of the pull request on
        successful merge (default false)

    Full Example:

    .. literalinclude::
        ../../tests/publishers/fixtures/github-pull-request-merge001.yaml
       :language: yaml

    Minimal Example:

    .. literalinclude::
        ../../tests/publishers/fixtures/github-pull-request-merge002.yaml
       :language: yaml
    """

    osb = XML.SubElement(xml_parent,
                         'org.jenkinsci.plugins.ghprb.GhprbPullRequestMerge')
    mapping = [
        # option, xml name, default value
        ("only-admins-merge", 'onlyAdminsMerge', 'false'),
        ("disallow-own-code", 'disallowOwnCode', 'false'),
        ("merge-comment", 'mergeComment', ''),
        ("fail-on-non-merge", 'failOnNonMerge', 'false'),
        ("delete-on-merge", 'deleteOnMerge', 'false'),
    ]

    helpers.convert_mapping_to_xml(osb, data, mapping, fail_required=True)


class Publishers(jenkins_jobs.modules.base.Base):
    sequence = 70

    component_type = 'publisher'
    component_list_type = 'publishers'

    def gen_xml(self, xml_parent, data):
        publishers = XML.SubElement(xml_parent, 'publishers')

        for action in data.get('publishers', []):
            self.registry.dispatch('publisher', publishers, action)
