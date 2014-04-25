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

import xml.etree.ElementTree as XML
import jenkins_jobs.modules.base
from jenkins_jobs.modules.builders import create_builders


def ci_skip(parser, xml_parent, data):
    """yaml: ci-skip
    Skip making a build for certain push.
    Just add [ci skip] into your commit's message to let Jenkins know,
    that you do not want to perform build for the next push.
    Requires the Jenkins `Ci Skip Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/Ci+Skip+Plugin>`_

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


def timeout(parser, xml_parent, data):
    """yaml: timeout
    Abort the build if it runs too long.
    Requires the Jenkins `Build Timeout Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/Build-timeout+Plugin>`_

    :arg bool fail: Mark the build as failed (default false)
    :arg bool write-description: Write a message in the description
        (default false)
    :arg int timeout: Abort the build after this number of minutes (default 3)
    :arg str timeout-var: Export an environment variable to reference the
        timeout value (optional)
    :arg str type: Timeout type to use (default absolute)
    :arg int elastic-percentage: Percentage of the three most recent builds
        where to declare a timeout (default 0)
    :arg int elastic-default-timeout: Timeout to use if there were no previous
        builds (default 3)

    :type values:
     * **likely-stuck**
     * **elastic**
     * **absolute**

    Example:

    .. literalinclude:: /../../tests/wrappers/fixtures/timeout001.yaml

    .. literalinclude:: /../../tests/wrappers/fixtures/timeout002.yaml

    .. literalinclude:: /../../tests/wrappers/fixtures/timeout003.yaml
    """
    twrapper = XML.SubElement(xml_parent,
                              'hudson.plugins.build__timeout.'
                              'BuildTimeoutWrapper')
    XML.SubElement(twrapper, 'timeoutMinutes').text = str(
        data.get('timeout', 3))
    timeout_env_var = data.get('timeout-var')
    if timeout_env_var:
        XML.SubElement(twrapper, 'timeoutEnvVar').text = str(timeout_env_var)
    XML.SubElement(twrapper, 'failBuild').text = str(
        data.get('fail', 'false')).lower()
    XML.SubElement(twrapper, 'writingDescription').text = str(
        data.get('write-description', 'false')).lower()
    XML.SubElement(twrapper, 'timeoutPercentage').text = str(
        data.get('elastic-percentage', 0))
    XML.SubElement(twrapper, 'timeoutMinutesElasticDefault').text = str(
        data.get('elastic-default-timeout', 3))
    tout_type = str(data.get('type', 'absolute')).lower()
    if tout_type == 'likely-stuck':
        tout_type = 'likelyStuck'
    XML.SubElement(twrapper, 'timeoutType').text = tout_type


def timestamps(parser, xml_parent, data):
    """yaml: timestamps
    Add timestamps to the console log.
    Requires the Jenkins `Timestamper Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/Timestamper>`_

    Example::

      wrappers:
        - timestamps
    """
    XML.SubElement(xml_parent,
                   'hudson.plugins.timestamper.TimestamperBuildWrapper')


def ansicolor(parser, xml_parent, data):
    """yaml: ansicolor
    Translate ANSI color codes to HTML in the console log.
    Requires the Jenkins `Ansi Color Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/AnsiColor+Plugin>`_

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


def mask_passwords(parser, xml_parent, data):
    """yaml: mask-passwords
    Hide passwords in the console log.
    Requires the Jenkins `Mask Passwords Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/Mask+Passwords+Plugin>`_

    Example::

      wrappers:
        - mask-passwords
    """
    XML.SubElement(xml_parent,
                   'com.michelin.cio.hudson.plugins.maskpasswords.'
                   'MaskPasswordsBuildWrapper')


def workspace_cleanup(parser, xml_parent, data):
    """yaml: workspace-cleanup (pre-build)

    Requires the Jenkins `Workspace Cleanup Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/Workspace+Cleanup+Plugin>`_

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


def rvm_env(parser, xml_parent, data):
    """yaml: rvm-env
    Set the RVM implementation
    Requires the Jenkins `Rvm Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/RVM+Plugin>`_

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
    Requires the Jenkins `rbenv plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/rbenv+plugin>`_

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
    Requires the Jenkins `Build Name Setter Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/Build+Name+Setter+Plugin>`_

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
    Requires the Jenkins `Port Allocator Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/Port+Allocator+Plugin>`_

    :arg str name: Variable name of the port or a specific port number

    Example::

      wrappers:
        - port-allocator:
            name: SERVER_PORT
    """
    pa = XML.SubElement(xml_parent,
                        'org.jvnet.hudson.plugins.port__allocator.'
                        'PortAllocator')
    ports = XML.SubElement(pa, 'ports')
    dpt = XML.SubElement(ports,
                         'org.jvnet.hudson.plugins.port__allocator.'
                         'DefaultPortType')
    XML.SubElement(dpt, 'name').text = data['name']


def locks(parser, xml_parent, data):
    """yaml: locks
    Control parallel execution of jobs.
    Requires the Jenkins `Locks and Latches Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/Locks+and+Latches+plugin>`_

    :arg: list of locks to use

    Example::

      wrappers:
        - locks:
            - FOO
            - FOO2
    """
    lw = XML.SubElement(xml_parent,
                        'hudson.plugins.locksandlatches.LockWrapper')
    locktop = XML.SubElement(lw, 'locks')
    locks = data
    for lock in locks:
        lockwrapper = XML.SubElement(locktop,
                                     'hudson.plugins.locksandlatches.'
                                     'LockWrapper_-LockWaitConfig')
        XML.SubElement(lockwrapper, 'name').text = lock


def copy_to_slave(parser, xml_parent, data):
    """yaml: copy-to-slave
    Copy files to slave before build
    Requires the Jenkins `Copy To Slave Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/Copy+To+Slave+Plugin>`_

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
    Requires the Jenkins `EnvInject Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/EnvInject+Plugin>`_

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


def inject_passwords(parser, xml_parent, data):
    """yaml: inject-passwords
    Inject passwords to the build as environment variables.
    Requires the Jenkins `EnvInject Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/EnvInject+Plugin>`_

    :arg bool global: inject global passwords to the job
    :arg list job-passwords: key value pair of job passwords

        :Parameter: * **name** (`str`) Name of password
                    * **password** (`str`) Encrypted password

    Example::

      wrappers:
        - inject-passwords:
            global: true
            job-passwords:
              - name: ADMIN
                password: 0v8ZCNaHwq1hcx+sHwRLdg9424uBh4Pin0zO4sBIb+U=
    """
    eib = XML.SubElement(xml_parent, 'EnvInjectPasswordWrapper')
    XML.SubElement(eib, 'injectGlobalPasswords').text = \
        str(data.get('global', False)).lower()
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
    Requires the Jenkins `Environment File Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/Envfile+Plugin>`_

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


def jclouds(parser, xml_parent, data):
    """yaml: jclouds
    Uses JClouds to provide slave launching on most of the currently
    usable Cloud infrastructures.
    Requires the Jenkins `JClouds Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/JClouds+Plugin>`_

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
    Requires the Jenkins `Build User Vars Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/Build+User+Vars+Plugin>`_

    Example::

      wrappers:
        - build-user-vars
    """
    XML.SubElement(xml_parent, 'org.jenkinsci.plugins.builduser.BuildUser')


def release(parser, xml_parent, data):
    """yaml: release
    Add release build configuration
    Requires the Jenkins `Release Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/Release+Plugin>`_

    :arg bool keep-forever: Keep build forever (default is 'true')
    :arg bool override-build-parameters: Enable build-parameter override
    :arg string version-template: Release version template
    :arg list parameters: Release parameters (see the :ref:`Parameters` module)
    :arg list pre-build: Pre-build steps (see the :ref:`Builders` module)
    :arg list post-build: Post-build steps (see :ref:`Builders`)
    :arg list post-success: Post successful-build steps (see :ref:`Builders`)
    :arg list post-failed: Post failed-build steps (see :ref:`Builders`)

    Example::

      wrappers:
        - release:
            keep-forever: false
            parameters:
                - string:
                    name: RELEASE_BRANCH
                    default: ''
                    description: Git branch to release from.
            post-success:
                - shell: |
                    #!/bin/bash
                    copy_build_artefacts.sh

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
    for param in data.get('parameters', []):
        parser.registry.dispatch('parameter', parser,
                                 XML.SubElement(relwrap,
                                                'parameterDefinitions'),
                                 param)

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
    the Sauce OnDemand results videos per test.  Requires the Jenkins `Sauce
    OnDemand Plugin
    <https://wiki.jenkins-ci.org/display/JENKINS/Sauce+OnDemand+Plugin>`_.

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

    Requires the Jenkins `Pathignore Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/Pathignore+Plugin>`_

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
    Requires the Jenkins `pre-scm-buildstep.
    <https://wiki.jenkins-ci.org/display/JENKINS/pre-scm-buildstep>`_

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
    Requires the Jenkins `logstash plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/Logstash+Plugin>`_

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


def delivery_pipeline(parser, xml_parent, data):
    """yaml: delivery-pipeline
    If enabled the job will create a version based on the template.
    The version will be set to the environment variable PIPELINE_VERSION and
    will also be set in the downstream jobs.

    Requires the Jenkins `Delivery Pipeline Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/Delivery+Pipeline+Plugin>`_

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
    Requires the Jenkins `Matrix Tie Parent Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/Matrix+Tie+Parent+Plugin>`_
    Note that from Jenkins version 1.532 this plugin's functionality is
    available under the "advanced" option of the matrix project configuration.

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

    Requires the Jenkins `Exclusion Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/Exclusion-Plugin>`_

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


class Wrappers(jenkins_jobs.modules.base.Base):
    sequence = 80

    component_type = 'wrapper'
    component_list_type = 'wrappers'

    def gen_xml(self, parser, xml_parent, data):
        wrappers = XML.SubElement(xml_parent, 'buildWrappers')

        for wrap in data.get('wrappers', []):
            self.registry.dispatch('wrapper', parser, wrappers, wrap)
