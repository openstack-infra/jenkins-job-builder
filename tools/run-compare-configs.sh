#!/bin/bash -e
#
# Copyright 2016 Hewlett-Packard Development Company, L.P.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

rm -fr .test
mkdir -p .test/run-conf/config

CONFIGS_DIR=$(dirname ${0})/configs
CONFIGS=$(ls -1 ${CONFIGS_DIR}/*.conf 2>/dev/null)

cd .test
if [ -e /usr/zuul-env/bin/zuul-cloner ];
then
    /usr/zuul-env/bin/zuul-cloner -m ../tools/run-compare-clonemap.yaml --cache-dir /opt/git https://git.openstack.org openstack-infra/project-config
else
    git clone --depth=1 https://git.openstack.org/openstack-infra/project-config
fi
# setup a default configuration to compare results against
cp -r project-config/jenkins/jobs/* run-conf/config
cd ..

mkdir -p .test/run-conf/default/out
tox -e compare-xml-config

echo "############################################################"
echo "Starting processing configs"
for conf_file in ${CONFIGS}
do
    echo "============================================================"
    echo "Processing non-default config ${conf_file}"
    conf_name=$(basename ${conf_file%%.conf})
    mkdir -p .test/run-conf/${conf_name}/out
    tox -e compare-xml-config -- --conf ${conf_file} test -o .test/run-conf/${conf_name}/out/ .test/run-conf/config
    echo "------------------------------------------------------------"
done

echo "############################################################"
echo "Comparing differences from default to alternative configs"

for conf_file in ${CONFIGS}
do
    echo "^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^"
    echo "Comparing config ${conf_file}"
    conf_name=$(basename ${conf_file%%.conf})
    CHANGED=0
    for x in `(cd .test/run-conf/default/out/ && find -type f)`
    do
        differences=$(diff -u .test/run-conf/default/out/${x} .test/run-conf/${conf_name}/out/${x} 2>&1)
        if [ $? -ne 0 ]
        then
            CHANGED=1
            echo "============================================================"
            echo ${x}
            echo "------------------------------------------------------------"
            echo "${differences}"
        fi
    done
    if [ "${CHANGED}" -eq "0" ]
    then
        echo "No differences between default and ${conf_name} configs"
    fi
done
# should only fail if previous command exited with a non-zero status
exit 0
