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
import xml.etree.ElementTree as XML
from xml.dom import minidom
import jenkins
import ConfigParser
from StringIO import StringIO
import re
import pkgutil

import modules

class JenkinsJobsException(Exception): pass

parser = argparse.ArgumentParser()
subparser = parser.add_subparsers(help='update, test or delete job', dest='command')
parser_update = subparser.add_parser('update')
parser_update.add_argument('file', help='YAML file for update', type=file)
parser_update = subparser.add_parser('test')
parser_update.add_argument('file', help='YAML file for test', type=file)
parser_delete = subparser.add_parser('delete')
parser_delete.add_argument('name', help='name of job')
parser.add_argument('--conf', dest='conf', help='Configuration file')
options = parser.parse_args()

if options.conf:
    conf = options.conf
else:
    conf = 'jenkins_jobs.ini'

if not options.command == 'test':
    conffp = open(conf, 'r')
    config = ConfigParser.ConfigParser()
    config.readfp(conffp)

class YamlParser(object):
    def __init__(self, yfile):
        self.registry = ModuleRegistry()
        self.data = yaml.load_all(yfile)
        self.it = self.data.__iter__()
        self.job_name = None
        self.template_data = None
        self.current = None
        self.current_template = None
        self.template_it = None
        self.reading_template = False
        self.eof = False
        self.seek_next_xml()

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
        self.template_data = yaml.load_all(template_steam)
        self.template_it = self.template_data.__iter__()
        self.reading_template = True

    def get_next_xml(self):
        if not self.eof:
            if self.reading_template:
                data = XmlParser(self.current_template, self.registry)
                self.job_name = self.current_template['main']['name']
            else:
                data = XmlParser(self.current, self.registry)
                self.job_name = self.current['main']['name']
            self.seek_next_xml()
            return data
        else:
            raise JenkinsJobsException('End of file')

    def seek_next_xml(self):
        if self.reading_template:
            try:
                self.current_template = self.template_it.next()
                return
            except StopIteration:
                self.reading_template = False
        try:
            self.current = self.it.next()
        except StopIteration:
            self.eof = True

        if self.current.has_key('project'):
            self.process_template()
            self.current_template = self.template_it.next()

    def get_name(self):
        return self.job_name

class ModuleRegistry(object):
    # TODO: make this extensible

    def __init__(self):
        self.modules = []
        self.handlers = {}

        for importer, modname, ispkg in pkgutil.iter_modules(modules.__path__):
            module = __import__('modules.'+modname, fromlist=['register'])
            register = getattr(module, 'register', None)
            if register:
                register(self)

    def registerModule(self, mod):
        self.modules.append(mod)
        self.modules.sort(lambda a, b: cmp(a.sequence, b.sequence))

    def registerHandler(self, category, name, method):
        cat_dict = self.handlers.get(category, {})
        if not cat_dict:
            self.handlers[category] = cat_dict
        cat_dict[name] = method

    def getHandler(self, category, name):
        return self.handlers[category][name]

class XmlParser(object):
    def __init__(self, data, registry):
        self.data = data
        self.registry = registry
        self._build()

    def _build(self):
        for module in self.registry.modules:
            if hasattr(module, 'root_xml'):
                element = module.root_xml(self.data)
                if element is not None:
                    self.xml = element

        for module in self.registry.modules:
            if hasattr(module, 'handle_data'):
                module.handle_data(self.data)
        
        XML.SubElement(self.xml, 'actions')
        description = XML.SubElement(self.xml, 'description')
        description.text = "THIS JOB IS MANAGED BY PUPPET AND WILL BE OVERWRITTEN.\n\n\
DON'T EDIT THIS JOB THROUGH THE WEB\n\n\
If you would like to make changes to this job, please see:\n\n\
https://github.com/openstack/openstack-ci-puppet\n\n\
In modules/jenkins_jobs"
        XML.SubElement(self.xml, 'keepDependencies').text = 'false'
        if self.data['main'].get('disabled'):
            XML.SubElement(self.xml, 'disabled').text = 'true'
        else:
            XML.SubElement(self.xml, 'disabled').text = 'false'
        XML.SubElement(self.xml, 'blockBuildWhenDownstreamBuilding').text = 'false'
        XML.SubElement(self.xml, 'blockBuildWhenUpstreamBuilding').text = 'false'
        if self.data['main'].get('concurrent'):
            XML.SubElement(self.xml, 'concurrentBuild').text = 'true'
        else:
            XML.SubElement(self.xml, 'concurrentBuild').text = 'false'

        for module in self.registry.modules:
            if hasattr(module, 'gen_xml'):
                module.gen_xml(self.xml, self.data)

    def md5(self):
        return hashlib.md5(self.output()).hexdigest()

    # Pretty printing ideas from http://stackoverflow.com/questions/749796/pretty-printing-xml-in-python
    pretty_text_re = re.compile('>\n\s+([^<>\s].*?)\n\s+</', re.DOTALL)

    def output(self):
        out = minidom.parseString(XML.tostring(self.xml)).toprettyxml(indent='  ')
        return self.pretty_text_re.sub('>\g<1></', out)


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
         if self.is_job(job_name):
             self.jenkins.reconfig_job(job_name, xml)
         else:
             self.jenkins.create_job(job_name, xml)

     def is_job(self, job_name):
         return self.jenkins.job_exists(job_name)

     def get_job_md5(self, job_name):
         xml = self.jenkins.get_job_config(job_name)
         return hashlib.md5(xml).hexdigest()

     def delete_job(self, job_name):
         if self.is_job(job_name):
             self.jenkins.delete_job(job_name)

def delete_job():
    remote_jenkins = Jenkins(config.get('jenkins','url'), config.get('jenkins','user'), config.get('jenkins','password'))
    remote_jenkins.delete_job(options.name)

def update_job(test = False):
    yparse = YamlParser(options.file)
    cache = CacheStorage()
    if not test:
        remote_jenkins = Jenkins(config.get('jenkins','url'), config.get('jenkins','user'), config.get('jenkins','password'))
    while True:
        try:
            xml = yparse.get_next_xml()
            job = yparse.get_name()
            if test:
                print xml.output()
                continue
            md5 = xml.md5()
            if remote_jenkins.is_job(job) and not cache.is_cached(job):
                old_md5 = remote_jenkins.get_job_md5(job)
                cache.set(job, old_md5)

            if cache.has_changed(job, md5):
                remote_jenkins.update_job(job, xml.output())
                cache.set(job, md5)
        except JenkinsJobsException:
            break

if options.command == 'delete':
    delete_job()
elif options.command == 'update':
    update_job()
elif options.command == 'test':
    update_job(True)

