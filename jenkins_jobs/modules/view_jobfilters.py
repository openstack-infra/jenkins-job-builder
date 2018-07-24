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
import jenkins_jobs.modules.helpers as helpers


def build_duration(xml_parent, data):
    xml = XML.SubElement(xml_parent, 'hudson.views.BuildDurationFilter')
    xml.set('plugin', 'view-job-filters')
    mapping = [
        ('match-type', 'includeExcludeTypeString', 'includeMatched'),
        ('build-duration-type', 'buildCountTypeString', 'Latest'),
        ('amount-type', 'amountTypeString', 'Hours'),
        ('amount', 'amount', '0'),
        ('less-than', 'lessThan', True),
        ('build-duration-minutes', 'buildDurationMinutes', '0'),
    ]
    helpers.convert_mapping_to_xml(xml, data, mapping, fail_required=True)


def build_status(xml_parent, data):
    xml = XML.SubElement(xml_parent, 'hudson.views.BuildStatusFilter')
    xml.set('plugin', 'view-job-filters')
    mapping = [
        ('match-type', 'includeExcludeTypeString', 'includeMatched'),
        ('never-built', 'neverBuilt', False),
        ('building', 'building', False),
        ('in-build-queue', 'inBuildQueue', False),
    ]
    helpers.convert_mapping_to_xml(xml, data, mapping, fail_required=True)


def build_trend(xml_parent, data):
    xml = XML.SubElement(xml_parent, 'hudson.views.BuildTrendFilter')
    xml.set('plugin', 'view-job-filters')
    mapping = [
        ('match-type', 'includeExcludeTypeString', 'includeMatched'),
        ('build-trend-type', 'buildCountTypeString', 'Latest'),
        ('amount-type', 'amountTypeString', 'Hours'),
        ('amount', 'amount', '0'),
        ('status', 'statusTypeString', 'Completed'),
    ]
    helpers.convert_mapping_to_xml(xml, data, mapping, fail_required=True)


def fallback(xml_parent, data):
    xml = XML.SubElement(xml_parent, 'hudson.views.AddRemoveFallbackFilter')
    xml.set('plugin', 'view-job-filters')
    mapping = [
        ('fallback-type', 'fallbackTypeString', 'REMOVE_ALL_IF_ALL_INCLUDED'),
        ('fallback-type', 'fallbackType', 'REMOVE_ALL_IF_ALL_INCLUDED'),
    ]
    helpers.convert_mapping_to_xml(xml, data, mapping, fail_required=True)


def job_status(xml_parent, data):
    xml = XML.SubElement(xml_parent, 'hudson.views.JobStatusFilter')
    xml.set('plugin', 'view-job-filters')
    mapping = [
        ('match-type', 'includeExcludeTypeString', 'includeMatched'),
        ('unstable', 'unstable', False),
        ('failed', 'failed', False),
        ('aborted', 'aborted', False),
        ('disabled', 'disabled', False),
        ('stable', 'stable', False),
    ]
    helpers.convert_mapping_to_xml(xml, data, mapping, fail_required=True)


def job_type(xml_parent, data):
    xml = XML.SubElement(xml_parent, 'hudson.views.JobTypeFilter')
    xml.set('plugin', 'view-job-filters')
    mapping = [
        ('match-type', 'includeExcludeTypeString', 'includeMatched'),
        ('job-type', 'jobType', 'hudson.model.FreeStyleProject'),
    ]
    helpers.convert_mapping_to_xml(xml, data, mapping, fail_required=True)


def most_recent(xml_parent, data):
    xml = XML.SubElement(xml_parent, 'hudson.views.MostRecentJobsFilter')
    xml.set('plugin', 'view-job-filters')
    mapping = [
        ('max-to-include', 'maxToInclude', '0'),
        ('check-start-time', 'checkStartTime', False),
    ]
    helpers.convert_mapping_to_xml(xml, data, mapping, fail_required=True)


def other_views(xml_parent, data):
    xml = XML.SubElement(xml_parent, 'hudson.views.OtherViewsFilter')
    xml.set('plugin', 'view-job-filters')
    mapping = [
        ('match-type', 'includeExcludeTypeString', 'includeMatched'),
        ('view-name', 'otherViewName',
         '&lt;select a view other than this one&gt;'),
    ]
    helpers.convert_mapping_to_xml(xml, data, mapping, fail_required=True)


def parameter(xml_parent, data):
    xml = XML.SubElement(xml_parent, 'hudson.views.ParameterFilter')
    xml.set('plugin', 'view-job-filters')
    mapping = [
        ('match-type', 'includeExcludeTypeString', 'includeMatched'),
        ('name', 'nameRegex', ''),
        ('value', 'valueRegex', ''),
        ('description', 'descriptionRegex', ''),
        ('use-default', 'useDefaultValue', False),
        ('match-builds-in-progress', 'matchBuildsInProgress', False),
        ('match-all-builds', 'matchAllBuilds', False),
        ('max-builds-to-match', 'maxBuildsToMatch', 0),
    ]
    helpers.convert_mapping_to_xml(xml, data, mapping, fail_required=True)


def scm(xml_parent, data):
    xml = XML.SubElement(xml_parent, 'hudson.views.ScmTypeFilter')
    xml.set('plugin', 'view-job-filters')
    mapping = [
        ('match-type', 'includeExcludeTypeString', 'includeMatched'),
        ('scm-type', 'scmType', 'hudson.scm.NullSCM'),
    ]
    helpers.convert_mapping_to_xml(xml, data, mapping, fail_required=True)


def secured_job(xml_parent, data):
    xml = XML.SubElement(xml_parent, 'hudson.views.SecuredJobsFilter')
    xml.set('plugin', 'view-job-filters')
    mapping = [
        ('match-type', 'includeExcludeTypeString', 'includeMatched'),
    ]
    helpers.convert_mapping_to_xml(xml, data, mapping, fail_required=True)


def regex_job(xml_parent, data):
    xml = XML.SubElement(xml_parent, 'hudson.views.RegExJobFilter')
    xml.set('plugin', 'view-job-filters')
    mapping = [
        ('match-type', 'includeExcludeTypeString', 'includeMatched'),
        ('regex-name', 'valueTypeString', ''),
        ('regex', 'regex', ''),
    ]
    helpers.convert_mapping_to_xml(xml, data, mapping, fail_required=True)


def unclassified(xml_parent, data):
    xml = XML.SubElement(xml_parent, 'hudson.views.UnclassifiedJobsFilter')
    xml.set('plugin', 'view-job-filters')
    mapping = [
        ('match-type', 'includeExcludeTypeString', 'includeMatched'),
    ]
    helpers.convert_mapping_to_xml(xml, data, mapping, fail_required=True)


def upstream_downstream(xml_parent, data):
    xml = XML.SubElement(
        xml_parent, 'hudson.views.UpstreamDownstreamJobsFilter')
    xml.set('plugin', 'view-job-filters')
    mapping = [
        ('include-upstream', 'includeUpstream', False),
        ('include-downstream', 'includeDownstream', False),
        ('recursive', 'recursive', False),
        ('exclude-originals', 'excludeOriginals', False),
    ]
    helpers.convert_mapping_to_xml(xml, data, mapping, fail_required=True)


def user_permissions(xml_parent, data):
    xml = XML.SubElement(xml_parent, 'hudson.views.SecurityFilter')
    xml.set('plugin', 'view-job-filters')
    mapping = [
        ('match-type', 'includeExcludeTypeString', 'includeMatched'),
        ('configure', 'configure', False),
        ('build', 'build', False),
        ('workspace', 'workspace', False),
        ('permission-check', 'permissionCheckType', 'MustMatchAll'),
    ]
    helpers.convert_mapping_to_xml(xml, data, mapping, fail_required=True)


def user_relevence(xml_parent, data):
    xml = XML.SubElement(xml_parent, 'hudson.views.UserRelevanceFilter')
    xml.set('plugin', 'view-job-filters')
    mapping = [
        ('match-type', 'includeExcludeTypeString', 'includeMatched'),
        ('build-count', 'buildCountTypeString', 'AtLeastOne'),
        ('amount-type', 'amountTypeString', 'Hours'),
        ('amount', 'amount', '0'),
        ('match-user-id', 'matchUserId', False),
        ('match-user-fullname', 'matchUserFullName', False),
        ('ignore-case', 'ignoreCase', False),
        ('ignore-whitespace', 'ignoreWhitespace', False),
        ('ignore-non-alphaNumeric', 'ignoreNonAlphaNumeric', False),
        ('match-builder', 'matchBuilder', False),
        ('match-email', 'matchEmail', False),
        ('match-scm-changes', 'matchScmChanges', False),
    ]
    helpers.convert_mapping_to_xml(xml, data, mapping, fail_required=True)
