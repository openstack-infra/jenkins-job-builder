.. _quick-start-guide:

Quick Start Guide
=================

This guide was made with the impatient in mind so explanation is sparse.
It will guide users through a set of typical use cases for JJB using the same
job definitions we use to test JJB.

#. Clone the repository_ to get the JJB job definition examples_
#. The :doc:`installation` can be either from pypi_ (released version) or from the clone (master).

Usage of the commands below assumes that you are at the root of the cloned directory.

.. _repository: http://git.openstack.org/cgit/openstack-infra/jenkins-job-builder/
.. _pypi: https://pypi.python.org/pypi/jenkins-job-builder/
.. _examples: http://git.openstack.org/cgit/openstack-infra/jenkins-job-builder/tree/tests


.. _use-case-1:

Use Case 1: Test a job definition
---------------------------------

JJB creates Jenkins XML configuration file from a YAML/JSON definition file and
just uploads it to Jenkins.  JJB provides a convenient ``test`` command to allow
you to validate the XML before you attempt to upload it to Jenkins.

Test a YAML job definition::

    jenkins-jobs test tests/yamlparser/fixtures/templates002.yaml


The above command prints the generated Jenkins XML to the console.  If you
prefer to send it to a directory::

    jenkins-jobs test -o output tests/yamlparser/fixtures/templates002.yaml


The `output` directory will contain files with the XML configurations.

.. _use-case-2:

Use Case 2: Updating Jenkins Jobs
---------------------------------

Once you've tested your job definition and are happy with it then you can use the
``update`` command to deploy the job to Jenkins.  The ``update`` command requires a
configuration file.  An example file is supplied in the etc folder, you should
update it to match your Jenkins master::

    jenkins-jobs --conf etc/jenkins_jobs.ini-sample update tests/yamlparser/fixtures/templates002.yaml

The above command will update your Jenkins master with the generated jobs.

**Caution**: JJB caches Jenkins job information locally.  Changes
made using the Jenkins UI will not update that cache, which may
lead to confusion.  See :ref:`updating-jobs` for more information.

.. _use-case-3:

Use Case 3: Working with JSON job definitions
---------------------------------------------

You can also define your jobs in json instead of yaml::

    jenkins-jobs --conf etc/jenkins_jobs.ini-sample update tests/jsonparser/fixtures/simple.json

The above command just uses a simple job definition.  You can also convert any
of the YAML examples to JSON and feed that to JJB.

.. _use-case-4:

Use Case 4: Deleting a job
--------------------------

To delete a job::

    jenkins-jobs --conf etc/jenkins_jobs.ini-sample delete simple

The above command deletes the job `simple` from the Jenkins master.



Please refer to the jenkins-jobs :ref:`command-reference` and the
:doc:`definition` pages for more details.
