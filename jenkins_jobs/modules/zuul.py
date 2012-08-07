# Copyright 2012 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

# Jenkins Job module for Zuul

import jenkins_jobs.modules.base


ZUUL_PARAMETERS = [
    {'string':
         {'description': 'Zuul provided key to link builds with Gerrit events',
          'name': 'UUID'}},
    {'string':
         {'description': 'Zuul provided project name',
          'name': 'GERRIT_PROJECT'}},
    {'string':
         {'description': 'Zuul provided branch name',
          'name': 'GERRIT_BRANCH'}},
    {'string':
         {'description': 'Zuul provided list of dependent changes to merge',
          'name': 'GERRIT_CHANGES'}},
    ]

ZUUL_POST_PARAMETERS = [
    {'string':
         {'description': 'Zuul provided key to link builds with Gerrit events',
          'name': 'UUID'}},
    {'string':
         {'description': 'Zuul provided project name',
          'name': 'GERRIT_PROJECT'}},
    {'string':
         {'description': 'Zuul provided ref name',
          'name': 'GERRIT_REFNAME'}},
    {'string':
         {'description': 'Zuul provided old reference for ref-updated',
          'name': 'GERRIT_OLDREV'}},
    {'string':
         {'description': 'Zuul provided new reference for ref-updated',
          'name': 'GERRIT_NEWREV'}},
    ]

ZUUL_NOTIFICATIONS = [
    {'http':
         {'url': 'http://127.0.0.1:8001/jenkins_endpoint'}}
    ]

class Zuul(jenkins_jobs.modules.base.Base):
    sequence = 0

    def handle_data(self, parser):
        changed = False
        jobs = (parser.data.get('job', {}).values() +
                parser.data.get('job-template', {}).values())
        for job in jobs:
            triggers = job.get('triggers')
            if not triggers:
                continue

            if ('zuul' not in job.get('triggers', []) and
                'zuul_post' not in job.get('triggers', [])):
                continue
            if 'parameters' not in job:
                job['parameters'] = []
            if 'notifications' not in job:
                job['notifications'] = []
            job['notifications'].extend(ZUUL_NOTIFICATIONS)
            if 'zuul' in job.get('triggers', []):
                job['parameters'].extend(ZUUL_PARAMETERS)
                job['triggers'].remove('zuul')
            if 'zuul_post' in job.get('triggers', []):
                job['parameters'].extend(ZUUL_POST_PARAMETERS)
                job['triggers'].remove('zuul_post')
            changed = True
        return changed
