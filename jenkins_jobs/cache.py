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
import logging
import os
import re
import tempfile

import fasteners
import yaml

from jenkins_jobs import errors

logger = logging.getLogger(__name__)


class JobCache(object):
    # ensure each instance of the class has a reference to the required
    # modules so that they are available to be used when the destructor
    # is being called since python will not guarantee that it won't have
    # removed global module references during teardown.
    _logger = logger
    _os = os
    _tempfile = tempfile
    _yaml = yaml

    def __init__(self, jenkins_url, flush=False):
        cache_dir = self.get_cache_dir()
        # One cache per remote Jenkins URL:
        host_vary = re.sub('[^A-Za-z0-9\-\~]', '_', jenkins_url)
        self.cachefilename = os.path.join(
            cache_dir, 'cache-host-jobs-' + host_vary + '.yml')

        # generate named lockfile if none exists, and lock it
        self._locked = self._lock()
        if not self._locked:
            raise errors.JenkinsJobsException(
                "Unable to lock cache for '%s'" % jenkins_url)

        if flush or not os.path.isfile(self.cachefilename):
            self.data = {}
        else:
            with io.open(self.cachefilename, 'r', encoding='utf-8') as yfile:
                self.data = yaml.load(yfile)
        logger.debug("Using cache: '{0}'".format(self.cachefilename))

    def _lock(self):
        self._fastener = fasteners.InterProcessLock("%s.lock" %
                                                    self.cachefilename)

        return self._fastener.acquire(delay=1, max_delay=2, timeout=60)

    def _unlock(self):
        if getattr(self, '_locked', False):
            if getattr(self, '_fastener', None) is not None:
                self._fastener.release()
            self._locked = None

    @staticmethod
    def get_cache_dir():
        home = os.path.expanduser('~')
        if home == '~':
            raise OSError('Could not locate home folder')
        xdg_cache_home = os.environ.get('XDG_CACHE_HOME') or \
            os.path.join(home, '.cache')
        path = os.path.join(xdg_cache_home, 'jenkins_jobs')
        if not os.path.isdir(path):
            try:
                os.makedirs(path)
            except OSError as ose:
                # it could happen that two jjb instances are running at the
                # same time and that the other instance created the directory
                # after we made the check, in which case there is no error
                if ose.errno != errno.EEXIST:
                    raise
        return path

    def set(self, job, md5):
        self.data[job] = md5

    def clear(self):
        self.data.clear()

    def is_cached(self, job):
        if job in self.data:
            return True
        return False

    def has_changed(self, job, md5):
        if job in self.data and self.data[job] == md5:
            return False
        return True

    def save(self):
        # use self references to required modules in case called via __del__
        # write to tempfile under same directory and then replace to avoid
        # issues around corruption such the process be killed
        tfile = self._tempfile.NamedTemporaryFile(dir=self.get_cache_dir(),
                                                  delete=False)
        tfile.write(self._yaml.dump(self.data).encode('utf-8'))
        # force contents to be synced on disk before overwriting cachefile
        tfile.flush()
        self._os.fsync(tfile.fileno())
        tfile.close()
        try:
            self._os.rename(tfile.name, self.cachefilename)
        except OSError:
            # On Windows, if dst already exists, OSError will be raised even if
            # it is a file. Remove the file first in that case and try again.
            self._os.remove(self.cachefilename)
            self._os.rename(tfile.name, self.cachefilename)

        self._logger.debug("Cache written out to '%s'" % self.cachefilename)

    def __del__(self):
        # check we initialized sufficiently in case called
        # due to an exception occurring in the __init__
        if getattr(self, 'data', None) is not None:
            try:
                self.save()
            except Exception as e:
                self._logger.error("Failed to write to cache file '%s' on "
                                   "exit: %s" % (self.cachefilename, e))
        self._unlock()
