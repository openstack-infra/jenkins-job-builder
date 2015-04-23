.. _extending:

Extending
=========

Jenkins Job Builder is quite modular.  It is easy to add new
attributes to existing components, a new module to support a Jenkins
plugin, or include locally defined methods to deal with an
idiosyncratic build system.

The Builder
-----------

The ``Builder`` class manages Jenkins jobs. It's responsible for
creating/deleting/updating jobs and can be called from your application. You
can pass it a filename or an open file-like object that represents your YAML
configuration. See the ``jenkins_jobs/builder.py`` file for more details.

XML Processing
--------------

Most of the work of building XML from the YAML configuration file is
handled by individual functions that implement a single
characteristic.  For example, see the
``jenkins_jobs/modules/builders.py`` file for the Python module that
implements the standard Jenkins builders.  The ``shell`` function at
the top of the file implements the standard `Execute a shell` build
step.  All of the YAML to XML functions in Jenkins Job Builder have
the same signature:

.. _component_interface:
.. py:function:: component(parser, xml_parent, data)
  :noindex:

  :arg YAMLParser parser: the jenkins jobs YAML parser
  :arg Element xml_parent: this attribute's parent XML element
  :arg dict data: the YAML data structure for this attribute and below

The function is expected to examine the YAML data structure and create
new XML nodes and attach them to the xml_parent element.  This general
pattern is applied throughout the included modules.

.. _module:

Modules
-------

Nearly all of Jenkins Job Builder is implemented in modules.  The main
program has no concept of builders, publishers, properties, or any
other aspects of job definition.  Each of those building blocks is
defined in a module, and due to the use of setuptools entry points,
most modules are easily extensible with new components.

To add a new module, define a class that inherits from
:py:class:`jenkins_jobs.modules.base.Base`, and add it to the
``jenkins_jobs.modules`` entry point in your setup.py.

.. autoclass:: jenkins_jobs.modules.base.Base
   :members:
   :undoc-members:
   :private-members:

.. _component:

Components
----------

Most of the standard modules supply a number of components, and it's
easy to provide your own components for use by those modules.  For
instance, the Builders module provides several builders, such as the
`shell` builder as well as the `trigger_builds` builder.  If you
wanted to add a new builder, all you need to do is write a function
that conforms to the :ref:`Component Interface <component_interface>`,
and then add that function to the appropriate entry point (via a
setup.py file).

.. _module_registry:

Module Registry
---------------

All modules and their associated components are registered in the
module registry. It can be accessed either from modules via the registry
field, or via the parser parameter of components.

.. autoclass:: jenkins_jobs.registry.ModuleRegistry
   :members:
