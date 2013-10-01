#!/usr/bin/env python
#
# Joint copyright:
#  - Copyright 2012,2013 Wikimedia Foundation
#  - Copyright 2012,2013 Antoine "hashar" Musso
#  - Copyright 2013 Arnaud Fabre
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

import os
import re


def get_scenarios(fixtures_path):
    """Returns a list of scenarios, each scenario being described
    by two parameters (yaml and xml filenames).
        - content of the fixture .xml file (aka expected)
    """
    scenarios = []
    files = os.listdir(fixtures_path)
    yaml_files = [f for f in files if re.match(r'.*\.yaml$', f)]

    for yaml_filename in yaml_files:
        xml_candidate = re.sub(r'\.yaml$', '.xml', yaml_filename)
        # Make sure the yaml file has a xml counterpart
        if xml_candidate not in files:
            raise Exception(
                "No XML file named '%s' to match " +
                "YAML file '%s'" % (xml_candidate, yaml_filename))

        scenarios.append((yaml_filename, {
            'yaml_filename': yaml_filename, 'xml_filename': xml_candidate
        }))

    return scenarios
