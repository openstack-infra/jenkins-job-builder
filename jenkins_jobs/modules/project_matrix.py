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
Currently it only supports label expression axes.

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
            * **type** (`str`) -- axis type, must be 'label-expression'
            * **name** (`str`) -- name of the axis
            * **values** (`list`) -- values of the axis

Example::

 - job:
    name: matrix-test
    project-type: matrix
    execution-strategy:
      combination-filter: |
        !(os=="fedora11" && arch=="amd64")
      sequential: true
      touchstone:
        expr: 'os == "fedora11"'
        result: unstable
    axes:
      - axis:
         type: label-expression
         name: os
         values:
          - ubuntu12.04
          - fedora11
      - axis:
         type: label-expression
         name: arch
         values:
          - amd64
          - i386
    builders:
      - shell: make && make check
"""


import xml.etree.ElementTree as XML
import jenkins_jobs.modules.base


class Matrix(jenkins_jobs.modules.base.Base):
    sequence = 0

    def root_xml(self, data):
        root = XML.Element('matrix-project')

        ex_r = XML.SubElement(root, 'executionStrategy',
                              {'class': 'hudson.matrix.'
                              'DefaultMatrixExecutionStrategyImpl'})
        ex_d = data.get('execution-strategy', {})
        XML.SubElement(root, 'combinationFilter').text = \
            str(ex_d.get('combination-filter', '')).rstrip()
        XML.SubElement(ex_r, 'runSequentially').text = \
            str(ex_d.get('sequential', 'false')).lower()
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
            if axis['type'] != 'label-expression':
                raise ValueError('Only label-expression axis type supported')
            lbl_root = XML.SubElement(ax_root, 'hudson.matrix.LabelExpAxis')
            name, values = axis['name'], axis['values']
            XML.SubElement(lbl_root, 'name').text = str(name)
            v_root = XML.SubElement(lbl_root, 'values')
            for v in values:
                XML.SubElement(v_root, 'string').text = str(v)

        return root
