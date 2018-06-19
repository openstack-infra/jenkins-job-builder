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

The module also supports additional, plugin-defined axes:

* DynamicAxis (``dynamic``), requires the Jenkins
  :jenkins-wiki:`DynamicAxis Plugin <DynamicAxis+Plugin>`
* GroovyAxis (``groovy``), requires the Jenkins
  :jenkins-wiki:`GroovyAxis Plugin <GroovyAxis>`
* YamlAxis (``yaml``), requires the Jenkins
  :jenkins-wiki:`Yaml Axis Plugin <Yaml+Axis+Plugin>`

To tie the parent job to a specific node, you should use ``node`` parameter.
On a matrix project, this will tie *only* the parent job.  To restrict axes
jobs, you can define a single value ``slave`` axis.

:Job Parameters:

    .. note::

       You can only pick one of the strategies.

    * **execution-strategy** (optional, built in Jenkins):
        * **combination-filter** (`str`): axes selection filter
        * **sequential** (`bool`): run builds sequentially (default false)
        * **touchstone** (optional):
            * **expr** (`str`) -- selection filter for the touchstone build
            * **result** (`str`) -- required result of the job: \
            stable (default) or unstable

    * **yaml-strategy** (optional, requires
      :jenkins-wiki:`Yaml Axis Plugin <Yaml+Axis+Plugin>`):

        * **exclude-key** (`str`) -- top key containing exclusion rules
        * Either one of:
        * **filename** (`str`) -- Yaml file containing exclusions
        * **text** (`str`) -- Inlined Yaml. Should be literal
          ``text: | exclude:...``

    * **axes** (`list`):
        * **axis**:
            * **type** (`str`) -- axis type, must be either type defined by
              :jenkins-wiki:`Matrix Project Plugin <Matrix+Project+Plugin>`
              (``label-expression``, ``user-defined``, ``slave`` or ``jdk``) or
              a type defined by a plugin (see top of this document for a list
              of supported plugins).
            * **name** (`str`) -- name of the axis
            * **values** (`list`) -- values of the axis

The module supports also ShiningPanda axes:

Example:

.. literalinclude::  /../../tests/general/fixtures/matrix-axis003.yaml

Requires the Jenkins :jenkins-wiki:`ShiningPanda Plugin <ShiningPanda+Plugin>`.

Example:

  .. literalinclude::  /../../tests/yamlparser/fixtures/project-matrix001.yaml
    :language: yaml

Examples for yaml axis:

  .. literalinclude::  /../../tests/general/fixtures/matrix-axis-yaml.yaml
    :language: yaml

  .. literalinclude::
     /../../tests/general/fixtures/matrix-axis-yaml-strategy-file.yaml
    :language: yaml

  .. literalinclude::
     /../../tests/general/fixtures/matrix-axis-yaml-strategy-inlined.yaml
    :language: yaml
"""

import xml.etree.ElementTree as XML

import jenkins_jobs.modules.base
from jenkins_jobs.errors import InvalidAttributeError
from jenkins_jobs.modules import hudson_model


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
        'groovy': 'org.jenkinsci.plugins.GroovyAxis',
        'yaml': 'org.jenkinsci.plugins.yamlaxis.YamlAxis',
    }

    supported_strategies = {
        # Jenkins built-in, default
        'execution-strategy':
            'hudson.matrix.DefaultMatrixExecutionStrategyImpl',
        'yaml-strategy':
            'org.jenkinsci.plugins.yamlaxis.YamlMatrixExecutionStrategy',
    }

    def root_xml(self, data):
        root = XML.Element('matrix-project')

        # Default to 'execution-strategy'
        strategies = ([s for s in data.keys() if s.endswith('-strategy')] or
                      ['execution-strategy'])

        # Job can not have multiple strategies
        if len(strategies) > 1:
            raise ValueError(
                'matrix-project does not support multiple strategies. '
                'Given %s: %s' % (len(strategies), ', '.join(strategies)))
        strategy_name = strategies[0]

        if strategy_name not in self.supported_strategies:
            raise ValueError(
                'Given strategy %s. Only %s strategies are supported'
                % (strategy_name, self.supported_strategies.keys()))

        ex_r = XML.SubElement(
            root, 'executionStrategy',
            {'class': self.supported_strategies[strategy_name]})

        strategy = data.get(strategy_name, {})

        if strategy_name == 'execution-strategy':
            XML.SubElement(root, 'combinationFilter').text = (
                str(strategy.get('combination-filter', '')).rstrip()
            )
            XML.SubElement(ex_r, 'runSequentially').text = (
                str(strategy.get('sequential', False)).lower()
            )
            if 'touchstone' in strategy:
                XML.SubElement(ex_r, 'touchStoneCombinationFilter').text = (
                    str(strategy['touchstone'].get('expr', ''))
                )

                threshold = strategy['touchstone'].get(
                    'result', 'stable').upper()
                supported_thresholds = ('STABLE', 'UNSTABLE')
                if threshold not in supported_thresholds:
                    raise InvalidAttributeError(
                        'touchstone', threshold, supported_thresholds)

                # Web ui uses Stable but hudson.model.Result has Success
                if threshold == 'STABLE':
                    threshold = 'SUCCESS'

                t_r = XML.SubElement(ex_r, 'touchStoneResultCondition')
                for sub_elem in ('name', 'ordinal', 'color'):
                    XML.SubElement(t_r, sub_elem).text = (
                        hudson_model.THRESHOLDS[threshold][sub_elem])

        elif strategy_name == 'yaml-strategy':
            filename = str(strategy.get('filename', ''))
            text = str(strategy.get('text', ''))
            exclude_key = str(strategy.get('exclude-key', ''))

            if bool(filename) == bool(text):  # xor with str
                raise ValueError('yaml-strategy must be given '
                                 'either "filename" or "text"')

            yamlType = (filename and 'file') or (text and 'text')
            XML.SubElement(ex_r, 'yamlType').text = yamlType

            XML.SubElement(ex_r, 'yamlFile').text = filename
            XML.SubElement(ex_r, 'yamlText').text = text

            XML.SubElement(ex_r, 'excludeKey').text = exclude_key

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
            if axis_type != "groovy":
                v_root = XML.SubElement(lbl_root, 'values')
            if axis_type == "dynamic":
                XML.SubElement(v_root, 'string').text = str(values[0])
                XML.SubElement(lbl_root, 'varName').text = str(values[0])
                v_root = XML.SubElement(lbl_root, 'axisValues')
                XML.SubElement(v_root, 'string').text = 'default'
            elif axis_type == "groovy":
                command = XML.SubElement(lbl_root, 'groovyString')
                command.text = axis.get('command')
                XML.SubElement(lbl_root, 'computedValues').text = ''
            elif axis_type == "yaml":
                XML.SubElement(v_root, 'string').text = axis.get('filename')
            else:
                for v in values:
                    XML.SubElement(v_root, 'string').text = str(v)

        return root
