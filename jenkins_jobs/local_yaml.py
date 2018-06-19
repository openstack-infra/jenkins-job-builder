#!/usr/bin/env python
# Copyright (C) 2013 Hewlett-Packard.
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

# Provides local yaml parsing classes and extend yaml module

"""Custom application specific yamls tags are supported to provide
enhancements when reading yaml configuration.

Action Tags
^^^^^^^^^^^

These allow manipulation of data being stored in one layout in the source
yaml for convenience and/or clarity, to another format to be processed by
the targeted module instead of requiring all modules in JJB being capable
of supporting multiple input formats.

The tag ``!join:`` will treat the first element of the following list as
the delimiter to use, when joining the remaining elements into a string
and returning a single string to be consumed by the specified module option.

This allows users to maintain elements of data in a list structure for ease
of review/maintenance, and have the yaml parser convert it to a string for
consumption as any argument for modules. The main expected use case is to
allow for generic plugin data such as shell properties to be populated from
a list construct which the yaml parser converts to a single string, instead
of trying to support this within the module code which would require a
templating engine similar to Jinja.

Generic Example:

    .. literalinclude:: /../../tests/localyaml/fixtures/joinlists.yaml


Environment Inject:

    .. literalinclude:: /../../tests/yamlparser/fixtures/string_join.yaml


While this mechanism can also be used items where delimiters are supported by
the module, that should be considered a bug that the existing code doesn't
handle being provided a list and delimiter to perform the correct conversion
for you. Should you discover a module that takes arguments with delimiters and
the existing JJB codebase does not handle accepting lists, then this can be
used as a temporary solution in place of using very long strings:

Extended Params Example:

    .. literalinclude::
        /../../tests/parameters/fixtures/extended-choice-param-full.yaml


Inclusion Tags
^^^^^^^^^^^^^^

These allow inclusion of arbitrary files as a method of having blocks of data
managed separately to the yaml job configurations. A specific usage of this is
inlining scripts contained in separate files, although such tags may also be
used to simplify usage of macros or job templates.

The tag ``!include:`` will treat the following string as file which should be
parsed as yaml configuration data.

Example:

    .. literalinclude:: /../../tests/localyaml/fixtures/include001.yaml

    contents of include001.yaml.inc:

    .. literalinclude:: /../../tests/yamlparser/fixtures/include001.yaml.inc


The tag ``!include-raw:`` will treat the given string or list of strings as
filenames to be opened as one or more data blob, which should be read into
the calling yaml construct without any further parsing. Any data in a file
included through this tag, will be treated as string data.

Examples:

    .. literalinclude:: /../../tests/localyaml/fixtures/include-raw001.yaml

    contents of include-raw001-hello-world.sh:

        .. literalinclude::
            /../../tests/localyaml/fixtures/include-raw001-hello-world.sh

    contents of include-raw001-vars.sh:

        .. literalinclude::
            /../../tests/localyaml/fixtures/include-raw001-vars.sh

    using a list of files:

    .. literalinclude::
        /../../tests/localyaml/fixtures/include-raw-multi001.yaml

The tag ``!include-raw-escape:`` treats the given string or list of strings as
filenames to be opened as one or more data blobs, which should be escaped
before being read in as string data. This allows job-templates to use this tag
to include scripts from files without needing to escape braces in the original
file.

.. warning::

    When used as a macro ``!include-raw-escape:`` should only be used if
    parameters are passed into the escaped file and you would like to escape
    those parameters. If the file does not have any jjb parameters passed into
    it then ``!include-raw:`` should be used instead otherwise you will run
    into an interesting issue where ``include-raw-escape:`` actually adds
    additional curly braces around existing curly braces. For example
    ${PROJECT} becomes ${{PROJECT}} which may break bash scripts.

Examples:

    .. literalinclude::
        /../../tests/localyaml/fixtures/include-raw-escaped001.yaml

    contents of include-raw001-hello-world.sh:

        .. literalinclude::
            /../../tests/localyaml/fixtures/include-raw001-hello-world.sh

    contents of include-raw001-vars.sh:

        .. literalinclude::
            /../../tests/localyaml/fixtures/include-raw001-vars.sh

    using a list of files:

    .. literalinclude::
        /../../tests/localyaml/fixtures/include-raw-escaped-multi001.yaml


For all the multi file includes, the files are simply appended using a newline
character.


To allow for job templates to perform substitution on the path names, when a
filename containing a python format placeholder is encountered, lazy loading
support is enabled, where instead of returning the contents back during yaml
parsing, it is delayed until the variable substitution is performed.

Example:

    .. literalinclude:: /../../tests/yamlparser/fixtures/lazy-load-jobs001.yaml

    using a list of files:

    .. literalinclude::
        /../../tests/yamlparser/fixtures/lazy-load-jobs-multi001.yaml

.. note::

    Because lazy-loading involves performing the substitution on the file
    name, it means that jenkins-job-builder can not call the variable
    substitution on the contents of the file. This means that the
    ``!include-raw:`` tag will behave as though ``!include-raw-escape:`` tag
    was used instead whenever name substitution on the filename is to be
    performed.

    Given the behaviour described above, when substitution is to be performed
    on any filename passed via ``!include-raw-escape:`` the tag will be
    automatically converted to ``!include-raw:`` and no escaping will be
    performed.


The tag ``!include-jinja2:`` will treat the given string or list of strings as
filenames to be opened as Jinja2 templates, which should be rendered to a
string and included in the calling YAML construct.  (This is analogous to the
templating that will happen with ``!include-raw``.)

Examples:

    .. literalinclude:: /../../tests/yamlparser/fixtures/jinja01.yaml

    contents of jinja01.yaml.inc:

        .. literalinclude:: /../../tests/yamlparser/fixtures/jinja01.yaml.inc


The tag ``!j2:`` takes a string and treats it as a Jinja2 template.  It will be
rendered (with the variables in that context) and included in the calling YAML
construct.

Examples:

    .. literalinclude:: /../../tests/yamlparser/fixtures/jinja-string01.yaml
"""

import functools
import io
import logging
import os
import re

import jinja2
import yaml
from yaml.constructor import BaseConstructor
from yaml.representer import BaseRepresenter
from yaml import YAMLObject

from collections import OrderedDict


logger = logging.getLogger(__name__)


class OrderedConstructor(BaseConstructor):
    """The default constructor class for PyYAML loading uses standard python
    dictionaries which can have randomized ordering enabled (default in
    CPython from version 3.3). The order of the XML elements being outputted
    is both important for tests and for ensuring predictable generation based
    on the source. This subclass overrides this behaviour to ensure that all
    dict's created make use of OrderedDict to have iteration of keys to always
    follow the order in which the keys were inserted/created.
    """

    def construct_yaml_map(self, node):
        data = OrderedDict()
        yield data
        value = self.construct_mapping(node)

        if isinstance(node, yaml.MappingNode):
            self.flatten_mapping(node)
        else:
            raise yaml.constructor.ConstructorError(
                None, None,
                'expected a mapping node, but found %s' % node.id,
                node.start_mark)

        mapping = OrderedDict()
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=False)
            try:
                hash(key)
            except TypeError as exc:
                raise yaml.constructor.ConstructorError(
                    'while constructing a mapping', node.start_mark,
                    'found unacceptable key (%s)' % exc, key_node.start_mark)
            value = self.construct_object(value_node, deep=False)
            mapping[key] = value
        data.update(mapping)


class OrderedRepresenter(BaseRepresenter):

    def represent_yaml_mapping(self, mapping, flow_style=None):
        tag = u'tag:yaml.org,2002:map'
        node = self.represent_mapping(tag, mapping, flow_style=flow_style)
        return node


class LocalAnchorLoader(yaml.Loader):
    """Subclass for yaml.Loader which keeps Alias between calls"""
    anchors = {}

    def __init__(self, *args, **kwargs):
        super(LocalAnchorLoader, self).__init__(*args, **kwargs)
        self.anchors = LocalAnchorLoader.anchors

    @classmethod
    def reset_anchors(cls):
        cls.anchors = {}

    # override the default composer to skip resetting the anchors at the
    # end of the current document
    def compose_document(self):
        # Drop the DOCUMENT-START event.
        self.get_event()
        # Compose the root node.
        node = self.compose_node(None, None)
        # Drop the DOCUMENT-END event.
        self.get_event()
        return node


class LocalLoader(OrderedConstructor, LocalAnchorLoader):
    """Subclass for yaml.Loader which handles storing the search_path and
    escape_callback functions for use by the custom YAML objects to find files
    and escape the content where required.

    Constructor access a list of search paths to look under for the given
    file following each tag, taking the first match found. Search path by
    default will include the same directory as the yaml file and the current
    working directory.


    Loading::

        # use the load function provided in this module
        import local_yaml
        data = local_yaml.load(io.open(fn, 'r', encoding='utf-8'))


        # Loading by providing the alternate class to the default yaml load
        from local_yaml import LocalLoader
        data = yaml.load(io.open(fn, 'r', encoding='utf-8'), LocalLoader)

        # Loading with a search path
        from local_yaml import LocalLoader
        import functools
        data = yaml.load(io.open(fn, 'r', encoding='utf-8'),
                         functools.partial(LocalLoader, search_path=['path']))

    """

    def __init__(self, *args, **kwargs):
        # make sure to pop off any local settings before passing to
        # the parent constructor as any unknown args may cause errors.
        self.search_path = list()
        if 'search_path' in kwargs:
            for p in kwargs.pop('search_path'):
                logger.debug("Adding '{0}' to search path for include tags"
                             .format(p))
                self.search_path.append(os.path.normpath(p))

        if 'escape_callback' in kwargs:
            self.escape_callback = kwargs.pop('escape_callback')
        else:
            self.escape_callback = self._escape

        super(LocalLoader, self).__init__(*args, **kwargs)

        # constructor to preserve order of maps and ensure that the order of
        # keys returned is consistent across multiple python versions
        self.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
                             type(self).construct_yaml_map)

        if hasattr(self.stream, 'name'):
            self.search_path.append(os.path.normpath(
                os.path.dirname(self.stream.name)))
        self.search_path.append(os.path.normpath(os.path.curdir))

    def _escape(self, data):
        return re.sub(r'({|})', r'\1\1', data)


class LocalDumper(OrderedRepresenter, yaml.Dumper):
    def __init__(self, *args, **kwargs):
        super(LocalDumper, self).__init__(*args, **kwargs)

        # representer to ensure conversion back looks like normal
        # mapping and hides that we use OrderedDict internally
        self.add_representer(OrderedDict,
                             type(self).represent_yaml_mapping)
        # convert any tuples to lists as the JJB input is generally
        # in list format
        self.add_representer(tuple,
                             type(self).represent_list)


class BaseYAMLObject(YAMLObject):
    yaml_loader = LocalLoader
    yaml_dumper = LocalDumper


class J2String(BaseYAMLObject):
    yaml_tag = u'!j2:'

    @classmethod
    def from_yaml(cls, loader, node):
        return Jinja2Loader(node.value, loader.search_path)


class YamlListJoin(BaseYAMLObject):
    yaml_tag = u'!join:'

    @classmethod
    def from_yaml(cls, loader, node):
        if isinstance(node, yaml.SequenceNode):
            delimiter = node.value[0].value
            if not isinstance(node.value[1], yaml.SequenceNode):
                raise yaml.constructor.ConstructorError(
                    None, None, "expected sequence node for join data, but "
                                "found %s" % node.value[1].id, node.start_mark)

            return delimiter.join((v.value for v in node.value[1].value))
        else:
            raise yaml.constructor.ConstructorError(
                None, None, "expected sequence node, but found %s" % node.id,
                node.start_mark)


class YamlInclude(BaseYAMLObject):
    yaml_tag = u'!include:'

    @classmethod
    def _find_file(cls, filename, search_path):
        for dirname in search_path:
            candidate = os.path.expanduser(os.path.join(dirname, filename))
            if os.path.isfile(candidate):
                logger.debug("Including file '{0}' from path '{1}'"
                            .format(filename, dirname))
                return candidate
        return filename

    @classmethod
    def _open_file(cls, loader, node):
        node_str = loader.construct_yaml_str(node)
        try:
            node_str.format()
        except KeyError:
            return cls._lazy_load(loader, cls.yaml_tag, node)

        filename = cls._find_file(node_str, loader.search_path)
        try:
            with io.open(filename, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception:
            logger.error("Failed to include file using search path: '{0}'"
                         .format(':'.join(loader.search_path)))
            raise

    @classmethod
    def _from_file(cls, loader, node):
        contents = cls._open_file(loader, node)
        if isinstance(contents, LazyLoader):
            return contents

        data = yaml.load(contents,
                         functools.partial(cls.yaml_loader,
                                           search_path=loader.search_path))
        return data

    @classmethod
    def _lazy_load(cls, loader, tag, node_str):
        logger.info("Lazy loading of file template '{0}' enabled"
                    .format(node_str))
        return LazyLoader((cls, loader, node_str))

    @classmethod
    def from_yaml(cls, loader, node):
        if isinstance(node, yaml.ScalarNode):
            return cls._from_file(loader, node)
        elif isinstance(node, yaml.SequenceNode):
            contents = [cls._from_file(loader, scalar_node)
                        for scalar_node in node.value]
            if any(isinstance(s, CustomLoader) for s in contents):
                return CustomLoaderCollection(contents)

            return u'\n'.join(contents)
        else:
            raise yaml.constructor.ConstructorError(
                None, None, "expected either a sequence or scalar node, but "
                "found %s" % node.id, node.start_mark)


class YamlIncludeRaw(YamlInclude):
    yaml_tag = u'!include-raw:'

    @classmethod
    def _from_file(cls, loader, node):
        return cls._open_file(loader, node)


class YamlIncludeRawEscape(YamlIncludeRaw):
    yaml_tag = u'!include-raw-escape:'

    @classmethod
    def from_yaml(cls, loader, node):
        data = YamlIncludeRaw.from_yaml(loader, node)
        if isinstance(data, LazyLoader):
            logger.warning("Replacing %s tag with %s since lazy loading means "
                           "file contents will not be deep formatted for "
                           "variable substitution.", cls.yaml_tag,
                           YamlIncludeRaw.yaml_tag)
            return data
        else:
            return loader.escape_callback(data)


class YamlIncludeJinja2(YamlIncludeRaw):
    yaml_tag = u'!include-jinja2:'

    @classmethod
    def _from_file(cls, loader, node):
        contents = cls._open_file(loader, node)
        if isinstance(contents, LazyLoader):
            return contents
        return Jinja2Loader(contents, loader.search_path)


class DeprecatedTag(BaseYAMLObject):

    @classmethod
    def from_yaml(cls, loader, node):
        logger.warning("tag '%s' is deprecated, switch to using '%s'",
                       cls.yaml_tag, cls._new.yaml_tag)
        return cls._new.from_yaml(loader, node)


class YamlIncludeDeprecated(DeprecatedTag):
    yaml_tag = u'!include'
    _new = YamlInclude


class YamlIncludeRawDeprecated(DeprecatedTag):
    yaml_tag = u'!include-raw'
    _new = YamlIncludeRaw


class YamlIncludeRawEscapeDeprecated(DeprecatedTag):
    yaml_tag = u'!include-raw-escape'
    _new = YamlIncludeRawEscape


class CustomLoader(object):
    """Parent class for non-standard loaders."""


class Jinja2Loader(CustomLoader):
    """A loader for Jinja2-templated files."""

    def __init__(self, contents, search_path):
        self._template = jinja2.Template(contents)
        self._template.environment.undefined = jinja2.StrictUndefined
        self._template.environment.loader = jinja2.FileSystemLoader(
            search_path)

    def format(self, **kwargs):
        return self._template.render(kwargs)


class CustomLoaderCollection(object):
    """Helper class to format a collection of CustomLoader objects"""
    def __init__(self, sequence):
        self._data = sequence

    def format(self, *args, **kwargs):
        return u'\n'.join(item.format(*args, **kwargs) for item in self._data)


class LazyLoader(CustomLoader):
    """Helper class to provide lazy loading of files included using !include*
    tags where the path to the given file contains unresolved placeholders.
    """

    def __init__(self, data):
        # str subclasses can only have one argument, so assume it is a tuple
        # being passed and unpack as needed
        self._cls, self._loader, self._node = data

    def __str__(self):
        return "%s %s" % (self._cls.yaml_tag, self._node.value)

    def __repr__(self):
        return "%s %s" % (self._cls.yaml_tag, self._node.value)

    def format(self, *args, **kwargs):
        node = yaml.ScalarNode(
            tag=self._node.tag,
            value=self._node.value.format(*args, **kwargs))
        return self._cls.from_yaml(self._loader, node)


def load(stream, retain_anchors=False, **kwargs):
    if not retain_anchors:
        LocalAnchorLoader.reset_anchors()
    return yaml.load(stream, functools.partial(LocalLoader, **kwargs))


def dump(data, stream=None, **kwargs):
    return yaml.dump(data, stream, Dumper=LocalDumper, **kwargs)
