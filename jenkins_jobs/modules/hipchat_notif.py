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
Enable HipChat notifications of build execution.

Supports hipchat plugin versions < 1.9. Will automatically redirect to the
publishers module for newer versions, but still recommended that you convert
to the newer module.

:Parameters:
  * **enabled** *(bool)*: general cut off switch. If not explicitly set to
    ``true``, no hipchat parameters are written to XML. For Jenkins HipChat
    plugin of version prior to 0.1.5, also enables all build results to be
    reported in HipChat room. For later plugin versions, explicit notify-*
    setting is required (see below).
  * **room** *(str)*: name of HipChat room to post messages to (default '')

    .. deprecated:: 1.2.0  Please use 'rooms'.

  * **rooms** *(list)*: list of HipChat rooms to post messages to
    (default empty)
  * **start-notify** *(bool)*: post messages about build start event

    .. deprecated:: 1.2.0 use notify-start parameter instead

  * **notify-start** *(bool)*: post messages about build start event
    (default false)
  * **notify-success** *(bool)*: post messages about successful build event
    (Jenkins HipChat plugin >= 0.1.5) (default false)
  * **notify-aborted** *(bool)*: post messages about aborted build event
    (Jenkins HipChat plugin >= 0.1.5) (default false)
  * **notify-not-built** *(bool)*: post messages about build set to NOT_BUILT
    status (Jenkins HipChat plugin >= 0.1.5). This status code is used in a
    multi-stage build (like maven2) where a problem in earlier stage prevented
    later stages from building. (default false)
  * **notify-unstable** *(bool)*: post messages about unstable build event
    (Jenkins HipChat plugin >= 0.1.5) (default false)
  * **notify-failure** *(bool)*:  post messages about build failure event
    (Jenkins HipChat plugin >= 0.1.5) (default false)
  * **notify-back-to-normal** *(bool)*: post messages about build being back to
    normal after being unstable or failed (Jenkins HipChat plugin >= 0.1.5)
    (default false)


Example:

.. literalinclude:: /../../tests/hipchat/fixtures/hipchat001.yaml
   :language: yaml

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

import logging
import pkg_resources
import sys
import xml.etree.ElementTree as XML

from six.moves import configparser

import jenkins_jobs.errors
import jenkins_jobs.modules.base
import jenkins_jobs.modules.helpers as helpers


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
        jjb_config = self.registry.jjb_config
        if not self.authToken:
            try:
                self.authToken = jjb_config.get_plugin_config('hipchat',
                                                              'authtoken')
                # Require that the authtoken is non-null
                if self.authToken == '':
                    raise jenkins_jobs.errors.JenkinsJobsException(
                        "Hipchat authtoken must not be a blank string")
            except (configparser.NoSectionError,
                    jenkins_jobs.errors.JenkinsJobsException) as e:
                logger.fatal("The configuration file needs a hipchat section" +
                             " containing authtoken:\n{0}".format(e))
                sys.exit(1)
            self.jenkinsUrl = jjb_config.get_plugin_config('hipchat', 'url')
            self.sendAs = jjb_config.get_plugin_config('hipchat', 'send-as')

    def gen_xml(self, xml_parent, data):
        hipchat = data.get('hipchat')
        if not hipchat or not hipchat.get('enabled', True):
            return
        self._load_global_data()

        # convert for compatibility before dispatch
        if 'room' in hipchat:
            if 'rooms' in hipchat:
                logger.warning("Ignoring deprecated 'room' as 'rooms' also "
                               "defined.")
            else:
                logger.warning("'room' is deprecated, please use 'rooms'")
                hipchat['rooms'] = [hipchat['room']]

        plugin_info = self.registry.get_plugin_info("Jenkins HipChat Plugin")
        version = pkg_resources.parse_version(plugin_info.get('version', '0'))

        if version >= pkg_resources.parse_version("0.1.9"):
            publishers = xml_parent.find('publishers')
            if publishers is None:
                publishers = XML.SubElement(xml_parent, 'publishers')

            logger.warning(
                "'hipchat' module supports the old plugin versions <1.9, "
                "newer versions are supported via the 'publishers' module. "
                "Please upgrade you job definition")
            component = {'hipchat': hipchat}
            return self.registry.dispatch('publisher', publishers, component)
        else:
            properties = xml_parent.find('properties')
            if properties is None:
                properties = XML.SubElement(xml_parent, 'properties')
            pdefhip = XML.SubElement(properties,
                                     'jenkins.plugins.hipchat.'
                                     'HipChatNotifier_-HipChatJobProperty')

        room = XML.SubElement(pdefhip, 'room')
        if 'rooms' in hipchat:
            room.text = ",".join(hipchat['rooms'])

        # Handle backwards compatibility 'start-notify' but all add an element
        # of standardization with notify-*
        if hipchat.get('start-notify'):
            logger.warning("'start-notify' is deprecated, please use "
                           "'notify-start'")
        XML.SubElement(pdefhip, 'startNotification').text = str(
            hipchat.get('notify-start', hipchat.get('start-notify',
                                                    False))).lower()

        if version >= pkg_resources.parse_version("0.1.5"):
            mapping = [
                ('notify-success', 'notifySuccess', False),
                ('notify-aborted', 'notifyAborted', False),
                ('notify-not-built', 'notifyNotBuilt', False),
                ('notify-unstable', 'notifyUnstable', False),
                ('notify-failure', 'notifyFailure', False),
                ('notify-back-to-normal', 'notifyBackToNormal', False),
            ]
            helpers.convert_mapping_to_xml(pdefhip,
                hipchat, mapping, fail_required=True)

        publishers = xml_parent.find('publishers')
        if publishers is None:
            publishers = XML.SubElement(xml_parent, 'publishers')
        hippub = XML.SubElement(publishers,
                                'jenkins.plugins.hipchat.HipChatNotifier')

        if version >= pkg_resources.parse_version("0.1.8"):
            XML.SubElement(hippub, 'buildServerUrl').text = self.jenkinsUrl
            XML.SubElement(hippub, 'sendAs').text = self.sendAs
        else:
            XML.SubElement(hippub, 'jenkinsUrl').text = self.jenkinsUrl

        XML.SubElement(hippub, 'authToken').text = self.authToken
        # The room specified here is the default room.  The default is
        # redundant in this case since a room must be specified.  Leave empty.
        XML.SubElement(hippub, 'room').text = ''
