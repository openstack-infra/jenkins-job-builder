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
import hashlib
import io
import logging
import operator
import os
from pprint import pformat
import re
import time
import xml.etree.ElementTree as XML

import jenkins

from jenkins_jobs.cache import JobCache
from jenkins_jobs.constants import MAGIC_MANAGE_STRING
from jenkins_jobs.parallel import concurrent
from jenkins_jobs import utils

__all__ = [
    "JenkinsManager"
]

logger = logging.getLogger(__name__)

_DEFAULT_TIMEOUT = object()


class JenkinsManager(object):

    def __init__(self, jjb_config):
        url = jjb_config.jenkins['url']
        user = jjb_config.jenkins['user']
        password = jjb_config.jenkins['password']
        timeout = jjb_config.jenkins['timeout']

        if timeout != _DEFAULT_TIMEOUT:
            self.jenkins = jenkins.Jenkins(url, user, password, timeout)
        else:
            self.jenkins = jenkins.Jenkins(url, user, password)

        self.cache = JobCache(jjb_config.jenkins['url'],
                              flush=jjb_config.builder['flush_cache'])

        self._plugins_list = jjb_config.builder['plugins_info']
        self._jobs = None
        self._job_list = None
        self._jjb_config = jjb_config

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
        return hashlib.md5(xml.encode('utf-8')).hexdigest()

    def delete_job(self, job_name):
        if self.is_job(job_name):
            logger.info("Deleting jenkins job {0}".format(job_name))
            self.jenkins.delete_job(job_name)

    def get_plugins_info(self):
        """ Return a list of plugin_info dicts, one for each plugin on the
        Jenkins instance.
        """
        try:
            plugins_list = self.jenkins.get_plugins_info()
        except jenkins.JenkinsException as e:
            if re.search("Connection refused", str(e)):
                logger.warning(
                    "Unable to retrieve Jenkins Plugin Info from {0},"
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

    @property
    def plugins_list(self):
        if self._plugins_list is None:
            self._plugins_list = self.get_plugins_info()
        return self._plugins_list

    def delete_old_managed(self, keep=None):
        jobs = self.get_jobs()
        deleted_jobs = 0
        for job in jobs:
            if job['name'] not in keep:
                if self.is_managed(job['name']):
                    logger.info("Removing obsolete jenkins job {0}"
                                .format(job['name']))
                    self.delete_job(job['name'])
                    deleted_jobs += 1
                else:
                    logger.info("Not deleting unmanaged jenkins job %s",
                                job['name'])
            else:
                logger.debug("Keeping job %s", job['name'])
        return deleted_jobs

    def delete_jobs(self, jobs):
        if jobs is not None:
            logger.info("Removing jenkins job(s): %s" % ", ".join(jobs))
        for job in jobs:
            self.delete_job(job)
            if(self.cache.is_cached(job)):
                self.cache.set(job, '')
        self.cache.save()

    def delete_all_jobs(self):
        jobs = self.get_jobs()
        logger.info("Number of jobs to delete:  %d", len(jobs))
        script = ('for(job in jenkins.model.Jenkins.theInstance.getAllItems())'
                  '       { job.delete(); }')
        self.jenkins.run_script(script)
        # Need to clear the JJB cache after deletion
        self.cache.clear()

    def changed(self, job):
        md5 = job.md5()

        changed = (self._jjb_config.builder['ignore_cache'] or
                   self.cache.has_changed(job.name, md5))
        if not changed:
            logger.debug("'{0}' has not changed".format(job.name))
        return changed

    def update_jobs(self, xml_jobs, output=None, n_workers=None):
        orig = time.time()

        logger.info("Number of jobs generated:  %d", len(xml_jobs))
        xml_jobs.sort(key=operator.attrgetter('name'))

        if (output and not hasattr(output, 'write') and
                not os.path.isdir(output)):
            logger.info("Creating directory %s" % output)
            try:
                os.makedirs(output)
            except OSError:
                if not os.path.isdir(output):
                    raise

        if output:
            # ensure only wrapped once
            if hasattr(output, 'write'):
                output = utils.wrap_stream(output)

            for job in xml_jobs:
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
            return xml_jobs, len(xml_jobs)

        # Filter out the jobs that did not change
        logging.debug('Filtering %d jobs for changed jobs',
                      len(xml_jobs))
        step = time.time()
        jobs = [job for job in xml_jobs
                if self.changed(job)]
        logging.debug("Filtered for changed jobs in %ss",
                      (time.time() - step))

        if not jobs:
            return [], 0

        # Update the jobs
        logging.debug('Updating jobs')
        step = time.time()
        p_params = [{'job': job} for job in jobs]
        results = self.parallel_update_job(
            n_workers=n_workers,
            concurrent=p_params)
        logging.debug("Parsing results")
        # generalize the result parsing, as a concurrent job always returns a
        # list
        if len(p_params) in (1, 0):
            results = [results]
        for result in results:
            if isinstance(result, Exception):
                raise result
            else:
                # update in-memory cache
                j_name, j_md5 = result
                self.cache.set(j_name, j_md5)
        # write cache to disk
        self.cache.save()
        logging.debug("Updated %d jobs in %ss",
                      len(jobs),
                      time.time() - step)
        logging.debug("Total run took %ss", (time.time() - orig))
        return jobs, len(jobs)

    @concurrent
    def parallel_update_job(self, job):
        self.update_job(job.name, job.output().decode('utf-8'))
        return (job.name, job.md5())
