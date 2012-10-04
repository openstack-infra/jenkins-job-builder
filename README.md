# Jenkins Job Builder #

Jenkins Job Builder takes simple descriptions of Jenkins jobs in YAML format,
and uses them to configure Jenkins. You can keep your job descriptions in human
readable text format in a version control system to make changes and auditing
easier. It also has a flexible template system, so creating many similarly
configured jobs is easy.

To install:
    sudo python setup.py install

Online documentation:
- http://ci.openstack.org/jenkins-job-builder/


## developers ##
Bug report: https://bugs.launchpad.net/openstack-ci/

Cloning: https://review.openstack.org/p/openstack-ci/jenkins-job-builder.git

Patches are submitted via Gerrit at https://review.openstack.org/

More details on how you can contribute is available on our wiki at:
http://wiki.openstack.org/HowToContribute

## installing wihout setup.py ##

For YAML support, you will need libyaml installed.

    # Mac OS X:
    brew install libyaml

Then install the required python packages using pip:

    sudo pip install PyYAML python-jenkins

