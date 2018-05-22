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

# Manage interpolation of JJB variables into template strings.

import logging
from pprint import pformat
import re
from string import Formatter

from jenkins_jobs.errors import JenkinsJobsException
from jenkins_jobs.local_yaml import CustomLoader

logger = logging.getLogger(__name__)


def deep_format(obj, paramdict, allow_empty=False):
    """Apply the paramdict via str.format() to all string objects found within
       the supplied obj. Lists and dicts are traversed recursively."""
    # YAML serialisation was originally used to achieve this, but that places
    # limitations on the values in paramdict - the post-format result must
    # still be valid YAML (so substituting-in a string containing quotes, for
    # example, is problematic).
    if hasattr(obj, 'format'):
        try:
            ret = CustomFormatter(allow_empty).format(obj, **paramdict)
        except KeyError as exc:
            missing_key = exc.args[0]
            desc = "%s parameter missing to format %s\nGiven:\n%s" % (
                missing_key, obj, pformat(paramdict))
            raise JenkinsJobsException(desc)
        except Exception:
            logging.error("Problem formatting with args:\nallow_empty:"
                          "%s\nobj: %s\nparamdict: %s" %
                          (allow_empty, obj, paramdict))
            raise

    elif isinstance(obj, list):
        ret = type(obj)()
        for item in obj:
            ret.append(deep_format(item, paramdict, allow_empty))
    elif isinstance(obj, dict):
        ret = type(obj)()
        for item in obj:
            try:
                ret[CustomFormatter(allow_empty).format(item, **paramdict)] = \
                    deep_format(obj[item], paramdict, allow_empty)
            except KeyError as exc:
                missing_key = exc.args[0]
                desc = "%s parameter missing to format %s\nGiven:\n%s" % (
                    missing_key, obj, pformat(paramdict))
                raise JenkinsJobsException(desc)
            except Exception:
                logging.error("Problem formatting with args:\nallow_empty:"
                              "%s\nobj: %s\nparamdict: %s" %
                              (allow_empty, obj, paramdict))
                raise
    else:
        ret = obj
    if isinstance(ret, CustomLoader):
        # If we have a CustomLoader here, we've lazily-loaded a template;
        # attempt to format it.
        ret = deep_format(ret, paramdict, allow_empty=allow_empty)
    return ret


class CustomFormatter(Formatter):
    """
    Custom formatter to allow non-existing key references when formatting a
    string
    """
    _expr = """
        (?<!{){({{)*                # non-pair opening {
        (?:obj:)?                   # obj:
        (?P<key>\w+)                # key
        (?:\|(?P<default>[^}]*))?   # default fallback
        }(}})*(?!})                 # non-pair closing }
    """

    def __init__(self, allow_empty=False):
        super(CustomFormatter, self).__init__()
        self.allow_empty = allow_empty

    def vformat(self, format_string, args, kwargs):
        matcher = re.compile(self._expr, re.VERBOSE)

        # special case of returning the object if the entire string
        # matches a single parameter
        try:
            result = re.match('^%s$' % self._expr, format_string, re.VERBOSE)
        except TypeError:
            return format_string.format(**kwargs)
        if result is not None:
            try:
                return kwargs[result.group("key")]
            except KeyError:
                pass

        # handle multiple fields within string via a callback to re.sub()
        def re_replace(match):
            key = match.group("key")
            default = match.group("default")

            if default is not None:
                if key not in kwargs:
                    return default
                else:
                    return "{%s}" % key
            return match.group(0)

        format_string = matcher.sub(re_replace, format_string)

        return Formatter.vformat(self, format_string, args, kwargs)

    def get_value(self, key, args, kwargs):
        try:
            return Formatter.get_value(self, key, args, kwargs)
        except KeyError:
            if self.allow_empty:
                logger.debug(
                    'Found uninitialized key %s, replaced with empty string',
                    key
                )
                return ''
            raise
