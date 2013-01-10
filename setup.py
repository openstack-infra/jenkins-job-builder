# Copyright 2012 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import setuptools

from jenkins_jobs.openstack.common import setup
from jenkins_jobs.version import version_info as version

requires = setup.parse_requirements()
test_requires = setup.parse_requirements(['tools/test-requires'])
depend_links = setup.parse_dependency_links()


setuptools.setup(
    name='jenkins-job-builder',
    version=version.canonical_version_string(always=True),
    author='Hewlett-Packard Development Company, L.P.',
    author_email='openstack@lists.launchpad.net',
    description='Manage Jenkins jobs with YAML',
    license='Apache License, Version 2.0',
    url='https://github.com/openstack-ci/jenkins-job-builder',
    packages=setuptools.find_packages(exclude=['tests', 'tests.*']),
    include_package_data=True,
    cmdclass=setup.get_cmdclass(),
    install_requires=requires,
    setup_requires=['setuptools_git>=0.4'],
    dependency_links=depend_links,
    zip_safe=False,
    classifiers=[
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python'
    ],
    entry_points={
        'console_scripts': [
            'jenkins-jobs=jenkins_jobs.cmd:main',
        ],
        'jenkins_jobs.projects': [
            'freestyle=jenkins_jobs.modules.project_freestyle:Freestyle',
            'maven=jenkins_jobs.modules.project_maven:Maven',
            'matrix=jenkins_jobs.modules.project_matrix:Matrix',
        ],
        'jenkins_jobs.builders': [
            'shell=jenkins_jobs.modules.builders:shell',
            'ant=jenkins_jobs.modules.builders:ant',
            'trigger-builds=jenkins_jobs.modules.builders:trigger_builds',
            'builders-from=jenkins_jobs.modules.builders:builders_from',
            'inject=jenkins_jobs.modules.builders:inject',
            'artifact-resolver=jenkins_jobs.modules.builders:'
            'artifact_resolver',
            'copyartifact=jenkins_jobs.modules.builders:copyartifact',
            'gradle=jenkins_jobs.modules.builders:gradle',
            'batch=jenkins_jobs.modules.builders:batch',
        ],
        'jenkins_jobs.reporters': [
            'email=jenkins_jobs.modules.reporters:email',
        ],
        'jenkins_jobs.properties': [
            'github=jenkins_jobs.modules.properties:github',
            'throttle=jenkins_jobs.modules.properties:throttle',
            'inject=jenkins_jobs.modules.properties:inject',
            'authenticated-build=jenkins_jobs.modules.properties:'
            'authenticated_build',
            'authorization=jenkins_jobs.modules.properties:authorization',
        ],
        'jenkins_jobs.parameters': [
            'string=jenkins_jobs.modules.parameters:string_param',
            'bool=jenkins_jobs.modules.parameters:bool_param',
            'file=jenkins_jobs.modules.parameters:file_param',
            'text=jenkins_jobs.modules.parameters:text_param',
            'label=jenkins_jobs.modules.parameters:label_param',
            'choice=jenkins_jobs.modules.parameters:choice_param',
            'validating-string=jenkins_jobs.modules.parameters:'
            'validating_string_param',
            'svn-tags=jenkins_jobs.modules.parameters:svn_tags_param',
        ],
        'jenkins_jobs.notifications': [
            'http=jenkins_jobs.modules.notifications:http_endpoint',
        ],
        'jenkins_jobs.publishers': [
            'archive=jenkins_jobs.modules.publishers:archive',
            'trigger-parameterized-builds='
            'jenkins_jobs.modules.publishers:trigger_parameterized_builds',
            'trigger=jenkins_jobs.modules.publishers:trigger',
            'coverage=jenkins_jobs.modules.publishers:coverage',
            'ftp=jenkins_jobs.modules.publishers:ftp',
            'junit=jenkins_jobs.modules.publishers:junit',
            'xunit=jenkins_jobs.modules.publishers:xunit',
            'violations=jenkins_jobs.modules.publishers:violations',
            'scp=jenkins_jobs.modules.publishers:scp',
            'pipeline=jenkins_jobs.modules.publishers:pipeline',
            'email=jenkins_jobs.modules.publishers:email',
            'claim-build=jenkins_jobs.modules.publishers:claim_build',
            'email-ext=jenkins_jobs.modules.publishers:email_ext',
            'fingerprint=jenkins_jobs.modules.publishers:fingerprint',
            'aggregate-tests=jenkins_jobs.modules.publishers:aggregate_tests',
            'cppcheck=jenkins_jobs.modules.publishers:cppcheck',
            'logparser=jenkins_jobs.modules.publishers:logparser',
            'copy-to-master=jenkins_jobs.modules.publishers:copy_to_master',
            'jira=jenkins_jobs.modules.publishers:jira',
        ],
        'jenkins_jobs.scm': [
            'git=jenkins_jobs.modules.scm:git',
            'svn=jenkins_jobs.modules.scm:svn',
        ],
        'jenkins_jobs.triggers': [
            'gerrit=jenkins_jobs.modules.triggers:gerrit',
            'pollscm=jenkins_jobs.modules.triggers:pollscm',
            'timed=jenkins_jobs.modules.triggers:timed',
        ],
        'jenkins_jobs.wrappers': [
            'timeout=jenkins_jobs.modules.wrappers:timeout',
            'timestamps=jenkins_jobs.modules.wrappers:timestamps',
            'ansicolor=jenkins_jobs.modules.wrappers:ansicolor',
            'mask-passwords=jenkins_jobs.modules.wrappers:mask_passwords',
            'build-name=jenkins_jobs.modules.wrappers:build_name',
            'workspace-cleanup=jenkins_jobs.modules.wrappers:'
            'workspace_cleanup',
            'port-allocator=jenkins_jobs.modules.wrappers:port_allocator',
            'locks=jenkins_jobs.modules.wrappers:locks',
            'copy-to-slave=jenkins_jobs.modules.wrappers:copy_to_slave',
            'inject=jenkins_jobs.modules.wrappers:inject',
            'jclouds=jenkins_jobs.modules.wrappers:jclouds',
        ],
        'jenkins_jobs.modules': [
            'general=jenkins_jobs.modules.general:General',
            'builders=jenkins_jobs.modules.builders:Builders',
            'properties=jenkins_jobs.modules.properties:Properties',
            'parameters=jenkins_jobs.modules.parameters:Parameters',
            'notifications=jenkins_jobs.modules.notifications:Notifications',
            'publishers=jenkins_jobs.modules.publishers:Publishers',
            'reporters=jenkins_jobs.modules.reporters:Reporters',
            'scm=jenkins_jobs.modules.scm:SCM',
            'triggers=jenkins_jobs.modules.triggers:Triggers',
            'wrappers=jenkins_jobs.modules.wrappers:Wrappers',
            'zuul=jenkins_jobs.modules.zuul:Zuul',
            'hipchat=jenkins_jobs.modules.hipchat_notif:HipChat',
        ]
    }
)
