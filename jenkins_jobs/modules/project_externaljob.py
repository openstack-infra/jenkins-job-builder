# Copyright 2015 Hewlett-Packard Development Company, L.P.
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
The External Job Project module handles creating ExternalJob Jenkins projects.
You may specify ``externaljob`` in the ``project-type`` attribute of the
:ref:`Job` definition.

This type of job allows you to record the execution of a process run outside
Jenkins, even on a remote machine. This is designed so that you can use
Jenkins as a dashboard of your existing automation system.

Requires the Jenkins :jenkins-wiki:`External Monitor Job Type Plugin
<Monitoring+external+jobs>`.

Example:

    .. literalinclude:: /../../tests/general/fixtures/project-type005.yaml

"""

import xml.etree.ElementTree as XML

import jenkins_jobs.modules.base


class ExternalJob(jenkins_jobs.modules.base.Base):
    sequence = 0

    def root_xml(self, data):
        xml_parent = XML.Element('hudson.model.ExternalJob')
        return xml_parent
