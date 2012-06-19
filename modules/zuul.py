#! /usr/bin/env python
# Copyright (C) 2012 OpenStack, LLC.
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

ZUUL_PARAMETERS = [
    {'description': 'Zuul provided key to link builds with Gerrit events',
     'name': 'UUID',
     'type': 'string'},
    {'description': 'Zuul provided project name',
     'name': 'GERRIT_PROJECT',
     'type': 'string'},
    {'description': 'Zuul provided branch name',
     'name': 'GERRIT_BRANCH',
     'type': 'string'},
    {'description': 'Zuul provided list of dependent changes to merge',
     'name': 'GERRIT_CHANGES',
     'type': 'string'}
    ]

ZUUL_POST_PARAMETERS = [
    {'description': 'Zuul provided key to link builds with Gerrit events',
     'name': 'UUID',
     'type': 'string'},
    {'description': 'Zuul provided project name',
     'name': 'GERRIT_PROJECT',
     'type': 'string'},
    {'description': 'Zuul provided ref name',
     'name': 'GERRIT_REFNAME',
     'type': 'string'},
    {'description': 'Zuul provided old reference for ref-updated',
     'name': 'GERRIT_OLDREV',
     'type': 'string'},
    {'description': 'Zuul provided new reference for ref-updated',
     'name': 'GERRIT_NEWREV',
     'type': 'string'}
    ]

ZUUL_NOTIFICATIONS = [
    {'URL': 'http://127.0.0.1:8001/jenkins_endpoint',
     'protocol': 'HTTP'}
    ]


def register(registry):
    mod = Zuul()
    registry.registerModule(mod)


class Zuul(object):
    sequence = 0

    def handle_data(self, data):
        if ('zuul' not in data.get('triggers', []) and
            'zuul_post' not in data.get('triggers', [])):
            return
        if 'parameters' not in data:
            data['parameters'] = []
        if 'notification_endpoints' not in data:
            data['notification_endpoints'] = []
        data['notification_endpoints'].extend(ZUUL_NOTIFICATIONS)
        if 'zuul' in data.get('triggers', []):
            data['parameters'].extend(ZUUL_PARAMETERS)
            data['triggers'].remove('zuul')
        if 'zuul_post' in data.get('triggers', []):
            data['parameters'].extend(ZUUL_POST_PARAMETERS)
            data['triggers'].remove('zuul_post')
