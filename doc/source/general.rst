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
      display-name: 'Fancy job name'
      concurrent: true
      workspace: /srv/build-area/job-name
      quiet-period: 5
      block-downstream: false
      block-upstream: false
      retry-count: 3

:Job Parameters:
    * **project-type**:
      Defaults to "freestyle", but "maven" can also be specified.

    * **defaults**:
      Specifies a set of :ref:`defaults` to use for this job, defaults to
      ''global''.  If you have values that are common to all of your jobs,
      create a ``global`` :ref:`defaults` object to hold them, and no further
      configuration of individual jobs is necessary.  If some jobs
      should not use the ``global`` defaults, use this field to specify a
      different set of defaults.

    * **disabled**:
      Boolean value to set whether or not this job should be disabled in
      Jenkins. Defaults to ``false`` (job will be enabled).

    * **display-name**:
      Optional name shown for the project throughout the Jenkins web GUI in
      place of the actual job name.  The jenkins_jobs tool cannot fully remove
      this trait once it is set, so use caution when setting it.  Setting it to
      the same string as the job's name is an effective un-set workaround.
      Alternately, the field can be cleared manually using the Jenkins web
      interface.

    * **concurrent**:
      Boolean value to set whether or not Jenkins can run this job
      concurrently. Defaults to ``false``.

    * **workspace**:
      Path for a custom workspace. Defaults to Jenkins default
      configuration.

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

    * **auth-token**:
      Specifies an authentication token that allows new builds to be
      triggered by accessing a special predefined URL. Only those who
      know the token will be able to trigger builds remotely.

    * **retry-count**:
      If a build fails to checkout from the repository, Jenkins will
      retry the specified number of times before giving up.

.. automodule:: general
   :members:
