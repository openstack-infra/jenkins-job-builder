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
from jenkins_jobs.modules.helpers import build_trends_publisher
from jenkins_jobs.modules.helpers import findbugs_settings
from jenkins_jobs.errors import JenkinsJobsException


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


def findbugs(parser, xml_parent, data):
    """yaml: findbugs
    FindBugs reporting for builds

    Requires the Jenkins :jenkins-wiki:`FindBugs Plugin
    <FindBugs+Plugin>`.

    :arg bool rank-priority: Use rank as priority (default: false)
    :arg str include-files: Comma separated list of files to include.
                            (Optional)
    :arg str exclude-files: Comma separated list of files to exclude.
                            (Optional)
    :arg bool can-run-on-failed: Weather or not to run plug-in on failed builds
                                 (default: false)
    :arg int healthy: Sunny threshold (optional)
    :arg int unhealthy: Stormy threshold (optional)
    :arg str health-threshold: Threshold priority for health status
      ('low', 'normal' or 'high', defaulted to 'low')
    :arg bool dont-compute-new: If set to false, computes new warnings based on
                                the reference build (default true)
    :arg bool use-delta-values: Use delta for new warnings. (Default: false)
    :arg bool use-previous-build-as-reference:  If set then the number of new
      warnings will always be calculated based on the previous build. Otherwise
      the reference build. (Default: false)
    :arg bool use-stable-build-as-reference: The number of new warnings will be
      calculated based on the last stable build, allowing reverts of unstable
      builds where the number of warnings was decreased. (default false)
    :arg dict thresholds:
        :thresholds:
            * **unstable** (`dict`)
                :unstable: * **total-all** (`int`)
                           * **total-high** (`int`)
                           * **total-normal** (`int`)
                           * **total-low** (`int`)
                           * **new-all** (`int`)
                           * **new-high** (`int`)
                           * **new-normal** (`int`)
                           * **new-low** (`int`)

            * **failed** (`dict`)
                :failed: * **total-all** (`int`)
                         * **total-high** (`int`)
                         * **total-normal** (`int`)
                         * **total-low** (`int`)
                         * **new-all** (`int`)
                         * **new-high** (`int`)
                         * **new-normal** (`int`)
                         * **new-low** (`int`)

    Minimal Example:

    .. literalinclude::  /../../tests/reporters/fixtures/findbugs-minimal.yaml

    Full Example:

    .. literalinclude::  /../../tests/reporters/fixtures/findbugs01.yaml

    """
    findbugs = XML.SubElement(xml_parent,
                              'hudson.plugins.findbugs.FindBugsReporter')
    findbugs.set('plugin', 'findbugs')

    findbugs_settings(findbugs, data)
    build_trends_publisher('[FINDBUGS] ', findbugs, data)


class Reporters(jenkins_jobs.modules.base.Base):
    sequence = 55

    component_type = 'reporter'
    component_list_type = 'reporters'

    def gen_xml(self, parser, xml_parent, data):
        if 'reporters' not in data:
            return

        if xml_parent.tag != 'maven2-moduleset':
            raise JenkinsJobsException("Reporters may only be used for Maven "
                                       "modules.")

        reporters = XML.SubElement(xml_parent, 'reporters')

        for action in data.get('reporters', []):
            self.registry.dispatch('reporter', parser, reporters, action)
