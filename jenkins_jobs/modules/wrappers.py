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
Wrappers can alter the way the build is run as well as the build output.

**Component**: wrappers
  :Macro: wrapper
  :Entry Point: jenkins_jobs.wrappers

"""

import logging
import pkg_resources
import sys
import xml.etree.ElementTree as XML

from jenkins_jobs.errors import InvalidAttributeError
from jenkins_jobs.errors import JenkinsJobsException
import jenkins_jobs.modules.base
from jenkins_jobs.modules.builders import create_builders
import jenkins_jobs.modules.helpers as helpers

logger = logging.getLogger(__name__)

MIN_TO_SEC = 60


def docker_custom_build_env(registry, xml_parent, data):
    """yaml: docker-custom-build-env
    Allows the definition of a build environment for a job using a Docker
    container.
    Requires the Jenkins :jenkins-wiki:`CloudBees Docker Custom Build
    Environment Plugin<CloudBees+Docker+Custom+Build+Environment+Plugin>`.

    :arg str image-type: Docker image type. Valid values and their
        additional attributes described in the image_types_ table
    :arg str docker-tool: The name of the docker installation to use
        (default 'Default')
    :arg str host: URI to the docker host you are using
    :arg str credentials-id: Argument to specify the ID of credentials to use
        for docker host (optional)
    :arg str registry-credentials-id: Argument to specify the ID of
        credentials to use for docker registry (optional)
    :arg list volumes: Volumes to bind mound from slave host into container

        :volume: * **host-path** (`str`) Path on host
                 * **path** (`str`) Path inside container

    :arg bool verbose: Log docker commands executed by plugin on build log
        (default false)
    :arg bool privileged: Run in privileged mode (default false)
    :arg bool force-pull: Force pull (default false)
    :arg str group: The user to run build has to be the same as the Jenkins
        slave user so files created in workspace have adequate owner and
        permission set
    :arg str command: Container start command (default '/bin/cat')
    :arg str net: Network bridge (default 'bridge')

    .. _image_types:

    ================== ====================================================
    Image Type         Description
    ================== ====================================================
    dockerfile         Build docker image from a Dockerfile in project
                       workspace. With this option, project can define the
                       build environment as a Dockerfile stored in SCM with
                       project source code

                         :context-path: (str) Path to docker context
                           (default '.')
                         :dockerfile: (str) Use an alternate Dockerfile to
                           build the container hosting this build
                           (default 'Dockerfile')
    pull               Pull specified docker image from Docker repository

                         :image: (str) Image id/tag
    ================== ====================================================

    Example:

    .. literalinclude::
        /../../tests/wrappers/fixtures/docker-custom-build-env001.yaml
       :language: yaml
    """
    core_prefix = 'com.cloudbees.jenkins.plugins.okidocki.'
    entry_xml = XML.SubElement(
        xml_parent, core_prefix + 'DockerBuildWrapper')
    entry_xml.set('plugin', 'docker-custom-build-environment')

    selectorobj = XML.SubElement(entry_xml, 'selector')
    image_type = data['image-type']
    if image_type == 'dockerfile':
        selectorobj.set('class', core_prefix + 'DockerfileImageSelector')
        dockerfile_mapping = [
            ('context-path', 'contextPath', '.'),
            ('dockerfile', 'dockerfile', 'Dockerfile'),
        ]
        helpers.convert_mapping_to_xml(selectorobj, data,
            dockerfile_mapping, fail_required=True)

    elif image_type == 'pull':
        selectorobj.set('class', core_prefix + 'PullDockerImageSelector')
        pull_mapping = [
            ('image', 'image', ''),
        ]
        helpers.convert_mapping_to_xml(selectorobj, data,
            pull_mapping, fail_required=True)

    XML.SubElement(entry_xml, 'dockerInstallation').text = data.get(
        'docker-tool', 'Default')

    host = XML.SubElement(entry_xml, 'dockerHost')
    host.set('plugin', 'docker-commons')
    mapping_optional = [
        ('host', 'uri', None),
        ('credentials-id', 'credentialsId', None),
    ]
    helpers.convert_mapping_to_xml(
        host, data, mapping_optional, fail_required=False)

    XML.SubElement(entry_xml, 'dockerRegistryCredentials').text = data.get(
        'registry-credentials-id', '')
    volumesobj = XML.SubElement(entry_xml, 'volumes')
    volumes = data.get('volumes', [])
    if not volumes:
        volumesobj.set('class', 'empty-list')
    else:
        for volume in volumes:
            volumeobj = XML.SubElement(
                volumesobj, 'com.cloudbees.jenkins.plugins.okidocki.Volume')
            XML.SubElement(volumeobj, 'hostPath').text = volume['volume'].get(
                'host-path', '')
            XML.SubElement(volumeobj, 'path').text = volume['volume'].get(
                'path', '')
    mapping = [
        ('force-pull', 'forcePull', False),
        ('privileged', 'privileged', False),
        ('verbose', 'verbose', False),
        ('group', 'group', ''),
        ('command', 'command', '/bin/cat'),
        ('net', 'net', 'bridge'),
    ]
    helpers.convert_mapping_to_xml(
        entry_xml, data, mapping, fail_required=True)


def ci_skip(registry, xml_parent, data):
    """yaml: ci-skip
    Skip making a build for certain push.
    Just add [ci skip] into your commit's message to let Jenkins know,
    that you do not want to perform build for the next push.
    Requires the Jenkins :jenkins-wiki:`Ci Skip Plugin <Ci+Skip+Plugin>`.

    Example:

    .. literalinclude:: /../../tests/wrappers/fixtures/ci-skip001.yaml
    """
    rpobj = XML.SubElement(xml_parent, 'ruby-proxy-object')
    robj = XML.SubElement(rpobj, 'ruby-object', attrib={
        'pluginid': 'ci-skip',
        'ruby-class': 'Jenkins::Tasks::BuildWrapperProxy'
    })
    pluginid = XML.SubElement(robj, 'pluginid', {
        'pluginid': 'ci-skip', 'ruby-class': 'String'
    })
    pluginid.text = 'ci-skip'
    obj = XML.SubElement(robj, 'object', {
        'ruby-class': 'CiSkipWrapper', 'pluginid': 'ci-skip'
    })
    XML.SubElement(obj, 'ci__skip', {
        'pluginid': 'ci-skip', 'ruby-class': 'NilClass'
    })


def config_file_provider(registry, xml_parent, data):
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
                (default '')
              * **variable** (`str`) -- Define an environment variable to be
                used (default '')
              * **replace-tokens** (`bool`) -- Replace tokens in config file.
                For example "password: ${PYPI_JENKINS_PASS}" will be replaced
                with the global variable configured in Jenkins.

    Example:

    .. literalinclude:: \
    /../../tests/wrappers/fixtures/config-file-provider003.yaml
       :language: yaml
    """
    cfp = XML.SubElement(xml_parent, 'org.jenkinsci.plugins.configfiles.'
                         'buildwrapper.ConfigFileBuildWrapper')
    cfp.set('plugin', 'config-file-provider')
    helpers.config_file_provider_builder(cfp, data)


def logfilesize(registry, xml_parent, data):
    """yaml: logfilesize
    Abort the build if its logfile becomes too big.
    Requires the Jenkins :jenkins-wiki:`Logfilesizechecker Plugin
    <Logfilesizechecker+Plugin>`.

    :arg bool set-own: Use job specific maximum log size instead of global
        config value (default false).
    :arg bool fail: Make builds aborted by this wrapper be marked as "failed"
        (default false).
    :arg int size: Abort the build if logfile size is bigger than this
        value (in MiB, default 128). Only applies if set-own is true.

    Full Example:

    .. literalinclude:: /../../tests/wrappers/fixtures/logfilesize-full.yaml

    Minimal Example:

    .. literalinclude:: /../../tests/wrappers/fixtures/logfilesize-minimal.yaml
    """
    lfswrapper = XML.SubElement(xml_parent,
                                'hudson.plugins.logfilesizechecker.'
                                'LogfilesizecheckerWrapper')
    lfswrapper.set("plugin", "logfilesizechecker")

    mapping = [
        ('set-own', 'setOwn', False),
        ('size', 'maxLogSize', 128),
        ('fail', 'failBuild', False),
    ]
    helpers.convert_mapping_to_xml(
        lfswrapper, data, mapping, fail_required=True)


def timeout(registry, xml_parent, data):
    """yaml: timeout
    Abort the build if it runs too long.
    Requires the Jenkins :jenkins-wiki:`Build Timeout Plugin
    <Build-timeout+Plugin>`.

    :arg bool fail: Mark the build as failed (default false)
    :arg bool abort: Mark the build as aborted (default false)
    :arg bool write-description: Write a message in the description
        (default false)
    :arg int timeout: Abort the build after this number of minutes (default 3)
    :arg str timeout-var: Export an environment variable to reference the
        timeout value (optional)
    :arg str type: Timeout type to use (default absolute)
    :type values:
        * **likely-stuck**
        * **no-activity**
        * **elastic**
        * **absolute**
        * **deadline**

    :arg int elastic-percentage: Percentage of the three most recent builds
        where to declare a timeout, only applies to **elastic** type.
        (default 0)
    :arg int elastic-number-builds: Number of builds to consider computing
        average duration, only applies to **elastic** type. (default 3)
    :arg int elastic-default-timeout: Timeout to use if there were no previous
        builds, only applies to **elastic** type. (default 3)

    :arg str deadline-time: Build terminate automatically at next deadline time
        (HH:MM:SS), only applies to **deadline** type. (default 0:00:00)
    :arg int deadline-tolerance: Period in minutes after deadline when a job
        should be immediately aborted, only applies to **deadline** type.
        (default 1)

    Example (Version < 1.14):

    .. literalinclude:: /../../tests/wrappers/fixtures/timeout/timeout001.yaml

    .. literalinclude:: /../../tests/wrappers/fixtures/timeout/timeout002.yaml

    .. literalinclude:: /../../tests/wrappers/fixtures/timeout/timeout003.yaml

    Example (Version >= 1.14):

    .. literalinclude::
        /../../tests/wrappers/fixtures/timeout/version-1.14/absolute001.yaml

    .. literalinclude::
        /../../tests/wrappers/fixtures/timeout/version-1.14/no-activity001.yaml

    .. literalinclude::
        /../../tests/wrappers/fixtures/timeout/version-1.14/likely-stuck001.yaml

    .. literalinclude::
        /../../tests/wrappers/fixtures/timeout/version-1.14/elastic001.yaml

    .. literalinclude::
        /../../tests/wrappers/fixtures/timeout/version-1.15/deadline001.yaml

    """
    prefix = 'hudson.plugins.build__timeout.'
    twrapper = XML.SubElement(xml_parent, prefix + 'BuildTimeoutWrapper')

    plugin_info = registry.get_plugin_info("Build Timeout")
    if "version" not in plugin_info:
        plugin_info = registry.get_plugin_info("Jenkins build timeout plugin")
    version = plugin_info.get("version", None)
    if version:
        version = pkg_resources.parse_version(version)

    valid_strategies = ['absolute', 'no-activity', 'likely-stuck', 'elastic',
                        'deadline']

    # NOTE(toabctl): if we don't know the version assume that we
    # use a newer version of the plugin
    if not version or version >= pkg_resources.parse_version("1.14"):
        strategy = data.get('type', 'absolute')
        if strategy not in valid_strategies:
            InvalidAttributeError('type', strategy, valid_strategies)

        if strategy == "absolute":
            strategy_element = XML.SubElement(
                twrapper, 'strategy',
                {'class': "hudson.plugins.build_timeout."
                          "impl.AbsoluteTimeOutStrategy"})
            mapping = [
                ('timeout', 'timeoutMinutes', 3),
            ]
            helpers.convert_mapping_to_xml(strategy_element,
                data, mapping, fail_required=True)
        elif strategy == "no-activity":
            strategy_element = XML.SubElement(
                twrapper, 'strategy',
                {'class': "hudson.plugins.build_timeout."
                          "impl.NoActivityTimeOutStrategy"})
            timeout_sec = int(data.get('timeout', 3)) * MIN_TO_SEC
            mapping = [
                ('', 'timeoutSecondsString', timeout_sec),
            ]
            helpers.convert_mapping_to_xml(strategy_element,
                data, mapping, fail_required=True)
        elif strategy == "likely-stuck":
            strategy_element = XML.SubElement(
                twrapper, 'strategy',
                {'class': "hudson.plugins.build_timeout."
                          "impl.LikelyStuckTimeOutStrategy"})
            mapping = [
                ('timeout', 'timeoutMinutes', 3),
            ]
            helpers.convert_mapping_to_xml(strategy_element,
                data, mapping, fail_required=True)
        elif strategy == "elastic":
            strategy_element = XML.SubElement(
                twrapper, 'strategy',
                {'class': "hudson.plugins.build_timeout."
                          "impl.ElasticTimeOutStrategy"})
            mapping = [
                ('elastic-percentage', 'timeoutPercentage', 0),
                ('elastic-number-builds', 'numberOfBuilds', 0),
                ('elastic-default-timeout', 'timeoutMinutesElasticDefault', 3),
            ]
            helpers.convert_mapping_to_xml(strategy_element,
                data, mapping, fail_required=True)

        elif strategy == "deadline":
            strategy_element = XML.SubElement(
                twrapper, 'strategy',
                {'class': "hudson.plugins.build_timeout."
                          "impl.DeadlineTimeOutStrategy"})
            deadline_time = str(data.get('deadline-time', '0:00:00'))
            deadline_tolerance = int(data.get('deadline-tolerance', 1))
            mapping = [
                ('', 'deadlineTime', deadline_time),
                ('', 'deadlineToleranceInMinutes', deadline_tolerance),
            ]
            helpers.convert_mapping_to_xml(strategy_element,
                data, mapping, fail_required=True)

        actions = []

        for action in ['fail', 'abort']:
            if str(data.get(action, 'false')).lower() == 'true':
                actions.append(action)

        # Set the default action to "abort"
        if len(actions) == 0:
            actions.append("abort")

        description = data.get('write-description', None)
        if description is not None:
            actions.append('write-description')

        operation_list = XML.SubElement(twrapper, 'operationList')

        for action in actions:
            fmt_str = prefix + "operations.{0}Operation"
            if action == "abort":
                XML.SubElement(operation_list, fmt_str.format("Abort"))
            elif action == "fail":
                XML.SubElement(operation_list, fmt_str.format("Fail"))
            elif action == "write-description":
                write_description = XML.SubElement(
                    operation_list, fmt_str.format("WriteDescription"))
                XML.SubElement(write_description, "description"
                               ).text = description
            else:
                raise JenkinsJobsException("Unsupported BuiltTimeoutWrapper "
                                           "plugin action: {0}".format(action))
        mapping = [
            ('timeout-var', 'timeoutEnvVar', None),
        ]
        helpers.convert_mapping_to_xml(twrapper,
            data, mapping, fail_required=False)
    else:
        mapping = [
            ('timeout', 'timeoutMinutes', 3),
            ('timeout-var', 'timeoutEnvVar', None),
            ('fail', 'failBuild', 'false'),
            ('write-description', 'writingDescription', 'false'),
            ('elastic-percentage', 'timeoutPercentage', 0),
            ('elastic-default-timeout', 'timeoutMinutesElasticDefault', 3),
        ]
        helpers.convert_mapping_to_xml(twrapper,
                data, mapping, fail_required=False)

        tout_type = str(data.get('type', 'absolute')).lower()
        if tout_type == 'likely-stuck':
            tout_type = 'likelyStuck'
        XML.SubElement(twrapper, 'timeoutType').text = tout_type


def timestamps(registry, xml_parent, data):
    """yaml: timestamps
    Add timestamps to the console log.
    Requires the Jenkins :jenkins-wiki:`Timestamper Plugin <Timestamper>`.

    Example::

      wrappers:
        - timestamps
    """
    XML.SubElement(xml_parent,
                   'hudson.plugins.timestamper.TimestamperBuildWrapper')


def ansicolor(registry, xml_parent, data):
    """yaml: ansicolor
    Translate ANSI color codes to HTML in the console log.
    Requires the Jenkins :jenkins-wiki:`Ansi Color Plugin <AnsiColor+Plugin>`.

    :arg string colormap: (optional) color mapping to use

    Examples::

      wrappers:
        - ansicolor

      # Explicitly setting the colormap
      wrappers:
        - ansicolor:
            colormap: vga
    """
    cwrapper = XML.SubElement(
        xml_parent,
        'hudson.plugins.ansicolor.AnsiColorBuildWrapper')
    mapping = [
        ('colormap', 'colorMapName', None),
    ]
    helpers.convert_mapping_to_xml(
        cwrapper, data, mapping, fail_required=False)


def build_keeper(registry, xml_parent, data):
    """yaml: build-keeper
    Keep builds based on specific policy.
    Requires the Jenkins :jenkins-wiki:`Build Keeper Plugin
    <Build+Keeper+Plugin>`.

    :arg str policy: Policy to keep builds.

        :policy values:
          * **by-day**
          * **keep-since**
          * **build-number**
          * **keep-first-failed**
    :arg int build-period: Number argument to calculate build to keep,
        depends on the policy. (default 0)
    :arg bool dont-keep-failed: Flag to indicate if to keep failed builds.
        (default false)
    :arg int number-of-fails: number of consecutive failed builds in order
        to mark first as keep forever, only applies to keep-first-failed
        policy (default 0)

    Example:

    .. literalinclude:: /../../tests/wrappers/fixtures/build-keeper0001.yaml

    .. literalinclude:: /../../tests/wrappers/fixtures/build-keeper0002.yaml

    """
    root = XML.SubElement(xml_parent,
                          'org.jenkins__ci.plugins.build__keeper.BuildKeeper')

    valid_policies = ('by-day', 'keep-since', 'build-number',
                      'keep-first-failed')
    policy = data.get('policy')

    mapping = [
        ('build-period', 'buildPeriod', 0),
        ('dont-keep-failed', 'dontKeepFailed', False),
    ]

    if policy == 'by-day':
        policy_element = XML.SubElement(root,
                                        'policy',
                                        {'class': 'org.jenkins_ci.plugins.'
                                         'build_keeper.ByDayPolicy'})
    elif policy == 'keep-since':
        policy_element = XML.SubElement(root,
                                        'policy',
                                        {'class': 'org.jenkins_ci.plugins.'
                                         'build_keeper.KeepSincePolicy'})
    elif policy == 'build-number':
        policy_element = XML.SubElement(root,
                                        'policy',
                                        {'class': 'org.jenkins_ci.plugins.'
                                         'build_keeper.BuildNumberPolicy'})
    elif policy == 'keep-first-failed':
        policy_element = XML.SubElement(root,
                                        'policy',
                                        {'class': 'org.jenkins_ci.plugins.'
                                         'build_keeper.KeepFirstFailedPolicy'})
        mapping = [
            ('number-of-fails', 'numberOfFails', 0),
        ]
    else:
        InvalidAttributeError('policy', policy, valid_policies)

    helpers.convert_mapping_to_xml(
        policy_element, data, mapping, fail_required=True)


def live_screenshot(registry, xml_parent, data):
    """yaml: live-screenshot
    Show live screenshots of running jobs in the job list.
    Requires the Jenkins :jenkins-wiki:`Live-Screenshot Plugin
    <LiveScreenshot+Plugin>`.

    :arg str full-size: name of screenshot file (default 'screenshot.png')
    :arg str thumbnail: name of thumbnail file (default 'screenshot-thumb.png')

    File type must be .png and they must be located inside the $WORKDIR.

    Full Example:

    .. literalinclude::
       /../../tests/wrappers/fixtures/live-screenshot-full.yaml

    Minimal Example:

    .. literalinclude::
       /../../tests/wrappers/fixtures/live-screenshot-minimal.yaml
    """
    live = XML.SubElement(
        xml_parent,
        'org.jenkinsci.plugins.livescreenshot.LiveScreenshotBuildWrapper')
    live.set('plugin', 'livescreenshot')
    mapping = [
        ('full-size', 'fullscreenFilename', 'screenshot.png'),
        ('thumbnail', 'thumbnailFilename', 'screenshot-thumb.png'),
    ]
    helpers.convert_mapping_to_xml(live, data, mapping, fail_required=True)


def mask_passwords(registry, xml_parent, data):
    """yaml: mask-passwords
    Hide passwords in the console log.
    Requires the Jenkins :jenkins-wiki:`Mask Passwords Plugin
    <Mask+Passwords+Plugin>`.

    Example::

      wrappers:
        - mask-passwords
    """
    XML.SubElement(xml_parent,
                   'com.michelin.cio.hudson.plugins.maskpasswords.'
                   'MaskPasswordsBuildWrapper')


def workspace_cleanup(registry, xml_parent, data):
    """yaml: workspace-cleanup (pre-build)

    Requires the Jenkins :jenkins-wiki:`Workspace Cleanup Plugin
    <Workspace+Cleanup+Plugin>`.

    The post-build workspace-cleanup is available as a publisher.

    :arg list include: list of files to be included
    :arg list exclude: list of files to be excluded
    :arg bool dirmatch: Apply pattern to directories too (default false)
    :arg str check-parameter: boolean environment variable to check to
        determine whether to actually clean up
    :arg str external-deletion-command: external deletion command to run
        against files and directories

    Full Example:

    .. literalinclude::
        /../../tests/wrappers/fixtures/workspace-cleanup-full.yaml
       :language: yaml

    Minimal Example:

    .. literalinclude::
        /../../tests/wrappers/fixtures/workspace-cleanup-min.yaml
       :language: yaml
    """

    p = XML.SubElement(xml_parent,
                       'hudson.plugins.ws__cleanup.PreBuildCleanup')
    p.set("plugin", "ws-cleanup")

    if "include" in data or "exclude" in data:
        patterns = XML.SubElement(p, 'patterns')

    for inc in data.get("include", []):
        ptrn = XML.SubElement(patterns, 'hudson.plugins.ws__cleanup.Pattern')
        mapping = [
            ('', 'pattern', inc),
            ('', 'type', "INCLUDE"),
        ]
        helpers.convert_mapping_to_xml(ptrn, data, mapping, fail_required=True)

    for exc in data.get("exclude", []):
        ptrn = XML.SubElement(patterns, 'hudson.plugins.ws__cleanup.Pattern')
        mapping = [
            ('', 'pattern', exc),
            ('', 'type', "EXCLUDE"),
        ]
        helpers.convert_mapping_to_xml(ptrn, data, mapping, fail_required=True)

    mapping = [
        ("dirmatch", 'deleteDirs', False),
        ('check-parameter', 'cleanupParameter', ''),
        ('external-deletion-command', 'externalDelete', ''),
    ]
    helpers.convert_mapping_to_xml(p, data, mapping, fail_required=True)


def m2_repository_cleanup(registry, xml_parent, data):
    """yaml: m2-repository-cleanup
    Configure M2 Repository Cleanup
    Requires the Jenkins :jenkins-wiki:`M2 Repository Cleanup
    <M2+Repository+Cleanup+Plugin>`.

    :arg list patterns: List of patterns for artifacts to cleanup before
                        building. (optional)

    This plugin allows you to configure a maven2 job to clean some or all of
    the artifacts from the repository before it runs.

    Example:

        .. literalinclude:: \
../../tests/wrappers/fixtures/m2-repository-cleanup001.yaml
    """
    m2repo = XML.SubElement(
        xml_parent,
        'hudson.plugins.m2__repo__reaper.M2RepoReaperWrapper')
    m2repo.set("plugin", "m2-repo-reaper")
    patterns = data.get("patterns", [])
    XML.SubElement(m2repo, 'artifactPatterns').text = ",".join(patterns)
    p = XML.SubElement(m2repo, 'patterns')
    for pattern in patterns:
        XML.SubElement(p, 'string').text = pattern


def rvm_env(registry, xml_parent, data):
    """yaml: rvm-env
    Set the RVM implementation
    Requires the Jenkins :jenkins-wiki:`Rvm Plugin <RVM+Plugin>`.

    :arg str implementation: Type of implementation. Syntax is RUBY[@GEMSET],
                             such as '1.9.3' or 'jruby@foo'.

    Example::

      wrappers:
        - rvm-env:
            implementation: 1.9.3
    """
    rpo = XML.SubElement(xml_parent,
                         'ruby-proxy-object')

    ro_class = "Jenkins::Plugin::Proxies::BuildWrapper"

    plugin_info = registry.get_plugin_info("RVM Plugin")
    plugin_ver = pkg_resources.parse_version(
        plugin_info.get("version", str(sys.maxsize)))

    if plugin_ver >= pkg_resources.parse_version("0.5"):
        ro_class = "Jenkins::Tasks::BuildWrapperProxy"

    ro = XML.SubElement(rpo,
                        'ruby-object',
                        {'ruby-class': ro_class,
                         'pluginid': 'rvm'})

    o = XML.SubElement(ro,
                       'object',
                       {'ruby-class': 'RvmWrapper',
                        'pluginid': 'rvm'})

    XML.SubElement(o,
                   'impl',
                   {'pluginid': 'rvm',
                    'ruby-class': 'String'}).text = data['implementation']

    XML.SubElement(ro,
                   'pluginid',
                   {'pluginid': 'rvm',
                    'ruby-class': 'String'}).text = "rvm"


def rbenv(registry, xml_parent, data):
    """yaml: rbenv
    Set the rbenv implementation.
    Requires the Jenkins :jenkins-wiki:`rbenv plugin <rbenv+plugin>`.

    All parameters are optional.

    :arg str ruby-version: Version of Ruby to use  (default 1.9.3-p484)
    :arg bool ignore-local-version: If true, ignore local Ruby
        version (defined in the ".ruby-version" file in workspace) even if it
        has been defined  (default false)
    :arg str preinstall-gem-list: List of gems to install
        (default 'bundler,rake')
    :arg str rbenv-root: RBENV_ROOT  (default $HOME/.rbenv)
    :arg str rbenv-repo: Which repo to clone rbenv from
        (default https://github.com/rbenv/rbenv)
    :arg str rbenv-branch: Which branch to clone rbenv from  (default master)
    :arg str ruby-build-repo: Which repo to clone ruby-build from
        (default https://github.com/rbenv/ruby-build)
    :arg str ruby-build-branch: Which branch to clone ruby-build from
        (default master)

    Example:

    .. literalinclude:: /../../tests/wrappers/fixtures/rbenv003.yaml
    """

    mapping = [
        # option, xml name, default value (text), attributes (hard coded)
        ("preinstall-gem-list", 'gem__list', 'bundler,rake'),
        ("rbenv-root", 'rbenv__root', '$HOME/.rbenv'),
        ("rbenv-repo", 'rbenv__repository',
            'https://github.com/rbenv/rbenv'),
        ("rbenv-branch", 'rbenv__revision', 'master'),
        ("ruby-build-repo", 'ruby__build__repository',
            'https://github.com/rbenv/ruby-build'),
        ("ruby-build-branch", 'ruby__build__revision', 'master'),
        ("ruby-version", 'version', '1.9.3-p484'),
    ]

    rpo = XML.SubElement(xml_parent,
                         'ruby-proxy-object')

    ro_class = "Jenkins::Tasks::BuildWrapperProxy"
    ro = XML.SubElement(rpo,
                        'ruby-object',
                        {'ruby-class': ro_class,
                         'pluginid': 'rbenv'})

    XML.SubElement(ro,
                   'pluginid',
                   {'pluginid': "rbenv",
                    'ruby-class': "String"}).text = "rbenv"

    o = XML.SubElement(ro,
                       'object',
                       {'ruby-class': 'RbenvWrapper',
                        'pluginid': 'rbenv'})

    for elem in mapping:
        (optname, xmlname, val) = elem[:3]
        xe = XML.SubElement(o,
                            xmlname,
                            {'ruby-class': "String",
                             'pluginid': "rbenv"})
        if optname and optname in data:
            val = data[optname]
        if type(val) == bool:
            xe.text = str(val).lower()
        else:
            xe.text = val

    ignore_local_class = 'FalseClass'

    if 'ignore-local-version' in data:
        ignore_local_string = str(data['ignore-local-version']).lower()
        if ignore_local_string == 'true':
            ignore_local_class = 'TrueClass'

    XML.SubElement(o,
                   'ignore__local__version',
                   {'ruby-class': ignore_local_class,
                    'pluginid': 'rbenv'})


def build_name(registry, xml_parent, data):
    """yaml: build-name
    Set the name of the build
    Requires the Jenkins :jenkins-wiki:`Build Name Setter Plugin
    <Build+Name+Setter+Plugin>`.

    :arg str name: Name for the build.  Typically you would use a variable
                   from Jenkins in the name.  The syntax would be ${FOO} for
                   the FOO variable.

    Example::

      wrappers:
        - build-name:
            name: Build-${FOO}
    """
    bsetter = XML.SubElement(xml_parent,
                             'org.jenkinsci.plugins.buildnamesetter.'
                             'BuildNameSetter')
    mapping = [
        ('name', 'template', None),
    ]
    helpers.convert_mapping_to_xml(bsetter, data, mapping, fail_required=True)


def port_allocator(registry, xml_parent, data):
    """yaml: port-allocator
    Assign unique TCP port numbers
    Requires the Jenkins :jenkins-wiki:`Port Allocator Plugin
    <Port+Allocator+Plugin>`.

    :arg str name: Deprecated, use names instead
    :arg list names: Variable list of names of the port or list of
        specific port numbers

    Example:

    .. literalinclude::  /../../tests/wrappers/fixtures/port-allocator002.yaml
    """
    pa = XML.SubElement(xml_parent,
                        'org.jvnet.hudson.plugins.port__allocator.'
                        'PortAllocator')
    ports = XML.SubElement(pa, 'ports')
    names = data.get('names')
    if not names:
        logger = logging.getLogger(__name__)
        logger.warning(
            'port_allocator name is deprecated, use a names list '
            ' instead')
        names = [data['name']]
    for name in names:
        dpt = XML.SubElement(ports,
                             'org.jvnet.hudson.plugins.port__allocator.'
                             'DefaultPortType')
        XML.SubElement(dpt, 'name').text = name


def locks(registry, xml_parent, data):
    """yaml: locks
    Control parallel execution of jobs.
    Requires the Jenkins :jenkins-wiki:`Locks and Latches Plugin
    <Locks+and+Latches+plugin>`.

    :arg: list of locks to use

    Example:

    .. literalinclude::  /../../tests/wrappers/fixtures/locks002.yaml
       :language: yaml
    """
    locks = data
    if locks:
        lw = XML.SubElement(xml_parent,
                            'hudson.plugins.locksandlatches.LockWrapper')
        locktop = XML.SubElement(lw, 'locks')
        for lock in locks:
            lockwrapper = XML.SubElement(locktop,
                                         'hudson.plugins.locksandlatches.'
                                         'LockWrapper_-LockWaitConfig')
            XML.SubElement(lockwrapper, 'name').text = lock


def copy_to_slave(registry, xml_parent, data):
    """yaml: copy-to-slave
    Copy files to slave before build
    Requires the Jenkins :jenkins-wiki:`Copy To Slave Plugin
    <Copy+To+Slave+Plugin>`.

    :arg list includes: list of file patterns to copy (optional)
    :arg list excludes: list of file patterns to exclude (optional)
    :arg bool flatten: flatten directory structure (default false)
    :arg str relative-to: base location of includes/excludes, must be home
        ($JENKINS_HOME), somewhereElse ($JENKINS_HOME/copyToSlave),
        userContent ($JENKINS_HOME/userContent) or workspace
        (default userContent)
    :arg bool include-ant-excludes: exclude ant's default excludes
        (default false)

    Minimal Example:

    .. literalinclude::  /../../tests/wrappers/fixtures/copy-to-slave001.yaml
       :language: yaml

    Full Example:

    .. literalinclude::  /../../tests/wrappers/fixtures/copy-to-slave002.yaml
       :language: yaml
    """
    p = 'com.michelin.cio.hudson.plugins.copytoslave.CopyToSlaveBuildWrapper'
    cs = XML.SubElement(xml_parent, p)

    XML.SubElement(cs, 'includes').text = ','.join(data.get('includes', ['']))
    XML.SubElement(cs, 'excludes').text = ','.join(data.get('excludes', ['']))

    locations = ['home', 'somewhereElse', 'userContent', 'workspace']
    mapping = [
        ('flatten', 'flatten', False),
        ('include-ant-excludes', 'includeAntExcludes', False),
        ('relative-to', 'relativeTo', 'userContent', locations),
        ('', 'hudsonHomeRelative', False),
    ]
    helpers.convert_mapping_to_xml(cs, data, mapping, fail_required=True)


def inject(registry, xml_parent, data):
    """yaml: inject
    Add or override environment variables to the whole build process
    Requires the Jenkins :jenkins-wiki:`EnvInject Plugin <EnvInject+Plugin>`.

    :arg str properties-file: path to the properties file (optional)
    :arg str properties-content: key value pair of properties (optional)
    :arg str script-file: path to the script file (optional)
    :arg str script-content: contents of a script (optional)
    :arg bool load-from-master: load files from master (default false)
    :arg str groovy-script: contents of the groovy script (optional)
    :arg bool groovy-sandbox: use groovy sandbox (default false)

    Minimal Example:

    .. literalinclude:: /../../tests/wrappers/fixtures/inject-minimal.yaml

    Full Example:

    .. literalinclude:: /../../tests/wrappers/fixtures/inject-full.yaml

    """
    eib = XML.SubElement(xml_parent, 'EnvInjectBuildWrapper')
    info = XML.SubElement(eib, 'info')
    mapping = [
        ('properties-file', 'propertiesFilePath', None),
        ('properties-content', 'propertiesContent', None),
        ('script-file', 'scriptFilePath', None),
        ('script-content', 'scriptContent', None),
        ('load-from-master', 'loadFilesFromMaster', False),
    ]
    helpers.convert_mapping_to_xml(info, data, mapping, fail_required=False)

    secure_groovy_script = XML.SubElement(info, 'secureGroovyScript')
    mapping = [
        ('groovy-script', 'script', None),
        ('groovy-sandbox', 'sandbox', False),
    ]
    helpers.convert_mapping_to_xml(secure_groovy_script, data, mapping,
                           fail_required=False)


def inject_ownership_variables(registry, xml_parent, data):
    """yaml: inject-ownership-variables
    Inject ownership variables to the build as environment variables.
    Requires the Jenkins :jenkins-wiki:`EnvInject Plugin <EnvInject+Plugin>`
    and Jenkins :jenkins-wiki:`Ownership plugin <Ownership+Plugin>`.

    :arg bool job-variables: inject job ownership variables to the job
        (default false)
    :arg bool node-variables: inject node ownership variables to the job
        (default false)

    Example:

    .. literalinclude:: /../../tests/wrappers/fixtures/ownership001.yaml

    """
    ownership = XML.SubElement(xml_parent, 'com.synopsys.arc.jenkins.plugins.'
                               'ownership.wrappers.OwnershipBuildWrapper')
    mapping = [
        ('node-variables', 'injectNodeOwnership', False),
        ('job-variables', 'injectJobOwnership', False),
    ]
    helpers.convert_mapping_to_xml(
        ownership, data, mapping, fail_required=True)


def inject_passwords(registry, xml_parent, data):
    """yaml: inject-passwords
    Inject passwords to the build as environment variables.
    Requires the Jenkins :jenkins-wiki:`EnvInject Plugin <EnvInject+Plugin>`.

    :arg bool global: inject global passwords to the job
    :arg bool mask-password-params: mask password parameters
    :arg list job-passwords: key value pair of job passwords

        :Parameter: * **name** (`str`) Name of password
                    * **password** (`str`) Encrypted password

    Example:

    .. literalinclude:: /../../tests/wrappers/fixtures/passwords001.yaml

    """
    eib = XML.SubElement(xml_parent, 'EnvInjectPasswordWrapper')
    mapping = [
        ('global', 'injectGlobalPasswords', False),
        ('mask-password-params', 'maskPasswordParameters', False),
    ]
    helpers.convert_mapping_to_xml(eib, data, mapping, fail_required=True)

    entries = XML.SubElement(eib, 'passwordEntries')
    passwords = data.get('job-passwords', [])
    if passwords:
        for password in passwords:
            entry = XML.SubElement(entries, 'EnvInjectPasswordEntry')
            mapping = [
                ('name', 'name', None),
                ('password', 'value', None),
            ]
            helpers.convert_mapping_to_xml(entry, password,
                mapping, fail_required=True)


def vault_secrets(registry, xml_parent, data):
    """yaml: vault-secrets
    Inject environment variables from a HashiCorp Vault secret.

    Secrets are generally masked in the build log.

    Requires the Jenkins
        :jenkins-wiki:`HashiCorp Vault Plugin <HashiCorp+Vault+Plugin>`.

    :arg str vault-url: Vault URL
    :arg str credentials-id: Vault Credential
    :arg list secrets: List of secrets

      :secrets:
        * **secret-path** (`str`) --
          The path of the secret in the vault server

        :secret-values:
          * **secret-values** (`list`) -- List of key / value pairs

            * **env-var** (`str`) --
              The environment variable to set with the value of the
              vault key
            * **vault-key** (`str`) -- The vault key whose value with
              populate the environment variable

    Minimal Example:

    .. literalinclude:: /../../tests/wrappers/fixtures/vault-minimal.yaml
       :language: yaml

    Full Example:

    .. literalinclude:: /../../tests/wrappers/fixtures/vault-full.yaml
       :language: yaml

    """
    vault = XML.SubElement(xml_parent,
                           'com.datapipe.jenkins.vault.VaultBuildWrapper')
    vault.set('plugin', 'hashicorp-vault-plugin')
    configuration = XML.SubElement(vault, 'configuration')
    conf_mapping = [
        ('vault-url', 'vaultUrl', ''),
        ('credentials-id', 'vaultCredentialId', ''),
    ]
    helpers.convert_mapping_to_xml(
        configuration, data, conf_mapping, fail_required=True)

    secretsobj = XML.SubElement(vault, 'vaultSecrets')
    secrets = data.get('secrets', [])
    for secret in secrets:
        secretobj = XML.SubElement(
            secretsobj, 'com.datapipe.jenkins.vault.model.VaultSecret')
        XML.SubElement(
            secretobj, 'path').text = secret.get('secret-path', '')
        secretvaluesobj = XML.SubElement(secretobj, 'secretValues')
        for secretvalue in secret['secret-values']:
            secretvalueobj = XML.SubElement(
                secretvaluesobj,
                'com.datapipe.jenkins.vault.model.VaultSecretValue')
            XML.SubElement(
                secretvalueobj,
                'envVar').text = \
                secretvalue.get('env-var', '')
            XML.SubElement(
                secretvalueobj,
                'vaultKey').text = \
                secretvalue.get('vault-key', '')
    XML.SubElement(vault, 'valuesToMask')
    XML.SubElement(vault, 'vaultAccessor')


def env_file(registry, xml_parent, data):
    """yaml: env-file
    Add or override environment variables to the whole build process
    Requires the Jenkins :jenkins-wiki:`Environment File Plugin
    <Envfile+Plugin>`.

    :arg str properties-file: path to the properties file (optional)

    Example::

      wrappers:
        - env-file:
            properties-file: ${WORKSPACE}/foo
    """
    eib = XML.SubElement(xml_parent,
                         'hudson.plugins.envfile.EnvFileBuildWrapper')
    mapping = [
        ('properties-file', 'filePath', None),
    ]
    helpers.convert_mapping_to_xml(eib, data, mapping, fail_required=False)


def env_script(registry, xml_parent, data):
    """yaml: env-script
    Add or override environment variables to the whole build process.
    Requires the Jenkins :jenkins-wiki:`Environment Script Plugin
    <Environment+Script+Plugin>`.

    :arg script-content: The script to run (default '')
    :arg str script-type: The script type.

        :script-types supported:
            * **unix-script** (default)
            * **power-shell**
            * **batch-script**
    :arg only-run-on-parent: Only applicable for Matrix Jobs. If true, run only
      on the matrix parent job (default false)

    Example:

    .. literalinclude:: /../../tests/wrappers/fixtures/env-script001.yaml

    """
    el = XML.SubElement(xml_parent, 'com.lookout.jenkins.EnvironmentScript')

    valid_script_types = {
        'unix-script': 'unixScript',
        'power-shell': 'powerShell',
        'batch-script': 'batchScript',
    }
    mapping = [
        ('script-content', 'script', ''),
        ('script-type', 'scriptType', 'unix-script', valid_script_types),
        ('only-run-on-parent', 'runOnlyOnParent', False),
    ]
    helpers.convert_mapping_to_xml(el, data, mapping, fail_required=True)


def jclouds(registry, xml_parent, data):
    """yaml: jclouds
    Uses JClouds to provide slave launching on most of the currently
    usable Cloud infrastructures.
    Requires the Jenkins :jenkins-wiki:`JClouds Plugin <JClouds+Plugin>`.

    :arg bool single-use: Whether or not to terminate the slave after use
                          (default false).
    :arg list instances: The name of the jclouds template to create an
                         instance from, and its parameters.
    :arg str cloud-name: The name of the jclouds profile containing the
                         specified template.
    :arg int count: How many instances to create (default 1).
    :arg bool stop-on-terminate: Whether or not to suspend instead of terminate
                                 the instance (default false).

    Example:

    .. literalinclude:: /../../tests/wrappers/fixtures/jclouds001.yaml
       :language: yaml

    """
    if 'instances' in data:
        buildWrapper = XML.SubElement(
            xml_parent, 'jenkins.plugins.jclouds.compute.JCloudsBuildWrapper')
        instances = XML.SubElement(buildWrapper, 'instancesToRun')
        for foo in data['instances']:
            for template, params in foo.items():
                instance = XML.SubElement(instances,
                                          'jenkins.plugins.jclouds.compute.'
                                          'InstancesToRun')
                XML.SubElement(instance, 'templateName').text = template
                XML.SubElement(instance, 'cloudName').text = \
                    params.get('cloud-name', '')
                XML.SubElement(instance, 'count').text = \
                    str(params.get('count', 1))
                XML.SubElement(instance, 'suspendOrTerminate').text = \
                    str(params.get('stop-on-terminate', False)).lower()
    if data.get('single-use'):
        XML.SubElement(xml_parent,
                       'jenkins.plugins.jclouds.compute.'
                       'JCloudsOneOffSlave')


def openstack(registry, xml_parent, data):
    """yaml: openstack
    Provision slaves from OpenStack on demand.  Requires the Jenkins
    :jenkins-wiki:`Openstack Cloud Plugin <Openstack+Cloud+Plugin>`.

    :arg list instances: List of instances to be launched at the beginning of
        the build.

        :instances:
            * **cloud-name** (`str`) -- The name of the cloud profile which
              contains the specified cloud instance template (required).
            * **template-name** (`str`) -- The name of the cloud instance
              template to create an instance from(required).
            * **manual-template** (`bool`) -- If True, instance template name
              will be put in 'Specify Template Name as String' option. Not
              specifying or specifying False, instance template name will be
              put in 'Select Template from List' option. To use parameter
              replacement, set this to True.  (default false)
            * **count** (`int`) -- How many instances to create (default 1).

    :arg bool single-use: Whether or not to terminate the slave after use
        (default false).

    Example:

    .. literalinclude:: /../../tests/wrappers/fixtures/openstack001.yaml
    """
    tag_prefix = 'jenkins.plugins.openstack.compute.'

    if 'instances' in data:
        clouds_build_wrapper = XML.SubElement(
            xml_parent, tag_prefix + 'JCloudsBuildWrapper')
        instances_wrapper = XML.SubElement(
            clouds_build_wrapper, 'instancesToRun')

        for instance in data['instances']:
            instances_to_run = XML.SubElement(
                instances_wrapper, tag_prefix + 'InstancesToRun')

            instance_mapping = [('cloud-name', 'cloudName', None),
                ('count', 'count', 1)]

            if instance.get('manual-template', False):
                instance_mapping.append(('template-name',
                    'manualTemplateName', None))
            else:
                instance_mapping.append(('template-name',
                    'templateName', None))
            helpers.convert_mapping_to_xml(instances_to_run,
                instance, instance_mapping, fail_required=True)

    if data.get('single-use', False):
        XML.SubElement(xml_parent, tag_prefix + 'JCloudsOneOffSlave')


def build_user_vars(registry, xml_parent, data):
    """yaml: build-user-vars
    Set environment variables to the value of the user that started the build.
    Requires the Jenkins :jenkins-wiki:`Build User Vars Plugin
    <Build+User+Vars+Plugin>`.

    Example::

      wrappers:
        - build-user-vars
    """
    XML.SubElement(xml_parent, 'org.jenkinsci.plugins.builduser.BuildUser')


def release(registry, xml_parent, data):
    """yaml: release
    Add release build configuration
    Requires the Jenkins :jenkins-wiki:`Release Plugin <Release+Plugin>`.

    :arg bool keep-forever: Keep build forever (default true)
    :arg bool override-build-parameters: Enable build-parameter override
        (default false)
    :arg string version-template: Release version template (default '')
    :arg list parameters: Release parameters (see the :ref:`Parameters` module)
    :arg list pre-build: Pre-build steps (see the :ref:`Builders` module)
    :arg list post-build: Post-build steps (see :ref:`Builders`)
    :arg list post-success: Post successful-build steps (see :ref:`Builders`)
    :arg list post-failed: Post failed-build steps (see :ref:`Builders`)

    Example:

    .. literalinclude:: /../../tests/wrappers/fixtures/release001.yaml

    """
    relwrap = XML.SubElement(xml_parent,
                             'hudson.plugins.release.ReleaseWrapper')
    # For 'keep-forever', the sense of the XML flag is the opposite of
    # the YAML flag.
    mapping = [
        ('do-not-keep-log',
         'doNotKeepLog',
         not data.get('keep-forever', True)),
        ('override-build-parameters', 'overrideBuildParameters', False),
        ('version-template', 'releaseVersionTemplate', ''),
    ]
    helpers.convert_mapping_to_xml(relwrap, data, mapping, fail_required=True)

    parameters = data.get('parameters', [])
    if parameters:
        pdef = XML.SubElement(relwrap, 'parameterDefinitions')
        for param in parameters:
            registry.dispatch('parameter', pdef, param)
    builder_steps = {
        'pre-build': 'preBuildSteps',
        'post-build': 'postBuildSteps',
        'post-success': 'postSuccessfulBuildSteps',
        'post-fail': 'postFailedBuildSteps',
    }
    for step in builder_steps.keys():
        for builder in data.get(step, []):
            registry.dispatch('builder',
                              XML.SubElement(relwrap, builder_steps[step]),
                              builder)


def sauce_ondemand(registry, xml_parent, data):
    """yaml: sauce-ondemand
    Allows you to integrate Sauce OnDemand with Jenkins.  You can
    automate the setup and tear down of Sauce Connect and integrate
    the Sauce OnDemand results videos per test. Requires the Jenkins
    :jenkins-wiki:`Sauce OnDemand Plugin <Sauce+OnDemand+Plugin>`.

    :arg bool enable-sauce-connect: launches a SSH tunnel from their cloud
        to your private network (default false)
    :arg str sauce-host: The name of the selenium host to be used.  For
        tests run using Sauce Connect, this should be localhost.
        ondemand.saucelabs.com can also be used to conenct directly to
        Sauce OnDemand,  The value of the host will be stored in the
        SAUCE_ONDEMAND_HOST environment variable.  (default '')
    :arg str sauce-port: The name of the Selenium Port to be used.  For
        tests run using Sauce Connect, this should be 4445.  If using
        ondemand.saucelabs.com for the Selenium Host, then use 4444.
        The value of the port will be stored in the SAUCE_ONDEMAND_PORT
        environment variable.  (default '')
    :arg str override-username: If set then api-access-key must be set.
        Overrides the username from the global config. (default '')
    :arg str override-api-access-key: If set then username must be set.
        Overrides the api-access-key set in the global config. (default '')
    :arg str starting-url: The value set here will be stored in the
        SELENIUM_STARTING_ULR environment variable.  Only used when type
        is selenium. (default '')
    :arg str type: Type of test to run (default selenium)

        :type values:
          * **selenium**
          * **webdriver**
    :arg list platforms: The platforms to run the tests on.  Platforms
        supported are dynamically retrieved from sauce labs.  The format of
        the values has only the first letter capitalized, no spaces, underscore
        between os and version, underscore in internet_explorer, everything
        else is run together.  If there are not multiple version of the browser
        then just the first version number is used.
        Examples: Mac_10.8iphone5.1 or Windows_2003firefox10
        or Windows_2012internet_explorer10 (default '')
    :arg bool launch-sauce-connect-on-slave: Whether to launch sauce connect
        on the slave. (default false)
    :arg str https-protocol: The https protocol to use (default '')
    :arg str sauce-connect-options: Options to pass to sauce connect
        (default '')

    Example::

      wrappers:
        - sauce-ondemand:
            enable-sauce-connect: true
            sauce-host: foo
            sauce-port: 8080
            override-username: foo
            override-api-access-key: 123lkj123kh123l;k12323
            type: webdriver
            platforms:
              - Linuxandroid4
              - Linuxfirefox10
              - Linuxfirefox11
            launch-sauce-connect-on-slave: true
    """
    sauce = XML.SubElement(xml_parent, 'hudson.plugins.sauce__ondemand.'
                           'SauceOnDemandBuildWrapper')
    mapping = [
        ('enable-sauce-connect', 'enableSauceConnect', False),
        ('sauce-host', 'seleniumHost', ''),
        ('sauce-port', 'seleniumPort', ''),
        ('launch-sauce-connect-on-slave', 'launchSauceConnectOnSlave', False),
        ('https-protocol', 'httpsProtocol', ''),
        ('sauce-connect-options', 'options', ''),
    ]
    helpers.convert_mapping_to_xml(sauce, data, mapping, fail_required=True)

    # Optional override global authentication
    username = data.get('override-username')
    key = data.get('override-api-access-key')
    if username and key:
        cred = XML.SubElement(sauce, 'credentials')
        mapping = [
            ('override-username', 'username', None),
            ('override-api-access-key', 'apiKey', None),
        ]
        helpers.convert_mapping_to_xml(cred, data, mapping, fail_required=True)
    atype = data.get('type', 'selenium')
    info = XML.SubElement(sauce, 'seleniumInformation')

    if atype == 'selenium':
        selenium_mapping = [
            ('starting-url', 'seleniumBrowsers', ''),
            ('', 'isWebDriver', False),
        ]
        helpers.convert_mapping_to_xml(
            info, data, selenium_mapping, fail_required=True)

        browsers = XML.SubElement(info, 'seleniumBrowsers')
        for platform in data['platforms']:
            mapping = [
                ('', 'string', platform),
            ]
            helpers.convert_mapping_to_xml(
                browsers, data, mapping, fail_required=True)
        XML.SubElement(sauce, 'seleniumBrowsers',
                       {'reference': '../seleniumInformation/'
                        'seleniumBrowsers'})
    if atype == 'webdriver':
        browsers = XML.SubElement(info, 'webDriverBrowsers')
        for platform in data['platforms']:
            mapping = [
                ('', 'string', platform),
            ]
            helpers.convert_mapping_to_xml(
                browsers, data, mapping, fail_required=True)
        webdriver_mapping = [
            ('', 'isWebDriver', True),
        ]
        helpers.convert_mapping_to_xml(
            info, data, webdriver_mapping, fail_required=True)
        XML.SubElement(sauce, 'webDriverBrowsers',
                       {'reference': '../seleniumInformation/'
                        'webDriverBrowsers'})


def sonar(registry, xml_parent, data):
    """yaml: sonar
    Wrapper for SonarQube Plugin
    Requires :jenkins-wiki:`SonarQube plugin <SonarQube+plugin>`

    :arg str install-name: Release goals and options (default '')

    Minimal Example:

    .. literalinclude:: /../../tests/wrappers/fixtures/sonar-minimal.yaml
       :language: yaml

    Full Example:

    .. literalinclude:: /../../tests/wrappers/fixtures/sonar-full.yaml
       :language: yaml
    """
    sonar = XML.SubElement(
        xml_parent, 'hudson.plugins.sonar.SonarBuildWrapper')
    sonar.set('plugin', 'sonar')

    if data.get('install-name'):
        mapping = [
            ('install-name', 'installationName', ''),
        ]
        helpers.convert_mapping_to_xml(
            sonar, data, mapping, fail_required=True)


def pathignore(registry, xml_parent, data):
    """yaml: pathignore
    This plugin allows SCM-triggered jobs to ignore
    build requests if only certain paths have changed.

    Requires the Jenkins :jenkins-wiki:`Pathignore Plugin <Pathignore+Plugin>`.

    :arg str ignored: A set of patterns to define ignored changes

    Example::

      wrappers:
        - pathignore:
            ignored: "docs, tests"
    """
    ruby = XML.SubElement(xml_parent, 'ruby-proxy-object')
    robj = XML.SubElement(ruby, 'ruby-object', attrib={
        'pluginid': 'pathignore',
        'ruby-class': 'Jenkins::Plugin::Proxies::BuildWrapper'
    })
    pluginid = XML.SubElement(robj, 'pluginid', {
        'pluginid': 'pathignore', 'ruby-class': 'String'
    })
    pluginid.text = 'pathignore'
    obj = XML.SubElement(robj, 'object', {
        'ruby-class': 'PathignoreWrapper', 'pluginid': 'pathignore'
    })
    ignored = XML.SubElement(obj, 'ignored__paths', {
        'pluginid': 'pathignore', 'ruby-class': 'String'
    })
    ignored.text = data.get('ignored', '')
    XML.SubElement(obj, 'invert__ignore', {
        'ruby-class': 'FalseClass', 'pluginid': 'pathignore'
    })


def pre_scm_buildstep(registry, xml_parent, data):
    """yaml: pre-scm-buildstep
    Execute a Build Step before running the SCM
    Requires the Jenkins :jenkins-wiki:`pre-scm-buildstep <pre-scm-buildstep>`.

    :arg string failOnError: Specifies if the job should fail on error
        (plugin >= 0.3) (default false).
    :arg list buildsteps: List of build steps to execute

        :Buildstep: Any acceptable builder, as seen in the example

    Example:

    .. literalinclude::
       /../../tests/wrappers/fixtures/pre-scm-buildstep001.yaml
       :language: yaml
    """
    # Get plugin information to maintain backwards compatibility
    info = registry.get_plugin_info('preSCMbuildstep')
    version = pkg_resources.parse_version(info.get('version', "0"))

    bsp = XML.SubElement(xml_parent,
                         'org.jenkinsci.plugins.preSCMbuildstep.'
                         'PreSCMBuildStepsWrapper')
    bs = XML.SubElement(bsp, 'buildSteps')
    stepList = data if type(data) is list else data.get('buildsteps')

    for step in stepList:
        for edited_node in create_builders(registry, step):
            bs.append(edited_node)
    if version >= pkg_resources.parse_version("0.3"):
        mapping = [
            ('failOnError', 'failOnError', False),
        ]
        helpers.convert_mapping_to_xml(bsp, data, mapping, fail_required=True)


def logstash(registry, xml_parent, data):
    """yaml: logstash build wrapper
    Dump the Jenkins console output to Logstash
    Requires the Jenkins :jenkins-wiki:`logstash plugin <Logstash+Plugin>`.

    :arg use-redis: Boolean to use Redis. (default true)
    :arg redis: Redis config params

        :Parameter: * **host** (`str`) Redis hostname\
        (default 'localhost')
        :Parameter: * **port** (`int`) Redis port number (default 6397)
        :Parameter: * **database-number** (`int`)\
        Redis database number (default 0)
        :Parameter: * **database-password** (`str`)\
        Redis database password (default '')
        :Parameter: * **data-type** (`str`)\
        Redis database type (default 'list')
        :Parameter: * **key** (`str`) Redis key (default 'logstash')

    Example:

    .. literalinclude:: /../../tests/wrappers/fixtures/logstash001.yaml

    """
    logstash = XML.SubElement(xml_parent,
                              'jenkins.plugins.logstash.'
                              'LogstashBuildWrapper')
    logstash.set('plugin', 'logstash@0.8.0')

    mapping = [
        ('use-redis', 'useRedis', True),
    ]
    helpers.convert_mapping_to_xml(logstash, data, mapping, fail_required=True)

    if data.get('use-redis'):
        redis_config = data.get('redis', {})
        redis_sub_element = XML.SubElement(logstash, 'redis')

        mapping = [
            ('host', 'host', 'localhost'),
            ('port', 'port', '6379'),
            ('database-number', 'numb', '0'),
            ('database-password', 'pass', ''),
            ('data-type', 'dataType', 'list'),
            ('key', 'key', 'logstash'),
        ]
        helpers.convert_mapping_to_xml(redis_sub_element,
            redis_config, mapping, fail_required=True)


def mongo_db(registry, xml_parent, data):
    """yaml: mongo-db build wrapper
    Initializes a MongoDB database while running the build.
    Requires the Jenkins :jenkins-wiki:`MongoDB plugin <MongoDB+Plugin>`.

    :arg str name: The name of the MongoDB install to use (required)
    :arg str data-directory: Data directory for the server (default '')
    :arg int port: Port for the server (default '')
    :arg str startup-params: Startup parameters for the server (default '')
    :arg int start-timeout: How long to wait for the server to start in
        milliseconds. 0 means no timeout. (default 0)

    Full Example:

    .. literalinclude:: /../../tests/wrappers/fixtures/mongo-db-full.yaml

    Minimal Example:

    .. literalinclude:: /../../tests/wrappers/fixtures/mongo-db-minimal.yaml
    """
    mongodb = XML.SubElement(xml_parent,
                             'org.jenkinsci.plugins.mongodb.'
                             'MongoBuildWrapper')
    mongodb.set('plugin', 'mongodb')

    mapping = [
        ('name', 'mongodbName', None),
        ('port', 'port', ''),
        ('data-directory', 'dbpath', ''),
        ('startup-params', 'parameters', ''),
        ('start-timeout', 'startTimeout', 0),
    ]
    helpers.convert_mapping_to_xml(mongodb, data, mapping, fail_required=True)


def delivery_pipeline(registry, xml_parent, data):
    """yaml: delivery-pipeline
    If enabled the job will create a version based on the template.
    The version will be set to the environment variable PIPELINE_VERSION and
    will also be set in the downstream jobs.

    Requires the Jenkins :jenkins-wiki:`Delivery Pipeline Plugin
    <Delivery+Pipeline+Plugin>`.

    :arg str version-template: Template for generated version e.g
        1.0.${BUILD_NUMBER} (default '')
    :arg bool set-display-name: Set the generated version as the display name
        for the build (default false)

    Minimal Example:

    .. literalinclude::
       /../../tests/wrappers/fixtures/delivery-pipeline-minimal.yaml
       :language: yaml

    Full Example:

    .. literalinclude::
       /../../tests/wrappers/fixtures/delivery-pipeline-full.yaml
       :language: yaml
    """
    pvc = XML.SubElement(
        xml_parent, 'se.diabol.jenkins.pipeline.PipelineVersionContributor')
    pvc.set('plugin', 'delivery-pipeline-plugin')

    mapping = [
        ('version-template', 'versionTemplate', ''),
        ('set-display-name', 'updateDisplayName', False),
    ]
    helpers.convert_mapping_to_xml(pvc, data, mapping, fail_required=True)


def matrix_tie_parent(registry, xml_parent, data):
    """yaml: matrix-tie-parent
    Tie parent to a node.
    Requires the Jenkins :jenkins-wiki:`Matrix Tie Parent Plugin
    <Matrix+Tie+Parent+Plugin>`.
    Note that from Jenkins version 1.532 this plugin's functionality is
    available under the "advanced" option of the matrix project configuration.
    You can use the top level ``node`` parameter to control where the parent
    job is tied in Jenkins 1.532 and higher.

    :arg str node: Name of the node (required)

    Example:

    .. literalinclude:: /../../tests/wrappers/fixtures/matrix-tie-parent.yaml
    """
    mtp = XML.SubElement(xml_parent, 'matrixtieparent.BuildWrapperMtp')
    mapping = [
        ('node', 'labelName', None),
    ]
    helpers.convert_mapping_to_xml(mtp, data, mapping, fail_required=True)


def exclusion(registry, xml_parent, data):
    """yaml: exclusion
    Add a resource to use for critical sections to establish a mutex on. If
    another job specifies the same resource, the second job will wait for the
    blocked resource to become available.

    Requires the Jenkins :jenkins-wiki:`Exclusion Plugin <Exclusion-Plugin>`.

    :arg list resources: List of resources to add for exclusion

    Example:

    .. literalinclude:: /../../tests/wrappers/fixtures/exclusion002.yaml

    """
    exl = XML.SubElement(xml_parent,
                         'org.jvnet.hudson.plugins.exclusion.IdAllocator')
    exl.set('plugin', 'Exclusion')
    ids = XML.SubElement(exl, 'ids')
    resources = data.get('resources', [])
    for resource in resources:
        dit = XML.SubElement(ids,
                           'org.jvnet.hudson.plugins.exclusion.DefaultIdType')
        mapping = [
            ('', 'name', resource.upper()),
        ]
        helpers.convert_mapping_to_xml(dit, data, mapping, fail_required=True)


def ssh_agent_credentials(registry, xml_parent, data):
    """yaml: ssh-agent-credentials
    Sets up the user for the ssh agent plugin for jenkins.

    Requires the Jenkins :jenkins-wiki:`SSH-Agent Plugin <SSH+Agent+Plugin>`.

    :arg list users: A list of Jenkins users credential IDs (required)
    :arg str user: The user id of the jenkins user credentials (deprecated)

    Example:

    .. literalinclude::
            /../../tests/wrappers/fixtures/ssh-agent-credentials002.yaml


    if both **users** and **user** parameters specified, **users** will be
        preferred, **user** will be ignored.

    Example:

    .. literalinclude::
            /../../tests/wrappers/fixtures/ssh-agent-credentials003.yaml

    The **users** with one value in list equals to the **user**. In this
    case old style XML will be generated. Use this format if you use
    SSH-Agent plugin < 1.5.

    Example:

    .. literalinclude::
            /../../tests/wrappers/fixtures/ssh-agent-credentials004.yaml

    equals to:

    .. literalinclude::
            /../../tests/wrappers/fixtures/ssh-agent-credentials001.yaml

    """

    logger = logging.getLogger(__name__)

    entry_xml = XML.SubElement(
        xml_parent,
        'com.cloudbees.jenkins.plugins.sshagent.SSHAgentBuildWrapper')
    xml_key = 'user'

    user_list = list()
    if 'users' in data:
        user_list += data['users']
        if len(user_list) > 1:
            entry_xml = XML.SubElement(entry_xml, 'credentialIds')
            xml_key = 'string'
        if 'user' in data:
            logger.warning(
                "Both 'users' and 'user' parameters specified for "
                "ssh-agent-credentials. 'users' is used, 'user' is "
                "ignored.")
    elif 'user' in data:
        logger.warning("The 'user' param has been deprecated, "
                       "use the 'users' param instead.")
        user_list.append(data['user'])
    else:
        raise JenkinsJobsException("Missing 'user' or 'users' parameter "
                                   "for ssh-agent-credentials")

    for user in user_list:
        XML.SubElement(entry_xml, xml_key).text = user


def credentials_binding(registry, xml_parent, data):
    """yaml: credentials-binding
    Binds credentials to environment variables using the credentials binding
    plugin for jenkins.

    Requires the Jenkins :jenkins-wiki:`Credentials Binding Plugin
    <Credentials+Binding+Plugin>` version 1.1 or greater.

    :arg list binding-type: List of each bindings to create.  Bindings may be
      of type `zip-file`, `file`, `username-password`, `text`,
      `username-password-separated` or `amazon-web-services`.
      username-password sets a variable to the username and password given in
      the credentials, separated by a colon.
      username-password-separated sets one variable to the username and one
      variable to the password given in the credentials.
      amazon-web-services sets one variable to the access key and one
      variable to the secret access key. Requires the
      :jenkins-wiki:`AWS Credentials Plugin <CloudBees+AWS+Credentials+Plugin>`
      .

        :Parameters: * **credential-id** (`str`) UUID of the credential being
                       referenced
                     * **variable** (`str`) Environment variable where the
                       credential will be stored
                     * **username** (`str`) Environment variable for the
                       username (Required for binding-type
                       username-password-separated)
                     * **password** (`str`) Environment variable for the
                       password (Required for binding-type
                       username-password-separated)
                     * **access-key** (`str`) Environment variable for the
                       access key (Required for binding-type
                       amazon-web-services)
                     * **secret-key** (`str`) Environment variable for the
                       access secret key (Required for binding-type
                       amazon-web-services)

    Example:

    .. literalinclude::
            /../../tests/wrappers/fixtures/credentials_binding.yaml
            :language: yaml

    """
    entry_xml = xml_parent.find(
        'org.jenkinsci.plugins.credentialsbinding.impl.SecretBuildWrapper')
    if entry_xml is None:
        entry_xml = XML.SubElement(
            xml_parent,
            'org.jenkinsci.plugins.credentialsbinding.impl.SecretBuildWrapper')

    bindings_xml = entry_xml.find('bindings')
    if bindings_xml is None:
        bindings_xml = XML.SubElement(entry_xml, 'bindings')

    binding_types = {
        'zip-file': 'org.jenkinsci.plugins.credentialsbinding.impl.'
                    'ZipFileBinding',
        'file': 'org.jenkinsci.plugins.credentialsbinding.impl.FileBinding',
        'username-password': 'org.jenkinsci.plugins.credentialsbinding.impl.'
                             'UsernamePasswordBinding',
        'username-password-separated': 'org.jenkinsci.plugins.'
                                       'credentialsbinding.impl.'
                                       'UsernamePasswordMultiBinding',
        'text': 'org.jenkinsci.plugins.credentialsbinding.impl.StringBinding',
        'amazon-web-services':
            'com.cloudbees.jenkins.plugins.awscredentials'
            '.AmazonWebServicesCredentialsBinding'
    }
    for binding in data:
        for binding_type, params in binding.items():
            if binding_type not in binding_types.keys():
                raise JenkinsJobsException('binding-type must be one of %r' %
                                           binding_types.keys())

            binding_xml = XML.SubElement(bindings_xml,
                                         binding_types[binding_type])
            if binding_type == 'username-password-separated':
                mapping = [
                    ('username', 'usernameVariable', None),
                    ('password', 'passwordVariable', None),
                ]
                helpers.convert_mapping_to_xml(
                    binding_xml, params, mapping, fail_required=True)
            elif binding_type == 'amazon-web-services':
                mapping = [
                    ('access-key', 'accessKeyVariable', None),
                    ('secret-key', 'secretKeyVariable', None),
                ]
                helpers.convert_mapping_to_xml(
                    binding_xml, params, mapping, fail_required=True)
            else:
                mapping = [
                    ('variable', 'variable', None),
                ]
                helpers.convert_mapping_to_xml(
                    binding_xml, params, mapping, fail_required=False)
            mapping = [
                ('credential-id', 'credentialsId', None),
            ]
            helpers.convert_mapping_to_xml(binding_xml,
                params, mapping, fail_required=False)


def custom_tools(registry, xml_parent, data):
    """yaml: custom-tools
    Requires the Jenkins :jenkins-wiki:`Custom Tools Plugin
    <Custom+Tools+Plugin>`.

    :arg list tools: List of custom tools to add
                     (optional)
    :arg bool skip-master-install: skips the install in top level matrix job
                                   (default 'false')
    :arg bool convert-homes-to-upper: Converts the home env vars to uppercase
                                      (default 'false')

    Example:

    .. literalinclude:: /../../tests/wrappers/fixtures/custom-tools001.yaml
    """
    base = 'com.cloudbees.jenkins.plugins.customtools'
    wrapper = XML.SubElement(xml_parent,
                             base + ".CustomToolInstallWrapper")

    wrapper_tools = XML.SubElement(wrapper, 'selectedTools')
    tools = data.get('tools', [])
    tool_node = base + '.CustomToolInstallWrapper_-SelectedTool'
    for tool in tools:
        tool_wrapper = XML.SubElement(wrapper_tools, tool_node)
        mapping = [
            ('', 'name', tool),
        ]
        helpers.convert_mapping_to_xml(
            tool_wrapper, data, mapping, fail_required=True)

    opts = XML.SubElement(wrapper,
                          'multiconfigOptions')
    mapping = [
        ('skip-master-install', 'skipMasterInstallation', False),
    ]
    helpers.convert_mapping_to_xml(opts, data, mapping, fail_required=True)

    mapping = [
        ('convert-homes-to-upper', 'convertHomesToUppercase', False),
    ]
    helpers.convert_mapping_to_xml(wrapper, data, mapping, fail_required=True)


def nodejs_installator(registry, xml_parent, data):
    """yaml: nodejs-installator
    Requires the Jenkins :jenkins-wiki:`NodeJS Plugin
    <NodeJS+Plugin>`.

    :arg str name: nodejs installation name (required)

    Example:

    .. literalinclude::
            /../../tests/wrappers/fixtures/nodejs-installator001.yaml
    """
    npm_node = XML.SubElement(xml_parent,
                              'jenkins.plugins.nodejs.'
                              'NodeJSBuildWrapper')

    version = registry.get_plugin_info('nodejs').get('version', '0')
    npm_node.set("plugin", "nodejs@" + version)
    mapping = [
        ('name', 'nodeJSInstallationName', None),
    ]
    helpers.convert_mapping_to_xml(npm_node, data, mapping, fail_required=True)


def xvnc(registry, xml_parent, data):
    """yaml: xvnc
    Enable xvnc during the build.
    Requires the Jenkins :jenkins-wiki:`xvnc plugin <Xvnc+Plugin>`.

    :arg bool screenshot: Take screenshot upon build completion (default false)
    :arg bool xauthority: Create a dedicated Xauthority file per build (default
        true)

    Full Example:

    .. literalinclude:: /../../tests/wrappers/fixtures/xvnc-full.yaml
       :language: yaml

    Minimal Example:

    .. literalinclude:: /../../tests/wrappers/fixtures/xvnc-minimal.yaml
       :language: yaml
    """
    xwrapper = XML.SubElement(xml_parent,
                              'hudson.plugins.xvnc.Xvnc')
    xwrapper.set('plugin', 'xvnc')

    mapping = [
        ('screenshot', 'takeScreenshot', False),
        ('xauthority', 'useXauthority', True),
    ]
    helpers.convert_mapping_to_xml(xwrapper, data, mapping, fail_required=True)


def job_log_logger(registry, xml_parent, data):
    """yaml: job-log-logger
    Enable writing the job log to the underlying logging system.
    Requires the Jenkins :jenkins-wiki:`Job Log Logger plugin
    <Job+Log+Logger+Plugin>`.

    :arg bool suppress-empty: Suppress empty log messages
                              (default true)

    Example:

    .. literalinclude:: /../../tests/wrappers/fixtures/job-log-logger001.yaml

    """
    top = XML.SubElement(xml_parent,
                         'org.jenkins.ci.plugins.jobloglogger.'
                         'JobLogLoggerBuildWrapper')
    mapping = [
        ('suppress-empty', 'suppressEmpty', True),
    ]
    helpers.convert_mapping_to_xml(top, data, mapping, fail_required=True)


def xvfb(registry, xml_parent, data):
    """yaml: xvfb
    Enable xvfb during the build.
    Requires the Jenkins :jenkins-wiki:`Xvfb Plugin <Xvfb+Plugin>`.

    :arg str installation-name: The name of the Xvfb tool installation (default
        'default')
    :arg bool auto-display-name: Uses the -displayfd option of Xvfb by which it
        chooses it's own display name (default false)
    :arg str display-name: Ordinal of the display Xvfb will be running on, if
        left empty chosen based on current build executor number (default '')
    :arg str assigned-labels: If you want to start Xvfb only on specific nodes
        specify its name or label (default '')
    :arg bool parallel-build: When running multiple Jenkins nodes on the same
        machine this setting influences the display number generation (default
        false)
    :arg int timeout: A timeout of given seconds to wait before returning
        control to the job (default 0)
    :arg str screen: Resolution and color depth. (default '1024x768x24')
    :arg int display-name-offset: Offset for display names. (default 1)
    :arg str additional-options: Additional options to be added with the
        options above to the Xvfb command line (default '')
    :arg bool debug: If Xvfb output should appear in console log of this job
        (default false)
    :arg bool shutdown-with-build: Should the display be kept until the whole
        job ends (default false)

    Full Example:

    .. literalinclude:: /../../tests/wrappers/fixtures/xvfb-full.yaml
       :language: yaml

    Minimal Example:

    .. literalinclude:: /../../tests/wrappers/fixtures/xvfb-minimal.yaml
       :language: yaml
    """
    xwrapper = XML.SubElement(xml_parent,
                              'org.jenkinsci.plugins.xvfb.XvfbBuildWrapper')

    mapping = [
        ('installation-name', 'installationName', 'default'),
        ('auto-display-name', 'autoDisplayName', False),
        ('display-name', 'displayName', ''),
        ('assigned-labels', 'assignedLabels', ''),
        ('parallel-build', 'parallelBuild', False),
        ('timeout', 'timeout', 0),
        ('screen', 'screen', '1024x768x24'),
        ('display-name-offset', 'displayNameOffset', 1),
        ('additional-options', 'additionalOptions', ''),
        ('debug', 'debug', False),
        ('shutdown-with-build', 'shutdownWithBuild', False),
    ]
    helpers.convert_mapping_to_xml(xwrapper, data, mapping, fail_required=True)


def android_emulator(registry, xml_parent, data):
    """yaml: android-emulator
    Automates many Android development tasks including SDK installation,
    build file generation, emulator creation and launch,
    APK (un)installation...
    Requires the Jenkins :jenkins-wiki:`Android Emulator Plugin
    <Android+Emulator+Plugin>`.

    :arg str avd: Enter the name of an existing Android emulator configuration.
        If this is exclusive with the 'os' arg.
    :arg str os: Can be an OS version, target name or SDK add-on
    :arg str screen-density: Density in dots-per-inch (dpi) or as an alias,
        e.g. "160" or "mdpi". (default mdpi)
    :arg str screen-resolution: Can be either a named resolution or explicit
        size, e.g. "WVGA" or "480x800". (default WVGA)
    :arg str locale: Language and country pair. (default en_US)
    :arg str target-abi: Name of the ABI / system image to be used. (optional)
    :arg str sd-card: sd-card size e.g. "32M" or "10240K". (optional)
    :arg bool wipe: if true, the emulator will have its user data reset at
        start-up (default false)
    :arg bool show-window: if true, the Android emulator user interface will
        be displayed on screen during the build. (default false)
    :arg bool snapshot: Start emulator from stored state (default false)
    :arg bool delete: Delete Android emulator at the end of build
        (default false)
    :arg int startup-delay: Wait this many seconds before attempting
        to start the emulator (default 0)
    :arg str commandline-options: Will be given when starting the
        Android emulator executable (optional)
    :arg str exe: The emulator executable. (optional)
    :arg list hardware-properties: Dictionary of hardware properties. Allows
        you to override the default values for an AVD. (optional)

    Example:

    .. literalinclude:: /../../tests/wrappers/fixtures/android003.yaml
    """
    root = XML.SubElement(xml_parent,
                          'hudson.plugins.android__emulator.AndroidEmulator')

    if data.get('avd') and data.get('os'):
        raise JenkinsJobsException("'avd' and 'os' options are "
                                   "exclusive, please pick one only")

    if not data.get('avd') and not data.get('os'):
        raise JenkinsJobsException("AndroidEmulator requires an AVD name or"
                                   "OS version to run: specify 'os' or 'avd'")

    if data.get('avd'):
        XML.SubElement(root, 'avdName').text = str(data['avd'])

    else:
        mapping = [
            ('os', 'osVersion', None),
            ('screen-density', 'screenDensity', 'mdpi'),
            ('screen-resolution', 'screenResolution', 'WVGA'),
            ('locale', 'deviceLocale', 'en_US'),
            ('target-abi', 'targetAbi', ''),
            ('sd-card', 'sdCardSize', ''),
        ]
        helpers.convert_mapping_to_xml(root, data, mapping, fail_required=True)

    hardware = XML.SubElement(root, 'hardwareProperties')
    for prop_name, prop_val in data.get('hardware-properties', {}).items():
        prop_node = XML.SubElement(hardware,
                                   'hudson.plugins.android__emulator'
                                   '.AndroidEmulator_-HardwareProperty')
        mapping = [
            ('', 'key', prop_name),
            ('', 'value', prop_val),
        ]
        helpers.convert_mapping_to_xml(
            prop_node, data, mapping, fail_required=True)
    mapping = [
        ('wipe', 'wipeData', False),
        ('show-window', 'showWindow', False),
        ('snapshot', 'useSnapshots', False),
        ('delete', 'deleteAfterBuild', False),
        ('startup-delay', 'startupDelay', 0),
        ('commandline-options', 'commandLineOptions', ''),
        ('exe', 'executable', ''),
    ]
    helpers.convert_mapping_to_xml(root, data, mapping, fail_required=True)


def artifactory_maven(registry, xml_parent, data):
    """yaml: artifactory-maven
    Wrapper for non-Maven projects. Requires the
    :jenkins-wiki:`Artifactory Plugin <Artifactory+Plugin>`

    :arg str url: URL of the Artifactory server. e.g.
        https://www.jfrog.com/artifactory/ (default '')
    :arg str name: Artifactory user with permissions use for
        connected to the selected Artifactory Server
        (default '')
    :arg str repo-key: Name of the repository to search for
        artifact dependencies. Provide a single repo-key or provide
        separate release-repo-key and snapshot-repo-key.
    :arg str release-repo-key: Release repository name. Value of
        repo-key take priority over release-repo-key if provided.
    :arg str snapshot-repo-key: Snapshots repository name. Value of
        repo-key take priority over release-repo-key if provided.

    Example:

    .. literalinclude:: /../../tests/wrappers/fixtures/artifactory001.yaml
       :language: yaml

    """

    artifactory = XML.SubElement(
        xml_parent,
        'org.jfrog.hudson.maven3.ArtifactoryMaven3NativeConfigurator')

    # details
    details = XML.SubElement(artifactory, 'details')
    helpers.artifactory_common_details(details, data)

    if 'repo-key' in data:
        mapping = [('repo-key', 'downloadRepositoryKey', None)]
    else:
        mapping = [
            ('snapshot-repo-key', 'downloadSnapshotRepositoryKey', ''),
            ('release-repo-key', 'downloadReleaseRepositoryKey', ''),
        ]
    helpers.convert_mapping_to_xml(details, data, mapping, fail_required=True)


def artifactory_generic(registry, xml_parent, data):
    """yaml: artifactory-generic
    Wrapper for non-Maven projects. Requires the
    :jenkins-wiki:`Artifactory Plugin <Artifactory+Plugin>`

    :arg str url: URL of the Artifactory server. e.g.
        https://www.jfrog.com/artifactory/ (default '')
    :arg str name: Artifactory user with permissions use for
        connected to the selected Artifactory Server
        (default '')
    :arg str repo-key: Release repository name (plugin < 2.3.0) (default '')
    :arg str snapshot-repo-key: Snapshots repository name (plugin < 2.3.0)
        (default '')
    :arg str key-from-select: Repository key to use (plugin >= 2.3.0)
        (default '')
    :arg str key-from-text: Repository key to use that can be configured
        dynamically using Jenkins variables (plugin >= 2.3.0) (default '')
    :arg list deploy-pattern: List of patterns for mappings
        build artifacts to published artifacts. Supports Ant-style wildcards
        mapping to target directories. E.g.: */*.zip=>dir (default [])
    :arg list resolve-pattern: List of references to other
        artifacts that this build should use as dependencies.
    :arg list matrix-params: List of properties to attach to all deployed
        artifacts in addition to the default ones: build.name, build.number,
        and vcs.revision (default [])
    :arg bool deploy-build-info: Deploy jenkins build metadata with
        artifacts to Artifactory (default false)
    :arg bool env-vars-include: Include environment variables accessible by
        the build process. Jenkins-specific env variables are always included.
        Use the env-vars-include-patterns and env-vars-exclude-patterns to
        filter the environment variables published to artifactory.
        (default false)
    :arg list env-vars-include-patterns: List of environment variable patterns
        for including env vars as part of the published build info. Environment
        variables may contain the * and the ? wildcards (default [])
    :arg list env-vars-exclude-patterns: List of environment variable patterns
        that determine the env vars excluded from the published build info
        (default [])
    :arg bool discard-old-builds:
        Remove older build info from Artifactory (default false)
    :arg bool discard-build-artifacts:
        Remove older build artifacts from Artifactory (default false)

    Example:

    .. literalinclude:: /../../tests/wrappers/fixtures/artifactory002.yaml
       :language: yaml

    """

    artifactory = XML.SubElement(
        xml_parent,
        'org.jfrog.hudson.generic.ArtifactoryGenericConfigurator')

    # details
    details = XML.SubElement(artifactory, 'details')
    helpers.artifactory_common_details(details, data)

    # Get plugin information to maintain backwards compatibility
    info = registry.get_plugin_info('artifactory')
    # Note: Assume latest version of plugin is preferred config format
    version = pkg_resources.parse_version(
        info.get('version', str(sys.maxsize)))

    if version >= pkg_resources.parse_version('2.3.0'):
        deployReleaseRepo = XML.SubElement(details, 'deployReleaseRepository')
        XML.SubElement(deployReleaseRepo, 'keyFromText').text = data.get(
            'key-from-text', '')
        XML.SubElement(deployReleaseRepo, 'keyFromSelect').text = data.get(
            'key-from-select', '')
        XML.SubElement(deployReleaseRepo, 'dynamicMode').text = str(
            'key-from-text' in data.keys()).lower()
    else:
        XML.SubElement(details, 'repositoryKey').text = data.get(
            'repo-key', '')
        XML.SubElement(details, 'snapshotsRepositoryKey').text = data.get(
            'snapshot-repo-key', '')

    XML.SubElement(artifactory, 'deployPattern').text = ','.join(data.get(
        'deploy-pattern', []))
    XML.SubElement(artifactory, 'resolvePattern').text = ','.join(
        data.get('resolve-pattern', []))
    XML.SubElement(artifactory, 'matrixParams').text = ','.join(
        data.get('matrix-params', []))

    XML.SubElement(artifactory, 'deployBuildInfo').text = str(
        data.get('deploy-build-info', False)).lower()
    XML.SubElement(artifactory, 'includeEnvVars').text = str(
        data.get('env-vars-include', False)).lower()
    XML.SubElement(artifactory, 'discardOldBuilds').text = str(
        data.get('discard-old-builds', False)).lower()
    XML.SubElement(artifactory, 'discardBuildArtifacts').text = str(
        data.get('discard-build-artifacts', True)).lower()

    # envVarsPatterns
    helpers.artifactory_env_vars_patterns(artifactory, data)


def artifactory_maven_freestyle(registry, xml_parent, data):
    """yaml: artifactory-maven-freestyle
    Wrapper for Free Stype projects. Requires the Artifactory plugin.
    Requires :jenkins-wiki:`Artifactory Plugin <Artifactory+Plugin>`

    :arg str url: URL of the Artifactory server. e.g.
        https://www.jfrog.com/artifactory/ (default '')
    :arg str name: Artifactory user with permissions use for
        connected to the selected Artifactory Server (default '')
    :arg str release-repo-key: Release repository name (default '')
    :arg str snapshot-repo-key: Snapshots repository name (default '')
    :arg bool publish-build-info: Push build metadata with artifacts
        (default false)
    :arg bool discard-old-builds:
        Remove older build info from Artifactory (default true)
    :arg bool discard-build-artifacts:
        Remove older build artifacts from Artifactory (default false)
    :arg bool include-env-vars: Include all environment variables
        accessible by the build process. Jenkins-specific env variables
        are always included (default false)
    :arg bool run-checks: Run automatic license scanning check after the
        build is complete (default false)
    :arg bool include-publish-artifacts: Include the build's published
        module artifacts in the license violation checks if they are
        also used as dependencies for other modules in this build
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
    :arg bool filter-excluded-artifacts-from-build: Add the excluded
        files to the excludedArtifacts list and remove them from the
        artifacts list in the build info (default false)
    :arg str scopes:  A list of dependency scopes/configurations to run
        license violation checks on. If left empty all dependencies from
        all scopes will be checked (default '')
    :arg str violation-recipients: Recipients that need to be notified
        of license violations in the build info (default '')
    :arg list matrix-params: List of properties to attach to all
        deployed artifacts in addition to the default ones:
        build.name, build.number, and vcs.revision (default '')
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
        Server. The specific artifacts to push are controlled using
        the deployment-include-patterns and deployment-exclude-patterns.
        (default true)
    :arg list deployment-include-patterns: List of patterns for including
        build artifacts to publish to artifactory. (default[]')
    :arg list deployment-exclude-patterns: List of patterns
        for excluding artifacts from deployment to Artifactory
        (default [])
    :arg bool env-vars-include: Include environment variables
        accessible by the build process. Jenkins-specific env variables
        are always included. Environment variables can be filtered using
        the env-vars-include-patterns nad env-vars-exclude-patterns.
        (default false)
    :arg list env-vars-include-patterns: List of environment variable patterns
        that will be included as part of the published build info. Environment
        variables may contain the * and the ? wildcards (default [])
    :arg list env-vars-exclude-patterns: List of environment variable patterns
        that will be excluded from the published build info
        (default [])

    Example:

    .. literalinclude:: /../../tests/wrappers/fixtures/artifactory003.yaml
       :language: yaml

    """

    artifactory = XML.SubElement(
        xml_parent,
        'org.jfrog.hudson.maven3.ArtifactoryMaven3Configurator')

    # details
    details = XML.SubElement(artifactory, 'details')
    helpers.artifactory_common_details(details, data)

    deploy_release = XML.SubElement(details, 'deployReleaseRepository')
    helpers.artifactory_repository(deploy_release, data, 'release')

    deploy_snapshot = XML.SubElement(details, 'deploySnapshotRepository')
    helpers.artifactory_repository(deploy_snapshot, data, 'snapshot')

    XML.SubElement(details, 'stagingPlugin').text = data.get(
        'resolve-staging-plugin', '')

    # resolverDetails
    resolver = XML.SubElement(artifactory, 'resolverDetails')
    helpers.artifactory_common_details(resolver, data)

    resolve_snapshot = XML.SubElement(resolver, 'resolveSnapshotRepository')
    helpers.artifactory_repository(resolve_snapshot, data, 'snapshot')

    deploy_release = XML.SubElement(resolver, 'resolveReleaseRepository')
    helpers.artifactory_repository(deploy_release, data, 'release')

    XML.SubElement(resolver, 'stagingPlugin').text = data.get(
        'resolve-staging-plugin', '')

    # artifactDeploymentPatterns
    helpers.artifactory_deployment_patterns(artifactory, data)

    # envVarsPatterns
    helpers.artifactory_env_vars_patterns(artifactory, data)

    XML.SubElement(artifactory, 'matrixParams').text = ','.join(
        data.get('matrix-params', []))

    # optional__props
    helpers.artifactory_optional_props(artifactory, data, 'wrappers')


def maven_release(registry, xml_parent, data):
    """yaml: maven-release
    Wrapper for Maven projects
    Requires :jenkins-wiki:`M2 Release Plugin <M2+Release+Plugin>`

    :arg str release-goals: Release goals and options (default '')
    :arg str dry-run-goals: DryRun goals and options (default '')
    :arg int num-successful-builds: Number of successful release builds to keep
        (default 1)
    :arg bool select-custom-scm-comment-prefix: Preselect 'Specify custom SCM
        comment prefix' (default false)
    :arg bool select-append-jenkins-username: Preselect 'Append Jenkins
        Username' (default false)
    :arg bool select-scm-credentials: Preselect 'Specify SCM login/password'
        (default false)
    :arg str release-env-var: Release environment variable (default '')
    :arg str scm-user-env-var: SCM username environment variable (default '')
    :arg str scm-password-env-var: SCM password environment variable
        (default '')

    Example:

    .. literalinclude:: /../../tests/wrappers/fixtures/maven-release001.yaml
       :language: yaml

    """
    mvn_release = XML.SubElement(xml_parent,
                                 'org.jvnet.hudson.plugins.m2release.'
                                 'M2ReleaseBuildWrapper')

    mapping = [
        ('release-goals', 'releaseGoals', ''),
        ('dry-run-goals', 'dryRunGoals', ''),
        ('num-successful-builds', 'numberOfReleaseBuildsToKeep', 1),
        ('select-custom-scm-comment-prefix', 'selectCustomScmCommentPrefix',
         False),
        ('select-append-jenkins-username', 'selectAppendHudsonUsername',
         False),
        ('select-scm-credentials', 'selectScmCredentials', False),
        ('release-env-var', 'releaseEnvVar', ''),
        ('scm-user-env-var', 'scmUserEnvVar', ''),
        ('scm-password-env-var', 'scmPasswordEnvVar', ''),
    ]
    helpers.convert_mapping_to_xml(
        mvn_release, data, mapping, fail_required=True)


def version_number(parser, xml_parent, data):
    """yaml: version-number
    Generate a version number for the build using a format string. See the
    wiki page for more detailed descriptions of options.

    Requires the Jenkins :jenkins-wiki:`version number plugin
    <Version+Number+Plugin>`.

    :arg str variable-name: Name of environment variable to assign version
        number to (required)
    :arg str format-string: Format string used to generate version number
        (required)
    :arg str prefix-variable: Variable that contains version number prefix
        (optional)
    :arg bool skip-failed-builds: If the build fails, DO NOT increment any
        auto-incrementing component of the version number (default: false)
    :arg bool display-name: Use the version number for the build display
        name (default: false)
    :arg str start-date: The date the project began as a UTC timestamp
        (default 1970-1-1 00:00:00.0 UTC)
    :arg int builds-today: The number of builds that have been executed
        today (optional)
    :arg int builds-this-month: The number of builds that have been executed
        since the start of the month (optional)
    :arg int builds-this-year: The number of builds that have been executed
        since the start of the year (optional)
    :arg int builds-all-time: The number of builds that have been executed
        since the start of the project (optional)

    Example:

    .. literalinclude:: /../../tests/wrappers/fixtures/version-number001.yaml
       :language: yaml

    """
    version_number = XML.SubElement(
        xml_parent, 'org.jvnet.hudson.tools.versionnumber.VersionNumberBuilder'
    )

    mapping = [
        # option, xml name, default value
        ("variable-name", 'environmentVariableName', None),
        ("format-string", 'versionNumberString', None),
        ("prefix-variable", 'environmentPrefixVariable', ''),
        ("skip-failed-builds", 'skipFailedBuilds', False),
        ("display-name", 'useAsBuildDisplayName', False),
        ("start-date", 'projectStartDate', '1970-1-1 00:00:00.0 UTC'),
        ("builds-today", 'oBuildsToday', '-1'),
        ("builds-this-month", 'oBuildsThisMonth', '-1'),
        ("builds-this-year", 'oBuildsThisYear', '-1'),
        ("builds-all-time", 'oBuildsAllTime', '-1'),
    ]

    helpers.convert_mapping_to_xml(
        version_number, data, mapping, fail_required=True)


def github_pull_request(parser, xml_parent, data):
    """yaml: github-pull-request
    Set GitHub commit status with custom context and message.
    Requires the Jenkins :jenkins-wiki:`GitHub Pull Request Builder Plugin
    <GitHub+pull+request+builder+plugin>`.

    :arg bool show-matrix-status: Only post commit status of parent matrix job
        (default false)
    :arg str status-context: The context to include on PR status comments
        (default '')
    :arg str triggered-status: The status message to set when the build has
        been triggered (default '')
    :arg str started-status: The status message to set when the build has
        been started (default '')
    :arg str status-url: The status URL to set (default '')
    :arg bool status-add-test-results: Add test result one-liner to status
        message (default false)
    :arg list statuses: List of custom statuses on the commit for when a build
        is completed

        :Status:
            * **message** (`str`) -- The message that is appended to a comment
              when a build finishes with the desired build status. If no status
              updates should be made when a build finishes with the indicated
              build status, use "--none--" to alert the trigger. (required)
            * **result** (`str`) -- Build result. Can be one of 'SUCCESS',
              'ERROR' or 'FAILURE'. (required)

    Minimal Example:

    .. literalinclude::
        /../../tests/wrappers/fixtures/github-pull-request-minimal.yaml
       :language: yaml

    Full Example:

    .. literalinclude::
        /../../tests/wrappers/fixtures/github-pull-request-full.yaml
       :language: yaml

    """
    ghprb = XML.SubElement(
        xml_parent, 'org.jenkinsci.plugins.ghprb.upstream.GhprbUpstreamStatus'
    )

    mapping = [
        # option, xml name, default value
        ("show-matrix-status", 'showMatrixStatus', False),
        ("status-context", 'commitStatusContext', ''),
        ("triggered-status", 'triggeredStatus', ''),
        ("started-status", 'startedStatus', ''),
        ("status-url", 'statusUrl', ''),
        ("status-add-test-results", 'addTestResults', False),
    ]
    helpers.convert_mapping_to_xml(ghprb, data, mapping, fail_required=True)

    statuses = data.get('statuses', [])
    if statuses:
        status_mapping = [
            ('message', 'message', None),
            ('result', 'result', ''),
        ]
        result_list = ['ERROR', 'SUCCESS', 'FAILURE']

        completed_tag = XML.SubElement(ghprb, 'completedStatus')
        for status in statuses:
            result = status.get('result', '')
            if result not in result_list:
                raise JenkinsJobsException(
                    "'result' must be one of: " + ', '.join(result_list))

            result_tag = XML.SubElement(
                completed_tag,
                'org.jenkinsci.plugins.ghprb.extensions'
                '.comments.GhprbBuildResultMessage'
            )
            helpers.convert_mapping_to_xml(
                result_tag, status, status_mapping, fail_required=True)


class Wrappers(jenkins_jobs.modules.base.Base):
    sequence = 80

    component_type = 'wrapper'
    component_list_type = 'wrappers'

    def gen_xml(self, xml_parent, data):
        wrappers = XML.SubElement(xml_parent, 'buildWrappers')

        for wrap in data.get('wrappers', []):
            self.registry.dispatch('wrapper', wrappers, wrap)
