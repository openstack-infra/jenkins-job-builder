Installation
============

To install Jenkins Job Builder, run::

  sudo python setup.py install

The OpenStack project uses puppet to manage its infrastructure
systems, including Jenkins.  If you use Puppet, you can use the
`OpenStack Jenkins module`__ to install Jenkins Job Builder.

__ https://github.com/openstack-infra/config/tree/master/modules/jenkins

Documentation
-------------

Documentation have been included and are in the 'doc' folder. To generate docs
locally execute the command::

    tox -e venv -- python setup.py build_sphinx

Unit Tests
----------

Unit tests have been included and are in the 'tests' folder.  We recently
started including unit tests as examples in our documentation so to keep the
examples up to date it is very important that we include a unit tests for
every module.  You can run the unit tests by execute the command::

    tox -epy27

*Note - view tox.ini to run test on other versions of python

Configuration File
------------------

After installation, you will need to create a configuration file.  By
default, `jenkins-jobs` looks in
``/etc/jenkins_jobs/jenkins_jobs.ini`` but you may specify an
alternate location when running `jenkins-jobs`.  The file should have
the following format::

  [jenkins]
  user=USERNAME
  password=PASSWORD
  url=JENKINS_URL
  ignore_cache=IGNORE_CACHE_FLAG

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
  (Optional) If set to True, jenkins job builder
  won't be using any cache.


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

That will write XML files to the output directory for all of the jobs
defined in the configuration directory.  

Updating Jenkins
^^^^^^^^^^^^^^^^
When you're satisfied with the generated xml from the test, you can run::

  jenkins-jobs update /path/to/config

Which will upload the configurations to Jenkins if needed.  Jenkins Job
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
         can be overridden by setting the ``XDG_CACHE_HOME`` environment variable.
