# Copyright 2015 Openstack Foundation

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
The view pipeline module handles creating Jenkins Build Pipeline views.
To create a pipeline view specify ``pipeline`` in the ``view-type`` attribute
to the :ref:`view_pipeline` definition.
Requires the Jenkins
:jenkins-wiki:`Build Pipeline Plugin <build+pipeline+plugin>`.

:View Parameters:
    * **name** (`str`): The name of the view.
    * **view-type** (`str`): The type of view.
    * **description** (`str`): A description of the view. (optional)
    * **filter-executors** (`bool`): Show only executors that can
      execute the included views. (default false)
    * **filter-queue** (`bool`): Show only included jobs in builder
      queue. (default false)
    * **first-job** (`str`): Parent Job in the view.
    * **no-of-displayed-builds** (`str`): Number of builds to display.
      (default 1)
    * **title** (`str`): Build view title. (optional)
    * **linkStyle** (`str`): Console output link style. Can be
      'Lightbox', 'New Window', or 'This Window'. (default Lightbox)
    * **css-Url** (`str`): Url for Custom CSS files (optional)
    * **latest-job-only** (`bool`) Trigger only latest job.
      (default false)
    * **manual-trigger** (`bool`) Always allow manual trigger.
      (default false)
    * **show-parameters** (`bool`) Show pipeline parameters.
      (default false)
    * **parameters-in-headers** (`bool`) Show pipeline parameters in
      headers. (default false)
    * **starts-with-parameters** (`bool`) Use Starts with parameters.
      (default false)
    * **refresh-frequency** (`str`) Frequency to refresh in seconds.
      (default '3')
    * **definition-header** (`bool`) Show pipeline definition header.
      (default false)

Example:

    .. literalinclude::
        /../../tests/views/fixtures/view_pipeline001.yaml

Example:

    .. literalinclude::
        /../../tests/views/fixtures/view_pipeline002.yaml
"""

import xml.etree.ElementTree as XML
import jenkins_jobs.modules.base
import jenkins_jobs.modules.helpers as helpers


class Pipeline(jenkins_jobs.modules.base.Base):
    sequence = 0

    def root_xml(self, data):
        linktypes = ['Lightbox', 'New Window']
        root = XML.Element('au.com.centrumsystems.hudson.'
                           'plugin.buildpipeline.BuildPipelineView',
                           {'plugin': 'build-pipeline-plugin'})

        mapping_optional = [
            ('description', 'description', None),
            ('filter-executors', 'filterExecutors', False),
            ('filter-queue', 'filterQueue', False),
        ]
        helpers.convert_mapping_to_xml(root, data,
            mapping_optional, fail_required=False)

        XML.SubElement(root, 'properties',
                       {'class': 'hudson.model.View$PropertyList'})

        GBurl = ('au.com.centrumsystems.hudson.plugin.buildpipeline.'
                 'DownstreamProjectGridBuilder')
        gridBuilder = XML.SubElement(root, 'gridBuilder', {'class': GBurl})

        jobname = data.get('first-job', '')
        XML.SubElement(gridBuilder, 'firstJob').text = jobname

        mapping = [
            ('name', 'name', None),
            ('no-of-displayed-builds', 'noOfDisplayedBuilds', 1),
            ('title', 'buildViewTitle', ''),
            ('link-style', 'consoleOutputLinkStyle', 'Lightbox', linktypes),
            ('css-Url', 'cssUrl', ''),
            ('latest-job-only', 'triggerOnlyLatestJob', False),
            ('manual-trigger', 'alwaysAllowManualTrigger', False),
            ('show-parameters', 'showPipelineParameters', False),
            ('parameters-in-headers',
                'showPipelineParametersInHeaders', False),
            ('start-with-parameters', 'startsWithParameters', False),
            ('refresh-frequency', 'refreshFrequency', 3),
            ('definition-header', 'showPipelineDefinitionHeader', False),
        ]
        helpers.convert_mapping_to_xml(root, data, mapping, fail_required=True)

        return root
