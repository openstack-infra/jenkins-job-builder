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

Example::

  job:
    name: test_job

    wrappers:
      - timeout:
          timeout: 90
          fail: true
"""

import xml.etree.ElementTree as XML
import jenkins_jobs.modules.base


def timeout(parser, xml_parent, data):
    """yaml: timeout
    Abort the build if it runs too long.
    Requires the Jenkins `Build Timeout Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/Build-timeout+Plugin>`_

    :arg int timeout: Abort the build after this number of minutes
    :arg bool fail: Mark the build as failed (default false)

    Example::

      wrappers:
        - timeout:
            timeout: 90
            fail: true
    """
    twrapper = XML.SubElement(xml_parent,
        'hudson.plugins.build__timeout.BuildTimeoutWrapper')
    tminutes = XML.SubElement(twrapper, 'timeoutMinutes')
    tminutes.text = str(data['timeout'])
    failbuild = XML.SubElement(twrapper, 'failBuild')
    fail = data.get('fail', False)
    if fail:
        failbuild.text = 'true'
    else:
        failbuild.text = 'false'


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

    Example::

      wrappers:
        - ansicolor
    """
    XML.SubElement(xml_parent,
                   'hudson.plugins.ansicolor.AnsiColorBuildWrapper')


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
     'com.michelin.cio.hudson.plugins.maskpasswords.MaskPasswordsBuildWrapper')


def workspace_cleanup(parser, xml_parent, data):
    """yaml: workspace-cleanup

    See `Workspace Cleanup Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/Workspace+Cleanup+Plugin>`_

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
    p.set("plugin", "ws-cleanup@0.10")
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
    deldirs.text = str(data.get("dirmatch", "false")).lower()


def build_name(parser, xml_parent, data):
    """yaml: build-name
    Set the name of the build
    Requires the Jenkins `Build Name Setter Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/Build+Name+Setter+Plugin>`_

    :arg str name: Name for the build.  Typically you would use a variable
    from Jenkins in the name.  The syntax would be ${FOO} for the FOO variable.

    Example::

      wrappers:
        - build-name:
            name: Build-${FOO}
    """
    bsetter = XML.SubElement(xml_parent,
               'org.jenkinsci.plugins.buildnamesetter.BuildNameSetter')
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
            'org.jvnet.hudson.plugins.port__allocator.PortAllocator')
    ports = XML.SubElement(pa, 'ports')
    dpt = XML.SubElement(ports,
             'org.jvnet.hudson.plugins.port__allocator.DefaultPortType')
    XML.SubElement(dpt, 'name').text = data['name']


class Wrappers(jenkins_jobs.modules.base.Base):
    sequence = 80

    def gen_xml(self, parser, xml_parent, data):
        wrappers = XML.SubElement(xml_parent, 'buildWrappers')

        for wrap in data.get('wrappers', []):
            self._dispatch('wrapper', 'wrappers',
                           parser, wrappers, wrap)
