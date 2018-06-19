#!/bin/bash
set -exou pipefail

VAL1=$(jenkins-jobs --version 2>&1) || exit 1
VAL2=$(python -m jenkins_jobs --version 2>&1) || exit 2

# we assure that both calling methods to get the same output
[ "${VAL1}" == "${VAL2}" ] || exit 3
