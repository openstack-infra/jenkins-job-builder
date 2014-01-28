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

# Representation of the hudson.model.Result class

SUCCESS = {
    'name': 'SUCCESS',
    'ordinal': '0',
    'color': 'BLUE',
    'complete': True
}

UNSTABLE = {
    'name': 'UNSTABLE',
    'ordinal': '1',
    'color': 'YELLOW',
    'complete': True
}

FAILURE = {
    'name': 'FAILURE',
    'ordinal': '2',
    'color': 'RED',
    'complete': True
}

NOTBUILD = {
    'name': 'NOT_BUILD',
    'ordinal': '3',
    'color': 'NOTBUILD',
    'complete': False
}

ABORTED = {
    'name': 'ABORTED',
    'ordinal': '4',
    'color': 'ABORTED',
    'complete': False
}

THRESHOLDS = {
    'SUCCESS': SUCCESS,
    'UNSTABLE': UNSTABLE,
    'FAILURE': FAILURE,
    'NOT_BUILD': NOTBUILD,
    'ABORTED': ABORTED
}
