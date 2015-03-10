# -*- coding: utf-8 -*-
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
The flow Project module handles creating Jenkins flow projects.
You may specify ``flow`` in the ``project-type`` attribute of
the :ref:`Job` definition.

Requires the Jenkins :jenkins-wiki:`Build Flow Plugin <Build+Flow+Plugin>`.

In order to use it for job-template you have to escape the curly braces by
doubling them in the DSL: { -> {{ , otherwise it will be interpreted by the
python str.format() command.

:Job Parameters:
    * **dsl** (`str`): The DSL content. (optional)
    * **needs-workspace** (`bool`): This build needs a workspace. \
    (default false)
    * **dsl-file** (`str`): Path to the DSL script in the workspace. \
    Has effect only when `needs-workspace` is true. (optional)

Job example:

    .. literalinclude::
      /../../tests/yamlparser/fixtures/project_flow_template001.yaml

Job template example:

    .. literalinclude::
      /../../tests/yamlparser/fixtures/project_flow_template002.yaml

Job example runninng a DSL file from the workspace:

    .. literalinclude::
      /../../tests/yamlparser/fixtures/project_flow_template003.yaml

"""

import xml.etree.ElementTree as XML
import jenkins_jobs.modules.base


class Flow(jenkins_jobs.modules.base.Base):
    sequence = 0

    def root_xml(self, data):
        xml_parent = XML.Element('com.cloudbees.plugins.flow.BuildFlow')
        if 'dsl' in data:
            XML.SubElement(xml_parent, 'dsl').text = data['dsl']
        else:
            XML.SubElement(xml_parent, 'dsl').text = ''

        needs_workspace = data.get('needs-workspace', False)
        XML.SubElement(xml_parent, 'buildNeedsWorkspace').text = str(
            needs_workspace).lower()

        if needs_workspace and 'dsl-file' in data:
            XML.SubElement(xml_parent, 'dslFile').text = data['dsl-file']

        return xml_parent
