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

import xml.etree.ElementTree as XML
import jenkins_jobs.modules.base

"""
The view list module handles creating Jenkins List views.

To create a list view specify ``list`` in the ``view-type`` attribute
to the :ref:`View-list` definition.

:View Parameters:
    * **name** (`str`): The name of the view.
    * **view-type** (`str`): The type of view.
    * **description** (`str`): A description of the view. (optional)
    * **filter-executors** (`bool`): Show only executors that can
      execute the included views. (default false)
    * **filter-queue** (`bool`): Show only included jobs in builder
      queue. (default false)
    * **job-name** (`list`): List of jobs to be included.
    * **columns** (`list`): List of columns to be shown in view.
    * **regex** (`str`): . Regular expression for selecting jobs
      (optional)
    * **recurse** (`bool`): Recurse in subfolders.(default false)
    * **status-filter** (`bool`): Filter job list by enabled/disabled
      status. (optional)
"""

COLUMN_DICT = {
    'status': 'hudson.views.StatusColumn',
    'weather': 'hudson.views.WeatherColumn',
    'job': 'hudson.views.JobColumn',
    'last-success': 'hudson.views.LastSuccessColumn',
    'last-failure': 'hudson.views.LastFailureColumn',
    'last-duration': 'hudson.views.LastDurationColumn',
    'build-button': 'hudson.views.BuildButtonColumn',
    'last-stable': 'hudson.views.LastStableColumn',
}


class List(jenkins_jobs.modules.base.Base):
    sequence = 0

    def root_xml(self, data):
        root = XML.Element('hudson.model.ListView')
        XML.SubElement(root, 'name').text = data['name']
        desc_text = data.get('description', None)
        if desc_text is not None:
            XML.SubElement(root, 'description').text = desc_text

        filterExecutors = data.get('filter-executors', False)
        FE_element = XML.SubElement(root, 'filterExecutors')
        FE_element.text = 'true' if filterExecutors else 'false'

        filterQueue = data.get('filter-queue', False)
        FQ_element = XML.SubElement(root, 'filterQueue')
        FQ_element.text = 'true' if filterQueue else 'false'

        XML.SubElement(root, 'properties',
                       {'class': 'hudson.model.View$PropertyList'})

        jn_xml = XML.SubElement(root, 'jobNames')
        jobnames = data.get('job-name', None)
        XML.SubElement(jn_xml, 'comparator', {'class':
                       'hudson.util.CaseInsensitiveComparator'})
        if jobnames is not None:
            for jobname in jobnames:
                XML.SubElement(jn_xml, 'string').text = str(jobname)
        XML.SubElement(root, 'jobFilters')

        c_xml = XML.SubElement(root, 'columns')
        columns = data.get('columns', [])
        for column in columns:
            if column in COLUMN_DICT:
                XML.SubElement(c_xml, COLUMN_DICT[column])

        regex = data.get('regex', None)
        if regex is not None:
            XML.SubElement(root, 'includeRegex').text = regex

        recurse = data.get('recurse', False)
        R_element = XML.SubElement(root, 'recurse')
        R_element.text = 'true' if recurse else 'false'

        statusfilter = data.get('status-filter', None)
        if statusfilter is not None:
            SF_element = XML.SubElement(root, 'statusFilter')
            SF_element.text = 'true' if statusfilter else 'false'

        return root
