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

# Base class for a jenkins_jobs module

import pkg_resources
import yaml


class Base(object):
    sequence = 10

    def __init__(self, registry):
        self.registry = registry

    def _dispatch(self, component_type, component_list_type,
                  parser, xml_parent,
                  component, template_data={}):
        if isinstance(component, dict):
            # The component is a sigleton dictionary of name: dict(args)
            name, component_data = component.items()[0]
            if template_data:
                # Template data contains values that should be interpolated
                # into the component definition
                s = yaml.dump(component_data, default_flow_style=False)
                s = s.format(**template_data)
                component_data = yaml.load(s)
        else:
            # The component is a simple string name, eg "run-tests"
            name = component
            component_data = {}

        # Look for a component function defined in an entry point
        for ep in pkg_resources.iter_entry_points(
            group='jenkins_jobs.{0}'.format(component_list_type), name=name):
            func = ep.load()
            func(parser, xml_parent, component_data)
        else:
            # Otherwise, see if it's defined as a macro
            component = parser.data.get(component_type, {}).get(name)
            if component:
                for b in component[component_list_type]:
                    # Pass component_data in as template data to this function
                    # so that if the macro is invoked with arguments,
                    # the arguments are interpolated into the real defn.
                    self._dispatch(component_type, component_list_type,
                                   parser, xml_parent, b, component_data)
