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
import xml.etree.ElementTree as XML
import pkg_resources
import jenkins_jobs.modules.base
from jenkins_jobs.errors import (JenkinsJobsException,
                                 InvalidAttributeError,
                                 MissingAttributeError)
from jenkins_jobs.modules.builders import create_builders
from jenkins_jobs.modules.helpers import config_file_provider_builder

logger = logging.getLogger(__name__)

MIN_TO_SEC = 60


def ci_skip(parser, xml_parent, data):
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

    .. literalinclude:: \
    /../../tests/wrappers/fixtures/config-file-provider003.yaml
       :language: yaml
    """
    cfp = XML.SubElement(xml_parent, 'org.jenkinsci.plugins.configfiles.'
                         'buildwrapper.ConfigFileBuildWrapper')
    cfp.set('plugin', 'config-file-provider')
    config_file_provider_builder(cfp, data)


def logfilesize(parser, xml_parent, data):
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

    Minimum config example:

    .. literalinclude:: /../../tests/wrappers/fixtures/logfilesize002.yaml

    Full config example:

    .. literalinclude:: /../../tests/wrappers/fixtures/logfilesize001.yaml

    """
    lfswrapper = XML.SubElement(xml_parent,
                                'hudson.plugins.logfilesizechecker.'
                                'LogfilesizecheckerWrapper')
    lfswrapper.set("plugin", "logfilesizechecker")

    XML.SubElement(lfswrapper, 'setOwn').text = str(
        data.get('set-own', 'false')).lower()
    XML.SubElement(lfswrapper, 'maxLogSize').text = str(
        data.get('size', '128')).lower()
    XML.SubElement(lfswrapper, 'failBuild').text = str(
        data.get('fail', 'false')).lower()


def timeout(parser, xml_parent, data):
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

    :arg int elastic-percentage: Percentage of the three most recent builds
        where to declare a timeout, only applies to **elastic** type.
        (default 0)
    :arg int elastic-number-builds: Number of builds to consider computing
        average duration, only applies to **elastic** type. (default 3)
    :arg int elastic-default-timeout: Timeout to use if there were no previous
        builds, only applies to **elastic** type. (default 3)

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

    """
    prefix = 'hudson.plugins.build__timeout.'
    twrapper = XML.SubElement(xml_parent, prefix + 'BuildTimeoutWrapper')

    plugin_info = parser.registry.get_plugin_info(
        "Jenkins build timeout plugin")
    version = pkg_resources.parse_version(plugin_info.get("version", "0"))

    valid_strategies = ['absolute', 'no-activity', 'likely-stuck', 'elastic']

    if version >= pkg_resources.parse_version("1.14"):
        strategy = data.get('type', 'absolute')
        if strategy not in valid_strategies:
            InvalidAttributeError('type', strategy, valid_strategies)

        if strategy == "absolute":
            strategy_element = XML.SubElement(
                twrapper, 'strategy',
                {'class': "hudson.plugins.build_timeout."
                          "impl.AbsoluteTimeOutStrategy"})
            XML.SubElement(strategy_element, 'timeoutMinutes'
                           ).text = str(data.get('timeout', 3))
        elif strategy == "no-activity":
            strategy_element = XML.SubElement(
                twrapper, 'strategy',
                {'class': "hudson.plugins.build_timeout."
                          "impl.NoActivityTimeOutStrategy"})
            timeout_sec = int(data.get('timeout', 3)) * MIN_TO_SEC
            XML.SubElement(strategy_element,
                           'timeoutSecondsString').text = str(timeout_sec)
        elif strategy == "likely-stuck":
            strategy_element = XML.SubElement(
                twrapper, 'strategy',
                {'class': "hudson.plugins.build_timeout."
                          "impl.LikelyStuckTimeOutStrategy"})
            XML.SubElement(strategy_element,
                           'timeoutMinutes').text = str(data.get('timeout', 3))
        elif strategy == "elastic":
            strategy_element = XML.SubElement(
                twrapper, 'strategy',
                {'class': "hudson.plugins.build_timeout."
                          "impl.ElasticTimeOutStrategy"})
            XML.SubElement(strategy_element, 'timeoutPercentage'
                           ).text = str(data.get('elastic-percentage', 0))
            XML.SubElement(strategy_element, 'numberOfBuilds'
                           ).text = str(data.get('elastic-number-builds', 0))
            XML.SubElement(strategy_element, 'timeoutMinutesElasticDefault'
                           ).text = str(data.get('elastic-default-timeout', 3))

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
        timeout_env_var = data.get('timeout-var')
        if timeout_env_var:
            XML.SubElement(twrapper,
                           'timeoutEnvVar').text = str(timeout_env_var)
    else:
        XML.SubElement(twrapper,
                       'timeoutMinutes').text = str(data.get('timeout', 3))
        timeout_env_var = data.get('timeout-var')
        if timeout_env_var:
            XML.SubElement(twrapper,
                           'timeoutEnvVar').text = str(timeout_env_var)
        XML.SubElement(twrapper, 'failBuild'
                       ).text = str(data.get('fail', 'false')).lower()
        XML.SubElement(twrapper, 'writingDescription'
                       ).text = str(data.get('write-description', 'false')
                                    ).lower()
        XML.SubElement(twrapper, 'timeoutPercentage'
                       ).text = str(data.get('elastic-percentage', 0))
        XML.SubElement(twrapper, 'timeoutMinutesElasticDefault'
                       ).text = str(data.get('elastic-default-timeout', 3))

        tout_type = str(data.get('type', 'absolute')).lower()
        if tout_type == 'likely-stuck':
            tout_type = 'likelyStuck'
        XML.SubElement(twrapper, 'timeoutType').text = tout_type


def timestamps(parser, xml_parent, data):
    """yaml: timestamps
    Add timestamps to the console log.
    Requires the Jenkins :jenkins-wiki:`Timestamper Plugin <Timestamper>`.

    Example::

      wrappers:
        - timestamps
    """
    XML.SubElement(xml_parent,
                   'hudson.plugins.timestamper.TimestamperBuildWrapper')


def ansicolor(parser, xml_parent, data):
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

    # Optional colormap
    colormap = data.get('colormap')
    if colormap:
        XML.SubElement(cwrapper, 'colorMapName').text = colormap


def live_screenshot(parser, xml_parent, data):
    """yaml: live-screenshot
    Show live screenshots of running jobs in the job list.
    Requires the Jenkins :jenkins-wiki:`Live-Screenshot Plugin
    <LiveScreenshot+Plugin>`.

    :arg str full-size: name of screenshot file (default 'screenshot.png')
    :arg str thumbnail: name of thumbnail file (default 'screenshot-thumb.png')

    File type must be .png and they must be located inside the $WORKDIR.

    Example using defaults:

    .. literalinclude:: /../../tests/wrappers/fixtures/live_screenshot001.yaml

    or specifying the files to use:

    .. literalinclude:: /../../tests/wrappers/fixtures/live_screenshot002.yaml
    """
    live = XML.SubElement(
        xml_parent,
        'org.jenkinsci.plugins.livescreenshot.LiveScreenshotBuildWrapper')
    XML.SubElement(live, 'fullscreenFilename').text = data.get(
        'full-size', 'screenshot.png')
    XML.SubElement(live, 'thumbnailFilename').text = data.get(
        'thumbnail', 'screenshot-thumb.png')


def mask_passwords(parser, xml_parent, data):
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


def workspace_cleanup(parser, xml_parent, data):
    """yaml: workspace-cleanup (pre-build)

    Requires the Jenkins :jenkins-wiki:`Workspace Cleanup Plugin
    <Workspace+Cleanup+Plugin>`.

    The post-build workspace-cleanup is available as a publisher.

    :arg list include: list of files to be included
    :arg list exclude: list of files to be excluded
    :arg bool dirmatch: Apply pattern to directories too

    Example::

      wrappers:
        - workspace-cleanup:
            include:
              - "*.zip"
    """

    p = XML.SubElement(xml_parent,
                       'hudson.plugins.ws__cleanup.PreBuildCleanup')
    p.set("plugin", "ws-cleanup@0.14")
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

    deldirs = XML.SubElement(p, 'deleteDirs')
    deldirs.text = str(data.get("dirmatch", False)).lower()


def m2_repository_cleanup(parser, xml_parent, data):
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


def rvm_env(parser, xml_parent, data):
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


def rbenv(parser, xml_parent, data):
    """yaml: rbenv
    Set the rbenv implementation.
    Requires the Jenkins :jenkins-wiki:`rbenv plugin <rbenv+plugin>`.

    All parameters are optional.

    :arg str ruby-version: Version of Ruby to use  (default: 1.9.3-p484)
    :arg bool ignore-local-version: If true, ignore local Ruby
        version (defined in the ".ruby-version" file in workspace) even if it
        has been defined  (default: false)
    :arg str preinstall-gem-list: List of gems to install
        (default: 'bundler,rake')
    :arg str rbenv-root: RBENV_ROOT  (default: $HOME/.rbenv)
    :arg str rbenv-repo: Which repo to clone rbenv from
        (default: https://github.com/sstephenson/rbenv.git)
    :arg str rbenv-branch: Which branch to clone rbenv from  (default: master)
    :arg str ruby-build-repo: Which repo to clone ruby-build from
        (default: https://github.com/sstephenson/ruby-build.git)
    :arg str ruby-build-branch: Which branch to clone ruby-build from
        (default: master)

    Example:

    .. literalinclude:: /../../tests/wrappers/fixtures/rbenv003.yaml
    """

    mapping = [
        # option, xml name, default value (text), attributes (hard coded)
        ("preinstall-gem-list", 'gem__list', 'bundler,rake'),
        ("rbenv-root", 'rbenv__root', '$HOME/.rbenv'),
        ("rbenv-repo", 'rbenv__repository',
            'https://github.com/sstephenson/rbenv.git'),
        ("rbenv-branch", 'rbenv__revision', 'master'),
        ("ruby-build-repo", 'ruby__build__repository',
            'https://github.com/sstephenson/ruby-build.git'),
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


def build_name(parser, xml_parent, data):
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
    XML.SubElement(bsetter, 'template').text = data['name']


def port_allocator(parser, xml_parent, data):
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
        logger.warn('port_allocator name is deprecated, use a names list '
                    ' instead')
        names = [data['name']]
    for name in names:
        dpt = XML.SubElement(ports,
                             'org.jvnet.hudson.plugins.port__allocator.'
                             'DefaultPortType')
        XML.SubElement(dpt, 'name').text = name


def locks(parser, xml_parent, data):
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


def copy_to_slave(parser, xml_parent, data):
    """yaml: copy-to-slave
    Copy files to slave before build
    Requires the Jenkins :jenkins-wiki:`Copy To Slave Plugin
    <Copy+To+Slave+Plugin>`.

    :arg list includes: list of file patterns to copy
    :arg list excludes: list of file patterns to exclude
    :arg bool flatten: flatten directory structure
    :arg str relative-to: base location of includes/excludes,
                          must be userContent ($JENKINS_HOME/userContent)
                          home ($JENKINS_HOME) or workspace
    :arg bool include-ant-excludes: exclude ant's default excludes

    Example::

      wrappers:
        - copy-to-slave:
            includes:
              - file1
              - file2*.txt
            excludes:
              - file2bad.txt
    """
    p = 'com.michelin.cio.hudson.plugins.copytoslave.CopyToSlaveBuildWrapper'
    cs = XML.SubElement(xml_parent, p)

    XML.SubElement(cs, 'includes').text = ','.join(data.get('includes', ['']))
    XML.SubElement(cs, 'excludes').text = ','.join(data.get('excludes', ['']))
    XML.SubElement(cs, 'flatten').text = \
        str(data.get('flatten', False)).lower()
    XML.SubElement(cs, 'includeAntExcludes').text = \
        str(data.get('include-ant-excludes', False)).lower()

    rel = str(data.get('relative-to', 'userContent'))
    opt = ('userContent', 'home', 'workspace')
    if rel not in opt:
        raise ValueError('relative-to must be one of %r' % opt)
    XML.SubElement(cs, 'relativeTo').text = rel

    # seems to always be false, can't find it in source code
    XML.SubElement(cs, 'hudsonHomeRelative').text = 'false'


def inject(parser, xml_parent, data):
    """yaml: inject
    Add or override environment variables to the whole build process
    Requires the Jenkins :jenkins-wiki:`EnvInject Plugin <EnvInject+Plugin>`.

    :arg str properties-file: path to the properties file (default '')
    :arg str properties-content: key value pair of properties (default '')
    :arg str script-file: path to the script file (default '')
    :arg str script-content: contents of a script (default '')

    Example::

      wrappers:
        - inject:
            properties-file: /usr/local/foo
            properties-content: PATH=/foo/bar
            script-file: /usr/local/foo.sh
            script-content: echo $PATH
    """
    eib = XML.SubElement(xml_parent, 'EnvInjectBuildWrapper')
    info = XML.SubElement(eib, 'info')
    jenkins_jobs.modules.base.add_nonblank_xml_subelement(
        info, 'propertiesFilePath', data.get('properties-file'))
    jenkins_jobs.modules.base.add_nonblank_xml_subelement(
        info, 'propertiesContent', data.get('properties-content'))
    jenkins_jobs.modules.base.add_nonblank_xml_subelement(
        info, 'scriptFilePath', data.get('script-file'))
    jenkins_jobs.modules.base.add_nonblank_xml_subelement(
        info, 'scriptContent', data.get('script-content'))
    XML.SubElement(info, 'loadFilesFromMaster').text = 'false'


def inject_ownership_variables(parser, xml_parent, data):
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
    XML.SubElement(ownership, 'injectNodeOwnership').text = \
        str(data.get('node-variables', False)).lower()
    XML.SubElement(ownership, 'injectJobOwnership').text = \
        str(data.get('job-variables', False)).lower()


def inject_passwords(parser, xml_parent, data):
    """yaml: inject-passwords
    Inject passwords to the build as environment variables.
    Requires the Jenkins :jenkins-wiki:`EnvInject Plugin <EnvInject+Plugin>`.

    :arg bool global: inject global passwords to the job
    :arg bool mask-password-params: mask passsword parameters
    :arg list job-passwords: key value pair of job passwords

        :Parameter: * **name** (`str`) Name of password
                    * **password** (`str`) Encrypted password

    Example:

    .. literalinclude:: /../../tests/wrappers/fixtures/passwords001.yaml

    """
    eib = XML.SubElement(xml_parent, 'EnvInjectPasswordWrapper')
    XML.SubElement(eib, 'injectGlobalPasswords').text = \
        str(data.get('global', False)).lower()
    XML.SubElement(eib, 'maskPasswordParameters').text = \
        str(data.get('mask-password-params', False)).lower()
    entries = XML.SubElement(eib, 'passwordEntries')
    passwords = data.get('job-passwords', [])
    if passwords:
        for password in passwords:
            entry = XML.SubElement(entries, 'EnvInjectPasswordEntry')
            XML.SubElement(entry, 'name').text = password['name']
            XML.SubElement(entry, 'value').text = password['password']


def env_file(parser, xml_parent, data):
    """yaml: env-file
    Add or override environment variables to the whole build process
    Requires the Jenkins :jenkins-wiki:`Environment File Plugin
    <Envfile+Plugin>`.

    :arg str properties-file: path to the properties file (default '')

    Example::

      wrappers:
        - env-file:
            properties-file: ${WORKSPACE}/foo
    """
    eib = XML.SubElement(xml_parent,
                         'hudson.plugins.envfile.EnvFileBuildWrapper')
    jenkins_jobs.modules.base.add_nonblank_xml_subelement(
        eib, 'filePath', data.get('properties-file'))


def env_script(parser, xml_parent, data):
    """yaml: env-script
    Add or override environment variables to the whole build process.
    Requires the Jenkins :jenkins-wiki:`Environment Script Plugin
    <Environment+Script+Plugin>`.

    :arg script-content: The script to run (default: '')
    :arg only-run-on-parent: Only applicable for Matrix Jobs. If true, run only
      on the matrix parent job (default: false)

    Example:

    .. literalinclude:: /../../tests/wrappers/fixtures/env-script001.yaml

    """
    el = XML.SubElement(xml_parent, 'com.lookout.jenkins.EnvironmentScript')
    XML.SubElement(el, 'script').text = data.get('script-content', '')
    only_on_parent = str(data.get('only-run-on-parent', False)).lower()
    XML.SubElement(el, 'onlyRunOnParent').text = only_on_parent


def jclouds(parser, xml_parent, data):
    """yaml: jclouds
    Uses JClouds to provide slave launching on most of the currently
    usable Cloud infrastructures.
    Requires the Jenkins :jenkins-wiki:`JClouds Plugin <JClouds+Plugin>`.

    :arg bool single-use: Whether or not to terminate the slave after use
                          (default: False).
    :arg list instances: The name of the jclouds template to create an
                         instance from, and its parameters.
    :arg str cloud-name: The name of the jclouds profile containing the
                         specified template.
    :arg int count: How many instances to create (default: 1).
    :arg bool stop-on-terminate: Whether or not to suspend instead of terminate
                                 the instance (default: False).

    Example::

      wrappers:
        - jclouds:
            single-use: True
            instances:
              - jenkins-dev-slave:
                  cloud-name: mycloud1
                  count: 1
                  stop-on-terminate: True
              - jenkins-test-slave:
                  cloud-name: mycloud2
                  count: 2
                  stop-on-terminate: False
    """
    buildWrapper = XML.SubElement(xml_parent,
                                  'jenkins.plugins.jclouds.compute.'
                                  'JCloudsBuildWrapper')
    instances = XML.SubElement(buildWrapper, 'instancesToRun')
    if 'instances' in data:
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


def build_user_vars(parser, xml_parent, data):
    """yaml: build-user-vars
    Set environment variables to the value of the user that started the build.
    Requires the Jenkins :jenkins-wiki:`Build User Vars Plugin
    <Build+User+Vars+Plugin>`.

    Example::

      wrappers:
        - build-user-vars
    """
    XML.SubElement(xml_parent, 'org.jenkinsci.plugins.builduser.BuildUser')


def release(parser, xml_parent, data):
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
    no_keep_forever = 'false'
    if str(data.get('keep-forever', True)).lower() == 'false':
        no_keep_forever = 'true'
    XML.SubElement(relwrap, 'doNotKeepLog').text = no_keep_forever
    XML.SubElement(relwrap, 'overrideBuildParameters').text = str(
        data.get('override-build-parameters', False)).lower()
    XML.SubElement(relwrap, 'releaseVersionTemplate').text = data.get(
        'version-template', '')
    parameters = data.get('parameters', [])
    if parameters:
        pdef = XML.SubElement(relwrap, 'parameterDefinitions')
        for param in parameters:
            parser.registry.dispatch('parameter', parser, pdef, param)

    builder_steps = {
        'pre-build': 'preBuildSteps',
        'post-build': 'postBuildSteps',
        'post-success': 'postSuccessfulBuildSteps',
        'post-fail': 'postFailedBuildSteps',
    }
    for step in builder_steps.keys():
        for builder in data.get(step, []):
            parser.registry.dispatch('builder', parser,
                                     XML.SubElement(relwrap,
                                                    builder_steps[step]),
                                     builder)


def sauce_ondemand(parser, xml_parent, data):
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
    XML.SubElement(sauce, 'enableSauceConnect').text = str(data.get(
        'enable-sauce-connect', False)).lower()
    host = data.get('sauce-host', '')
    XML.SubElement(sauce, 'seleniumHost').text = host
    port = data.get('sauce-port', '')
    XML.SubElement(sauce, 'seleniumPort').text = port
    # Optional override global authentication
    username = data.get('override-username')
    key = data.get('override-api-access-key')
    if username and key:
        cred = XML.SubElement(sauce, 'credentials')
        XML.SubElement(cred, 'username').text = username
        XML.SubElement(cred, 'apiKey').text = key
    atype = data.get('type', 'selenium')
    info = XML.SubElement(sauce, 'seleniumInformation')
    if atype == 'selenium':
        url = data.get('starting-url', '')
        XML.SubElement(info, 'startingURL').text = url
        browsers = XML.SubElement(info, 'seleniumBrowsers')
        for platform in data['platforms']:
            XML.SubElement(browsers, 'string').text = platform
        XML.SubElement(info, 'isWebDriver').text = 'false'
        XML.SubElement(sauce, 'seleniumBrowsers',
                       {'reference': '../seleniumInformation/'
                        'seleniumBrowsers'})
    if atype == 'webdriver':
        browsers = XML.SubElement(info, 'webDriverBrowsers')
        for platform in data['platforms']:
            XML.SubElement(browsers, 'string').text = platform
        XML.SubElement(info, 'isWebDriver').text = 'true'
        XML.SubElement(sauce, 'webDriverBrowsers',
                       {'reference': '../seleniumInformation/'
                        'webDriverBrowsers'})
    XML.SubElement(sauce, 'launchSauceConnectOnSlave').text = str(data.get(
        'launch-sauce-connect-on-slave', False)).lower()
    protocol = data.get('https-protocol', '')
    XML.SubElement(sauce, 'httpsProtocol').text = protocol
    options = data.get('sauce-connect-options', '')
    XML.SubElement(sauce, 'options').text = options


def pathignore(parser, xml_parent, data):
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


def pre_scm_buildstep(parser, xml_parent, data):
    """yaml: pre-scm-buildstep
    Execute a Build Step before running the SCM
    Requires the Jenkins :jenkins-wiki:`pre-scm-buildstep <pre-scm-buildstep>`.

    :arg list buildsteps: List of build steps to execute

        :Buildstep: Any acceptable builder, as seen in the example

    Example::

      wrappers:
        - pre-scm-buildstep:
          - shell: |
              #!/bin/bash
              echo "Doing somethiung cool"
          - shell: |
              #!/bin/zsh
              echo "Doing somethin cool with zsh"
          - ant: "target1 target2"
            ant-name: "Standard Ant"
          - inject:
               properties-file: example.prop
               properties-content: EXAMPLE=foo-bar
    """
    bsp = XML.SubElement(xml_parent,
                         'org.jenkinsci.plugins.preSCMbuildstep.'
                         'PreSCMBuildStepsWrapper')
    bs = XML.SubElement(bsp, 'buildSteps')
    for step in data:
        for edited_node in create_builders(parser, step):
            bs.append(edited_node)


def logstash(parser, xml_parent, data):
    """yaml: logstash build wrapper
    Dump the Jenkins console output to Logstash
    Requires the Jenkins :jenkins-wiki:`logstash plugin <Logstash+Plugin>`.

    :arg use-redis: Boolean to use Redis. (default: true)
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

    redis_bool = XML.SubElement(logstash, 'useRedis')
    redis_bool.text = str(data.get('use-redis', True)).lower()

    if data.get('use-redis'):
        redis_config = data.get('redis', {})
        redis_sub_element = XML.SubElement(logstash, 'redis')

        host_sub_element = XML.SubElement(redis_sub_element, 'host')
        host_sub_element.text = str(
            redis_config.get('host', 'localhost'))

        port_sub_element = XML.SubElement(redis_sub_element, 'port')
        port_sub_element.text = str(redis_config.get('port', '6379'))

        database_numb_sub_element = XML.SubElement(redis_sub_element, 'numb')
        database_numb_sub_element.text = \
            str(redis_config.get('database-number', '0'))

        database_pass_sub_element = XML.SubElement(redis_sub_element, 'pass')
        database_pass_sub_element.text = \
            str(redis_config.get('database-password', ''))

        data_type_sub_element = XML.SubElement(redis_sub_element, 'dataType')
        data_type_sub_element.text = \
            str(redis_config.get('data-type', 'list'))

        key_sub_element = XML.SubElement(redis_sub_element, 'key')
        key_sub_element.text = str(redis_config.get('key', 'logstash'))


def mongo_db(parser, xml_parent, data):
    """yaml: mongo-db build wrapper
    Initalizes a MongoDB database while running the build.
    Requires the Jenkins :jenkins-wiki:`MongoDB plugin <MongoDB+Plugin>`.

    :arg str name: The name of the MongoDB install to use
    :arg str data-directory: Data directory for the server (optional)
    :arg int port: Port for the server (optional)
    :arg str startup-params: Startup parameters for the server (optional)
    :arg int start-timeout: How long to wait for the server to start in
        milliseconds. 0 means no timeout. (default '0')

    Example:

    .. literalinclude:: /../../tests/wrappers/fixtures/mongo-db001.yaml

    """
    mongodb = XML.SubElement(xml_parent,
                             'org.jenkinsci.plugins.mongodb.'
                             'MongoBuildWrapper')
    mongodb.set('plugin', 'mongodb')

    if not str(data.get('name', '')):
        raise JenkinsJobsException('The mongo install name must be specified.')
    XML.SubElement(mongodb, 'mongodbName').text = str(data.get('name', ''))
    XML.SubElement(mongodb, 'port').text = str(data.get('port', ''))
    XML.SubElement(mongodb, 'dbpath').text = str(data.get(
        'data-directory', ''))
    XML.SubElement(mongodb, 'parameters').text = str(data.get(
        'startup-params', ''))
    XML.SubElement(mongodb, 'startTimeout').text = str(data.get(
        'start-timeout', '0'))


def delivery_pipeline(parser, xml_parent, data):
    """yaml: delivery-pipeline
    If enabled the job will create a version based on the template.
    The version will be set to the environment variable PIPELINE_VERSION and
    will also be set in the downstream jobs.

    Requires the Jenkins :jenkins-wiki:`Delivery Pipeline Plugin
    <Delivery+Pipeline+Plugin>`.

    :arg str version-template: Template for generated version e.g
        1.0.${BUILD_NUMBER} (default: '')
    :arg bool set-display-name: Set the generated version as the display name
        for the build (default: false)

    Example:

    .. literalinclude:: /../../tests/wrappers/fixtures/delivery-pipeline1.yaml

    """
    pvc = XML.SubElement(xml_parent,
                         'se.diabol.jenkins.pipeline.'
                         'PipelineVersionContributor')
    XML.SubElement(pvc, 'versionTemplate').text = data.get(
        'version-template', '')
    XML.SubElement(pvc, 'updateDisplayName').text = str(data.get(
        'set-display-name', False)).lower()


def matrix_tie_parent(parser, xml_parent, data):
    """yaml: matrix-tie-parent
    Tie parent to a node.
    Requires the Jenkins :jenkins-wiki:`Matrix Tie Parent Plugin
    <Matrix+Tie+Parent+Plugin>`.
    Note that from Jenkins version 1.532 this plugin's functionality is
    available under the "advanced" option of the matrix project configuration.
    You can use the top level ``node`` parameter to control where the parent
    job is tied in Jenkins 1.532 and higher.

    :arg str node: Name of the node.

    Example:

    .. literalinclude:: /../../tests/wrappers/fixtures/matrix-tie-parent.yaml
    """
    mtp = XML.SubElement(xml_parent, 'matrixtieparent.BuildWrapperMtp')
    XML.SubElement(mtp, 'labelName').text = data['node']


def exclusion(parser, xml_parent, data):
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
        dit = \
            XML.SubElement(ids,
                           'org.jvnet.hudson.plugins.exclusion.DefaultIdType')
        XML.SubElement(dit, 'name').text = str(resource).upper()


def ssh_agent_credentials(parser, xml_parent, data):
    """yaml: ssh-agent-credentials
    Sets up the user for the ssh agent plugin for jenkins.

    Requires the Jenkins :jenkins-wiki:`SSH-Agent Plugin <SSH+Agent+Plugin>`.

    :arg list users: A list of Jenkins users credential IDs (required)
    :arg str user: The user id of the jenkins user credentials (deprecated)

    Example:

    .. literalinclude::
            /../../tests/wrappers/fixtures/ssh-agent-credentials002.yaml


    if both **users** and **user** parameters specified, **users** will be
        prefered, **user** will be ignored.

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
            logger.warn("Both 'users' and 'user' parameters specified for "
                        "ssh-agent-credentials. 'users' is used, 'user' is "
                        "ignored.")
    elif 'user' in data:
        logger.warn("The 'user' param has been deprecated, "
                    "use the 'users' param instead.")
        user_list.append(data['user'])
    else:
        raise JenkinsJobsException("Missing 'user' or 'users' parameter "
                                   "for ssh-agent-credentials")

    for user in user_list:
        XML.SubElement(entry_xml, xml_key).text = user


def credentials_binding(parser, xml_parent, data):
    """yaml: credentials-binding
    Binds credentials to environment variables using the credentials binding
    plugin for jenkins.

    Requires the Jenkins :jenkins-wiki:`Credentials Binding Plugin
    <Credentials+Binding+Plugin>` version 1.1 or greater.

    :arg list binding-type: List of each bindings to create.  Bindings may be
      of type `zip-file`, `file`, `username-password`, `text` or
      `username-password-separated`.
      username-password sets a variable to the username and password given in
      the credentials, separated by a colon.
      username-password-separated sets one variable to the username and one
      variable to the password given in the credentials.

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

    Example:

    .. literalinclude::
            /../../tests/wrappers/fixtures/credentials_binding.yaml
            :language: yaml

    """
    entry_xml = XML.SubElement(
        xml_parent,
        'org.jenkinsci.plugins.credentialsbinding.impl.SecretBuildWrapper')
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
        'text': 'org.jenkinsci.plugins.credentialsbinding.impl.StringBinding'
    }
    if not data:
        raise JenkinsJobsException('At least one binding-type must be '
                                   'specified for the credentials-binding '
                                   'element')
    for binding in data:
        for binding_type, params in binding.items():
            if binding_type not in binding_types.keys():
                raise JenkinsJobsException('binding-type must be one of %r' %
                                           binding_types.keys())

            binding_xml = XML.SubElement(bindings_xml,
                                         binding_types[binding_type])
            if binding_type == 'username-password-separated':
                try:
                    XML.SubElement(binding_xml, 'usernameVariable'
                                   ).text = params['username']
                    XML.SubElement(binding_xml, 'passwordVariable'
                                   ).text = params['password']
                except KeyError as e:
                    raise MissingAttributeError(e.args[0])
            else:
                variable_xml = XML.SubElement(binding_xml, 'variable')
                variable_xml.text = params.get('variable')
            credential_xml = XML.SubElement(binding_xml, 'credentialsId')
            credential_xml.text = params.get('credential-id')


def custom_tools(parser, xml_parent, data):
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
        XML.SubElement(tool_wrapper, 'name').text = str(tool)

    opts = XML.SubElement(wrapper,
                          'multiconfigOptions')
    skip_install = str(data.get('skip-master-install', 'false'))
    XML.SubElement(opts,
                   'skipMasterInstallation').text = skip_install

    convert_home = str(data.get('convert-homes-to-upper', 'false'))
    XML.SubElement(wrapper,
                   'convertHomesToUppercase').text = convert_home


def xvnc(parser, xml_parent, data):
    """yaml: xvnc
    Enable xvnc during the build.
    Requires the Jenkins :jenkins-wiki:`xvnc plugin <Xvnc+Plugin>`.

    :arg bool screenshot: Take screenshot upon build completion
                          (default: false)
    :arg bool xauthority: Create a dedicated Xauthority file per build
                          (default: true)

    Example:

    .. literalinclude:: /../../tests/wrappers/fixtures/xvnc001.yaml

    """
    xwrapper = XML.SubElement(xml_parent,
                              'hudson.plugins.xvnc.Xvnc')
    XML.SubElement(xwrapper, 'takeScreenshot').text = str(
        data.get('screenshot', False)).lower()
    XML.SubElement(xwrapper, 'useXauthority').text = str(
        data.get('xauthority', True)).lower()


def job_log_logger(parser, xml_parent, data):
    """yaml: job-log-logger
    Enable writing the job log to the underlying logging system.
    Requires the Jenkins :jenkins-wiki:`Job Log Logger plugin
    <Job+Log+Logger+Plugin>`.

    :arg bool suppress-empty: Suppress empty log messages
                              (default: true)

    Example:

    .. literalinclude:: /../../tests/wrappers/fixtures/job-log-logger001.yaml

    """
    top = XML.SubElement(xml_parent,
                         'org.jenkins.ci.plugins.jobloglogger.'
                         'JobLogLoggerBuildWrapper')
    XML.SubElement(top, 'suppressEmpty').text = str(
        data.get('suppress-empty', True)).lower()


def xvfb(parser, xml_parent, data):
    """yaml: xvfb
    Enable xvfb during the build.
    Requires the Jenkins :jenkins-wiki:`Xvfb Plugin <Xvfb+Plugin>`.

    :arg str installation-name: The name of the Xvfb tool instalation
                                (default: default)
    :arg bool auto-display-name: Uses the -displayfd option of Xvfb by which it
                                 chooses it's own display name
                                 (default: false)
    :arg str display-name: Ordinal of the display Xvfb will be running on, if
                           left empty choosen based on current build executor
                           number (optional)
    :arg str assigned-labels: If you want to start Xvfb only on specific nodes
                              specify its name or label (optional)
    :arg bool parallel-build: When running multiple Jenkins nodes on the same
                              machine this setting influences the display
                              number generation (default: false)
    :arg int timeout: A timeout of given seconds to wait before returning
                      control to the job (default: 0)
    :arg str screen: Resolution and color depth. (default: 1024x768x24)
    :arg str display-name-offset: Offset for display names. (default: 1)
    :arg str additional-options: Additional options to be added with the
                                 options above to the Xvfb command line
                                 (optional)
    :arg bool debug: If Xvfb output should appear in console log of this job
                     (default: false)
    :arg bool shutdown-with-build: Should the display be kept until the whole
                                   job ends (default: false)

    Example:

    .. literalinclude:: /../../tests/wrappers/fixtures/xvfb001.yaml

    """
    xwrapper = XML.SubElement(xml_parent,
                              'org.jenkinsci.plugins.xvfb.XvfbBuildWrapper')
    XML.SubElement(xwrapper, 'installationName').text = str(data.get(
        'installation-name', 'default'))
    XML.SubElement(xwrapper, 'autoDisplayName').text = str(data.get(
        'auto-display-name', False)).lower()
    if 'display-name' in data:
        XML.SubElement(xwrapper, 'displayName').text = str(data.get(
            'display-name', ''))
    XML.SubElement(xwrapper, 'assignedLabels').text = str(data.get(
        'assigned-labels', ''))
    XML.SubElement(xwrapper, 'parallelBuild').text = str(data.get(
        'parallel-build', False)).lower()
    XML.SubElement(xwrapper, 'timeout').text = str(data.get('timeout', '0'))
    XML.SubElement(xwrapper, 'screen').text = str(data.get(
        'screen', '1024x768x24'))
    XML.SubElement(xwrapper, 'displayNameOffset').text = str(data.get(
        'display-name-offset', '1'))
    XML.SubElement(xwrapper, 'additionalOptions').text = str(data.get(
        'additional-options', ''))
    XML.SubElement(xwrapper, 'debug').text = str(data.get(
        'debug', False)).lower()
    XML.SubElement(xwrapper, 'shutdownWithBuild').text = str(data.get(
        'shutdown-with-build', False)).lower()


class Wrappers(jenkins_jobs.modules.base.Base):
    sequence = 80

    component_type = 'wrapper'
    component_list_type = 'wrappers'

    def gen_xml(self, parser, xml_parent, data):
        wrappers = XML.SubElement(xml_parent, 'buildWrappers')

        for wrap in data.get('wrappers', []):
            self.registry.dispatch('wrapper', parser, wrappers, wrap)
