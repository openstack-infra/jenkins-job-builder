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
Reporters are like publishers but only applicable to Maven projets.

**Component**: reporters
  :Macro: reporter
  :Entry Point: jenkins_jobs.reporters

Example::

  job:
    name: test_job
    project-type: maven

    reporters:
      - email:
          recipients: breakage@example.com
"""


import xml.etree.ElementTree as XML
import jenkins_jobs.modules.base


def email(parser, xml_parent, data):
    """yaml: email
    Email notifications on build failure.

    :arg str recipients: Recipient email addresses
    :arg bool notify-every-unstable-build: Send an email for every
      unstable build (default true)
    :arg bool send-to-individuals: Send an email to the individual
      who broke the build (default false)

    Example::

      reporters:
        - email:
            recipients: breakage@example.com
    """

    mailer = XML.SubElement(xml_parent,
                            'hudson.maven.reporters.Mailer')
    XML.SubElement(mailer, 'recipients').text = data['recipients']

    # Note the logic reversal (included here to match the GUI
    if data.get('notify-every-unstable-build', True):
        XML.SubElement(mailer, 'dontNotifyEveryUnstableBuild').text = 'false'
    else:
        XML.SubElement(mailer, 'dontNotifyEveryUnstableBuild').text = 'true'
    XML.SubElement(mailer, 'sendToIndividuals').text = str(
        data.get('send-to-individuals', False)).lower()
    # TODO: figure out what this is:
    XML.SubElement(mailer, 'perModuleEmail').text = 'true'


class Reporters(jenkins_jobs.modules.base.Base):
    sequence = 55

    def gen_xml(self, parser, xml_parent, data):
        if 'reporters' not in data:
            return

        if xml_parent.tag != 'maven2-moduleset':
            raise Exception("Reporters may only be used for Maven modules.")

        reporters = XML.SubElement(xml_parent, 'reporters')

        for action in data.get('reporters', []):
            self._dispatch('reporter', 'reporters',
                           parser, reporters, action)
