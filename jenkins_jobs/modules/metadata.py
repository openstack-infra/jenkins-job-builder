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
The Metadata plugin module enables the ability to add metadata to the projects
that can be exposed to job environment.
Requires the Jenkins :jenkins-wiki:`Metadata Plugin <Metadata+plugin>`.

**Component**: metadata
  :Macro: metadata
  :Entry Point: jenkins_jobs.metadata

Example::

    metadata:
      - string:
          name: FOO
          value: bar
          expose-to-env: true
"""


import xml.etree.ElementTree as XML
import jenkins_jobs.modules.base


def base_metadata(parser, xml_parent, data, mtype):
    pdef = XML.SubElement(xml_parent, mtype)
    XML.SubElement(pdef, 'name').text = data['name']
    XML.SubElement(pdef, 'generated').text = 'false'
    XML.SubElement(pdef, 'parent', attrib={"class": "job-metadata",
                                           "reference": "../../.."})

    exposed_to_env = XML.SubElement(pdef, 'exposedToEnvironment')
    exposed_to_env.text = str(data.get('expose-to-env', False)).lower()
    return pdef


def string_metadata(parser, xml_parent, data):
    """yaml: string
    A string metadata.

    :arg str name: the name of the metadata
    :arg str value: the value of the metadata
    :arg bool expose-to-env: expose to environment (optional)

    Example::

      metadata:
        - string:
            name: FOO
            value: bar
            expose-to-env: true
    """
    pdef = base_metadata(parser, xml_parent, data,
                         'metadata-string')
    value = data.get('value', '')
    XML.SubElement(pdef, 'value').text = value


def number_metadata(parser, xml_parent, data):
    """yaml: number
    A number metadata.

    :arg str name: the name of the metadata
    :arg str value: the value of the metadata
    :arg bool expose-to-env: expose to environment (optional)

    Example::

      metadata:
        - number:
            name: FOO
            value: 1
            expose-to-env: true
    """
    pdef = base_metadata(parser, xml_parent, data,
                         'metadata-number')
    value = data.get('value', '')
    XML.SubElement(pdef, 'value').text = value


def date_metadata(parser, xml_parent, data):
    """yaml: date
    A date metadata

    :arg str name: the name of the metadata
    :arg str time: time value in millisec since 1970-01-01 00:00:00 UTC
    :arg str timezone: time zone of the metadata
    :arg bool expose-to-env: expose to environment (optional)

    Example::

      metadata:
        - date:
            name: FOO
            value: 1371708900268
            timezone: Australia/Melbourne
            expose-to-env: true
    """
    pdef = base_metadata(parser, xml_parent, data,
                         'metadata-date')
    # TODO: convert time from any reasonable format into epoch
    mval = XML.SubElement(pdef, 'value')
    XML.SubElement(mval, 'time').text = data['time']
    XML.SubElement(mval, 'timezone').text = data['timezone']
    XML.SubElement(pdef, 'checked').text = 'true'


class Metadata(jenkins_jobs.modules.base.Base):
    sequence = 21

    component_type = 'metadata'
    component_list_type = 'metadata'

    def gen_xml(self, parser, xml_parent, data):
        properties = xml_parent.find('properties')
        if properties is None:
            properties = XML.SubElement(xml_parent, 'properties')

        metadata = data.get('metadata', [])
        if metadata:
            pdefp = XML.SubElement(properties,
                                   'job-metadata', plugin="metadata@1.0b")
            pdefs = XML.SubElement(pdefp, 'values')
            for mdata in metadata:
                self.registry.dispatch('metadata',
                                       parser, pdefs, mdata)
