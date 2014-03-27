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
The Logrotate section allows you to automatically remove old build
history. It adds the ``logrotate`` attribute to the :ref:`Job`
definition.
All logrotate attributes have default "-1" value so you don't need to specify
that explicitly

Example::

  - job:
      name: test_job
      logrotate:
        daysToKeep: 3
        numToKeep: 20
        artifactDaysToKeep: -1
        artifactNumToKeep: -1

The Assigned Node section allows you to specify which Jenkins node (or
named group) should run the specified job. It adds the ``node``
attribute to the :ref:`Job` definition.

Example::

  - job:
      name: test_job
      node: precise

That speficies that the job should be run on a Jenkins node or node group
named ``precise``.
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
