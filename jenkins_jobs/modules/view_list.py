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
            if jobfilter == 'most-recent':
                mr_xml = XML.SubElement(job_filter_xml,
                                        'hudson.views.MostRecentJobsFilter')
                mr_xml.set('plugin', 'view-job-filters')
                mr_data = jobfilters.get('most-recent')
                mapping = [
                    ('max-to-include', 'maxToInclude', '0'),
                    ('check-start-time', 'checkStartTime', False),
                ]
                helpers.convert_mapping_to_xml(mr_xml, mr_data, mapping,
                                       fail_required=True)

            if jobfilter == 'build-duration':
                bd_xml = XML.SubElement(job_filter_xml,
                                        'hudson.views.BuildDurationFilter')
                bd_xml.set('plugin', 'view-job-filters')
                bd_data = jobfilters.get('build-duration')
                mapping = [
                    ('match-type', 'includeExcludeTypeString',
                     'includeMatched'),
                    ('build-duration-type', 'buildCountTypeString', 'Latest'),
                    ('amount-type', 'amountTypeString', 'Hours'),
                    ('amount', 'amount', '0'),
                    ('less-than', 'lessThan', True),
                    ('build-duration-minutes', 'buildDurationMinutes', '0'),
                ]
                helpers.convert_mapping_to_xml(bd_xml, bd_data, mapping,
                                       fail_required=True)

            if jobfilter == 'build-trend':
                bt_xml = XML.SubElement(job_filter_xml,
                                        'hudson.views.BuildTrendFilter')
                bt_xml.set('plugin', 'view-job-filters')
                bt_data = jobfilters.get('build-trend')
                mapping = [
                    ('match-type', 'includeExcludeTypeString',
                     'includeMatched'),
                    ('build-trend-type', 'buildCountTypeString', 'Latest'),
                    ('amount-type', 'amountTypeString', 'Hours'),
                    ('amount', 'amount', '0'),
                    ('status', 'statusTypeString', 'Completed'),
                ]
                helpers.convert_mapping_to_xml(bt_xml, bt_data, mapping,
                                       fail_required=True)

            if jobfilter == 'job-status':
                js_xml = XML.SubElement(job_filter_xml,
                                        'hudson.views.JobStatusFilter')
                js_xml.set('plugin', 'view-job-filters')
                js_data = jobfilters.get('job-status')
                mapping = [
                    ('match-type', 'includeExcludeTypeString',
                     'includeMatched'),
                    ('unstable', 'unstable', False),
                    ('failed', 'failed', False),
                    ('aborted', 'aborted', False),
                    ('disabled', 'disabled', False),
                    ('stable', 'stable', False),
                ]
                helpers.convert_mapping_to_xml(js_xml, js_data, mapping,
                                       fail_required=True)

            if jobfilter == 'upstream-downstream':
                ud_xml = XML.SubElement(
                    job_filter_xml,
                    'hudson.views.UpstreamDownstreamJobsFilter'
                )
                ud_xml.set('plugin', 'view-job-filters')
                ud_data = jobfilters.get('upstream-downstream')
                mapping = [
                    ('include-upstream', 'includeUpstream',
                     False),
                    ('include-downstream', 'includeDownstream', False),
                    ('recursive', 'recursive', False),
                    ('exclude-originals', 'excludeOriginals', False),
                ]
                helpers.convert_mapping_to_xml(ud_xml, ud_data, mapping,
                                       fail_required=True)

            if jobfilter == 'fallback':
                fb_xml = XML.SubElement(
                    job_filter_xml,
                    'hudson.views.AddRemoveFallbackFilter'
                )
                fb_xml.set('plugin', 'view-job-filters')
                fb_data = jobfilters.get('fallback')
                mapping = [
                    ('fallback-type', 'fallbackTypeString',
                     'REMOVE_ALL_IF_ALL_INCLUDED'),
                    ('fallback-type', 'fallbackType',
                     'REMOVE_ALL_IF_ALL_INCLUDED'),
                ]
                helpers.convert_mapping_to_xml(fb_xml, fb_data, mapping,
                                       fail_required=True)

            if jobfilter == 'build-status':
                bs_xml = XML.SubElement(job_filter_xml,
                                        'hudson.views.BuildStatusFilter')
                bs_xml.set('plugin', 'view-job-filters')
                bs_data = jobfilters.get('build-status')
                mapping = [
                    ('match-type', 'includeExcludeTypeString',
                     'includeMatched'),
                    ('never-built', 'neverBuilt', False),
                    ('building', 'building', False),
                    ('in-build-queue', 'inBuildQueue', False),
                ]
                helpers.convert_mapping_to_xml(bs_xml, bs_data, mapping,
                                       fail_required=True)

            if jobfilter == 'user-relevence':
                ur_xml = XML.SubElement(job_filter_xml,
                                        'hudson.views.UserRelevanceFilter')
                ur_xml.set('plugin', 'view-job-filters')
                ur_data = jobfilters.get('user-relevence')
                mapping = [
                    ('match-type', 'includeExcludeTypeString',
                     'includeMatched'),
                    ('build-count', 'buildCountTypeString', 'AtLeastOne'),
                    ('amount-type', 'amountTypeString', 'Hours'),
                    ('amount', 'amount', '0'),
                    ('match-user-id', 'matchUserId', False),
                    ('match-user-fullname', 'matchUserFullName', False),
                    ('ignore-case', 'ignoreCase', False),
                    ('ignore-whitespace', 'ignoreWhitespace', False),
                    ('ignore-non-alphaNumeric', 'ignoreNonAlphaNumeric',
                     False),
                    ('match-builder', 'matchBuilder', False),
                    ('match-email', 'matchEmail', False),
                    ('match-scm-changes', 'matchScmChanges', False),
                ]
                helpers.convert_mapping_to_xml(ur_xml, ur_data, mapping,
                                       fail_required=True)

            if jobfilter == 'regex-job':
                rj_xml = XML.SubElement(job_filter_xml,
                                        'hudson.views.RegExJobFilter')
                rj_xml.set('plugin', 'view-job-filters')
                rj_data = jobfilters.get('regex-job')
                mapping = [
                    ('match-type', 'includeExcludeTypeString',
                     'includeMatched'),
                    ('regex-name', 'valueTypeString', ''),
                    ('regex', 'regex', ''),
                ]
                helpers.convert_mapping_to_xml(rj_xml, rj_data, mapping,
                                       fail_required=True)

            if jobfilter == 'job-type':
                jt_xml = XML.SubElement(job_filter_xml,
                                        'hudson.views.JobTypeFilter')
                jt_xml.set('plugin', 'view-job-filters')
                jt_data = jobfilters.get('job-type')
                mapping = [
                    ('match-type', 'includeExcludeTypeString',
                     'includeMatched'),
                    ('job-type', 'jobType', 'hudson.model.FreeStyleProject'),
                ]
                helpers.convert_mapping_to_xml(jt_xml, jt_data, mapping,
                                       fail_required=True)

            if jobfilter == 'parameter':
                pr_xml = XML.SubElement(job_filter_xml,
                                        'hudson.views.ParameterFilter')
                pr_xml.set('plugin', 'view-job-filters')
                pr_data = jobfilters.get('parameter')
                mapping = [
                    ('match-type', 'includeExcludeTypeString',
                     'includeMatched'),
                    ('name', 'nameRegex', ''),
                    ('value', 'valueRegex', ''),
                    ('description', 'descriptionRegex', ''),
                    ('use-default', 'useDefaultValue', False),
                    ('match-builds-in-progress', 'matchBuildsInProgress',
                     False),
                    ('match-all-builds', 'matchAllBuilds', False),
                    ('max-builds-to-match', 'maxBuildsToMatch', 0),
                ]
                helpers.convert_mapping_to_xml(pr_xml, pr_data, mapping,
                                       fail_required=True)

            if jobfilter == 'other-views':
                ov_xml = XML.SubElement(job_filter_xml,
                                        'hudson.views.OtherViewsFilter')
                ov_xml.set('plugin', 'view-job-filters')
                ov_data = jobfilters.get('other-views')
                mapping = [
                    ('match-type', 'includeExcludeTypeString',
                     'includeMatched'),
                    ('view-name', 'otherViewName',
                     '&lt;select a view other than this one&gt;'),
                ]
                helpers.convert_mapping_to_xml(ov_xml, ov_data, mapping,
                                       fail_required=True)

            if jobfilter == 'scm':
                st_xml = XML.SubElement(job_filter_xml,
                                        'hudson.views.ScmTypeFilter')
                st_xml.set('plugin', 'view-job-filters')
                st_data = jobfilters.get('scm')
                mapping = [
                    ('match-type', 'includeExcludeTypeString',
                     'includeMatched'),
                    ('scm-type', 'scmType', 'hudson.scm.NullSCM'),
                ]
                helpers.convert_mapping_to_xml(st_xml, st_data, mapping,
                                       fail_required=True)

            if jobfilter == 'secured-job':
                sj_xml = XML.SubElement(job_filter_xml,
                                        'hudson.views.SecuredJobsFilter')
                sj_xml.set('plugin', 'view-job-filters')
                sj_data = jobfilters.get('secured-job')
                mapping = [
                    ('match-type', 'includeExcludeTypeString',
                     'includeMatched'),
                ]
                helpers.convert_mapping_to_xml(sj_xml, sj_data, mapping,
                                       fail_required=True)

            if jobfilter == 'user-permissions':
                up_xml = XML.SubElement(job_filter_xml,
                                        'hudson.views.SecurityFilter')
                up_xml.set('plugin', 'view-job-filters')
                up_data = jobfilters.get('user-permissions')
                mapping = [
                    ('match-type', 'includeExcludeTypeString',
                     'includeMatched'),
                    ('configure', 'configure', False),
                    ('build', 'build', False),
                    ('workspace', 'workspace', False),
                    ('permission-check', 'permissionCheckType',
                     'MustMatchAll'),
                ]
                helpers.convert_mapping_to_xml(up_xml, up_data, mapping,
                                       fail_required=True)

            if jobfilter == 'unclassified':
                uc_xml = XML.SubElement(job_filter_xml,
                                        'hudson.views.UnclassifiedJobsFilter')
                uc_xml.set('plugin', 'view-job-filters')
                uc_data = jobfilters.get('unclassified')
                mapping = [
                    ('match-type', 'includeExcludeTypeString',
                     'includeMatched'),
                ]
                helpers.convert_mapping_to_xml(uc_xml, uc_data, mapping,
                                       fail_required=True)

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
