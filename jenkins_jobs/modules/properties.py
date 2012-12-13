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
The Properties module supplies a wide range of options that are
implemented as Jenkins job properties.

**Component**: properties
  :Macro: property
  :Entry Point: jenkins_jobs.properties

Example::

  job:
    name: test_job

    properties:
      - github:
          url: https://github.com/openstack-ci/jenkins-job-builder/
"""


import xml.etree.ElementTree as XML
import jenkins_jobs.modules.base


def github(parser, xml_parent, data):
    """yaml: github
    Sets the GitHub URL for the project.

    :arg str url: the GitHub URL

    Example::

      properties:
        - github:
            url: https://github.com/openstack-ci/jenkins-job-builder/
    """
    github = XML.SubElement(xml_parent,
                            'com.coravy.hudson.plugins.github.'
                            'GithubProjectProperty')
    github_url = XML.SubElement(github, 'projectUrl')
    github_url.text = data['url']


def throttle(parser, xml_parent, data):
    """yaml: throttle
    Throttles the number of builds for this job.
    Requires the Jenkins `Throttle Concurrent Builds Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/
    Throttle+Concurrent+Builds+Plugin>`_

    :arg int max-per-node: max concurrent builds per node (default 0)
    :arg int max-total: max concurrent builds (default 0)
    :arg bool enabled: whether throttling is enabled (default True)
    :arg str option: throttle `project` or `category`
    :arg list categories: multiproject throttle categories

    Example::

      properties:
        - throttle:
            max-total: 4
            categories:
              - cat1
              - cat2

    """
    throttle = XML.SubElement(xml_parent,
                              'hudson.plugins.throttleconcurrents.'
                              'ThrottleJobProperty')
    XML.SubElement(throttle, 'maxConcurrentPerNode').text = str(
        data.get('max-per-node', '0'))
    XML.SubElement(throttle, 'maxConcurrentTotal').text = str(
        data.get('max-total', '0'))
    # TODO: What's "categories"?
    #XML.SubElement(throttle, 'categories')
    if data.get('enabled', True):
        XML.SubElement(throttle, 'throttleEnabled').text = 'true'
    else:
        XML.SubElement(throttle, 'throttleEnabled').text = 'false'
    cat = data.get('categories', [])
    if cat:
        cn = XML.SubElement(throttle, 'categories')
        for c in cat:
            XML.SubElement(cn, 'string').text = str(c)

    XML.SubElement(throttle, 'throttleOption').text = data.get('option')
    XML.SubElement(throttle, 'configVersion').text = '1'


def inject(parser, xml_parent, data):
    """yaml: inject
    Allows you to inject evironment variables into the build.
    Requires the Jenkins `Env Inject Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/EnvInject+Plugin>`_

    :arg str properties-file: file to read with properties (optional)
    :arg str properties-content: key=value properties (optional)
    :arg str script-file: file with script to run (optional)
    :arg str script-content: script to run (optional)
    :arg str groovy-content: groovy script to run (optional)
    :arg bool load-from-master: load files from master (default false)
    :arg bool enabled: injection enabled (default true)
    :arg bool keep-system-variables: keep system variables (default true)
    :arg bool keep-build-variables: keep build variable (default true)

    Example::

      properties:
        - inject:
            properties-content: FOO=bar
    """
    inject = XML.SubElement(xml_parent,
                            'EnvInjectJobProperty')
    info = XML.SubElement(inject, 'info')
    XML.SubElement(info, 'propertiesFilePath').text = str(
        data.get('properties-file', ''))
    XML.SubElement(info, 'propertiesContent').text = str(
        data.get('properties-content', ''))
    XML.SubElement(info, 'scriptFilePath').text = str(
        data.get('script-file', ''))
    XML.SubElement(info, 'scriptContent').text = str(
        data.get('script-content', ''))
    XML.SubElement(info, 'groovyScriptContent').text = str(
        data.get('groovy-content', ''))
    XML.SubElement(info, 'loadFilesFromMaster').text = str(
        data.get('load-from-master', 'false')).lower()
    XML.SubElement(inject, 'on').text = str(
        data.get('enabled', 'true')).lower()
    XML.SubElement(inject, 'keepJenkinsSystemVariables').text = str(
        data.get('keep-system-variables', 'true')).lower()
    XML.SubElement(inject, 'keepBuildVariables').text = str(
        data.get('keep-build-variables', 'true')).lower()


def authenticated_build(parser, xml_parent, data):
    """yaml: authenticated-build
    Specifies an authorization matrix where only authenticated users
    may trigger a build.

    DEPRECATED

    Example::

      properties:
        - authenticated-build
    """
    # TODO: generalize this
    if data:
        security = XML.SubElement(xml_parent,
                                  'hudson.security.'
                                  'AuthorizationMatrixProperty')
        XML.SubElement(security, 'permission').text = \
            'hudson.model.Item.Build:authenticated'


def authorization(parser, xml_parent, data):
    """yaml: authorization
    Specifies an authorization matrix

    The available rights are:
      job-delete
      job-configure
      job-read
      job-discover
      job-build
      job-workspace
      job-cancel
      run-delete
      run-update
      scm-tag

    Example::

      properties:
        - authorization:
            admin:
              - job-delete
              - job-configure
              - job-read
              - job-discover
              - job-build
              - job-workspace
              - job-cancel
              - run-delete
              - run-update
              - scm-tag
            anonymous:
              - job-discover
              - job-read
    """

    mapping = {
        'job-delete': 'hudson.model.Item.Delete',
        'job-configure': 'hudson.model.Item.Configure',
        'job-read': 'hudson.model.Item.Read',
        'job-discover': 'hudson.model.Item.Discover',
        'job-build': 'hudson.model.Item.Build',
        'job-workspace': 'hudson.model.Item.Workspace',
        'job-cancel': 'hudson.model.Item.Cancel',
        'run-delete': 'hudson.model.Run.Delete',
        'run-update': 'hudson.model.Run.Update',
        'scm-tag': 'hudson.scm.SCM.Tag'
    }

    if data:
        matrix = XML.SubElement(xml_parent,
                                'hudson.security.AuthorizationMatrixProperty')
        for (username, perms) in data.items():
            for perm in perms:
                pe = XML.SubElement(matrix, 'permission')
                pe.text = "{0}:{1}".format(mapping[perm], username)


class Properties(jenkins_jobs.modules.base.Base):
    sequence = 20

    def gen_xml(self, parser, xml_parent, data):
        properties = xml_parent.find('properties')
        if properties is None:
            properties = XML.SubElement(xml_parent, 'properties')

        for prop in data.get('properties', []):
            self._dispatch('property', 'properties',
                           parser, properties, prop)
