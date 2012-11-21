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
Enable hipchat notification of build execution.

Example::

  - job:
      name: test_job
      hipchat:
        enabled: true
        room:  Testjob Build Notifications
        start-notify: true

In the jenkins UI specification, the hipchat plugin must be explicitly
selected as a publisher.  This is not required (or supported) here - use the
``enabled`` parameter to enable/disable the publisher action.
If you set ``enabled: false``, no hipchat parameters are written to XML.
"""

# Enabling hipchat notifications on a job requires specifying the hipchat
# config in job properties, and adding the hipchat notifier to the job's
# publishers list.
# The publisher configuration contains extra details not specified per job:
#   - the hipchat authorisation token.
#   - the jenkins server url.
#   - a default room name/id.
# This complicates matters somewhat since the sensible place to store these
# details is in the global config file.
# The global config object is therefore passed down to the registry object,
# and this object is passed to the HipChat() class initialiser.

import xml.etree.ElementTree as XML
import jenkins_jobs.modules.base
import jenkins_jobs.errors
import logging
import ConfigParser

logger = logging.getLogger(__name__)


class HipChat(jenkins_jobs.modules.base.Base):
    sequence = 80

    def __init__(self, registry):
        self.authToken = None
        self.jenkinsUrl = None
        self.registry = registry

    def _load_global_data(self):
        """Load data from the global config object.
           This is done lazily to avoid looking up the '[hipchat]' section
           unless actually required.
        """
        if(not self.authToken):
            # Verify that the config object in the registry is of type
            # ConfigParser (it could possibly be a regular 'dict' object which
            # doesn't have the right get() method).
            if(not isinstance(self.registry.global_config,
                              ConfigParser.ConfigParser)):
                raise jenkins_jobs.errors.JenkinsJobsException(
                    'HipChat requires a config object in the registry.')
            self.authToken = self.registry.global_config.get(
                'hipchat', 'authtoken')
            self.jenkinsUrl = self.registry.global_config.get('jenkins', 'url')

    def gen_xml(self, parser, xml_parent, data):
        hipchat = data.get('hipchat')
        if not hipchat or not hipchat.get('enabled', True):
            return
        if('room' not in hipchat):
            raise jenkins_jobs.errors.YAMLFormatError(
                "Missing hipchat 'room' specifier")
        self._load_global_data()

        properties = xml_parent.find('properties')
        if properties is None:
            properties = XML.SubElement(xml_parent, 'properties')
        pdefhip = XML.SubElement(properties,
                                 'jenkins.plugins.hipchat.'
                                 'HipChatNotifier_-HipChatJobProperty')
        XML.SubElement(pdefhip, 'room').text = hipchat['room']
        XML.SubElement(pdefhip, 'startNotification').text = str(
            hipchat.get('start-notify', 'false')).lower()

        publishers = xml_parent.find('publishers')
        if publishers is None:
            publishers = XML.SubElement(xml_parent, 'publishers')
        hippub = XML.SubElement(publishers,
                                'jenkins.plugins.hipchat.HipChatNotifier')
        XML.SubElement(hippub, 'jenkinsUrl').text = self.jenkinsUrl
        XML.SubElement(hippub, 'authToken').text = self.authToken
        # The room specified here is the default room.  The default is
        # redundant in this case since a room must be specified.  Leave empty.
        XML.SubElement(hippub, 'room').text = ''
