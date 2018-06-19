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
import os
from pprint import pformat
import re
from six.moves.urllib.parse import quote
import time
import xml.etree.ElementTree as XML

import jenkins

from jenkins_jobs.alphanum import AlphanumSort
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
        self._views = None
        self._view_list = None
        self._jjb_config = jjb_config

    def _setup_output(self, output, item, config_xml=False):
        output_dir = output
        output_fn = os.path.join(output, item)
        if '/' in item:
            # in item folder
            output_fn = os.path.join(output, os.path.normpath(item))
            output_dir = os.path.dirname(output_fn)

        # if in a folder, re-adding name to the directory here
        if config_xml:
            output_dir = os.path.join(
                output_dir, os.path.basename(item))
            output_fn = os.path.join(output_dir, 'config.xml')
        else:
            logger.warn('(Deprecated) The default output behavior of'
                        ' `jenkins-jobs test` when given the --output'
                        ' flag will change in JJB 3.0.'
                        ' Instead of writing jobs to OUTPUT/jobname;'
                        ' they will be written to OUTPUT/jobname/config.xml.'
                        ' The new behavior can be enabled by the passing'
                        ' `--config-xml` parameter.')

        if output_dir != output:
            logger.debug("Creating directory %s" % output_dir)
            try:
                os.makedirs(output_dir)
            except OSError:
                if not os.path.isdir(output_dir):
                    raise

        return output_fn

    @property
    def jobs(self):
        if self._jobs is None:
            # populate jobs
            self._jobs = self.jenkins.get_all_jobs()

        return self._jobs

    @property
    def job_list(self):
        if self._job_list is None:
            # python-jenkins uses 'fullname' for folder/name combination
            self._job_list = set(job['fullname'] for job in self.jobs)
        return self._job_list

    def _job_format(self, job_name):
        # returns job name or url based on config option
        if self._jjb_config.builder['print_job_urls']:
            return self._jjb_config.jenkins['url'] + \
                '/job/' + quote(
                    '/job/'.join(job_name.split('/')).encode('utf8')) + '/'
        else:
            return job_name

    def _view_format(self, view_name):
        # returns job name or url based on config option
        if self._jjb_config.builder['print_job_urls']:
            parts = view_name.split('/')
            return self._jjb_config.jenkins['url'] + \
                ''.join(['/job/' + item for item in parts[:-1]]) + \
                '/view/' + parts[-1] + '/'
        else:
            return view_name

    def update_job(self, job_name, xml):
        if self.is_job(job_name):
            logger.info("Reconfiguring jenkins job {0}".format(
                self._job_format(job_name)))
            self.jenkins.reconfig_job(job_name, xml)
        else:
            logger.info("Creating jenkins job {0}".format(
                self._job_format(job_name)))
            self.jenkins.create_job(job_name, xml)

    def is_job(self, job_name, use_cache=True):
        if use_cache:
            if job_name in self.job_list:
                return True

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
            plugins_list = self.jenkins.get_plugins().values()

        except jenkins.JenkinsException as e:
            if re.search("(Connection refused|Forbidden)", str(e)):
                logger.warning(
                    "Unable to retrieve Jenkins Plugin Info from {0},"
                    " using default empty plugins info list.".format(
                        self.jenkins.server))
                plugins_list = [{'shortName': '',
                                 'version': '',
                                 'longName': ''}]
            else:
                raise
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
        if keep is None:
            keep = []
        for job in jobs:
            # python-jenkins stores the folder and name as 'fullname'
            # Check if the job was deleted when his parent folder was deleted
            if job['fullname'] not in keep and \
                    self.is_job(job['fullname'], use_cache=False):
                if self.is_managed(job['fullname']):
                    logger.info("Removing obsolete jenkins job {0}"
                                .format(job['fullname']))
                    self.delete_job(job['fullname'])
                    deleted_jobs += 1
                else:
                    logger.info("Not deleting unmanaged jenkins job %s",
                                job['fullname'])
            else:
                logger.debug("Keeping job %s", job['fullname'])
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

    def exists(self, job):
        exists = self.jenkins.job_exists(job.name)
        if not exists:
            logger.debug("'{0}' does not currently exist".format(job.name))
        return exists

    def update_jobs(self, xml_jobs, output=None, n_workers=None,
                    existing_only=None, config_xml=False):
        orig = time.time()

        logger.info("Number of jobs generated:  %d", len(xml_jobs))
        xml_jobs.sort(key=AlphanumSort)

        if (output and not hasattr(output, 'write') and
                not os.path.isdir(output)):
            logger.debug("Creating directory %s" % output)
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

                output_fn = self._setup_output(output, job.name, config_xml)

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

        if existing_only:
            # Filter out the jobs not already in the cache
            logging.debug('Filtering %d jobs for existing jobs',
                          len(jobs))
            step = time.time()
            jobs = [job for job in jobs
                    if self.exists(job)]
            logging.debug("Filtered for existing jobs in %ss",
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

    ################
    # View related #
    ################

    @property
    def views(self):
        if self._views is None:
            # populate views
            self._views = self.jenkins.get_views()
        return self._views

    @property
    def view_list(self):
        if self._view_list is None:
            self._view_list = set(view['name'] for view in self.views)
        return self._view_list

    def get_views(self, cache=True):
        if not cache:
            self._views = None
            self._view_list = None
        return self.views

    def is_view(self, view_name):
        # first use cache
        if view_name in self.view_list:
            return True

        # if not exists, use jenkins
        return self.jenkins.view_exists(view_name)

    def delete_view(self, view_name):
        if self.is_view(view_name):
            logger.info("Deleting jenkins view {}".format(view_name))
            self.jenkins.delete_view(view_name)

    def delete_views(self, views):
        if views is not None:
            logger.info("Removing jenkins view(s): %s" % ", ".join(views))
        for view in views:
            self.delete_view(view)
            if self.cache.is_cached(view):
                self.cache.set(view, '')
        self.cache.save()

    def delete_all_views(self):
        views = self.get_views()
        # Jenkins requires at least one view present. Don't remove the first
        # view as it is likely the default view.
        views.pop(0)
        logger.info("Number of views to delete:  %d", len(views))
        for view in views:
            self.delete_view(view['name'])
        # Need to clear the JJB cache after deletion
        self.cache.clear()

    def update_view(self, view_name, xml):
        if self.is_view(view_name):
            logger.info("Reconfiguring jenkins view {0}".format(
                self._view_format(view_name)))
            self.jenkins.reconfig_view(view_name, xml)
        else:
            logger.info("Creating jenkins view {0}".format(
                self._view_format(view_name)))
            self.jenkins.create_view(view_name, xml)

    def update_views(self, xml_views, output=None, n_workers=None,
                     existing_only=None, config_xml=False):
        orig = time.time()

        logger.info("Number of views generated:  %d", len(xml_views))
        xml_views.sort(key=AlphanumSort)

        if output:
            # ensure only wrapped once
            if hasattr(output, 'write'):
                output = utils.wrap_stream(output)

            for view in xml_views:
                if hasattr(output, 'write'):
                    # `output` is a file-like object
                    logger.info("View name:  %s", view.name)
                    logger.debug("Writing XML to '{0}'".format(output))
                    try:
                        output.write(view.output())
                    except IOError as exc:
                        if exc.errno == errno.EPIPE:
                            # EPIPE could happen if piping output to something
                            # that doesn't read the whole input (e.g.: the UNIX
                            # `head` command)
                            return
                        raise
                    continue

                output_fn = self._setup_output(output, view.name, config_xml)

                logger.debug("Writing XML to '{0}'".format(output_fn))
                with io.open(output_fn, 'w', encoding='utf-8') as f:
                    f.write(view.output().decode('utf-8'))
            return xml_views, len(xml_views)

        # Filter out the views that did not change
        logging.debug('Filtering %d views for changed views',
                      len(xml_views))
        step = time.time()
        views = [view for view in xml_views
                 if self.changed(view)]
        logging.debug("Filtered for changed views in %ss",
                      (time.time() - step))

        if existing_only:
            # Filter out the jobs not already in the cache
            logging.debug('Filtering %d views for existing jobs',
                          len(views))
            step = time.time()
            views = [view for view in views
                    if self.exists(view)]
            logging.debug("Filtered for existing views in %ss",
                          (time.time() - step))

        if not views:
            return [], 0

        # Update the views
        logging.debug('Updating views')
        step = time.time()
        p_params = [{'view': view} for view in views]
        results = self.parallel_update_view(
            n_workers=n_workers,
            concurrent=p_params)
        logging.debug("Parsing results")
        # generalize the result parsing, as a concurrent view always returns a
        # list
        if len(p_params) in (1, 0):
            results = [results]
        for result in results:
            if isinstance(result, Exception):
                raise result
            else:
                # update in-memory cache
                v_name, v_md5 = result
                self.cache.set(v_name, v_md5)
        # write cache to disk
        self.cache.save()
        logging.debug("Updated %d views in %ss",
                      len(views),
                      time.time() - step)
        logging.debug("Total run took %ss", (time.time() - orig))
        return views, len(views)

    @concurrent
    def parallel_update_view(self, view):
        self.update_view(view.name, view.output().decode('utf-8'))
        return (view.name, view.md5())
