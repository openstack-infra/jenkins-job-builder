Installation
============

To install Jenkins Job Builder, run::

  sudo python setup.py install

The OpenStack project uses Puppet to manage its infrastructure
systems, including Jenkins.  If you use Puppet, you can use the
`OpenStack Jenkins module`__ to install Jenkins Job Builder.

__ https://github.com/openstack-infra/config/tree/master/modules/jenkins

Documentation
-------------

Documentation is included in the ``doc`` folder. To generate docs
locally execute the command::

    tox -e doc

The generated documentation is then available under
``doc/build/html/index.html``.

Unit Tests
----------

Unit tests have been included and are in the ``tests`` folder.  We recently
started including unit tests as examples in our documentation so to keep the
examples up to date it is very important that we include unit tests for
every module.  To run the unit tests, execute the command::

    tox -e py27

* Note: View ``tox.ini`` to run tests on other versions of Python.

Configuration File
------------------

After installation, you will need to create a configuration file.  By
default, ``jenkins-jobs`` looks in
``/etc/jenkins_jobs/jenkins_jobs.ini`` but you may specify an
alternative location when running ``jenkins-jobs``.  The file should have
the following format:

.. literalinclude:: ../../etc/jenkins_jobs.ini-sample
   :language: ini

**user**
  This should be the name of a user previously defined in Jenkins.
  Appropriate user permissions must be set under the Jenkins security
  matrix: under the ``Global`` group of permissions, check ``Read``,
  then under the ``Job`` group of permissions, check ``Create``,
  ``Delete``, ``Configure`` and finally ``Read``.

**password**
  The API token for the user specified.  You can get this through the
  Jenkins management interface under ``People`` -> username ->
  ``Configure`` and then click the ``Show API Token`` button.

**url**
  The base URL for your Jenkins installation.

**ignore_cache**
  (Optional) If set to True, Jenkins Job Builder won't use any cache.


Running
-------

After it's installed and configured, you can invoke Jenkins Job
Builder by running ``jenkins-jobs``.  You won't be able to do anything
useful just yet without a configuration which is discussed in the next
section.

Usage
^^^^^
.. program-output:: jenkins-jobs --help

Testing JJB
^^^^^^^^^^^
Once you have a configuration defined, you can test the job builder by running::

  jenkins-jobs test /path/to/config -o /path/to/output

which will write XML files to the output directory for all of the jobs
defined in the configuration directory.

Updating Jenkins
^^^^^^^^^^^^^^^^
When you're satisfied with the generated XML from the test, you can run::

  jenkins-jobs update /path/to/config

which will upload the configurations to Jenkins if needed.  Jenkins Job
Builder maintains, for each host, a cache [#f1]_ of previously configured jobs,
so that you can run that command as often as you like, and it will only
update the configuration in Jenkins if the defined configuration has
changed since the last time it was run.  Note: if you modify a job
directly in Jenkins, jenkins-jobs will not know about it and will not
update it.

To update a specific list of jobs, simply pass them as additional
arguments after the configuration path. To update Foo1 and Foo2 run::

  jenkins-jobs update /path/to/config Foo1 Foo2


.. rubric:: Footnotes
.. [#f1] The cache default location is at ``~/.cache/jenkins_jobs``, which
         can be overridden by setting the ``XDG_CACHE_HOME`` environment
         variable.
