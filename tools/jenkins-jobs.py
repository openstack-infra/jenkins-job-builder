#!/usr/bin/env python
# Copyright (C) 2013 OpenStack Foundation
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

# A simple test script to invoke the command entry point from the
# source directory without the necessity of installation.

import os
import sys
sys.path.append(os.path.abspath('.'))

import jenkins_jobs.cmd

jenkins_jobs.cmd.main()
