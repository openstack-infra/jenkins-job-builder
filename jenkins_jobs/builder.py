#!/usr/bin/env python
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
import hashlib
import yaml
import xml.etree.ElementTree as XML
from xml.dom import minidom
import jenkins
import re
import pkg_resources
import logging
import copy
import itertools

logger = logging.getLogger(__name__)


def deep_format(obj, paramdict):
    """Apply the paramdict via str.format() to all string objects found within
       the supplied obj. Lists and dicts are traversed recursively."""
    # YAML serialisation was originally used to achieve this, but that places
    # limitations on the values in paramdict - the post-format result must
    # still be valid YAML (so substituting-in a string containing quotes, for
    # example, is problematic).
    if isinstance(obj, str):
        ret = obj.format(**paramdict)
    elif isinstance(obj, list):
        ret = []
        for item in obj:
            ret.append(deep_format(item, paramdict))
    elif isinstance(obj, dict):
        ret = {}
        for item in obj:
            ret[item] = deep_format(obj[item], paramdict)
    else:
        ret = obj
    return ret


class YamlParser(object):
    def __init__(self, config=None):
        self.registry = ModuleRegistry(config)
        self.data = {}
        self.jobs = []

    def parse(self, fn):
        data = yaml.load(open(fn))
        for item in data:
            cls, dfn = item.items()[0]
            group = self.data.get(cls, {})
            name = dfn['name']
            group[name] = dfn
            self.data[cls] = group

    def getJob(self, name):
        job = self.data.get('job', {}).get(name, None)
        if not job:
            return job
        return self.applyDefaults(job)

    def getJobGroup(self, name):
        return self.data.get('job-group', {}).get(name, None)

    def getJobTemplate(self, name):
        job = self.data.get('job-template', {}).get(name, None)
        if not job:
            return job
        return self.applyDefaults(job)

    def applyDefaults(self, data):
        whichdefaults = data.get('defaults', 'global')
        defaults = self.data.get('defaults', {}).get(whichdefaults, {})
        newdata = {}
        newdata.update(defaults)
        newdata.update(data)
        return newdata

    def generateXML(self):
        changed = True
        while changed:
            changed = False
            for module in self.registry.modules:
                if hasattr(module, 'handle_data'):
                    if module.handle_data(self):
                        changed = True

        for job in self.data.get('job', {}).values():
            logger.debug("XMLifying job '{0}'".format(job['name']))
            job = self.applyDefaults(job)
            self.getXMLForJob(job)
        for project in self.data.get('project', {}).values():
            logger.debug("XMLifying project '{0}'".format(project['name']))
            for jobspec in project.get('jobs', []):
                if isinstance(jobspec, dict):
                    # Singleton dict containing dict of job-specific params
                    jobname, jobparams = jobspec.items()[0]
                else:
                    jobname = jobspec
                    jobparams = {}
                job = self.getJob(jobname)
                if job:
                    # Just naming an existing defined job
                    continue
                # see if it's a job group
                group = self.getJobGroup(jobname)
                if group:
                    for group_jobname in group['jobs']:
                        job = self.getJob(group_jobname)
                        if job:
                            continue
                        template = self.getJobTemplate(group_jobname)
                        # Allow a group to override parameters set by a project
                        d = {}
                        d.update(project)
                        d.update(group)
                        # Except name, since the group's name is not useful
                        d['name'] = project['name']
                        if template:
                            self.getXMLForTemplateJob(d, template)
                    continue
                # see if it's a template
                template = self.getJobTemplate(jobname)
                if template:
                    d = {}
                    d.update(project)
                    d.update(jobparams)
                    self.getXMLForTemplateJob(d, template)

    def getXMLForTemplateJob(self, project, template):
        dimensions = []
        for (k, v) in project.items():
            if type(v) == list and k not in ['jobs']:
                dimensions.append(zip([k] * len(v), v))
        # XXX somewhat hackish to ensure we actually have a single
        # pass through the loop
        if len(dimensions) == 0:
            dimensions = [(("", ""),)]
        for values in itertools.product(*dimensions):
            params = copy.deepcopy(project)
            params.update(values)
            logger.debug("Generating XML for template job {0}"
                         " (params {1})".format(
                             template['name'], params))
            self.getXMLForJob(deep_format(template, params))

    def getXMLForJob(self, data):
        kind = data.get('project-type', 'freestyle')
        for ep in pkg_resources.iter_entry_points(
            group='jenkins_jobs.projects', name=kind):
            Mod = ep.load()
            mod = Mod(self.registry)
            xml = mod.root_xml(data)
            self.gen_xml(xml, data)
            job = XmlJob(xml, data['name'])
            self.jobs.append(job)
            break

    def gen_xml(self, xml, data):
        for module in self.registry.modules:
            if hasattr(module, 'gen_xml'):
                module.gen_xml(self, xml, data)


class ModuleRegistry(object):
    def __init__(self, config):
        self.modules = []
        self.handlers = {}
        self.global_config = config

        for entrypoint in pkg_resources.iter_entry_points(
            group='jenkins_jobs.modules'):
            Mod = entrypoint.load()
            mod = Mod(self)
            self.modules.append(mod)
            self.modules.sort(lambda a, b: cmp(a.sequence, b.sequence))

    def registerHandler(self, category, name, method):
        cat_dict = self.handlers.get(category, {})
        if not cat_dict:
            self.handlers[category] = cat_dict
        cat_dict[name] = method

    def getHandler(self, category, name):
        return self.handlers[category][name]


class XmlJob(object):
    def __init__(self, xml, name):
        self.xml = xml
        self.name = name

    def md5(self):
        return hashlib.md5(self.output()).hexdigest()

    # Pretty printing ideas from
    # http://stackoverflow.com/questions/749796/pretty-printing-xml-in-python
    pretty_text_re = re.compile('>\n\s+([^<>\s].*?)\n\s+</', re.DOTALL)

    def output(self):
        out = minidom.parseString(XML.tostring(self.xml))
        out = out.toprettyxml(indent='  ')
        return self.pretty_text_re.sub('>\g<1></', out)


class CacheStorage(object):
    def __init__(self):
        cache_dir = self.get_cache_dir()
        self.cachefilename = os.path.join(cache_dir, 'jenkins_jobs_cache.yml')
        try:
            yfile = file(self.cachefilename, 'r')
        except IOError:
            self.data = {}
            return
        self.data = yaml.load(yfile)
        yfile.close()

    @staticmethod
    def get_cache_dir():
        home = os.path.expanduser('~')
        if home == '~':
            raise OSError('Could not locate home folder')
        xdg_cache_home = os.environ.get('XDG_CACHE_HOME') or \
            os.path.join(home, '.cache')
        path = os.path.join(xdg_cache_home, 'jenkins_jobs')
        if not os.path.isdir(path):
            os.makedirs(path)
        return path

    def set(self, job, md5):
        self.data[job] = md5
        yfile = file(self.cachefilename, 'w')
        yaml.dump(self.data, yfile)
        yfile.close()

    def is_cached(self, job):
        if job in self.data:
            return True
        return False

    def has_changed(self, job, md5):
        if job in self.data and self.data[job] == md5:
            return False
        return True


class Jenkins(object):
    def __init__(self, url, user, password):
        self.jenkins = jenkins.Jenkins(url, user, password)

    def update_job(self, job_name, xml):
        if self.is_job(job_name):
            logger.info("Reconfiguring jenkins job {0}".format(job_name))
            self.jenkins.reconfig_job(job_name, xml)
        else:
            logger.info("Creating jenkins job {0}".format(job_name))
            self.jenkins.create_job(job_name, xml)

    def is_job(self, job_name):
        return self.jenkins.job_exists(job_name)

    def get_job_md5(self, job_name):
        xml = self.jenkins.get_job_config(job_name)
        return hashlib.md5(xml).hexdigest()

    def delete_job(self, job_name):
        if self.is_job(job_name):
            self.jenkins.delete_job(job_name)

    def get_jobs(self):
        return self.jenkins.get_jobs()


class Builder(object):
    def __init__(self, jenkins_url, jenkins_user, jenkins_password,
                 config=None):
        self.jenkins = Jenkins(jenkins_url, jenkins_user, jenkins_password)
        self.cache = CacheStorage()
        self.global_config = config

    def delete_job(self, name):
        self.jenkins.delete_job(name)
        if(self.cache.is_cached(name)):
            self.cache.set(name, '')

    def delete_all_jobs(self):
        jobs = self.jenkins.get_jobs()
        for job in jobs:
            self.delete_job(job['name'])

    def update_job(self, fn, name=None, output_dir=None):
        if os.path.isdir(fn):
            files_to_process = [os.path.join(fn, f)
                                for f in os.listdir(fn)
                                if (f.endswith('.yml') or f.endswith('.yaml'))]
        else:
            files_to_process = [fn]
        parser = YamlParser(self.global_config)
        for in_file in files_to_process:
            logger.debug("Parsing YAML file {0}".format(in_file))
            parser.parse(in_file)
        parser.generateXML()

        parser.jobs.sort(lambda a, b: cmp(a.name, b.name))
        for job in parser.jobs:
            if name and job.name != name:
                continue
            if output_dir:
                if name:
                    print job.output()
                    continue
                fn = os.path.join(output_dir, job.name)
                logger.debug("Writing XML to '{0}'".format(fn))
                f = open(fn, 'w')
                f.write(job.output())
                f.close()
                continue
            md5 = job.md5()
            if (self.jenkins.is_job(job.name)
                and not self.cache.is_cached(job.name)):
                old_md5 = self.jenkins.get_job_md5(job.name)
                self.cache.set(job.name, old_md5)

            if self.cache.has_changed(job.name, md5):
                self.jenkins.update_job(job.name, job.output())
                self.cache.set(job.name, md5)
