#!/bin/bash

# A simple script to verify that the XML output is unaltered after a change.
# Before you start work, run "./test.sh save".
# As you test your change, run "./test.sh" to see differences in XML output.

mkdir -p /tmp/jenkins_jobs_test/saved
mkdir -p /tmp/jenkins_jobs_test/test

if [ "$1" == "save" ]
then
    rm -f /tmp/jenkins_jobs_test/saved/*
    jenkins-jobs test -o /tmp/jenkins_jobs_test/saved/ example 
else
    rm -f /tmp/jenkins_jobs_test/test/*
    jenkins-jobs test -o /tmp/jenkins_jobs_test/test/ example 
    for x in `(cd /tmp/jenkins_jobs_test/saved && find -type f)`
    do
	if ! diff -u /tmp/jenkins_jobs_test/saved/$x /tmp/jenkins_jobs_test/test/$x >/dev/null 2>&1
	then
	    echo "============================================================"
	    echo $x
	    echo "------------------------------------------------------------"
	fi
	diff -u /tmp/jenkins_jobs_test/saved/$x /tmp/jenkins_jobs_test/test/$x
    done
fi
