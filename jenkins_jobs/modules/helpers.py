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

from jenkins_jobs.errors import JenkinsJobsException


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
