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
    """
    A base class for a Jenkins Job Builder Module.

    The module is initialized before any YAML is parsed.

    :arg ModuleRegistry registry: the global module registry.
    """

    #: The sequence number for the module.  Modules are invoked in the
    #: order of their sequence number in order to produce consistently
    #: ordered XML output.
    sequence = 10

    def __init__(self, registry):
        self.registry = registry

    def handle_data(self, parser):
        """This method is called before any XML is generated.  By
        overriding this method, the module may manipulate the YAML
        data structure on the parser however it likes before any XML
        is generated.  If it has changed the data structure at all, it
        must return ``True``, otherwise, it must return ``False``.

        :arg YAMLParser parser: the global YAML Parser
        :rtype: boolean
        """

        return False

    def gen_xml(self, parser, xml_parent, data):
        """Update the XML element tree based on YAML data.  Override
        this method to add elements to the XML output.  Create new
        Element objects and add them to the xml_parent.  The YAML data
        structure must not be modified.

        :arg YAMLParser parser: the global YAML Parser
        :arg Element xml_parent: the parent XML element
        :arg dict data: the YAML data structure
        """

        pass

    def _dispatch(self, component_type, component_list_type,
                  parser, xml_parent,
                  component, template_data={}):
        """This is a private helper method that you can call from your
        implementation of gen_xml.  It allows your module to define a
        type of component, and benefit from extensibility via Python
        entry points and Jenkins Job Builder :ref:`Macros <macro>`.

        :arg string component_type: the name of the component
          (e.g., `builder`)
        :arg string component_list_type: the plural name of the component
          type (e.g., `builders`)
        :arg YAMLParser parser: the global YMAL Parser
        :arg Element xml_parent: the parent XML element
        :arg dict template_data: values that should be interpolated into
          the component definition

        The value of `component_list_type` will be used to look up
        possible implementations of the component type via entry
        points (entry points provide a list of components, so it
        should be plural) while `component_type` will be used to look
        for macros (they are defined singularly, and should not be
        plural).

        See the Publishers module for a simple example of how to use
        this method.
        """

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
