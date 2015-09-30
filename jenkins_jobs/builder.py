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

import errno
import io
import os
import operator
import hashlib
import yaml
import xml.etree.ElementTree as XML
import jenkins
import re
from pprint import pformat
import logging

from jenkins_jobs.constants import MAGIC_MANAGE_STRING
from jenkins_jobs.parser import YamlParser

logger = logging.getLogger(__name__)

_DEFAULT_TIMEOUT = object()


class CacheStorage(object):
    # ensure each instance of the class has a reference to the required
    # modules so that they are available to be used when the destructor
    # is being called since python will not guarantee that it won't have
    # removed global module references during teardown.
    _yaml = yaml
    _logger = logger

    def __init__(self, jenkins_url, flush=False):
        cache_dir = self.get_cache_dir()
        # One cache per remote Jenkins URL:
        host_vary = re.sub('[^A-Za-z0-9\-\~]', '_', jenkins_url)
        self.cachefilename = os.path.join(
            cache_dir, 'cache-host-jobs-' + host_vary + '.yml')
        if flush or not os.path.isfile(self.cachefilename):
            self.data = {}
        else:
            with io.open(self.cachefilename, 'r', encoding='utf-8') as yfile:
                self.data = yaml.load(yfile)
        logger.debug("Using cache: '{0}'".format(self.cachefilename))

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

    def is_cached(self, job):
        if job in self.data:
            return True
        return False

    def has_changed(self, job, md5):
        if job in self.data and self.data[job] == md5:
            return False
        return True

    def save(self):
        # check we initialized sufficiently in case called via __del__
        # due to an exception occurring in the __init__
        if getattr(self, 'data', None) is not None:
            try:
                with io.open(self.cachefilename, 'w',
                             encoding='utf-8') as yfile:
                    self._yaml.dump(self.data, yfile)
            except Exception as e:
                self._logger.error("Failed to write to cache file '%s' on "
                                   "exit: %s" % (self.cachefilename, e))
            else:
                self._logger.info("Cache saved")
                self._logger.debug("Cache written out to '%s'" %
                                   self.cachefilename)

    def __del__(self):
        self.save()


class Jenkins(object):
    def __init__(self, url, user, password, timeout=_DEFAULT_TIMEOUT):
        if timeout != _DEFAULT_TIMEOUT:
            self.jenkins = jenkins.Jenkins(url, user, password, timeout)
        else:
            self.jenkins = jenkins.Jenkins(url, user, password)
        self._jobs = None
        self._job_list = None

    @property
    def jobs(self):
        if self._jobs is None:
            # populate jobs
            self._jobs = self.jenkins.get_jobs()

        return self._jobs

    @property
    def job_list(self):
        if self._job_list is None:
            self._job_list = set(job['name'] for job in self.jobs)
        return self._job_list

    def update_job(self, job_name, xml):
        if self.is_job(job_name):
            logger.info("Reconfiguring jenkins job {0}".format(job_name))
            self.jenkins.reconfig_job(job_name, xml)
        else:
            logger.info("Creating jenkins job {0}".format(job_name))
            self.jenkins.create_job(job_name, xml)

    def is_job(self, job_name):
        # first use cache
        if job_name in self.job_list:
            return True

        # if not exists, use jenkins
        return self.jenkins.job_exists(job_name)

    def get_job_md5(self, job_name):
        xml = self.jenkins.get_job_config(job_name)
        return hashlib.md5(xml).hexdigest()

    def delete_job(self, job_name):
        if self.is_job(job_name):
            logger.info("Deleting jenkins job {0}".format(job_name))
            self.jenkins.delete_job(job_name)

    def delete_all_jobs(self):
        # execute a groovy script to delete all jobs is much faster than
        # using the doDelete REST endpoint to delete one job at a time.
        script = ('for(job in jenkins.model.Jenkins.theInstance.getProjects())'
                  '       { job.delete(); }')
        self.jenkins.run_script(script)

    def get_plugins_info(self):
        """ Return a list of plugin_info dicts, one for each plugin on the
        Jenkins instance.
        """
        try:
            plugins_list = self.jenkins.get_plugins_info()
        except jenkins.JenkinsException as e:
            if re.search("Connection refused", str(e)):
                logger.warn("Unable to retrieve Jenkins Plugin Info from {0},"
                            " using default empty plugins info list.".format(
                                self.jenkins.server))
                plugins_list = [{'shortName': '',
                                 'version': '',
                                 'longName': ''}]
            else:
                raise e
        logger.debug("Jenkins Plugin Info {0}".format(pformat(plugins_list)))

        return plugins_list

    def get_jobs(self, cache=True):
        if not cache:
            self._jobs = None
            self._job_list = None
        return self.jobs

    def is_managed(self, job_name):
        xml = self.jenkins.get_job_config(job_name)
        try:
            out = XML.fromstring(xml)
            description = out.find(".//description").text
            return description.endswith(MAGIC_MANAGE_STRING)
        except (TypeError, AttributeError):
            pass
        return False


class Builder(object):
    def __init__(self, jenkins_url, jenkins_user, jenkins_password,
                 config=None, jenkins_timeout=_DEFAULT_TIMEOUT,
                 ignore_cache=False, flush_cache=False, plugins_list=None):
        self.jenkins = Jenkins(jenkins_url, jenkins_user, jenkins_password,
                               jenkins_timeout)
        self.cache = CacheStorage(jenkins_url, flush=flush_cache)
        self.global_config = config
        self.ignore_cache = ignore_cache
        self._plugins_list = plugins_list

    @property
    def plugins_list(self):
        if self._plugins_list is None:
            self._plugins_list = self.jenkins.get_plugins_info()
        return self._plugins_list

    def load_files(self, fn):
        self.parser = YamlParser(self.global_config, self.plugins_list)

        # handle deprecated behavior
        if not hasattr(fn, '__iter__'):
            logger.warning(
                'Passing single elements for the `fn` argument in '
                'Builder.load_files is deprecated. Please update your code '
                'to use a list as support for automatic conversion will be '
                'removed in a future version.')
            fn = [fn]

        files_to_process = []
        for path in fn:
            if os.path.isdir(path):
                files_to_process.extend([os.path.join(path, f)
                                         for f in os.listdir(path)
                                         if (f.endswith('.yml')
                                             or f.endswith('.yaml'))])
            else:
                files_to_process.append(path)

        # symlinks used to allow loading of sub-dirs can result in duplicate
        # definitions of macros and templates when loading all from top-level
        unique_files = []
        for f in files_to_process:
            rpf = os.path.realpath(f)
            if rpf not in unique_files:
                unique_files.append(rpf)
            else:
                logger.warning("File '%s' already added as '%s', ignoring "
                               "reference to avoid duplicating yaml "
                               "definitions." % (f, rpf))

        for in_file in unique_files:
            # use of ask-for-permissions instead of ask-for-forgiveness
            # performs better when low use cases.
            if hasattr(in_file, 'name'):
                fname = in_file.name
            else:
                fname = in_file
            logger.debug("Parsing YAML file {0}".format(fname))
            if hasattr(in_file, 'read'):
                self.parser.parse_fp(in_file)
            else:
                self.parser.parse(in_file)

    def delete_old_managed(self, keep=None):
        jobs = self.jenkins.get_jobs()
        deleted_jobs = 0
        if keep is None:
            keep = [job.name for job in self.parser.xml_jobs]
        for job in jobs:
            if job['name'] not in keep and \
                    self.jenkins.is_managed(job['name']):
                logger.info("Removing obsolete jenkins job {0}"
                            .format(job['name']))
                self.delete_job(job['name'])
                deleted_jobs += 1
            else:
                logger.debug("Ignoring unmanaged jenkins job %s",
                             job['name'])
        return deleted_jobs

    def delete_job(self, jobs_glob, fn=None):
        if fn:
            self.load_files(fn)
            self.parser.expandYaml([jobs_glob])
            jobs = [j['name'] for j in self.parser.jobs]
        else:
            jobs = [jobs_glob]

        if jobs is not None:
            logger.info("Removing jenkins job(s): %s" % ", ".join(jobs))
        for job in jobs:
            self.jenkins.delete_job(job)
            if(self.cache.is_cached(job)):
                self.cache.set(job, '')

    def delete_all_jobs(self):
        jobs = self.jenkins.get_jobs()
        logger.info("Number of jobs to delete:  %d", len(jobs))
        self.jenkins.delete_all_jobs()

    def update_job(self, input_fn, jobs_glob=None, output=None):
        self.load_files(input_fn)
        self.parser.expandYaml(jobs_glob)
        self.parser.generateXML()

        logger.info("Number of jobs generated:  %d", len(self.parser.xml_jobs))
        self.parser.xml_jobs.sort(key=operator.attrgetter('name'))

        if (output and not hasattr(output, 'write')
                and not os.path.isdir(output)):
            logger.info("Creating directory %s" % output)
            try:
                os.makedirs(output)
            except OSError:
                if not os.path.isdir(output):
                    raise

        updated_jobs = 0
        for job in self.parser.xml_jobs:
            if output:
                if hasattr(output, 'write'):
                    # `output` is a file-like object
                    logger.info("Job name:  %s", job.name)
                    logger.debug("Writing XML to '{0}'".format(output))
                    try:
                        output.write(job.output())
                    except IOError as exc:
                        if exc.errno == errno.EPIPE:
                            # EPIPE could happen if piping output to something
                            # that doesn't read the whole input (e.g.: the UNIX
                            # `head` command)
                            return
                        raise
                    continue

                output_fn = os.path.join(output, job.name)
                logger.debug("Writing XML to '{0}'".format(output_fn))
                with io.open(output_fn, 'w', encoding='utf-8') as f:
                    f.write(job.output().decode('utf-8'))
                continue
            md5 = job.md5()
            if (self.jenkins.is_job(job.name)
                    and not self.cache.is_cached(job.name)):
                old_md5 = self.jenkins.get_job_md5(job.name)
                self.cache.set(job.name, old_md5)

            if self.cache.has_changed(job.name, md5) or self.ignore_cache:
                self.jenkins.update_job(job.name, job.output())
                updated_jobs += 1
                self.cache.set(job.name, md5)
            else:
                logger.debug("'{0}' has not changed".format(job.name))
        return self.parser.xml_jobs, updated_jobs
