Installation
============

To install Jenkins Job Builder, run::

  sudo setup.py install

The OpenStack project uses puppet to manage its infrastructure
systems, including Jenkins.  If you use Puppet, you can use the
`OpenStack Jenkins module`__ to install Jenkins Job Builder.

__ https://github.com/openstack/openstack-ci-puppet/tree/master/modules/jenkins


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


Running
-------

After it's installed and configured, you can invoke Jenkins Job
Builder by running ``jenkins-jobs``.  You won't be able to do anything
useful just yet without a configuration which is discussed in the next
section).  But you should be able to get help on the various commands
by running::

  jenkins-jobs --help
  jenkins-jobs update --help
  jenkins-jobs test --help
  (etc.)

Once you have a configuration defined, you can test it with::

  jenkins-jobs test /path/to/config -o /path/to/output

That will write XML files to the output directory for all of the jobs
defined in the configuration directory.  When you're satisfied, you
can run::

  jenkins-jobs update /path/to/config

Which will upload the configurations to Jenkins if needed.  Jenkins
Job Builder maintains a cache of previously configured jobs, so that
you can run that command as often as you like, and it will only update
the configuration in Jenkins if the defined configuration has changed
since the last time it was run.  Note: if you modify a job directly in
Jenkins, jenkins-jobs will not know about it and will not update it.
