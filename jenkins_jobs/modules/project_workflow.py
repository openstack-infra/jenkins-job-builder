# -*- coding: utf-8 -*-
# Copyright (C) 2015 David Caro <david@dcaro.es>
#
# Based on jenkins_jobs/modules/project_flow.py by
# Copyright (C) 2013 eNovance SAS <licensing@enovance.com>
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
The workflow Project module handles creating Jenkins workflow projects.
You may specify ``workflow`` in the ``project-type`` attribute of
the :ref:`Job` definition.
For now only inline scripts are supported.

Requires the Jenkins :jenkins-wiki:`Workflow Plugin <Workflow+Plugin>`.

In order to use it for job-template you have to escape the curly braces by
doubling them in the DSL: { -> {{ , otherwise it will be interpreted by the
python str.format() command.

:Job Parameters:
    * **dsl** (`str`): The DSL content.
    * **sandbox** (`bool`): If the script should run in a sandbox (default
      false)

Job example:

    .. literalinclude::
      /../../tests/yamlparser/fixtures/project_workflow_template001.yaml

Job template example:

    .. literalinclude::
      /../../tests/yamlparser/fixtures/project_workflow_template002.yaml

"""
import xml.etree.ElementTree as XML

from jenkins_jobs.errors import MissingAttributeError
import jenkins_jobs.modules.base


class Workflow(jenkins_jobs.modules.base.Base):
    sequence = 0

    def root_xml(self, data):
        xml_parent = XML.Element('flow-definition',
                                 {'plugin': 'workflow-job'})
        xml_definition = XML.SubElement(xml_parent, 'definition',
                                        {'plugin': 'workflow-cps',
                                         'class': 'org.jenkinsci.plugins.'
                                         'workflow.cps.CpsFlowDefinition'})
        try:
            XML.SubElement(xml_definition, 'script').text = data['dsl']
        except KeyError as e:
            raise MissingAttributeError(e.arg[0])

        needs_workspace = data.get('sandbox', False)
        XML.SubElement(xml_definition, 'sandbox').text = str(
            needs_workspace).lower()

        return xml_parent
