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
The Parameters module allows you to specify build parameters for a job.

**Component**: parameters
  :Macro: parameter
  :Entry Point: jenkins_jobs.parameters

Example::

  job:
    name: test_job

    parameters:
      - string:
          name: FOO
          default: bar
          description: "A parameter named FOO, defaults to 'bar'."
"""


import xml.etree.ElementTree as XML
import jenkins_jobs.modules.base


def base_param(parser, xml_parent, data, do_default, ptype):
    pdef = XML.SubElement(xml_parent, ptype)
    XML.SubElement(pdef, 'name').text = data['name']
    XML.SubElement(pdef, 'description').text = data['description']
    if do_default:
        default = data.get('default', None)
        if default:
            XML.SubElement(pdef, 'defaultValue').text = default
        else:
            XML.SubElement(pdef, 'defaultValue')
    return pdef


def string_param(parser, xml_parent, data):
    """yaml: string
    A string parameter.

    :arg str name: the name of the parameter
    :arg str default: the default value of the parameter (optional)
    :arg str description: a description of the parameter (optional)

    Example::

      parameters:
        - string:
            name: FOO
            default: bar
            description: "A parameter named FOO, defaults to 'bar'."
    """
    base_param(parser, xml_parent, data, True,
               'hudson.model.StringParameterDefinition')


def bool_param(parser, xml_parent, data):
    """yaml: bool
    A boolean parameter.

    :arg str name: the name of the parameter
    :arg str default: the default value of the parameter (optional)
    :arg str description: a description of the parameter (optional)

    Example::

      parameters:
        - bool:
            name: FOO
            default: false
            description: "A parameter named FOO, defaults to 'false'."
    """
    data['default'] = str(data.get('default', 'false')).lower()
    base_param(parser, xml_parent, data, True,
               'hudson.model.BooleanParameterDefinition')


def file_param(parser, xml_parent, data):
    """yaml: file
    A file parameter.

    :arg str name: the target location for the file upload
    :arg str description: a description of the parameter (optional)

    Example::

      parameters:
        - file:
            name: test.txt
            description: "Upload test.txt."
    """
    base_param(parser, xml_parent, data, False,
               'hudson.model.FileParameterDefinition')


def text_param(parser, xml_parent, data):
    """yaml: text
    A text parameter.

    :arg str name: the name of the parameter
    :arg str default: the default value of the parameter (optional)
    :arg str description: a description of the parameter (optional)

    Example::

      parameters:
        - text:
            name: FOO
            default: bar
            description: "A parameter named FOO, defaults to 'bar'."
    """
    base_param(parser, xml_parent, data, True,
               'hudson.model.TextParameterDefinition')


def label_param(parser, xml_parent, data):
    """yaml: label
    A node label parameter.

    :arg str name: the name of the parameter
    :arg str default: the default value of the parameter (optional)
    :arg str description: a description of the parameter (optional)

    Example::

      parameters:
        - label:
            name: node
            default: precise
            description: "The node on which to run the job"
    """
    base_param(parser, xml_parent, data, True,
               'org.jvnet.jenkins.plugins.nodelabelparameter.'
               'LabelParameterDefinition')


def choice_param(parser, xml_parent, data):
    """yaml: choice
    A single selection parameter.

    :arg str name: the name of the parameter
    :arg list choices: the available choices
    :arg str description: a description of the parameter (optional)

    Example::

      parameters:
        - choice:
            name: project
            choices:
              - nova
              - glance
            description: "On which project to run?"
    """
    pdef = base_param(parser, xml_parent, data, False,
                      'hudson.model.ChoiceParameterDefinition')
    choices = XML.SubElement(pdef, 'choices',
                             {'class': 'java.util.Arrays$ArrayList'})
    a = XML.SubElement(choices, 'a', {'class': 'string-array'})
    for choice in data['choices']:
        XML.SubElement(a, 'string').text = choice


def validating_string_param(parser, xml_parent, data):
    """yaml: validating-string
    A validating string parameter
    Requires the Jenkins `Validating String Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/
    Validating+String+Parameter+Plugin>`_

    :arg str name: the name of the parameter
    :arg str default: the default value of the parameter (optional)
    :arg str description: a description of the parameter (optional)
    :arg str regex: a regular expression to validate the string
    :arg str msg: a message to display upon failed validation

    Example::

      parameters:
        - validating-string:
            name: FOO
            default: bar
            description: "A parameter named FOO, defaults to 'bar'."
            regex: [A-Za-z]*
            msg: Your entered value failed validation
    """
    pdef = base_param(parser, xml_parent, data, True,
                      'hudson.plugins.validating__string__parameter.'
                      'ValidatingStringParameterDefinition')
    XML.SubElement(pdef, 'regex').text = data['regex']
    XML.SubElement(pdef, 'failedValidationMessage').text = data['msg']


def svn_tags_param(parser, xml_parent, data):
    """yaml: svn-tags
    A svn tag parameter
    Requires the Jenkins `Parameterized Trigger Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/
    Parameterized+Trigger+Plugin>`_

    :arg str name: the name of the parameter
    :arg str default: the default value of the parameter (optional)
    :arg str description: a description of the parameter (optional)
    :arg str url: the url to list tags from
    :arg str filter: the regular expression to filter tags

    Example::

      parameters:
        - svn-tags:
            name: BRANCH_NAME
            default: release
            description: A parameter named BRANCH_NAME default is release
            url: http://svn.example.com/repo
            filter: [A-za-z0-9]*
    """
    pdef = base_param(parser, xml_parent, data, True,
                      'hudson.scm.listtagsparameter.'
                      'ListSubversionTagsParameterDefinition')
    XML.SubElement(pdef, 'tagsDir').text = data['url']
    XML.SubElement(pdef, 'tagsFilter').text = data.get('filter', None)
    XML.SubElement(pdef, 'reverseByDate').text = "true"
    XML.SubElement(pdef, 'reverseByName').text = "false"
    XML.SubElement(pdef, 'maxTags').text = "100"


class Parameters(jenkins_jobs.modules.base.Base):
    sequence = 21

    def gen_xml(self, parser, xml_parent, data):
        properties = xml_parent.find('properties')
        if properties is None:
            properties = XML.SubElement(xml_parent, 'properties')

        parameters = data.get('parameters', [])
        if parameters:
            pdefp = XML.SubElement(properties,
                                   'hudson.model.ParametersDefinitionProperty')
            pdefs = XML.SubElement(pdefp, 'parameterDefinitions')
            for param in parameters:
                self._dispatch('parameter', 'parameters',
                               parser, pdefs, param)
