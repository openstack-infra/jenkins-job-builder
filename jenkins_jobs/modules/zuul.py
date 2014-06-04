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
The Zuul module adds triggers that configure jobs for use with Zuul_. It
essentially adds the jobs parameters `expected by Zuul`_.

With Zuul version 2.0 and later, this is optional. The jobs are
triggered via the Jenkins Gearman plugin which passes the parameters
internally.  You might still want to explicitly define parameters to
retain the possibility of triggering jobs manually via the Jenkins web
interface (build with parameters).

To change the Zuul notification URL, set a global default::

  - defaults:
    name: global
    zuul-url: http://127.0.0.1:8001/jenkins_endpoint

The above URL is the default.

.. _Zuul: http://ci.openstack.org/zuul/
.. _expected by Zuul: \
http://ci.openstack.org/zuul/launchers.html#zuul-parameters
"""

import itertools


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

import jenkins_jobs.modules.base

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

DEFAULT_URL = 'http://127.0.0.1:8001/jenkins_endpoint'


class Zuul(jenkins_jobs.modules.base.Base):
    sequence = 0

    def handle_data(self, parser):
        changed = False
        jobs = itertools.chain(parser.data.get('job', {}).values(),
                               parser.data.get('job-template', {}).values())
        for job in jobs:
            triggers = job.get('triggers')
            if not triggers:
                continue

            if ('zuul' not in job.get('triggers', []) and
                'zuul-post' not in job.get('triggers', [])):
                continue
            if 'parameters' not in job:
                job['parameters'] = []
            if 'notifications' not in job:
                job['notifications'] = []
            # This isn't a good pattern, and somewhat violates the
            # spirit of the global defaults, but Zuul is working on
            # a better design that should obviate the need for most
            # of this module, so this gets it done with minimal
            # intrusion to the rest of JJB.
            if parser.data.get('defaults', {}).get('global'):
                url = parser.data['defaults']['global'].get(
                    'zuul-url', DEFAULT_URL)
                notifications = [{'http': {'url': url}}]
                job['notifications'].extend(notifications)
            if 'zuul' in job.get('triggers', []):
                job['parameters'].extend(ZUUL_PARAMETERS)
                job['triggers'].remove('zuul')
            if 'zuul-post' in job.get('triggers', []):
                job['parameters'].extend(ZUUL_POST_PARAMETERS)
                job['triggers'].remove('zuul-post')
            changed = True
        return changed
