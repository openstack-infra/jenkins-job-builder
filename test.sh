#!/bin/bash

# A simple script to verify that the XML output is unaltered after a change.
# Before you start work, run "./test.sh save".
# As you test your change, run "./test.sh" to see differences in XML output.

mkdir -p /tmp/jenkins_jobs_test/saved
mkdir -p /tmp/jenkins_jobs_test/test

if [ "$1" == "save" ]
then
    for x in `find projects/ -name *.yml`
    do
	echo $x
	BASENAME=`basename $x`
	python jenkins_jobs.py test $x > /tmp/jenkins_jobs_test/saved/$BASENAME.xml
    done
else
    for x in `find projects/ -name *.yml`
    do
	echo $x
	BASENAME=`basename $x`
	python jenkins_jobs.py test $x > /tmp/jenkins_jobs_test/test/$BASENAME.xml
    done
    diff -r /tmp/jenkins_jobs_test/saved /tmp/jenkins_jobs_test/test
fi
