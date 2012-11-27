.. _general:

General Job Configuration
=========================

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

:Job Parameters:
    * **project-type**:
      Defaults to "freestyle", but "maven" can also be specified.

    * **defaults**:
      Specifies a set of `Defaults`_ to use for this job, defaults to
      ''global''.  If you have values that are common to all of your jobs,
      create a ``global`` `Defaults`_ object to hold them, and no further
      configuration of individual jobs is necessary.  If some jobs
      should not use the ``global`` defaults, use this field to specify a
      different set of defaults.

    * **disabled**:
      Boolean value to set whether or not this job should be disabled in
      Jenkins. Defaults to ``false`` (job will be enabled).

    * **concurrent**:
      Boolean value to set whether or not Jenkins can run this job
      concurrently. Defaults to ``false``.

    * **quiet-period**:
      Number of seconds to wait between consecutive runs of this job.
      Defaults to ``0``.

    * **block-downstream**:
      Boolean value to set whether or not this job must block while
      downstream jobs are running. Downstream jobs are determined
      transitively. Defaults to ``false``.

    * **block-upstream**:
      Boolean value to set whether or not this job must block while
      upstream jobs are running. Upstream jobs are determined
      transitively. Defaults to ``false``.

.. automodule:: general
   :members:
