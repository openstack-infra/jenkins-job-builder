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

# A basic API class to talk to a Jenkins Server

import pycurl
from StringIO import StringIO

class JenkinsTalkerException(Exception): pass

class JenkinsTalker(object):
    def __init__(self, url, user, password):
        self.url = url
        self.user = user
        self.password = password

    def _post_xml(self, path, xml, pass_codes):
        curl = pycurl.Curl()
        response = StringIO()
        curl.setopt(pycurl.URL, self.url + path)
        curl.setopt(pycurl.USERPWD, self.user + ":" +  self.password)
        curl.setopt(pycurl.POST, 1)
        curl.setopt(pycurl.POSTFIELDS, xml)
        curl.setopt(pycurl.HTTPHEADER, [ "Content-Type: text/xml" ])
        curl.setopt(pycurl.POSTFIELDSIZE, len(xml))
        # should probably shove this response into a debug output somewhere
        curl.setopt(pycurl.WRITEFUNCTION, response.write)
        curl.perform()
        if curl.getinfo(pycurl.RESPONSE_CODE) not in pass_codes:
            raise JenkinsTalkerException('error posting XML')
        curl.close()

    def _get_request(self, path, pass_codes, post=False):
        curl = pycurl.Curl()
        response = StringIO()
        curl.setopt(pycurl.URL, self.url + path)
        if post == True:
            curl.setopt(pycurl.POST, 1)
            curl.setopt(pycurl.POSTFIELDSIZE, 0)
        curl.setopt(pycurl.USERPWD, self.user + ":" +  self.password)
        curl.setopt(pycurl.WRITEFUNCTION, response.write)
        curl.perform()
        print response.getvalue()
        if curl.getinfo(pycurl.RESPONSE_CODE) not in pass_codes:
            raise JenkinsTalkerException('error getting response')
        curl.close()
        return response.getvalue()

    def create_job(self, job_name, xml):
        path = 'createItem?name=' + job_name
        pass_codes = [ 200 ]
        self._post_xml(path, xml, pass_codes)

    def update_job(self, job_name, xml):
        path = 'job/' + job_name + '/config.xml'
        pass_codes = [ 200 ]
        self._post_xml(path, xml, pass_codes)

    def delete_job(self, job_name):
        path = 'job/' + job_name + '/doDelete'
        pass_codes = [ 302 ]
        self._get_request(path, pass_codes, True)

    def get_job_config(self, job_name):
        path = 'job/' + job_name + '/config.xml'
        pass_codes = [ 200 ]
        return self._get_request(path, pass_codes)

    def is_job(self, job_name):
        try:
            self.get_job_config(job_name)
        except JenkinsTalkerException:
            return False
        return True

