Job Definitions
===============

The job definitions for Jenkins Job Builder are kept in any number of
YAML or JSON files, in whatever way you would like to organize them.  When you
invoke ``jenkins-jobs`` you may specify either the path of a single
YAML file, or a directory.  If you choose a directory, all of
the .yaml/.yml or .json files in that directory will be read, and all the
jobs they define will be created or updated.

Definitions
-----------

Jenkins Job Builder understands a few basic object types which are
described in the next sections.

.. _job:

Job
^^^

The most straightforward way to create a job is simply to define a
Job in YAML.  It looks like this::

  - job:
      name: job-name

That's not very useful, so you'll want to add some actions such as
:ref:`builders`, and perhaps :ref:`publishers`.  Those are described
later.

.. automodule:: jenkins_jobs.modules.general

.. _job-template:

Job Template
^^^^^^^^^^^^

If you need several jobs defined that are nearly identical, except
perhaps in their names, SCP targets, etc., then you may use a Job
Template to specify the particulars of the job, and then use a
`Project`_ to realize the job with appropriate variable substitution.
Any variables not specified at the project level will be inherited from
the `Defaults`_.

A Job Template has the same syntax as a `Job`_, but you may add
variables anywhere in the definition.  Variables are indicated by
enclosing them in braces, e.g., ``{name}`` will substitute the
variable `name`.  When using a variable in a string field, it is good
practice to wrap the entire string in quotes, even if the rules of
YAML syntax don't require it because the value of the variable may
require quotes after substitution. In the rare situation that you must
encode braces within literals inside a template (for example a shell
function definition in a builder), doubling the braces will prevent
them from being interpreted as a template variable.

You must include a variable in the ``name`` field of a Job Template
(otherwise, every instance would have the same name).  For example::

  - job-template:
      name: '{name}-unit-tests'

Will not cause any job to be created in Jenkins, however, it will
define a template that you can use to create jobs with a `Project`_
definition.  It's name will depend on what is supplied to the
`Project`_.

If you use the variable ``{template-name}``, the name of the template
itself (e.g. ``{name}-unit-tests`` in the above example) will be
substituted in. This is useful in cases where you need to trace a job
back to its template.

Sometimes it is useful to have the same job name format used even
where the template contents may vary. `Ids` provide a mechanism to
support such use cases in addition to simplifying referencing
templates when the name contains the more complex substitution with
default values.


Default Values for Template Variables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To facilitate reuse of templates with many variables that can be
substituted, but where in most cases the same or no value is needed,
it is possible to specify defaults for the variables within the
templates themselves.

This can be used to provide common settings for particular templates.
For example:

.. literalinclude::
    /../../tests/yamlparser/fixtures/template_default_variables.yaml
   :language: yaml

To use a default value for a variable used in the name would be
uncommon unless it was in addition to another variable. However you
can use `Ids`_ simplify such use cases.

.. _project:

Project
^^^^^^^

The purpose of a project is to collect related jobs together, and
provide values for the variables in a `Job Template`_.  It looks like
this::

  - project:
      name: project-name
      jobs:
        - '{name}-unit-tests'

Any number of arbitrarily named additional fields may be specified,
and they will be available for variable substitution in the job
template.  Any job templates listed under ``jobs:`` will be realized
with those values.  The example above would create the job called
'project-name-unit-tests' in Jenkins.

The ``jobs:`` list can also allow for specifying job-specific
substitutions as follows::

  - project:
      name: project-name
      jobs:
        - '{name}-unit-tests':
            mail-to: developer@nowhere.net
        - '{name}-perf-tests':
            mail-to: projmanager@nowhere.net


If a variable is a list, the job template will be realized with the
variable set to each value in the list.  Multiple lists will lead to
the template being realized with the cartesian product of those
values.  Example::

  - project:
      name: project-name
      pyver:
        - 26
        - 27
      jobs:
        - '{name}-{pyver}'

If there are templates being realized that differ only in the variable
used for its name (thus not a use case for job-specific substitutions),
additional variables can be specified for project variables. Example:

.. literalinclude::  /../../tests/yamlparser/fixtures/templates002.yaml

You can also specify some variable combinations to exclude from the matrix with
the ``exclude`` keyword, to avoid generating jobs for those combinations. You
can specify all the variables of the combination or only a subset, if you
specify a subset, any value of the omited variable will match:

.. literalinclude:: /../../tests/yamlparser/fixtures/template_exclude.yaml

The above example will omit the jobs:

 * build-axe1val1-axe2val1-axe3val2
 * build-axe1val1-axe2val2-axe3val1
 * build-axe1val2-axe2val2-axe3val1

To achieve the same without the ``exclude`` tag one would have to do something
a bit more complicated, that gets more complicated for each dimension in the
combination, for the previous example, the counterpart would be:

.. literalinclude::
    /../../tests/yamlparser/fixtures/template_without_exclude.yaml

Job Group
^^^^^^^^^

If you have several Job Templates that should all be realized
together, you can define a Job Group to collect them.  Simply use the
Job Group where you would normally use a `Job Template`_ and all of
the Job Templates in the Job Group will be realized.  For example:

.. literalinclude::  /../../tests/yamlparser/fixtures/templates001.yaml

Would cause the jobs `project-name-unit-tests` and `project-name-perf-tests` to be created
in Jenkins.

.. _views:

Views
^^^^^

A view is a particular way of displaying a specific set of jobs. To
create a view, you must define a view in a YAML file and have a variable called view-type with a valid value. It looks like this::

  - view:
      name: view-name
      view-type: list

Views are processed differently than Jobs and therefore will not work within a `Project`_ or a `Job Template`_.

.. _macro:

Macro
^^^^^

Many of the actions of a `Job`_, such as builders or publishers, can
be defined as a Macro, and then that Macro used in the `Job`_
description.  Builders are described later, but let's introduce a
simple one now to illustrate the Macro functionality.  This snippet
will instruct Jenkins to execute "make test" as part of the job::

  - job:
      name: foo-test
      builders:
        - shell: 'make test'

If you wanted to define a macro (which won't save much typing in this
case, but could still be useful to centralize the definition of a
commonly repeated task), the configuration would look like::

  - builder:
      name: make-test
      builders:
        - shell: 'make test'

  - job:
      name: foo-test
      builders:
        - make-test

This allows you to create complex actions (and even sequences of
actions) in YAML that look like first-class Jenkins Job Builder
actions.  Not every attribute supports Macros, check the documentation
for the action before you try to use a Macro for it.

Macros can take parameters, letting you define a generic macro and more
specific ones without having to duplicate code::

    # The 'add' macro takes a 'number' parameter and will creates a
    # job which prints 'Adding ' followed by the 'number' parameter:
    - builder:
        name: add
        builders:
         - shell: "echo Adding {number}"

    # A specialized macro 'addtwo' reusing the 'add' macro but with
    # a 'number' parameter hardcoded to 'two':
    - builder:
        name: addtwo
        builders:
         - add:
            number: "two"

    # Glue to have Jenkins Job Builder to expand this YAML example:
    - job:
        name: "testingjob"
        builders:
         # The specialized macro:
         - addtwo
         # Generic macro call with a parameter
         - add:
            number: "ZERO"
         # Generic macro called without a parameter. Never do this!
         # See below for the resulting wrong output :(
         - add

Then ``<builders />`` section of the generated job show up as::

  <builders>
    <hudson.tasks.Shell>
      <command>echo Adding two</command>
    </hudson.tasks.Shell>
    <hudson.tasks.Shell>
      <command>echo Adding ZERO</command>
    </hudson.tasks.Shell>
    <hudson.tasks.Shell>
      <command>echo Adding {number}</command>
    </hudson.tasks.Shell>
  </builders>

As you can see, the specialized macro ``addtwo`` reused the definition from
the generic macro ``add``.

Macro Notes
~~~~~~~~~~~

If a macro is not passed any parameters it will not have any expansion
performed on it.  Thus if you forget to provide `any` parameters to a
macro that expects some, the parameter-templates (``{foo}``) will be
left as is in the resulting output; this is almost certainly not what
you want.  Note if you provide an invalid parameter, the expansion
will fail; the expansion will only be skipped if you provide `no`
parameters at all.

Macros are expanded using Python string substitution rules.  This can
especially cause confusion with shell snippets that use ``{`` as part
of their syntax.  As described, if a macro has `no` parameters, no
expansion will be performed and thus it is correct to write the script
with no escaping, e.g.::

  - builder:
    name: a_builder
    builders:
      - shell: |
          VARIABLE=${VARIABLE:-bar}
          function foo {
              echo "my shell function"
          }

However, if the macro `has` parameters, you must escape the ``{`` you
wish to make it through to the output, e.g.::

  - builder:
    name: a_builder
    builders:
       - shell: |
         PARAMETER={parameter}
         VARIABLE=${{VARIABLE:-bar}}
         function foo {{
              echo "my shell function"
         }}

Note that a ``job-template`` will have parameters by definition (at
least a ``name``).  Thus embedded-shell within a ``job-template`` should
always use ``{{`` to achieve a literal ``{``.  A generic builder will need
to consider the correct quoting based on its use of parameters.


.. _ids:

Item ID's
^^^^^^^^^

It's possible to assign an `id` to any of the blocks and then use that
to reference it instead of the name. This has two primary functions:

* A unique identifier where you wish to use the same naming format for
  multiple templates. This allows to follow a naming scheme while
  still using multiple templates to handle subtle variables in job
  requirements.
* Provides a simpler name for a `job-template` where you have multiple
  variables including default values in the name and don't wish to have
  to include this information in every use. This also makes changing
  the template output name without impacting references.

Example:

.. literalinclude::  /../../tests/yamlparser/fixtures/template_ids.yaml

.. _raw:

Raw config
^^^^^^^^^^

It is possible, but not recommended, to use `raw` within a module to
inject raw xml into the job configs.

This is relevant in case there is no appropriate module for a
Jenkins plugin or the module does not behave as you expect it to do.

For example:

.. literalinclude:: /../../tests/wrappers/fixtures/raw001.yaml

Is the raw way of adding support for the `xvnc` wrapper.

To get the appropriate xml to use you would need to create/edit a job
in Jenkins and grab the relevant raw xml segment from the
`config.xml`.

The xml string can refer to variables just like anything else and as
such can be parameterized like anything else.

You can use `raw` in most locations, the following example show them
with arbitrary xml-data:

.. literalinclude::
   /../../tests/yamlparser/fixtures/complete-raw001.yaml

Note: If you have a need to use `raw` please consider submitting a patch to
add or fix the module that will remove your need to use `raw`.


.. _defaults:

Defaults
^^^^^^^^

Defaults collect job attributes (including actions) and will supply
those values when the job is created, unless superseded by a value in
the 'Job'_ definition.  If a set of Defaults is specified with the
name ``global``, that will be used by all `Job`_ (and `Job Template`_)
definitions unless they specify a different Default object with the
``defaults`` attribute.  For example::

  - defaults:
      name: global
      description: 'Do not edit this job through the web!'

Will set the job description for every job created.

You can define variables that will be realized in a `Job Template`.

.. literalinclude::  /../../tests/yamlparser/fixtures/template_honor_defaults.yaml

Would create jobs ``build-i386`` and ``build-amd64``.

.. _variable_references:

Variable References
^^^^^^^^^^^^^^^^^^^

If you want to pass an object (boolean, list or dict) to templates you can
use an ``{obj:key}`` variable in the job template.  This triggers the use
of code that retains the original object type.

For example:

.. literalinclude::  /../../tests/yamlparser/fixtures/custom_distri.yaml


JJB also supports interpolation of parameters within parameters. This allows a
little more flexibility when ordering template jobs as components in different
projects and job groups.

For example:

.. literalinclude:: /../../tests/yamlparser/fixtures/second_order_parameter_interpolation002.yaml


By default JJB will fail if it tries to interpolate a variable that was not
defined, but you can change that behavior and allow empty variables with the
allow_empty_variables configuration option.

For example, having a configuration file with that option enabled:

.. literalinclude:: /../../tests/yamlparser/fixtures/allow_empty_variables.conf

Will prevent JJb from failing if there are any non-initialized variables used
and replace them with the empty string instead.


Yaml Anchors & Aliases
^^^^^^^^^^^^^^^^^^^^^^

The yaml specification supports `anchors and aliases`_ which means
that JJB definitions allow references to variables in templates.

For example:

.. literalinclude::  /../../tests/yamlparser/fixtures/yaml_anchor.yaml


The `anchors and aliases`_ are expanded internally within JJB's yaml loading
calls and are not limited to individual documents. That means you can't use
the same anchor name in included files without collisions.

A simple example can be seen in the specs `full length example`_ with the
following being more representative of usage within JJB:

.. literalinclude:: /../../tests/localyaml/fixtures/anchors_aliases.iyaml


Which will be expanded to the following yaml before being processed:

.. literalinclude:: /../../tests/localyaml/fixtures/anchors_aliases.oyaml


.. _full length example: http://www.yaml.org/spec/1.2/spec.html#id2761803
.. _anchors and aliases: http://www.yaml.org/spec/1.2/spec.html#id2765878


Custom Yaml Tags
----------------

.. automodule:: jenkins_jobs.local_yaml


Modules
-------

The bulk of the job definitions come from the following modules.

.. toctree::
   :maxdepth: 2
   :glob:

   project_*
   builders
   hipchat
   metadata
   notifications
   parameters
   properties
   publishers
   reporters
   scm
   triggers
   wrappers
   zuul


Module Execution
----------------

The jenkins job builder modules are executed in sequence.

Generally the sequence is:
    #. parameters/properties
    #. scm
    #. triggers
    #. wrappers
    #. prebuilders (maven only, configured like :ref:`builders`)
    #. builders (maven, freestyle, matrix, etc..)
    #. postbuilders (maven only, configured like :ref:`builders`)
    #. publishers/reporters/notifications
