# -*- coding: utf-8 -*-
# Copyright (C) 2015 Cisco Systems, Inc.
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
The folder Project module handles creating Jenkins folder projects.
You may specify ``folder`` in the ``project-type`` attribute of
the :ref:`Job` definition.

Requires the Jenkins :jenkins-wiki:`CloudBees Folder Plugin
<CloudBees+Folder+Plugin>`.

Job example:

    .. literalinclude::
      /../../tests/yamlparser/fixtures/project_folder_template001.yaml

Job template example:

    .. literalinclude::
      /../../tests/yamlparser/fixtures/project_folder_template002.yaml

"""

import xml.etree.ElementTree as XML
import jenkins_jobs.modules.base


class Folder(jenkins_jobs.modules.base.Base):
    sequence = 0

    def root_xml(self, data):
        xml_parent = XML.Element('com.cloudbees.hudson.plugins.folder.Folder',
                                 plugin="cloudbees-folder")
        XML.SubElement(xml_parent, 'actions')
        attributes = {"class": "com.cloudbees.hudson.plugins.folder."
                               "icons.StockFolderIcon"}
        XML.SubElement(xml_parent, 'icon', attrib=attributes)
        XML.SubElement(xml_parent, 'views')
        attributes = {"class": "hudson.views.DefaultViewsTabBar"}
        XML.SubElement(xml_parent, 'viewsTabBar', attrib=attributes)
        XML.SubElement(xml_parent, 'primaryView').text = 'All'
        XML.SubElement(xml_parent, 'healthMetrics')

        return xml_parent
