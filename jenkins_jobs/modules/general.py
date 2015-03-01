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


"""These are job parameters that are common to every type of Jenkins job.

Example:

.. literalinclude::  /../../tests/yamlparser/fixtures/general-example-001.yaml

:Job Parameters:
    * **project-type**:
      Defaults to "freestyle", but "maven" as well as "multijob" or "flow"
      can also be specified.

    * **defaults**:
      Specifies a set of :ref:`defaults` to use for this job, defaults to
      ''global''.  If you have values that are common to all of your jobs,
      create a ``global`` :ref:`defaults` object to hold them, and no further
      configuration of individual jobs is necessary.  If some jobs
      should not use the ``global`` defaults, use this field to specify a
      different set of defaults.

    * **description**:
      The description for the job.  By default, the description
      "!-- Managed by Jenkins Job Builder" is applied.

    * **disabled**:
      Boolean value to set whether or not this job should be disabled in
      Jenkins. Defaults to ``false`` (job will be enabled).

    * **display-name**:
      Optional name shown for the project throughout the Jenkins web GUI in
      place of the actual job name.  The jenkins_jobs tool cannot fully remove
      this trait once it is set, so use caution when setting it.  Setting it to
      the same string as the job's name is an effective un-set workaround.
      Alternately, the field can be cleared manually using the Jenkins web
      interface.

    * **concurrent**:
      Boolean value to set whether or not Jenkins can run this job
      concurrently. Defaults to ``false``.

    * **workspace**:
      Path for a custom workspace. Defaults to Jenkins default
      configuration.

    * **quiet-period**:
      Number of seconds to wait between consecutive runs of this job.
      Defaults to ``0``.

    * **block-downstream**:
      Boolean value to set whether or not this job must block while
      downstream jobs are running. Downstream jobs are determined
      transitively. Defaults to ``false``.

    * **block-upstream**:
      Boolean value to set whether or not this job must block while
      upstream jobs are running. Upstream jobs are determined
      transitively. Defaults to ``false``.

    * **auth-token**:
      Specifies an authentication token that allows new builds to be
      triggered by accessing a special predefined URL. Only those who
      know the token will be able to trigger builds remotely.

    * **retry-count**:
      If a build fails to checkout from the repository, Jenkins will
      retry the specified number of times before giving up.

    * **node**:
      Restrict where this job can be run. If there is a group of
      machines that the job can be built on, you can specify that
      label as the node to tie on, which will cause Jenkins to build the job on
      any of the machines with that label. For matrix projects, this parameter
      will only restrict where the parent job will run.

    * **logrotate**:
      The Logrotate section allows you to automatically remove old build
      history. It adds the ``logrotate`` attribute to the :ref:`Job`
      definition. All logrotate attributes default to "-1" (keep forever).

"""

import xml.etree.ElementTree as XML
import jenkins_jobs.modules.base


class General(jenkins_jobs.modules.base.Base):
    sequence = 10

    def gen_xml(self, parser, xml, data):
        jdk = data.get('jdk', None)
        if jdk:
            XML.SubElement(xml, 'jdk').text = jdk
        XML.SubElement(xml, 'actions')
        desc_text = data.get('description', None)
        if desc_text is not None:
            description = XML.SubElement(xml, 'description')
            description.text = desc_text
        XML.SubElement(xml, 'keepDependencies').text = 'false'
        disabled = data.get('disabled', None)
        if disabled is not None:
            if disabled:
                XML.SubElement(xml, 'disabled').text = 'true'
            else:
                XML.SubElement(xml, 'disabled').text = 'false'
        if 'display-name' in data:
            XML.SubElement(xml, 'displayName').text = data['display-name']
        if data.get('block-downstream'):
            XML.SubElement(xml,
                           'blockBuildWhenDownstreamBuilding').text = 'true'
        else:
            XML.SubElement(xml,
                           'blockBuildWhenDownstreamBuilding').text = 'false'
        if data.get('block-upstream'):
            XML.SubElement(xml,
                           'blockBuildWhenUpstreamBuilding').text = 'true'
        else:
            XML.SubElement(xml,
                           'blockBuildWhenUpstreamBuilding').text = 'false'
        if 'auth-token' in data:
            XML.SubElement(xml, 'authToken').text = data['auth-token']
        if data.get('concurrent'):
            XML.SubElement(xml, 'concurrentBuild').text = 'true'
        else:
            XML.SubElement(xml, 'concurrentBuild').text = 'false'
        if 'workspace' in data:
            XML.SubElement(xml, 'customWorkspace').text = \
                str(data['workspace'])
        if 'quiet-period' in data:
            XML.SubElement(xml, 'quietPeriod').text = str(data['quiet-period'])
        node = data.get('node', None)
        if node:
            XML.SubElement(xml, 'assignedNode').text = node
            XML.SubElement(xml, 'canRoam').text = 'false'
        else:
            XML.SubElement(xml, 'canRoam').text = 'true'
        if 'retry-count' in data:
            XML.SubElement(xml, 'scmCheckoutRetryCount').text = \
                str(data['retry-count'])

        if 'logrotate' in data:
            lr_xml = XML.SubElement(xml, 'logRotator')
            logrotate = data['logrotate']
            lr_days = XML.SubElement(lr_xml, 'daysToKeep')
            lr_days.text = str(logrotate.get('daysToKeep', -1))
            lr_num = XML.SubElement(lr_xml, 'numToKeep')
            lr_num.text = str(logrotate.get('numToKeep', -1))
            lr_adays = XML.SubElement(lr_xml, 'artifactDaysToKeep')
            lr_adays.text = str(logrotate.get('artifactDaysToKeep', -1))
            lr_anum = XML.SubElement(lr_xml, 'artifactNumToKeep')
            lr_anum.text = str(logrotate.get('artifactNumToKeep', -1))


def raw(parser, xml_parent, data):
    # documented in definition.rst since includes and docs is not working well
    # For cross cutting method like this
    root = XML.fromstring(data.get('xml'))
    xml_parent.append(root)
