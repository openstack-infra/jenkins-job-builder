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
The view list module handles creating Jenkins List views.

To create a list view specify ``list`` in the ``view-type`` attribute
to the :ref:`view_list` definition.

:View Parameters:
    * **name** (`str`): The name of the view.
    * **view-type** (`str`): The type of view.
    * **description** (`str`): A description of the view. (default '')
    * **filter-executors** (`bool`): Show only executors that can
      execute the included views. (default false)
    * **filter-queue** (`bool`): Show only included jobs in builder
      queue. (default false)
    * **job-name** (`list`): List of jobs to be included.
    * **job-filters** (`dict`): Job filters to be included. Requires
      :jenkins-wiki:`View Job Filters <View+Job+Filters>`

        * **most-recent** (`dict`)
            :most-recent:
                * **max-to-include** (`int`): Maximum number of jobs
                  to include. (default 0)
                * **check-start-time** (`bool`): Check job start
                  time. (default false)

        * **build-duration** (`dict`)
            :build-duration:
                * **match-type** ('str'): Jobs that match a filter
                  to include. (default includeMatched)
                * **build-duration-type** ('str'): Duration of the
                  build. (default Latest)
                * **amount-type**: ('str'): Duration in hours,
                  days or builds. (default Hours)
                * **amount**: ('int'): How far back to check.
                  (default 0)
                * **less-than**: ('bool'): Check build duration
                  less than or more than. (default True)
                * **build-duration-minutes**: ('int'): Build
                  duration minutes. (default 0)

        * **build-trend** (`dict`)
            :build-trend:
                * **match-type** ('str'): Jobs that match a filter
                  to include. (default includeMatched)
                * **build-trend-type** ('str'): Duration of the
                  build. (default Latest)
                * **amount-type**: ('str'): Duration in hours,
                  days or builds. (default Hours)
                * **amount**: ('int'): How far back to check.
                  (default 0)
                * **status**: ('str'): Job status.
                  (default Completed)

        * **job-status** (`dict`)
            :job-status:
                * **match-type** ('str'): Jobs that match a filter
                  to include. (default includeMatched)
                * **unstable** ('bool'): Jobs with status
                  unstable. (default False)
                * **failed** ('bool'): Jobs with status
                  failed. (default False)
                * **aborted** ('bool'): Jobs with status
                  aborted. (default False)
                * **disabled** ('bool'): Jobs with status
                  disabled. (default False)
                * **stable** ('bool'): Jobs with status
                  stable. (default False)

        * **fallback** (`dict`)
            :fallback:
                * **fallback-type** ('str'): Fallback type to include/exclude
                  for all jobs in a view, if no jobs have been included by
                  previous filters. (default REMOVE_ALL_IF_ALL_INCLUDED)

        * **build-status** (`dict`)
            :build-status:
                * **match-type** ('str'): Jobs that match a filter
                  to include. (default includeMatched)
                * **never-built** ('bool'): Jobs that are never
                  built. (default False)
                * **building** ('bool'): Jobs that are being
                  built. (default False)
                * **in-build-queue** ('bool'): Jobs that are in
                  the build queue. (default False)

        * **user-relevence** (`dict`)
            :user-relevence:
                * **match-type** ('str'): Jobs that match a filter
                  to include. (default includeMatched)
                * **build-count** ('str'): Count of builds.
                  (default AtLeastOne)
                * **amount-type**: ('str'): Duration in hours,
                  days or builds. (default Hours)
                * **amount**: ('int'): How far back to check.
                  (default 0)
                * **match-user-id** ('bool'): Jobs matching
                  user-id. (default False)
                * **match-user-fullname** ('bool'): Jobs
                  matching user fullname. (default False)
                * **ignore-case** ('bool'): Ignore case.
                  (default False)
                * **ignore-whitespace** ('bool'): Ignore
                  whitespace. (default False)
                * **ignore-non-alphaNumeric** ('bool'): Ignore
                  non-alphaNumeric. (default False)
                * **match-builder** ('bool'): Jobs matching
                  builder. (default False)
                * **match-email** ('bool'): Jobs matching
                  email. (default False)
                * **match-scm-changes** ('bool'): Jobs matching
                  scm changes. (default False)

        * **regex-job** (`dict`)
            :regex-job:
                * **match-type** ('str'): Jobs that match a filter
                  to include. (default includeMatched)
                * **regex-name** ('str'): Regular expression name.
                  (default '')
                * **regex** ('str'): Regular expression. (default '')

        * **job-tpye** (`dict`)
            :job-type:
                * **match-type** ('str'): Jobs that match a filter to include.
                  (default includeMatched)
                * **job-type** ('str'): Type of Job.
                  (default hudson.model.FreeStyleProject)

        * **parameter** (`dict`)
            :parameter:
                * **match-type** ('str'): Jobs that match a filter to include.
                  (default includeMatched)
                * **name** ('str'): Job name to match. (default '')
                * **value** ('str'): Value to match. (default '')
                * **desc** ('str'): Description to match. (default '')
                * **use-default-value** ('bool'): Use default value.
                  (default False)
                * **match-builds-in-progress** ('bool'): Match build in
                  progress. (default False)
                * **match-all-builds** ('bool'): Match all builds.
                  (default False)
                * **max-builds-to-match** ('int'): Maximum builds to match.
                  (default 0)

        * **other-views** (`dict`)
            :other-views:
                * **match-type** ('str'): Jobs that match a filter
                  to include. (default includeMatched)
                * **view-name** ('str'): View name.
                  (default select a view other than this one)

        * **scm** (`dict`)
            :scm:
                * **match-type** ('str'): Jobs that match a filter to include.
                  (default includeMatched)
                * **scm-type** ('str'): Type of SCM.
                  (default hudson.scm.NullSCM)

        * **secured-job** (`dict`)
            :secured-job:
                * **match-type** ('str'): Jobs that match a filter
                  to include. (default includeMatched)

        * **user-permissions** (`dict`)
            :user-permissions:
                * **match-type** ('str'): Jobs that match a filter to include.
                  (default includeMatched)
                * **configure** ('bool'): User with configure permissions.
                  (default false)
                * **amount-type**: ('bool'): User with build permissions.
                  (default false)
                * **amount**: ('bool'): User with workspace permissions.
                  (default false)
                * **permission-check**: ('str'): Match user permissions.
                  (default MustMatchAll)

        * **upstream-downstream** (`dict`)
            :upstream-downstream:
                * **include-upstream** ('bool'): Jobs that match upstream.
                  (default False)
                * **include-downstream** ('bool'): Jobs that match downstream.
                  (default False)
                * **recursive** ('bool'): Jobs that are recursive.
                  (default False)
                * **exclude-originals** ('bool'): Jobs that are originals.
                  (default False)

        * **unclassified** (`dict`)
            :unclassified:
                * **match-type** ('str'): Jobs that match a filter to include.
                  (default includeMatched)

    * **columns** (`list`): List of columns to be shown in view.
    * **regex** (`str`): . Regular expression for selecting jobs
      (optional)
    * **recurse** (`bool`): Recurse in subfolders.(default false)
    * **status-filter** (`bool`): Filter job list by enabled/disabled
      status. (optional)

Example:

    .. literalinclude::
        /../../tests/views/fixtures/view_list001.yaml

Example:

    .. literalinclude::
        /../../tests/views/fixtures/view_list002.yaml
"""

import xml.etree.ElementTree as XML
import jenkins_jobs.modules.base
import jenkins_jobs.modules.helpers as helpers
import jenkins_jobs.modules.view_jobfilters as view_jobfilters

COLUMN_DICT = {
    'status': 'hudson.views.StatusColumn',
    'weather': 'hudson.views.WeatherColumn',
    'job': 'hudson.views.JobColumn',
    'last-success': 'hudson.views.LastSuccessColumn',
    'last-failure': 'hudson.views.LastFailureColumn',
    'last-duration': 'hudson.views.LastDurationColumn',
    'build-button': 'hudson.views.BuildButtonColumn',
    'last-stable': 'hudson.views.LastStableColumn',
    'robot-list': 'hudson.plugins.robot.view.RobotListViewColumn',
    'find-bugs': 'hudson.plugins.findbugs.FindBugsColumn',
    'jacoco': 'hudson.plugins.jacococoveragecolumn.JaCoCoColumn',
    'git-branch': 'hudson.plugins.git.GitBranchSpecifierColumn',
    'schedule-build':
        'org.jenkinsci.plugins.schedulebuild.ScheduleBuildButtonColumn',
    'priority-sorter': 'jenkins.advancedqueue.PrioritySorterJobColumn',
    'build-filter': 'hudson.views.BuildFilterColumn',
    'desc': 'jenkins.branch.DescriptionColumn',
    'policy-violations':
        'com.sonatype.insight.ci.hudson.QualityColumn '
        'plugin="sonatype-clm-ci"',
    'member-graph-view':
        'com.barchart.jenkins.cascade.GraphViewColumn '
        'plugin="maven-release-cascade"',
    'extra-tests-total': [
        ['jenkins.plugins.extracolumns.TestResultColumn',
         {'plugin': 'extra-columns'}],
        '<testResultFormat>2</testResultFormat>'],
    'extra-tests-failed': [
        ['jenkins.plugins.extracolumns.TestResultColumn',
         {'plugin': 'extra-columns'}],
        '<testResultFormat>3</testResultFormat>'],
    'extra-tests-passed': [
        ['jenkins.plugins.extracolumns.TestResultColumn',
         {'plugin': 'extra-columns'}],
        '<testResultFormat>4</testResultFormat>'],
    'extra-tests-skipped': [
        ['jenkins.plugins.extracolumns.TestResultColumn',
         {'plugin': 'extra-columns'}],
        '<testResultFormat>5</testResultFormat>'],
    'extra-tests-format-0': [
        ['jenkins.plugins.extracolumns.TestResultColumn',
         {'plugin': 'extra-columns'}],
        '<testResultFormat>0</testResultFormat>'],
    'extra-tests-format-1': [
        ['jenkins.plugins.extracolumns.TestResultColumn',
         {'plugin': 'extra-columns'}],
        '<testResultFormat>1</testResultFormat>'],
    'extra-build-description': [
        ['jenkins.plugins.extracolumns.BuildDescriptionColumn',
         {'plugin': 'extra-columns'}],
        '<columnWidth>3</columnWidth>', '<forceWidth>false</forceWidth>'],
    'extra-build-parameters': [
        ['jenkins.plugins.extracolumns.BuildParametersColumn',
         {'plugin': 'extra-columns'}],
        '<singlePara>false</singlePara>', '<parameterName/>'],
    'extra-last-user-name':
        'jenkins.plugins.extracolumns.UserNameColumn'
        ' plugin="extra-columns"',
    'extra-last-output':
        'jenkins.plugins.extracolumns.LastBuildConsoleColumn'
        ' plugin="extra-columns"',
    'extra-workspace-link':
        'jenkins.plugins.extracolumns.WorkspaceColumn '
        'plugin="extra-columns"',
    'extra-configure-button':
        'jenkins.plugins.extracolumns.ConfigureProjectColumn'
        ' plugin="extra-columns"',
}
DEFAULT_COLUMNS = ['status', 'weather', 'job', 'last-success', 'last-failure',
                   'last-duration', 'build-button']


class List(jenkins_jobs.modules.base.Base):
    sequence = 0

    def root_xml(self, data):
        root = XML.Element('hudson.model.ListView')

        mapping = [
            ('name', 'name', None),
            ('description', 'description', ''),
            ('filter-executors', 'filterExecutors', False),
            ('filter-queue', 'filterQueue', False),
        ]
        helpers.convert_mapping_to_xml(root, data, mapping, fail_required=True)

        XML.SubElement(root, 'properties',
                       {'class': 'hudson.model.View$PropertyList'})

        jn_xml = XML.SubElement(root, 'jobNames')
        jobnames = data.get('job-name', None)
        XML.SubElement(
            jn_xml,
            'comparator', {
                'class': 'hudson.util.CaseInsensitiveComparator'
            }
        )
        if jobnames is not None:
            # Job names must be sorted in the xml
            jobnames = sorted(jobnames, key=str.lower)
            for jobname in jobnames:
                XML.SubElement(jn_xml, 'string').text = str(jobname)

        job_filter_xml = XML.SubElement(root, 'jobFilters')
        jobfilters = data.get('job-filters', [])

        for jobfilter in jobfilters:
            filter = getattr(view_jobfilters, jobfilter.replace('-', '_'))
            filter(job_filter_xml, jobfilters.get(jobfilter))

        c_xml = XML.SubElement(root, 'columns')
        columns = data.get('columns', DEFAULT_COLUMNS)

        for column in columns:
            if isinstance(column, dict):
                if 'extra-build-parameter' in column:
                    p_name = column['extra-build-parameter']
                    x = XML.SubElement(
                        c_xml,
                        'jenkins.plugins.extracolumns.BuildParametersColumn',
                        plugin='extra-columns'
                    )
                    x.append(XML.fromstring(
                        '<singlePara>true</singlePara>'))
                    x.append(XML.fromstring(
                        '<parameterName>%s</parameterName>' % p_name))
            else:
                if column in COLUMN_DICT:
                    if isinstance(COLUMN_DICT[column], list):
                        x = XML.SubElement(c_xml, COLUMN_DICT[column][0][0],
                                           **COLUMN_DICT[column][0][1])
                        for tag in COLUMN_DICT[column][1:]:
                            x.append(XML.fromstring(tag))
                    else:
                        XML.SubElement(c_xml, COLUMN_DICT[column])
        mapping = [
            ('regex', 'includeRegex', None),
            ('recurse', 'recurse', False),
            ('status-filter', 'statusFilter', None),
        ]
        helpers.convert_mapping_to_xml(
            root, data, mapping, fail_required=False)

        return root
