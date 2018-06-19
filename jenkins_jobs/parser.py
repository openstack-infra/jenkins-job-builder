#!/usr/bin/env python
# Copyright (C) 2015 OpenStack, LLC.
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

# Manage JJB yaml feature implementation

import copy
import fnmatch
import io
import itertools
import logging
import re
import os

from jenkins_jobs.constants import MAGIC_MANAGE_STRING
from jenkins_jobs.errors import JenkinsJobsException
from jenkins_jobs.formatter import deep_format
import jenkins_jobs.local_yaml as local_yaml
from jenkins_jobs import utils

__all__ = [
    "YamlParser"
]

logger = logging.getLogger(__name__)


def matches(what, glob_patterns):
    """
    Checks if the given string, ``what``, matches any of the glob patterns in
    the iterable, ``glob_patterns``

    :arg str what: String that we want to test if it matches a pattern
    :arg iterable glob_patterns: glob patterns to match (list, tuple, set,
    etc.)
    """
    return any(fnmatch.fnmatch(what, glob_pattern)
               for glob_pattern in glob_patterns)


def combination_matches(combination, match_combinations):
    """
    Checks if the given combination is matches for any of the given combination
    globs, being those a set of combinations where if a key is missing, it's
    considered matching

    (key1=2, key2=3)

    would match the combination match:
    (key2=3)

    but not:
    (key1=2, key2=2)
    """
    for cmatch in match_combinations:
        for key, val in combination.items():
            if cmatch.get(key, val) != val:
                break
        else:
            return True
    return False


class YamlParser(object):
    def __init__(self, jjb_config=None):
        self.data = {}
        self.jobs = []
        self.views = []

        self.jjb_config = jjb_config
        self.keep_desc = jjb_config.yamlparser['keep_descriptions']
        self.path = jjb_config.yamlparser['include_path']

    def load_files(self, fn):

        # handle deprecated behavior, and check that it's not a file like
        # object as these may implement the '__iter__' attribute.
        if not hasattr(fn, '__iter__') or hasattr(fn, 'read'):
            logger.warning(
                'Passing single elements for the `fn` argument in '
                'Builder.load_files is deprecated. Please update your code '
                'to use a list as support for automatic conversion will be '
                'removed in a future version.')
            fn = [fn]

        files_to_process = []
        for path in fn:
            if not hasattr(path, 'read') and os.path.isdir(path):
                files_to_process.extend([os.path.join(path, f)
                                         for f in sorted(os.listdir(path))
                                         if (f.endswith('.yml') or
                                             f.endswith('.yaml'))])
            else:
                files_to_process.append(path)

        # symlinks used to allow loading of sub-dirs can result in duplicate
        # definitions of macros and templates when loading all from top-level
        unique_files = []
        for f in files_to_process:
            if hasattr(f, 'read'):
                unique_files.append(f)
                continue
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
                self._parse_fp(in_file)
            else:
                self.parse(in_file)

    def _parse_fp(self, fp):
        # wrap provided file streams to ensure correct encoding used
        data = local_yaml.load(utils.wrap_stream(fp),
                               self.jjb_config.yamlparser['retain_anchors'],
                               search_path=self.path)
        if data:
            if not isinstance(data, list):
                raise JenkinsJobsException(
                    "The topmost collection in file '{fname}' must be a list,"
                    " not a {cls}".format(fname=getattr(fp, 'name', fp),
                                          cls=type(data)))
            for item in data:
                cls, dfn = next(iter(item.items()))
                group = self.data.get(cls, {})
                if len(item.items()) > 1:
                    n = None
                    for k, v in item.items():
                        if k == "name":
                            n = v
                            break
                    # Syntax error
                    raise JenkinsJobsException("Syntax error, for item "
                                               "named '{0}'. Missing indent?"
                                               .format(n))
                # allow any entry to specify an id that can also be used
                _id = dfn.get('id', dfn['name'])
                if _id in group:
                    self._handle_dups(
                        "Duplicate entry found in '{0}: '{1}' already "
                        "defined".format(fp.name, _id))
                group[_id] = dfn
                self.data[cls] = group

    def parse(self, fn):
        with io.open(fn, 'r', encoding='utf-8') as fp:
            self._parse_fp(fp)

    def _handle_dups(self, message):

        if not self.jjb_config.yamlparser['allow_duplicates']:
            logger.error(message)
            raise JenkinsJobsException(message)
        else:
            logger.warning(message)

    def _getJob(self, name):
        job = self.data.get('job', {}).get(name, None)
        if not job:
            return job
        return self._applyDefaults(job)

    def _getJobGroup(self, name):
        return self.data.get('job-group', {}).get(name, None)

    def _getJobTemplate(self, name):
        job = self.data.get('job-template', {}).get(name, None)
        if not job:
            return job
        return self._applyDefaults(job)

    def _applyDefaults(self, data, override_dict=None):
        if override_dict is None:
            override_dict = {}

        whichdefaults = data.get('defaults', 'global')
        defaults = copy.deepcopy(self.data.get('defaults',
                                 {}).get(whichdefaults, {}))
        if defaults == {} and whichdefaults != 'global':
            raise JenkinsJobsException("Unknown defaults set: '{0}'"
                                       .format(whichdefaults))

        for key in override_dict.keys():
            if key in defaults.keys():
                defaults[key] = override_dict[key]

        newdata = {}
        newdata.update(defaults)
        newdata.update(data)
        return newdata

    def _formatDescription(self, job):
        if self.keep_desc:
            description = job.get("description", None)
        else:
            description = job.get("description", '')
        if description is not None:
            job["description"] = description + \
                self._get_managed_string().lstrip()

    def _getfullname(self, data):
        if 'folder' in data:
            return "%s/%s" % (data['folder'], data['name'])

        return data['name']

    def expandYaml(self, registry, jobs_glob=None):
        changed = True
        while changed:
            changed = False
            for module in registry.modules:
                if hasattr(module, 'handle_data'):
                    if module.handle_data(self.data):
                        changed = True

        for job in self.data.get('job', {}).values():
            job = self._applyDefaults(job)
            job['name'] = self._getfullname(job)

            if jobs_glob and not matches(job['name'], jobs_glob):
                logger.debug("Ignoring job {0}".format(job['name']))
                continue
            logger.debug("Expanding job '{0}'".format(job['name']))
            self._formatDescription(job)
            self.jobs.append(job)

        for view in self.data.get('view', {}).values():
            view['name'] = self._getfullname(view)
            logger.debug("Expanding view '{0}'".format(view['name']))
            self._formatDescription(view)
            self.views.append(view)

        for project in self.data.get('project', {}).values():
            logger.debug("Expanding project '{0}'".format(project['name']))
            # use a set to check for duplicate job references in projects
            seen = set()
            for jobspec in project.get('jobs', []):
                if isinstance(jobspec, dict):
                    # Singleton dict containing dict of job-specific params
                    jobname, jobparams = next(iter(jobspec.items()))
                    if not isinstance(jobparams, dict):
                        jobparams = {}
                else:
                    jobname = jobspec
                    jobparams = {}
                job = self._getJob(jobname)
                if job:
                    # Just naming an existing defined job
                    if jobname in seen:
                        self._handle_dups("Duplicate job '{0}' specified "
                                          "for project '{1}'"
                                          .format(jobname, project['name']))
                    seen.add(jobname)
                    continue
                # see if it's a job group
                group = self._getJobGroup(jobname)
                if group:
                    for group_jobspec in group['jobs']:
                        if isinstance(group_jobspec, dict):
                            group_jobname, group_jobparams = \
                                next(iter(group_jobspec.items()))
                            if not isinstance(group_jobparams, dict):
                                group_jobparams = {}
                        else:
                            group_jobname = group_jobspec
                            group_jobparams = {}
                        job = self._getJob(group_jobname)
                        if job:
                            if group_jobname in seen:
                                self._handle_dups(
                                    "Duplicate job '{0}' specified for "
                                    "project '{1}'".format(group_jobname,
                                                           project['name']))
                            seen.add(group_jobname)
                            continue
                        template = self._getJobTemplate(group_jobname)
                        # Allow a group to override parameters set by a project
                        d = type(project)(project)
                        d.update(jobparams)
                        d.update(group)
                        d.update(group_jobparams)
                        # Except name, since the group's name is not useful
                        d['name'] = project['name']
                        if template:
                            self._expandYamlForTemplateJob(d, template,
                                                           jobs_glob)
                    continue
                # see if it's a template
                template = self._getJobTemplate(jobname)
                if template:
                    d = type(project)(project)
                    d.update(jobparams)
                    self._expandYamlForTemplateJob(d, template, jobs_glob)
                else:
                    raise JenkinsJobsException("Failed to find suitable "
                                               "template named '{0}'"
                                               .format(jobname))

            for viewspec in project.get('views', []):
                if isinstance(viewspec, dict):
                    # Singleton dict containing dict of view-specific params
                    viewname, viewparams = next(iter(viewspec.items()))
                    if not isinstance(viewparams, dict):
                        viewparams = {}
                else:
                    viewname = viewspec
                    viewparams = {}
                view = self._getView(viewname)
                if view:
                    # Just naming an existing defined view
                    if viewname in seen:
                        self._handle_dups("Duplicate view '{0}' specified "
                                          "for project '{1}'"
                                          .format(viewname, project['name']))
                    seen.add(viewname)
                    continue
                # see if it's a view group
                group = self._getViewGroup(viewname)
                if group:
                    for group_viewspec in group['views']:
                        if isinstance(group_viewspec, dict):
                            group_viewname, group_viewparams = \
                                next(iter(group_viewspec.items()))
                            if not isinstance(group_viewparams, dict):
                                group_viewparams = {}
                        else:
                            group_viewname = group_viewspec
                            group_viewparams = {}
                        view = self._getView(group_viewname)
                        if view:
                            if group_viewname in seen:
                                self._handle_dups(
                                    "Duplicate view '{0}' specified for "
                                    "project '{1}'".format(group_viewname,
                                                           project['name']))
                            seen.add(group_viewname)
                            continue
                        template = self._getViewTemplate(group_viewname)
                        # Allow a group to override parameters set by a project
                        d = type(project)(project)
                        d.update(viewparams)
                        d.update(group)
                        d.update(group_viewparams)
                        # Except name, since the group's name is not useful
                        d['name'] = project['name']
                        if template:
                            self._expandYamlForTemplateView(
                                d, template, jobs_glob)
                    continue
                # see if it's a template
                template = self._getViewTemplate(viewname)
                if template:
                    d = type(project)(project)
                    d.update(viewparams)
                    self._expandYamlForTemplateView(d, template, jobs_glob)
                else:
                    raise JenkinsJobsException("Failed to find suitable "
                                               "template named '{0}'"
                                               .format(viewname))

        # check for duplicate generated jobs
        seen = set()
        # walk the list in reverse so that last definition wins
        for job in self.jobs[::-1]:
            if job['name'] in seen:
                self._handle_dups("Duplicate definitions for job '{0}' "
                                  "specified".format(job['name']))
                self.jobs.remove(job)
            seen.add(job['name'])

        # check for duplicate generated views
        seen_views = set()
        # walk the list in reverse so that last definition wins
        for view in self.views[::-1]:
            if view['name'] in seen_views:
                self._handle_dups("Duplicate definitions for view '{0}' "
                                  "specified".format(view['name']))
                self.views.remove(view)
            seen_views.add(view['name'])

        return self.jobs, self.views

    def _expandYamlForTemplateJob(self, project, template, jobs_glob=None):
        dimensions = []
        template_name = template['name']
        # reject keys that are not useful during yaml expansion
        for k in ['jobs']:
            project.pop(k)
        excludes = project.pop('exclude', [])
        for (k, v) in project.items():
            tmpk = '{{{0}}}'.format(k)
            if tmpk not in template_name:
                continue
            if type(v) == list:
                dimensions.append(zip([k] * len(v), v))
        # XXX somewhat hackish to ensure we actually have a single
        # pass through the loop
        if len(dimensions) == 0:
            dimensions = [(("", ""),)]

        for values in itertools.product(*dimensions):
            params = copy.deepcopy(project)
            params = self._applyDefaults(params, template)
            params['template-name'] = re.sub(r'({|})', r'\1\1', template_name)

            try:
                expanded_values = {}
                for (k, v) in values:
                    if isinstance(v, dict):
                        inner_key = next(iter(v))
                        expanded_values[k] = inner_key
                        expanded_values.update(v[inner_key])
                    else:
                        expanded_values[k] = v
            except TypeError:
                project_name = project.pop('name')
                logger.error(
                    "Exception thrown while expanding template '%s' for "
                    "project '%s', with expansion arguments of:\n%s\n"
                    "Original project input variables for template:\n%s\n"
                    "Most likely the inputs have items indented incorrectly "
                    "to describe how they should be applied.\n\nNote yaml "
                    "'null' is mapped to python's 'None'", template_name,
                    project_name,
                    "".join(local_yaml.dump({k: v}, default_flow_style=False)
                            for (k, v) in values),
                    local_yaml.dump(project, default_flow_style=False))
                raise

            params.update(expanded_values)
            try:
                params = deep_format(params, params)
            except Exception:
                logging.error(
                    "Failure formatting params '%s' with itself", params)
                raise
            if combination_matches(params, excludes):
                logger.debug('Excluding combination %s', str(params))
                continue

            for key in template.keys():
                if key not in params:
                    params[key] = template[key]

            try:
                expanded = deep_format(
                    template, params,
                    self.jjb_config.yamlparser['allow_empty_variables'])
            except Exception:
                logging.error(
                    "Failure formatting template '%s', containing '%s' with "
                    "params '%s'", template_name, template, params)
                raise
            expanded['name'] = self._getfullname(expanded)

            job_name = expanded.get('name')
            if jobs_glob and not matches(job_name, jobs_glob):
                continue

            self._formatDescription(expanded)
            self.jobs.append(expanded)

    def _get_managed_string(self):
        # The \n\n is not hard coded, because they get stripped if the
        # project does not otherwise have a description.
        return "\n\n" + MAGIC_MANAGE_STRING

    # Views related
    def _getView(self, name):
        view = self.data.get('view', {}).get(name, None)
        if not view:
            return view
        return self._applyDefaults(view)

    def _getViewGroup(self, name):
        return self.data.get('view-group', {}).get(name, None)

    def _getViewTemplate(self, name):
        print(name)
        view = self.data.get('view-template', {}).get(name, None)
        if not view:
            return view
        return self._applyDefaults(view)

    def _expandYamlForTemplateView(self, project, template, views_glob=None):
        dimensions = []
        template_name = template['name']
        # reject keys that are not useful during yaml expansion
        for k in ['views']:
            project.pop(k)
        excludes = project.pop('exclude', [])
        for (k, v) in project.items():
            tmpk = '{{{0}}}'.format(k)
            if tmpk not in template_name:
                continue
            if type(v) == list:
                dimensions.append(zip([k] * len(v), v))
        # XXX somewhat hackish to ensure we actually have a single
        # pass through the loop
        if len(dimensions) == 0:
            dimensions = [(("", ""),)]

        for values in itertools.product(*dimensions):
            params = copy.deepcopy(project)
            params = self._applyDefaults(params, template)

            expanded_values = {}
            for (k, v) in values:
                if isinstance(v, dict):
                    inner_key = next(iter(v))
                    expanded_values[k] = inner_key
                    expanded_values.update(v[inner_key])
                else:
                    expanded_values[k] = v

            params.update(expanded_values)
            params = deep_format(params, params)
            if combination_matches(params, excludes):
                logger.debug('Excluding combination %s', str(params))
                continue

            for key in template.keys():
                if key not in params:
                    params[key] = template[key]

            params['template-name'] = template_name
            expanded = deep_format(
                template, params,
                self.jjb_config.yamlparser['allow_empty_variables'])

            view_name = expanded.get('name')
            if views_glob and not matches(view_name, views_glob):
                continue

            self._formatDescription(expanded)
            self.views.append(expanded)
