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
The Freestyle Project module handles creating freestyle Jenkins
projects (i.e., those that do not use Maven).  You may specify
``freestyle`` in the ``project-type`` attribute to the :ref:`Job`
definition if you wish, though it is the default, so you may omit
``project-type`` altogether if you are creating a freestyle project.

Example::

  job:
    name: test_job
    project-type: freestyle
"""

import xml.etree.ElementTree as XML

import jenkins_jobs.modules.base


class Freestyle(jenkins_jobs.modules.base.Base):
    sequence = 0

    def root_xml(self, data):
        xml_parent = XML.Element('project')
        return xml_parent
