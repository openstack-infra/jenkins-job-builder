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
            'trigger-builds=jenkins_jobs.modules.builders:trigger_builds',
            'builders-from=jenkins_jobs.modules.builders:builders_from',
            ],
        'jenkins_jobs.properties': [
            'github=jenkins_jobs.modules.properties:github',
            'throttle=jenkins_jobs.modules.properties:throttle',
            'inject=jenkins_jobs.modules.properties:inject',
            'authenticated-build=jenkins_jobs.modules.properties:'
              'authenticated_build',
            ],
        'jenkins_jobs.parameters': [
            'string=jenkins_jobs.modules.properties:string_param',
            'bool=jenkins_jobs.modules.properties:bool_param',
            'file=jenkins_jobs.modules.properties:file_param',
            'text=jenkins_jobs.modules.properties:text_param',
            'label=jenkins_jobs.modules.properties:label_param',
            ],
        'jenkins_jobs.notifications': [
            'http=jenkins_jobs.modules.properties:http_endpoint',
            ],
        'jenkins_jobs.publishers': [
            'archive=jenkins_jobs.modules.publishers:archive',
            'trigger-parameterized-builds='
                'jenkins_jobs.modules.publishers:trigger_parameterized_builds',
            'coverage=jenkins_jobs.modules.publishers:coverage',
            'ftp=jenkins_jobs.modules.publishers:ftp',
            'junit=jenkins_jobs.modules.publishers:junit',
            'violations=jenkins_jobs.modules.publishers:violations',
            'scp=jenkins_jobs.modules.publishers:scp',
            ],
        'jenkins_jobs.scm': [
            'git=jenkins_jobs.modules.scm:git',
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
            ],
        'jenkins_jobs.modules': [
            'assignednode=jenkins_jobs.modules.assignednode:AssignedNode',
            'builders=jenkins_jobs.modules.builders:Builders',
            'logrotate=jenkins_jobs.modules.logrotate:LogRotate',
            'properties=jenkins_jobs.modules.properties:Properties',
            'publishers=jenkins_jobs.modules.publishers:Publishers',
            'scm=jenkins_jobs.modules.scm:SCM',
            'triggers=jenkins_jobs.modules.triggers:Triggers',
            'wrappers=jenkins_jobs.modules.wrappers:Wrappers',
            'zuul=jenkins_jobs.modules.zuul:Zuul',
            ]
        }

      )
