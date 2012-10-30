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

from setuptools import find_packages
from setuptools import setup

setup(name='jenkins_job_builder',
      version='0.1',
      description="Manage Jenkins jobs with YAML",
      license='Apache License (2.0)',
      author='Hewlett-Packard Development Company, L.P.',
      author_email='openstack@lists.launchpad.net',
      scripts=['jenkins-jobs'],
      include_package_data=True,
      zip_safe=False,
      packages=find_packages(),

      entry_points={
        'jenkins_jobs.projects': [
            'freestyle=jenkins_jobs.modules.project_freestyle:Freestyle',
            'maven=jenkins_jobs.modules.project_maven:Maven',
            ],
        'jenkins_jobs.builders': [
            'shell=jenkins_jobs.modules.builders:shell',
            'ant=jenkins_jobs.modules.builders:ant',
            'trigger-builds=jenkins_jobs.modules.builders:trigger_builds',
            'builders-from=jenkins_jobs.modules.builders:builders_from',
            'inject=jenkins_jobs.modules.builders:inject',
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
            'claim-build=jenkins_jobs.modules.publishers:claimbuild',
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
            ],
        'jenkins_jobs.modules': [
            'assignednode=jenkins_jobs.modules.assignednode:AssignedNode',
            'builders=jenkins_jobs.modules.builders:Builders',
            'logrotate=jenkins_jobs.modules.logrotate:LogRotate',
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
