Configuration
=============

The job definitions for Jenkins Job Builder are kept in any number of
YAML files, in whatever way you would like to organize them.  When you
invoke ``jenkins-jobs`` you may specify either the path of a single
YAML file, or a directory.  If you choose a directory, all of
the .yaml (or .yml) files in that directory will be read, and all the
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
later.  There are a few basic optional fields for a Job definition::

  - job:
      name: job-name
      project-type: freestyle
      defaults: global
      disabled: false
      concurrent: true
      quiet-period: 5
      block-downstream: false
      block-upstream: false

**project-type**
  Defaults to "freestyle", but "maven" can also be specified.

**defaults**
  Specifies a set of `Defaults`_ to use for this job, defaults to
  ''global''.  If you have values that are common to all of your jobs,
  create a ``global`` `Defaults`_ object to hold them, and no further
  configuration of individual jobs is necessary.  If some jobs
  should not use the ``global`` defaults, use this field to specify a
  different set of defaults.

**disabled**
  Boolean value to set whether or not this job should be disabled in
  Jenkins. Defaults to ``false`` (job will be enabled).

**concurrent**
  Boolean value to set whether or not Jenkins can run this job
  concurrently. Defaults to ``false``.

**quiet-period**
  Number of seconds to wait between consecutive runs of this job.
  Defaults to ``0``.

**block-downstream**
  Boolean value to set whether or not this job must block while
  downstream jobs are running. Downstream jobs are determined
  transitively. Defaults to ``false``.

**block-upstream**
  Boolean value to set whether or not this job must block while
  upstream jobs are running. Upstream jobs are determined
  transitively. Defaults to ``false``.

.. _job-template:

Job Template
^^^^^^^^^^^^

If you need several jobs defined that are nearly identical, except
perhaps in their names, SCP targets, etc., then you may use a Job
Template to specify the particulars of the job, and then use a
`Project`_ to realize the job with appropriate variable substitution.

A Job Template has the same syntax as a `Job`_, but you may add
variables anywhere in the definition.  Variables are indicated by
enclosing them in braces, e.g., ``{name}`` will substitute the
variable `name`.  When using a variable in a string field, it is good
practice to wrap the entire string in quotes, even if the rules of
YAML syntax don't require it because the value of the variable may
require quotes after substitution.

You must include a variable in the ``name`` field of a Job Template
(otherwise, every instance would have the same name).  For example::

  - job-template:
      name: '{name}-unit-tests'

Will not cause any job to be created in Jenkins, however, it will
define a template that you can use to create jobs with a `Project`_
definition.  It's name will depend on what is supplied to the
`Project`_.

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

Job Group
^^^^^^^^^

If you have several Job Templates that should all be realized
together, you can define a Job Group to collect them.  Simply use the
Job Group where you would normally use a `Job Template`_ and all of
the Job Templates in the Job Group will be realized.  For example::

  - job-template:
      name: '{name}-python-26'

  - job-template:
      name: '{name}-python-27'

  - job-group:
      name: python-jobs
      jobs:
        - '{name}-python-26'
        - '{name}-python-27'

  - project:
      name: foo
      jobs:
        - python-jobs

Would cause the jobs `foo-python-26` and `foo-python-27` to be created
in Jekins.

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
the generic macro ``add``.  Whenever you forget a parameter from a macro,
it will not be expanded and left as is, which will most probably cause havoc in
your Jenkins builds.

Defaults
^^^^^^^^

Defaults collect job attributes (including actions) and will supply
those values when the job is created, unless superseded by a value in
the 'Job'_ definition.  If a set of Defaults is specified with the
name ``global``, that will be used by all `Job`_ (and `Job Template`_)
definitions unless they specify a different Default object with the
``default`` attribute.  For example::

  - defaults:
      name: global
      description: 'Do not edit this job through the web!'

Will set the job description for every job created.


Modules
-------

The bulk of the job definitions come from the following modules.

.. toctree::
   :maxdepth: 2

   project_freestyle
   project_maven
   project_matrix
   general
   builders
   hipchat
   notifications
   parameters
   properties
   publishers
   reporters
   scm
   triggers
   wrappers
   zuul
