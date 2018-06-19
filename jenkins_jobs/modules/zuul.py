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

"""
The Zuul module adds jobs parameters to manually run a build as Zuul would
have. It is entirely optional, Zuul 2.0+ pass the parameters over Gearman.

.. _expected by Zuul: \
http://docs.openstack.org/infra/zuul/launchers.html#zuul-parameters
"""

import itertools
import jenkins_jobs.modules.base


def zuul():
    """yaml: zuul
    Configure this job to be triggered by Zuul.

    Adds parameters describing the change triggering the build such as the
    branch name, change number and patchset.

    See parameters `expected by Zuul`_.

    Example::

      triggers:
        - zuul
    """


def zuul_post():
    """yaml: zuul-post
    Configure this post-merge job to be triggered by Zuul.

    Adds parameters describing the reference update triggering the build, which
    are the previous and next revisions in full (40 hexadecimal sha1) and short
    form.

    See parameters `expected by Zuul`_.

    Example::

      triggers:
        - zuul-post
    """


ZUUL_PARAMETERS = [
    {'string':
        {'description': 'Zuul provided key to link builds with Gerrit events',
         'name': 'ZUUL_UUID'}},
    {'string':
        {'description': 'Zuul provided key to link builds with Gerrit'
         ' events (deprecated use ZUUL_UUID instead)',
         'name': 'UUID'}},
    {'string':
        {'description': 'Zuul pipeline triggering this job',
         'name': 'ZUUL_PIPELINE'}},
    {'string':
        {'description': 'URL of Zuul\'s git repos accessible to workers',
         'name': 'ZUUL_URL'}},
    {'string':
        {'description': 'Branch name of triggering project',
         'name': 'ZUUL_PROJECT'}},
    {'string':
        {'description': 'Branch name of triggering change',
         'name': 'ZUUL_BRANCH'}},
    {'string':
        {'description': 'List of dependent changes to merge',
         'name': 'ZUUL_CHANGES'}},
    {'string':
        {'description': 'Reference for the merged commit(s) to use',
         'name': 'ZUUL_REF'}},
    {'string':
        {'description': 'The commit SHA1 at the head of ZUUL_REF',
         'name': 'ZUUL_COMMIT'}},
    {'string':
        {'description': 'List of included changes',
         'name': 'ZUUL_CHANGE_IDS'}},
    {'string':
        {'description': 'ID of triggering change',
         'name': 'ZUUL_CHANGE'}},
    {'string':
        {'description': 'Patchset of triggering change',
         'name': 'ZUUL_PATCHSET'}},
    {'string':
        {'description': 'Zuul considered this job voting or not',
         'name': 'ZUUL_VOTING'}},
]

ZUUL_POST_PARAMETERS = [
    {'string':
        {'description': 'Zuul provided key to link builds with Gerrit events',
         'name': 'ZUUL_UUID'}},
    {'string':
        {'description': 'Zuul provided key to link builds with Gerrit'
         ' events (deprecated use ZUUL_UUID instead)',
         'name': 'UUID'}},
    {'string':
        {'description': 'Zuul pipeline triggering this job',
         'name': 'ZUUL_PIPELINE'}},
    {'string':
        {'description': 'URL of Zuul\'s git repos accessible to workers',
         'name': 'ZUUL_URL'}},
    {'string':
        {'description': 'Branch name of triggering project',
         'name': 'ZUUL_PROJECT'}},
    {'string':
        {'description': 'Name of updated reference triggering this job',
         'name': 'ZUUL_REF'}},
    {'string':
        {'description': 'Name of updated reference triggering this job',
         'name': 'ZUUL_REFNAME'}},
    {'string':
        {'description': 'Old SHA at this reference',
         'name': 'ZUUL_OLDREV'}},
    {'string':
        {'description': 'New SHA at this reference',
         'name': 'ZUUL_NEWREV'}},
    {'string':
        {'description': 'Shortened new SHA at this reference',
         'name': 'ZUUL_SHORT_NEWREV'}},
]


class Zuul(jenkins_jobs.modules.base.Base):
    sequence = 0

    def handle_data(self, job_data):
        changed = False
        jobs = itertools.chain(
            job_data.get('job', {}).values(),
            job_data.get('job-template', {}).values())
        for job in jobs:
            triggers = job.get('triggers')
            if not triggers:
                continue

            if ('zuul' not in job.get('triggers', []) and
                    'zuul-post' not in job.get('triggers', [])):
                continue
            if 'parameters' not in job:
                job['parameters'] = []
            if 'zuul' in job.get('triggers', []):
                job['parameters'].extend(ZUUL_PARAMETERS)
                job['triggers'].remove('zuul')
            if 'zuul-post' in job.get('triggers', []):
                job['parameters'].extend(ZUUL_POST_PARAMETERS)
                job['triggers'].remove('zuul-post')
            changed = True
        return changed
