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

# Manage jobs in Jenkins server

import os
import argparse
import hashlib
import yaml
import sys
import xml.etree.ElementTree as XML
import pycurl
import jenkins
import ConfigParser
from StringIO import StringIO

parser = argparse.ArgumentParser()
subparser = parser.add_subparsers(help='update or delete job', dest='command')
parser_update = subparser.add_parser('update')
parser_update.add_argument('file', help='YAML file for update', type=file)
parser_delete = subparser.add_parser('delete')
parser_delete.add_argument('name', help='name of job')
parser.add_argument('--conf', dest='conf', help='Configuration file')
options = parser.parse_args()

if options.conf:
  conf = options.conf
else:
  conf = 'jenkins_jobs.ini'

conffp = open(conf, 'r')
config = ConfigParser.ConfigParser()
config.readfp(conffp)

class YamlParser(object):
    def __init__(self, yfile):
        self.data = yaml.load_all(yfile)
        self.it = self.data.__iter__()
        self.current = self.it.next()
        if self.current.has_key('project'):
            self.process_template()
        self.it = self.data.__iter__()

    def process_template(self):
        project_data = self.current['project']
        template_file = file('templates/' + project_data['template']  + '.yml', 'r')
        template = template_file.read()
        template_file.close()
        values = self.current['values'].iteritems()
        for key, value in values:
            key = '@' + key.upper() + '@'
            template = template.replace(key, value)
        template_steam = StringIO(template)
        self.data = yaml.load_all(template_steam)

    def get_next_xml(self):
        self.current = self.it.next()
        return XmlParser(self.current)

    def get_name(self):
        return self.current['main']['name']


class XmlParser(object):
    def __init__(self, data):
        self.data = data
        self.xml = XML.Element('project')
        self.modules = []
        self._load_modules()
        self._build()

    def _load_modules(self):
        for modulename in self.data['modules']:
            modulename = 'modules.{name}'.format(name=modulename)
            self._register_module(modulename)

    def _register_module(self, modulename):
        classname = modulename.rsplit('.', 1)[1]
        module = __import__(modulename, fromlist=[classname])
        cla = getattr(module, classname)
        self.modules.append(cla(self.data))

    def _build(self):
        XML.SubElement(self.xml, 'actions')
        description = XML.SubElement(self.xml, 'description')
        description.text = "THIS JOB IS MANAGED BY PUPPET AND WILL BE OVERWRITTEN.\n\n\
DON'T EDIT THIS JOB THROUGH THE WEB\n\n\
If you would like to make changes to this job, please see:\n\n\
https://github.com/openstack/openstack-ci-puppet\n\n\
In modules/jenkins_jobs"
        XML.SubElement(self.xml, 'keepDependencies').text = 'false'
        XML.SubElement(self.xml, 'disabled').text = self.data['main']['disabled']
        XML.SubElement(self.xml, 'blockBuildWhenDownstreamBuilding').text = 'false'
        XML.SubElement(self.xml, 'blockBuildWhenUpstreamBuilding').text = 'false'
        XML.SubElement(self.xml, 'concurrentBuild').text = 'false'
        XML.SubElement(self.xml, 'buildWrappers')
        self._insert_modules()

    def _insert_modules(self):
        for module in self.modules:
            module.gen_xml(self.xml)

    def md5(self):
        return hashlib.md5(self.output()).hexdigest()

    def output(self):
        return XML.tostring(self.xml)

class CacheStorage(object):
     def __init__(self):
         self.cachefilename = os.path.expanduser('~/.jenkins_jobs_cache.yml')
         try:
             yfile = file(self.cachefilename, 'r')
         except IOError:
             self.data = {}
             return
         self.data = yaml.load(yfile)
         yfile.close()

     def set(self, job, md5):
         self.data[job] = md5
         yfile = file(self.cachefilename, 'w')
         yaml.dump(self.data, yfile)
         yfile.close()

     def is_cached(self, job):
         if self.data.has_key(job):
            return True
         return False

     def has_changed(self, job, md5):
         if self.data.has_key(job) and self.data[job] == md5:
            return False
         return True
         
class Jenkins(object):
     def __init__(self, url, user, password):
         self.jenkins = jenkins.Jenkins(url, user, password)

     def update_job(self, job_name, xml):
         if self.jenkins.is_job(job_name):
             self.jenkins.reconfig_job(job_name, xml)
         else:
             self.jenkins.create_job(job_name, xml)

     def is_job(self, job_name):
         return self.jenkins.job_exists(job_name)

     def get_job_md5(self, job_name):
         xml = self.jenkins.get_job_config(job_name)
         return hashlib.md5(xml).hexdigest()

     def delete_job(self, job_name):
         if self.jenkins.is_job(job_name):
             self.jenkins.delete_job(job_name)

def delete_job():
    remote_jenkins = Jenkins(config.get('jenkins','url'), config.get('jenkins','user'), config.get('jenkins','password'))
    remote_jenkins.delete_job(options.name)

def update_job():
    yparse = YamlParser(options.file)
    cache = CacheStorage()
    remote_jenkins = Jenkins(config.get('jenkins','url'), config.get('jenkins','user'), config.get('jenkins','password'))
    while True:
        try:
            xml = yparse.get_next_xml()
            job = yparse.get_name()
            md5 = xml.md5()
            if remote_jenkins.is_job(job) and not cache.is_cached(job):
                old_md5 = remote_jenkins.get_job_md5(job)
                cache.set(job, old_md5)

            if cache.has_changed(job, md5):
                remote_jenkins.update_job(job, xml.output())
                cache.set(job, md5)
        except StopIteration:
            break

if options.command == 'delete':
    delete_job()
elif options.command == 'update':
    update_job()

