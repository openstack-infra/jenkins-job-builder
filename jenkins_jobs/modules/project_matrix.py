# Copyright 2012 Julian Taylor <jtaylor.debian@googlemail.com>
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
The matrix project module handles creating Jenkins matrix
projects. To create a matrix project specify ``matrix`` in the
``project-type`` attribute to the :ref:`Job` definition.
Currently it supports four axes which share the same
internal YAML structure:

* label expressions (``label-expression``)
* user-defined values (``user-defined``)
* slave name or label (``slave``)
* JDK name (``jdk``)

Requires the Jenkins :jenkins-wiki:`Matrix Project Plugin
<Matrix+Project+Plugin>`.

The module supports also dynamic axis:

* dynamic (``dynamic``)

Requires the Jenkins :jenkins-wiki:`dynamic axis Plugin <DynamicAxis+Plugin>`.

To tie the parent job to a specific node, you should use ``node`` parameter.
On a matrix project, this will tie *only* the parent job.  To restrict axes
jobs, you can define a single value ``slave`` axis.

:Job Parameters:
    * **execution-strategy** (optional):
        * **combination-filter** (`str`): axes selection filter
        * **sequential** (`bool`): run builds sequentially (default false)
        * **touchstone** (optional):
            * **expr** (`str`) -- selection filter for the touchstone build
            * **result** (`str`) -- required result of the job: \
            stable (default) or unstable
    * **axes** (`list`):
        * **axis**:
            * **type** (`str`) -- axis type, must be either
              'label-expression', 'user-defined', 'slave' or 'jdk'.
            * **name** (`str`) -- name of the axis
            * **values** (`list`) -- values of the axis

The module supports also ShiningPanda axes:

Example:

.. literalinclude::  /../../tests/general/fixtures/matrix-axis003.yaml

Requires the Jenkins :jenkins-wiki:`ShiningPanda Plugin <ShiningPanda+Plugin>`.

Example:

  .. literalinclude::  /../../tests/yamlparser/fixtures/project-matrix001.yaml
    :language: yaml

"""


import xml.etree.ElementTree as XML
import jenkins_jobs.modules.base


class Matrix(jenkins_jobs.modules.base.Base):
    sequence = 0
    # List the supported Axis names in our configuration
    # and map them to the Jenkins XML element name.
    supported_axis = {
        'label-expression': 'hudson.matrix.LabelExpAxis',
        'user-defined': 'hudson.matrix.TextAxis',
        'slave': 'hudson.matrix.LabelAxis',
        'jdk': 'hudson.matrix.JDKAxis',
        'dynamic': 'ca.silvermaplesolutions.jenkins.plugins.daxis.DynamicAxis',
        'python': 'jenkins.plugins.shiningpanda.matrix.PythonAxis',
        'tox': 'jenkins.plugins.shiningpanda.matrix.ToxAxis',
    }

    def root_xml(self, data):
        root = XML.Element('matrix-project')

        ex_r = XML.SubElement(root, 'executionStrategy',
                              {'class': 'hudson.matrix.'
                               'DefaultMatrixExecutionStrategyImpl'})
        ex_d = data.get('execution-strategy', {})
        XML.SubElement(root, 'combinationFilter').text = \
            str(ex_d.get('combination-filter', '')).rstrip()
        XML.SubElement(ex_r, 'runSequentially').text = \
            str(ex_d.get('sequential', False)).lower()
        if 'touchstone' in ex_d:
            XML.SubElement(ex_r, 'touchStoneCombinationFilter').text = \
                str(ex_d['touchstone'].get('expr', ''))
            t_r = XML.SubElement(ex_r, 'touchStoneResultCondition')
            n = ex_d['touchstone'].get('result', 'stable').upper()
            if n not in ('STABLE', 'UNSTABLE'):
                raise ValueError('Required result must be stable or unstable')

            XML.SubElement(t_r, 'name').text = n
            if n == "STABLE":
                XML.SubElement(t_r, 'ordinal').text = '0'
                XML.SubElement(t_r, 'color').text = 'BLUE'
            else:
                XML.SubElement(t_r, 'ordinal').text = '1'
                XML.SubElement(t_r, 'color').text = 'YELLOW'

        ax_root = XML.SubElement(root, 'axes')
        for axis_ in data.get('axes', []):
            axis = axis_['axis']
            axis_type = axis['type']
            if axis_type not in self.supported_axis:
                raise ValueError('Only %s axes types are supported'
                                 % self.supported_axis.keys())
            axis_name = self.supported_axis.get(axis_type)
            lbl_root = XML.SubElement(ax_root, axis_name)
            name, values = axis.get('name', ''), axis.get('values', [''])
            if axis_type == 'jdk':
                XML.SubElement(lbl_root, 'name').text = 'jdk'
            elif axis_type == 'python':
                XML.SubElement(lbl_root, 'name').text = 'PYTHON'
            elif axis_type == 'tox':
                XML.SubElement(lbl_root, 'name').text = 'TOXENV'
            else:
                XML.SubElement(lbl_root, 'name').text = str(name)
            v_root = XML.SubElement(lbl_root, 'values')
            if axis_type == "dynamic":
                XML.SubElement(v_root, 'string').text = str(values[0])
                XML.SubElement(lbl_root, 'varName').text = str(values[0])
                v_root = XML.SubElement(lbl_root, 'axisValues')
                XML.SubElement(v_root, 'string').text = 'default'
            else:
                for v in values:
                    XML.SubElement(v_root, 'string').text = str(v)

        return root
