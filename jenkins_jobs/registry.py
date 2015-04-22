#!/usr/bin/env python
# Copyright (C) 2015 OpenStack, LLC.
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

# Manage Jenkins plugin module registry.

import logging
import operator
import pkg_resources
import re
import yaml

from jenkins_jobs.errors import JenkinsJobsException
from jenkins_jobs.formatter import CustomFormatter

logger = logging.getLogger(__name__)


class ModuleRegistry(object):
    entry_points_cache = {}

    def __init__(self, config, plugins_list=None):
        self.modules = []
        self.modules_by_component_type = {}
        self.handlers = {}
        self.global_config = config

        if plugins_list is None:
            self.plugins_dict = {}
        else:
            self.plugins_dict = self._get_plugins_info_dict(plugins_list)

        for entrypoint in pkg_resources.iter_entry_points(
                group='jenkins_jobs.modules'):
            Mod = entrypoint.load()
            mod = Mod(self)
            self.modules.append(mod)
            self.modules.sort(key=operator.attrgetter('sequence'))
            if mod.component_type is not None:
                self.modules_by_component_type[mod.component_type] = mod

    @staticmethod
    def _get_plugins_info_dict(plugins_list):
        def mutate_plugin_info(plugin_info):
            """
            We perform mutations on a single member of plugin_info here, then
            return a dictionary with the longName and shortName of the plugin
            mapped to its plugin info dictionary.
            """
            version = plugin_info.get('version', '0')
            plugin_info['version'] = re.sub(r'(.*)-(?:SNAPSHOT|BETA)',
                                            r'\g<1>.preview', version)

            aliases = []
            for key in ['longName', 'shortName']:
                value = plugin_info.get(key, None)
                if value is not None:
                    aliases.append(value)

            plugin_info_dict = {}
            for name in aliases:
                plugin_info_dict[name] = plugin_info

            return plugin_info_dict

        list_of_dicts = [mutate_plugin_info(v) for v in plugins_list]

        plugins_info_dict = {}
        for d in list_of_dicts:
            plugins_info_dict.update(d)

        return plugins_info_dict

    def get_plugin_info(self, plugin_name):
        """ This method is intended to provide information about plugins within
        a given module's implementation of Base.gen_xml. The return value is a
        dictionary with data obtained directly from a running Jenkins instance.
        This allows module authors to differentiate generated XML output based
        on information such as specific plugin versions.

        :arg string plugin_name: Either the shortName or longName of a plugin
          as see in a query that looks like:
          ``http://<jenkins-hostname>/pluginManager/api/json?pretty&depth=2``

        During a 'test' run, it is possible to override JJB's query to a live
        Jenkins instance by passing it a path to a file containing a YAML list
        of dictionaries that mimics the plugin properties you want your test
        output to reflect::

          jenkins-jobs test -p /path/to/plugins-info.yaml

        Below is example YAML that might be included in
        /path/to/plugins-info.yaml.

        .. literalinclude:: /../../tests/cmd/fixtures/plugins-info.yaml

        """
        return self.plugins_dict.get(plugin_name, {})

    def registerHandler(self, category, name, method):
        cat_dict = self.handlers.get(category, {})
        if not cat_dict:
            self.handlers[category] = cat_dict
        cat_dict[name] = method

    def getHandler(self, category, name):
        return self.handlers[category][name]

    def dispatch(self, component_type,
                 parser, xml_parent,
                 component, template_data={}):
        """This is a method that you can call from your implementation of
        Base.gen_xml or component.  It allows modules to define a type
        of component, and benefit from extensibility via Python
        entry points and Jenkins Job Builder :ref:`Macros <macro>`.

        :arg string component_type: the name of the component
          (e.g., `builder`)
        :arg YAMLParser parser: the global YAML Parser
        :arg Element xml_parent: the parent XML element
        :arg dict template_data: values that should be interpolated into
          the component definition

        See :py:class:`jenkins_jobs.modules.base.Base` for how to register
        components of a module.

        See the Publishers module for a simple example of how to use
        this method.
        """

        if component_type not in self.modules_by_component_type:
            raise JenkinsJobsException("Unknown component type: "
                                       "'{0}'.".format(component_type))

        component_list_type = self.modules_by_component_type[component_type] \
            .component_list_type

        if isinstance(component, dict):
            # The component is a singleton dictionary of name: dict(args)
            name, component_data = next(iter(component.items()))
            if template_data:
                # Template data contains values that should be interpolated
                # into the component definition
                s = yaml.dump(component_data, default_flow_style=False)
                allow_empty_variables = self.global_config \
                    and self.global_config.has_section('job_builder') \
                    and self.global_config.has_option(
                        'job_builder', 'allow_empty_variables') \
                    and self.global_config.getboolean(
                        'job_builder', 'allow_empty_variables')
                s = CustomFormatter(
                    allow_empty_variables).format(s, **template_data)
                component_data = yaml.load(s)
        else:
            # The component is a simple string name, eg "run-tests"
            name = component
            component_data = {}

        # Look for a component function defined in an entry point
        eps = ModuleRegistry.entry_points_cache.get(component_list_type)
        if eps is None:
            module_eps = list(pkg_resources.iter_entry_points(
                group='jenkins_jobs.{0}'.format(component_list_type)))
            eps = {}
            for module_ep in module_eps:
                if module_ep.name in eps:
                    raise JenkinsJobsException(
                        "Duplicate entry point found for component type: "
                        "'{0}', '{0}',"
                        "name: '{1}'".format(component_type, name))
                eps[module_ep.name] = module_ep

            ModuleRegistry.entry_points_cache[component_list_type] = eps
            logger.debug("Cached entry point group %s = %s",
                         component_list_type, eps)

        if name in eps:
            func = eps[name].load()
            func(parser, xml_parent, component_data)
        else:
            # Otherwise, see if it's defined as a macro
            component = parser.data.get(component_type, {}).get(name)
            if component:
                for b in component[component_list_type]:
                    # Pass component_data in as template data to this function
                    # so that if the macro is invoked with arguments,
                    # the arguments are interpolated into the real defn.
                    self.dispatch(component_type,
                                  parser, xml_parent, b, component_data)
            else:
                raise JenkinsJobsException("Unknown entry point or macro '{0}'"
                                           " for component type: '{1}'.".
                                           format(name, component_type))
