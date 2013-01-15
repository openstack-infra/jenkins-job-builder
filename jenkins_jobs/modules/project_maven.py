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
The Maven Project module handles creating Maven Jenkins projects.  To
create a Maven project, specify ``maven`` in the ``project-type``
attribute to the :ref:`Job` definition.

It also requires a ``maven`` section in the :ref:`Job` definition.
All of the fields below are required, except ``root-pom``, whose
default is ``pom.xml``, and ``maven-name`` which will default to being
unset. Not setting ``maven-name`` appears to use the first maven
install defined in the global jenkins config.

Example::

  job:
    name: doc_job
    project-type: maven

    maven:
      root-module:
        group-id: org.example.docs
        artifact-id: example-guide
      root-pom: doc/src/pom.xml
      goals: "clean generate-sources"
      maven-name: Maven3
"""

import xml.etree.ElementTree as XML
import jenkins_jobs.modules.base


class Maven(jenkins_jobs.modules.base.Base):
    sequence = 0

    def root_xml(self, data):
        if 'maven' not in data:
            return None
        xml_parent = XML.Element('maven2-moduleset')
        root_module = XML.SubElement(xml_parent, 'root_module')
        XML.SubElement(root_module, 'groupId').text = \
            data['maven']['root-module']['group-id']
        XML.SubElement(root_module, 'artifactId').text = \
            data['maven']['root-module']['artifact-id']
        XML.SubElement(xml_parent, 'goals').text = data['maven']['goals']

        maven_name = data['maven'].get('maven-name')
        if maven_name:
            XML.SubElement(xml_parent, 'mavenName').text = maven_name

        XML.SubElement(xml_parent, 'rootPOM').text = \
            data['maven'].get('root-pom', 'pom.xml')
        XML.SubElement(xml_parent, 'aggregatorStyleBuild').text = 'true'
        XML.SubElement(xml_parent, 'incrementalBuild').text = 'false'
        XML.SubElement(xml_parent, 'perModuleEmail').text = 'true'
        XML.SubElement(xml_parent, 'ignoreUpstremChanges').text = 'true'
        XML.SubElement(xml_parent, 'archivingDisabled').text = 'false'
        XML.SubElement(xml_parent, 'resolveDependencies').text = 'false'
        XML.SubElement(xml_parent, 'processPlugins').text = 'false'
        XML.SubElement(xml_parent, 'mavenValidationLevel').text = '-1'
        XML.SubElement(xml_parent, 'runHeadless').text = 'false'
        XML.SubElement(xml_parent, 'settingConfigId')
        XML.SubElement(xml_parent, 'globalSettingConfigId')

        run_post_steps = XML.SubElement(xml_parent, 'runPostStepsIfResult')
        XML.SubElement(run_post_steps, 'name').text = 'FAILURE'
        XML.SubElement(run_post_steps, 'ordinal').text = '2'
        XML.SubElement(run_post_steps, 'color').text = 'red'

        return xml_parent
