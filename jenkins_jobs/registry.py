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

import copy
import logging
import operator
import pkg_resources
import re
import types

from jenkins_jobs.errors import JenkinsJobsException
from jenkins_jobs.formatter import deep_format

__all__ = [
    "ModuleRegistry"
]

logger = logging.getLogger(__name__)


class MacroRegistry(object):

    _component_to_component_list_mapping = {}
    _component_list_to_component_mapping = {}
    _macros_by_component_type = {}
    _macros_by_component_list_type = {}

    def __init__(self):

        for entrypoint in pkg_resources.iter_entry_points(
                group='jenkins_jobs.macros'):
            Mod = entrypoint.load()
            self._component_list_to_component_mapping[
                Mod.component_list_type] = Mod.component_type
            self._component_to_component_list_mapping[
                Mod.component_type] = Mod.component_list_type
            self._macros_by_component_type[
                Mod.component_type] = {}
            self._macros_by_component_list_type[
                Mod.component_list_type] = {}

        self._mask_warned = {}

    @property
    def _nonempty_component_list_types(self):
        return [clt for clt in self._macros_by_component_list_type
                if len(self._macros_by_component_list_type[clt]) != 0]

    @property
    def component_types(self):
        return self._macros_by_component_type.keys()

    def _is_macro(self, component_name, component_list_type):
        return (component_name in
                self._macros_by_component_list_type[component_list_type])

    def register(self, component_type, macro):
        macro_name = macro["name"]
        clt = self._component_to_component_list_mapping[component_type]
        self._macros_by_component_type[component_type][macro_name] = macro
        self._macros_by_component_list_type[clt][macro_name] = macro

    def expand_macros(self, jobish, template_data=None):
        """Create a copy of the given job-like thing, expand macros in place on
        the copy, and return that object to calling context.

        :arg dict jobish: A job-like JJB data structure. Could be anything that
        might provide JJB "components" that get expanded to XML configuration.
        This includes "job", "job-template", and "default" DSL items. This
        argument is not modified in place, but rather copied so that the copy
        may be returned to calling context.

        :arg dict template_data: If jobish is a job-template, use the same
        template data used to fill in job-template variables to fill in macro
        variables.
        """
        for component_list_type in self._nonempty_component_list_types:
            self._expand_macros_for_component_list_type(
                jobish, component_list_type, template_data)

    def _expand_macros_for_component_list_type(self,
                                               jobish,
                                               component_list_type,
                                               template_data=None):
        """In-place expansion of macros on jobish.

        :arg dict jobish: A job-like JJB data structure. Could be anything that
        might provide JJB "components" that get expanded to XML configuration.
        This includes "job", "job-template", and "default" DSL items. This
        argument is not modified in place, but rather copied so that the copy
        may be returned to calling context.

        :arg str component_list_type: A string value indicating which type of
        component we are expanding macros for.

        :arg dict template_data: If jobish is a job-template, use the same
        template data used to fill in job-template variables to fill in macro
        variables.
        """
        if (jobish.get("project-type", None) == "pipeline"
                and component_list_type == "scm"):
            # Pipeline projects have an atypical scm type, eg:
            #
            # - job:
            #   name: whatever
            #   project-type: pipeline
            #   pipeline-scm:
            #     script-path: nonstandard-scriptpath.groovy
            #     scm:
            #       - macro_name
            #
            # as opposed to the more typical:
            #
            # - job:
            #   name: whatever2
            #   scm:
            #     - macro_name
            #
            # So we treat that case specially here.
            component_list = jobish.get("pipeline-scm", {}).get("scm", [])
        else:
            component_list = jobish.get(component_list_type, [])

        component_substitutions = []
        for component in component_list:
            macro_component_list = self._maybe_expand_macro(
                component, component_list_type, template_data)

            if macro_component_list is not None:
                # Since macros can contain other macros, we need to recurse
                # into the newly-expanded macro component list to expand any
                # macros that might be hiding in there. In order to do this we
                # have to make the macro component list look like a job by
                # embedding it in a dictionary like so.
                self._expand_macros_for_component_list_type(
                    {component_list_type: macro_component_list},
                    component_list_type,
                    template_data)

                component_substitutions.append(
                    (component, macro_component_list))

        for component, macro_component_list in component_substitutions:
            component_index = component_list.index(component)
            component_list.remove(component)
            i = 0
            for macro_component in macro_component_list:
                component_list.insert(component_index + i, macro_component)
                i += 1

    def _maybe_expand_macro(self,
                            component,
                            component_list_type,
                            template_data=None):
        """For a given component, if it refers to a macro, return the
        components defined for that macro with template variables (if any)
        interpolated in.

        :arg str component_list_type: A string value indicating which type of
        component we are expanding macros for.

        :arg dict template_data: If component is a macro and contains template
        variables, use the same template data used to fill in job-template
        variables to fill in macro variables.
        """
        component_copy = copy.deepcopy(component)

        if isinstance(component, dict):
            # The component is a singleton dictionary of name:
            # dict(args)
            component_name, component_data = next(iter(component_copy.items()))
        else:
            # The component is a simple string name, eg "run-tests".
            component_name, component_data = component_copy, None

        if template_data:
            # Address the case where a macro name contains a variable to be
            # interpolated by template variables.
            component_name = deep_format(component_name, template_data, True)

        # Check that the component under consideration actually is a
        # macro.
        if not self._is_macro(component_name, component_list_type):
            return None

        # Warn if the macro shadows an actual module type name for this
        # component list type.
        if ModuleRegistry.is_module_name(component_name, component_list_type):
            self._mask_warned[component_name] = True
            logger.warning(
                "You have a macro ('%s') defined for '%s' "
                "component list type that is masking an inbuilt "
                "definition" % (component_name, component_list_type))

        macro_component_list = self._get_macro_components(component_name,
                                                          component_list_type)

        # If macro instance contains component_data, interpolate that
        # into macro components.
        if component_data:

            # Also use template_data, but prefer data obtained directly from
            # the macro instance.
            if template_data:
                template_data = copy.deepcopy(template_data)
                template_data.update(component_data)

                macro_component_list = deep_format(
                    macro_component_list, template_data, False)
            else:
                macro_component_list = deep_format(
                    macro_component_list, component_data, False)

        return macro_component_list

    def _get_macro_components(self, macro_name, component_list_type):
        """Return the list of components that a macro expands into. For example:

           - wrapper:
               name: timeout-wrapper
               wrappers:
                 - timeout:
                     fail: true
                     elastic-percentage: 150
                     elastic-default-timeout: 90
                     type: elastic

        Provides a single "wrapper" type (corresponding to the "wrappers" list
        type) component named "timeout" with the values shown above.

        The macro_name argument in this case would be "timeout-wrapper".
        """
        macro_component_list = self._macros_by_component_list_type[
            component_list_type][macro_name][component_list_type]
        return copy.deepcopy(macro_component_list)


class ModuleRegistry(object):
    _entry_points_cache = {}

    def __init__(self, jjb_config, plugins_list=None):
        self.modules = []
        self.modules_by_component_type = {}
        self.handlers = {}
        self.jjb_config = jjb_config
        self.masked_warned = {}

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
                self.modules_by_component_type[mod.component_type] = entrypoint

    @staticmethod
    def _get_plugins_info_dict(plugins_list):
        def mutate_plugin_info(plugin_info):
            """
            We perform mutations on a single member of plugin_info here, then
            return a dictionary with the longName and shortName of the plugin
            mapped to its plugin info dictionary.
            """
            version = plugin_info.get('version', '0')
            plugin_info['version'] = re.sub(r'(.*)-(?:SNAPSHOT|BETA).*',
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

    @property
    def parser_data(self):
        return self.__parser_data

    def set_parser_data(self, parser_data):
        self.__parser_data = parser_data

    def dispatch(self, component_type, xml_parent, component):
        """This is a method that you can call from your implementation of
        Base.gen_xml or component.  It allows modules to define a type
        of component, and benefit from extensibility via Python
        entry points and Jenkins Job Builder :ref:`Macros <macro>`.

        :arg string component_type: the name of the component
          (e.g., `builder`)
        :arg YAMLParser parser: the global YAML Parser
        :arg Element xml_parent: the parent XML element

        See :py:class:`jenkins_jobs.modules.base.Base` for how to register
        components of a module.

        See the Publishers module for a simple example of how to use
        this method.
        """

        if component_type not in self.modules_by_component_type:
            raise JenkinsJobsException("Unknown component type: "
                                       "'{0}'.".format(component_type))

        entry_point = self.modules_by_component_type[component_type]
        component_list_type = entry_point.load().component_list_type

        if isinstance(component, dict):
            # The component is a singleton dictionary of name: dict(args)
            name, component_data = next(iter(component.items()))
        else:
            # The component is a simple string name, eg "run-tests"
            name = component
            component_data = {}

        # Look for a component function defined in an entry point
        eps = self._entry_points_cache.get(component_list_type)
        if eps is None:
            module_eps = []
            # auto build entry points by inferring from base component_types
            mod = pkg_resources.EntryPoint(
                "__all__", entry_point.module_name, dist=entry_point.dist)

            Mod = mod.load()
            func_eps = [Mod.__dict__.get(a) for a in dir(Mod)
                        if isinstance(Mod.__dict__.get(a),
                                      types.FunctionType)]
            for func_ep in func_eps:
                try:
                    # extract entry point based on docstring
                    name_line = func_ep.__doc__.split('\n')
                    if not name_line[0].startswith('yaml:'):
                        logger.debug("Ignoring '%s' as an entry point" %
                                     name_line)
                        continue
                    ep_name = name_line[0].split(' ')[1]
                except (AttributeError, IndexError):
                    # AttributeError by docstring not being defined as
                    # a string to have split called on it.
                    # IndexError raised by name_line not containing anything
                    # after the 'yaml:' string.
                    logger.debug("Not including func '%s' as an entry point"
                                 % func_ep.__name__)
                    continue

                module_eps.append(
                    pkg_resources.EntryPoint(
                        ep_name, entry_point.module_name,
                        dist=entry_point.dist, attrs=(func_ep.__name__,)))
                logger.debug(
                    "Adding auto EP '%s=%s:%s'" %
                    (ep_name, entry_point.module_name, func_ep.__name__))

            # load from explicitly defined entry points
            module_eps.extend(list(pkg_resources.iter_entry_points(
                group='jenkins_jobs.{0}'.format(component_list_type))))

            eps = {}
            for module_ep in module_eps:
                if module_ep.name in eps:
                    raise JenkinsJobsException(
                        "Duplicate entry point found for component type: "
                        "'{0}', '{0}',"
                        "name: '{1}'".format(component_type, name))

                eps[module_ep.name] = module_ep

            # cache both sets of entry points
            self._entry_points_cache[component_list_type] = eps
            logger.debug("Cached entry point group %s = %s",
                         component_list_type, eps)

        if name in eps:
            func = eps[name].load()
            func(self, xml_parent, component_data)
        else:
            raise JenkinsJobsException("Unknown entry point or macro '{0}' "
                                       "for component type: '{1}'.".
                                       format(name, component_type))

    @classmethod
    def is_module_name(self, name, component_list_type):
        eps = self._entry_points_cache.get(component_list_type)
        if not eps:
            return False
        return (name in eps)
