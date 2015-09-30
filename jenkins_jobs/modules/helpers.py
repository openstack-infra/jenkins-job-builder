# Copyright 2015 Thanh Ha
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

import xml.etree.ElementTree as XML
import logging

from six.moves import configparser
from jenkins_jobs.errors import (JenkinsJobsException,
                                 MissingAttributeError,
                                 InvalidAttributeError)


def build_trends_publisher(plugin_name, xml_element, data):
    """Helper to create various trend publishers.
    """

    def append_thresholds(element, data, only_totals):
        """Appends the status thresholds.
        """

        for status in ['unstable', 'failed']:
            status_data = data.get(status, {})

            limits = [
                ('total-all', 'TotalAll'),
                ('total-high', 'TotalHigh'),
                ('total-normal', 'TotalNormal'),
                ('total-low', 'TotalLow')]

            if only_totals is False:
                limits.extend([
                    ('new-all', 'NewAll'),
                    ('new-high', 'NewHigh'),
                    ('new-normal', 'NewNormal'),
                    ('new-low', 'NewLow')])

            for key, tag_suffix in limits:
                tag_name = status + tag_suffix
                XML.SubElement(element, tag_name).text = str(
                    status_data.get(key, ''))

    # Tuples containing: setting name, tag name, default value
    settings = [
        ('healthy', 'healthy', ''),
        ('unhealthy', 'unHealthy', ''),
        ('health-threshold', 'thresholdLimit', 'low'),
        ('plugin-name', 'pluginName', plugin_name),
        ('default-encoding', 'defaultEncoding', ''),
        ('can-run-on-failed', 'canRunOnFailed', False),
        ('use-stable-build-as-reference', 'useStableBuildAsReference', False),
        ('use-delta-values', 'useDeltaValues', False),
        ('thresholds', 'thresholds', {}),
        ('should-detect-modules', 'shouldDetectModules', False),
        ('dont-compute-new', 'dontComputeNew', True),
        ('do-not-resolve-relative-paths', 'doNotResolveRelativePaths', False),
        ('pattern', 'pattern', '')]

    thresholds = ['low', 'normal', 'high']

    for key, tag_name, default in settings:
        xml_config = XML.SubElement(xml_element, tag_name)
        config_value = data.get(key, default)

        if key == 'thresholds':
            append_thresholds(
                xml_config,
                config_value,
                data.get('dont-compute-new', True))
        elif key == 'health-threshold' and config_value not in thresholds:
            raise JenkinsJobsException("health-threshold must be one of %s" %
                                       ", ".join(thresholds))
        else:
            if isinstance(default, bool):
                xml_config.text = str(config_value).lower()
            else:
                xml_config.text = str(config_value)


def config_file_provider_builder(xml_parent, data):
    """Builder / Wrapper helper"""
    xml_files = XML.SubElement(xml_parent, 'managedFiles')

    files = data.get('files', [])
    for file in files:
        xml_file = XML.SubElement(xml_files, 'org.jenkinsci.plugins.'
                                  'configfiles.buildwrapper.ManagedFile')
        file_id = file.get('file-id')
        if file_id is None:
            raise JenkinsJobsException("file-id is required for each "
                                       "managed configuration file")
        XML.SubElement(xml_file, 'fileId').text = str(file_id)
        XML.SubElement(xml_file, 'targetLocation').text = file.get(
            'target', '')
        XML.SubElement(xml_file, 'variable').text = file.get(
            'variable', '')


def config_file_provider_settings(xml_parent, data):
    settings = {
        'default-settings':
        'jenkins.mvn.DefaultSettingsProvider',
        'settings':
        'jenkins.mvn.FilePathSettingsProvider',
        'config-file-provider-settings':
        'org.jenkinsci.plugins.configfiles.maven.job.MvnSettingsProvider',
        'default-global-settings':
        'jenkins.mvn.DefaultGlobalSettingsProvider',
        'global-settings':
        'jenkins.mvn.FilePathGlobalSettingsProvider',
        'config-file-provider-global-settings':
        'org.jenkinsci.plugins.configfiles.maven.job.'
        'MvnGlobalSettingsProvider',
    }

    if 'settings' in data:
        # Support for Config File Provider
        settings_file = str(data['settings'])
        if settings_file.startswith(
            'org.jenkinsci.plugins.configfiles.maven.MavenSettingsConfig'):
            lsettings = XML.SubElement(
                xml_parent, 'settings',
                {'class': settings['config-file-provider-settings']})
            XML.SubElement(lsettings, 'settingsConfigId').text = settings_file
        else:
            lsettings = XML.SubElement(
                xml_parent, 'settings',
                {'class': settings['settings']})
            XML.SubElement(lsettings, 'path').text = settings_file
    else:
        XML.SubElement(xml_parent, 'settings',
                       {'class': settings['default-settings']})

    if 'global-settings' in data:
        # Support for Config File Provider
        global_settings_file = str(data['global-settings'])
        if global_settings_file.startswith(
                'org.jenkinsci.plugins.configfiles.maven.'
                'GlobalMavenSettingsConfig'):
            gsettings = XML.SubElement(
                xml_parent, 'globalSettings',
                {'class': settings['config-file-provider-global-settings']})
            XML.SubElement(
                gsettings,
                'settingsConfigId').text = global_settings_file
        else:
            gsettings = XML.SubElement(xml_parent, 'globalSettings',
                                       {'class': settings['global-settings']})
            XML.SubElement(gsettings, 'path').text = global_settings_file
    else:
        XML.SubElement(xml_parent, 'globalSettings',
                       {'class': settings['default-global-settings']})


def copyartifact_build_selector(xml_parent, data, select_tag='selector'):

    select = data.get('which-build', 'last-successful')
    selectdict = {'last-successful': 'StatusBuildSelector',
                  'last-completed': 'LastCompletedBuildSelector',
                  'specific-build': 'SpecificBuildSelector',
                  'last-saved': 'SavedBuildSelector',
                  'upstream-build': 'TriggeredBuildSelector',
                  'permalink': 'PermalinkBuildSelector',
                  'workspace-latest': 'WorkspaceSelector',
                  'build-param': 'ParameterizedBuildSelector'}
    if select not in selectdict:
        raise InvalidAttributeError('which-build',
                                    select,
                                    selectdict.keys())
    permalink = data.get('permalink', 'last')
    permalinkdict = {'last': 'lastBuild',
                     'last-stable': 'lastStableBuild',
                     'last-successful': 'lastSuccessfulBuild',
                     'last-failed': 'lastFailedBuild',
                     'last-unstable': 'lastUnstableBuild',
                     'last-unsuccessful': 'lastUnsuccessfulBuild'}
    if permalink not in permalinkdict:
        raise InvalidAttributeError('permalink',
                                    permalink,
                                    permalinkdict.keys())
    selector = XML.SubElement(xml_parent, select_tag,
                              {'class': 'hudson.plugins.copyartifact.' +
                               selectdict[select]})
    if select == 'specific-build':
        XML.SubElement(selector, 'buildNumber').text = data['build-number']
    if select == 'last-successful':
        XML.SubElement(selector, 'stable').text = str(
            data.get('stable', False)).lower()
    if select == 'upstream-build':
        XML.SubElement(selector, 'fallbackToLastSuccessful').text = str(
            data.get('fallback-to-last-successful', False)).lower()
    if select == 'permalink':
        XML.SubElement(selector, 'id').text = permalinkdict[permalink]
    if select == 'build-param':
        XML.SubElement(selector, 'parameterName').text = data['param']


def findbugs_settings(xml_parent, data):
    # General Options
    rank_priority = str(data.get('rank-priority', False)).lower()
    XML.SubElement(xml_parent, 'isRankActivated').text = rank_priority
    include_files = data.get('include-files', '')
    XML.SubElement(xml_parent, 'includePattern').text = include_files
    exclude_files = data.get('exclude-files', '')
    XML.SubElement(xml_parent, 'excludePattern').text = exclude_files
    use_previous_build = str(data.get('use-previous-build-as-reference',
                                      False)).lower()
    XML.SubElement(xml_parent,
                   'usePreviousBuildAsReference').text = use_previous_build


def get_value_from_yaml_or_config_file(key, section, data, parser):
    logger = logging.getLogger(__name__)
    result = data.get(key, '')
    if result == '':
        try:
            result = parser.config.get(
                section, key
            )
        except (configparser.NoSectionError, configparser.NoOptionError,
                JenkinsJobsException) as e:
            logger.warning("You didn't set a " + key +
                           " neither in the yaml job definition nor in" +
                           " the " + section + " section, blank default" +
                           " value will be applied:\n{0}".format(e))
    return result


def cloudformation_region_dict():
    region_dict = {'us-east-1': 'US_East_Northern_Virginia',
                   'us-west-1': 'US_WEST_Northern_California',
                   'us-west-2': 'US_WEST_Oregon',
                   'eu-central-1': 'EU_Frankfurt',
                   'eu-west-1': 'EU_Ireland',
                   'ap-southeast-1': 'Asia_Pacific_Singapore',
                   'ap-southeast-2': 'Asia_Pacific_Sydney',
                   'ap-northeast-1': 'Asia_Pacific_Tokyo',
                   'sa-east-1': 'South_America_Sao_Paulo'}
    return region_dict


def cloudformation_init(xml_parent, data, xml_tag):
    cloudformation = XML.SubElement(
        xml_parent, 'com.syncapse.jenkinsci.'
                    'plugins.awscloudformationwrapper.' + xml_tag)
    return XML.SubElement(cloudformation, 'stacks')


def cloudformation_stack(xml_parent, stack, xml_tag, stacks, region_dict):
    if 'name' not in stack or stack['name'] == '':
        raise MissingAttributeError('name')
    step = XML.SubElement(
        stacks, 'com.syncapse.jenkinsci.plugins.'
                'awscloudformationwrapper.' + xml_tag)
    try:
        XML.SubElement(step, 'stackName').text = stack['name']
        XML.SubElement(step, 'awsAccessKey').text = stack['access-key']
        XML.SubElement(step, 'awsSecretKey').text = stack['secret-key']
        region = stack['region']
    except KeyError as e:
        raise MissingAttributeError(e.args[0])
    if region not in region_dict:
        raise InvalidAttributeError('region', region, region_dict.keys())
    XML.SubElement(step, 'awsRegion').text = region_dict.get(region)
    if xml_tag == 'SimpleStackBean':
        prefix = str(stack.get('prefix', False)).lower()
        XML.SubElement(step, 'isPrefixSelected').text = prefix
    else:
        XML.SubElement(step, 'description').text = stack.get('description', '')
        XML.SubElement(step, 'parameters').text = ','.join(
            stack.get('parameters', []))
        XML.SubElement(step, 'timeout').text = str(stack.get('timeout', '0'))
        XML.SubElement(step, 'sleep').text = str(stack.get('sleep', '0'))
        try:
            XML.SubElement(step, 'cloudFormationRecipe').text = stack['recipe']
        except KeyError as e:
            raise MissingAttributeError(e.args[0])


def include_exclude_patterns(xml_parent, data, yaml_prefix,
                             xml_elem_name):
    xml_element = XML.SubElement(xml_parent, xml_elem_name)
    XML.SubElement(xml_element, 'includePatterns').text = ','.join(
        data.get(yaml_prefix + '-include-patterns', []))
    XML.SubElement(xml_element, 'excludePatterns').text = ','.join(
        data.get(yaml_prefix + '-exclude-patterns', []))


def artifactory_deployment_patterns(xml_parent, data):
    include_exclude_patterns(xml_parent, data, 'deployment',
                             'artifactDeploymentPatterns')


def artifactory_env_vars_patterns(xml_parent, data):
    include_exclude_patterns(xml_parent, data, 'env-vars',
                             'envVarsPatterns')


def artifactory_optional_props(xml_parent, data, target):
    optional_str_props = [
        ('scopes', 'scopes'),
        ('violationRecipients', 'violation-recipients'),
        ('blackDuckAppName', 'black-duck-app-name'),
        ('blackDuckAppVersion', 'black-duck-app-version'),
        ('blackDuckReportRecipients', 'black-duck-report-recipients'),
        ('blackDuckScopes', 'black-duck-scopes')
    ]

    for (xml_prop, yaml_prop) in optional_str_props:
        XML.SubElement(xml_parent, xml_prop).text = data.get(
            yaml_prop, '')

    common_bool_props = [
        # xml property name, yaml property name, default value
        ('deployArtifacts', 'deploy-artifacts', True),
        ('discardOldBuilds', 'discard-old-builds', False),
        ('discardBuildArtifacts', 'discard-build-artifacts', False),
        ('deployBuildInfo', 'publish-build-info', False),
        ('includeEnvVars', 'env-vars-include', False),
        ('runChecks', 'run-checks', False),
        ('includePublishArtifacts', 'include-publish-artifacts', False),
        ('licenseAutoDiscovery', 'license-auto-discovery', True),
        ('enableIssueTrackerIntegration', 'enable-issue-tracker-integration',
            False),
        ('aggregateBuildIssues', 'aggregate-build-issues', False),
        ('blackDuckRunChecks', 'black-duck-run-checks', False),
        ('blackDuckIncludePublishedArtifacts',
            'black-duck-include-published-artifacts', False),
        ('autoCreateMissingComponentRequests',
            'auto-create-missing-component-requests', True),
        ('autoDiscardStaleComponentRequests',
            'auto-discard-stale-component-requests', True),
        ('filterExcludedArtifactsFromBuild',
            'filter-excluded-artifacts-from-build', False)
    ]

    for (xml_prop, yaml_prop, default_value) in common_bool_props:
        XML.SubElement(xml_parent, xml_prop).text = str(data.get(
            yaml_prop, default_value)).lower()

    if 'wrappers' in target:
        wrapper_bool_props = [
            ('enableResolveArtifacts', 'enable-resolve-artifacts', False),
            ('disableLicenseAutoDiscovery',
                'disable-license-auto-discovery', False),
            ('recordAllDependencies',
                'record-all-dependencies', False)
        ]

        for (xml_prop, yaml_prop, default_value) in wrapper_bool_props:
            XML.SubElement(xml_parent, xml_prop).text = str(data.get(
                yaml_prop, default_value)).lower()

    if 'publishers' in target:
        publisher_bool_props = [
            ('evenIfUnstable', 'even-if-unstable', False),
            ('passIdentifiedDownstream', 'pass-identified-downstream', False),
            ('allowPromotionOfNonStagedBuilds',
                'allow-promotion-of-non-staged-builds', False)
        ]

        for (xml_prop, yaml_prop, default_value) in publisher_bool_props:
            XML.SubElement(xml_parent, xml_prop).text = str(data.get(
                yaml_prop, default_value)).lower()


def artifactory_common_details(details, data):
    XML.SubElement(details, 'artifactoryName').text = data.get('name', '')
    XML.SubElement(details, 'artifactoryUrl').text = data.get('url', '')


def artifactory_repository(xml_parent, data, target):
    if 'release' in target:
        XML.SubElement(xml_parent, 'keyFromText').text = data.get(
            'deploy-release-repo-key', '')
        XML.SubElement(xml_parent, 'keyFromSelect').text = data.get(
            'deploy-release-repo-key', '')
        XML.SubElement(xml_parent, 'dynamicMode').text = str(
            data.get('deploy-dynamic-mode', False)).lower()

    if 'snapshot' in target:
        XML.SubElement(xml_parent, 'keyFromText').text = data.get(
            'deploy-snapshot-repo-key', '')
        XML.SubElement(xml_parent, 'keyFromSelect').text = data.get(
            'deploy-snapshot-repo-key', '')
        XML.SubElement(xml_parent, 'dynamicMode').text = str(
            data.get('deploy-dynamic-mode', False)).lower()
