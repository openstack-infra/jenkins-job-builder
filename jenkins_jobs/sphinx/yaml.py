# Copyright 2012 Hewlett-Packard Development Company, L.P.
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

# Most of this code originated in sphinx.domains.python and
# sphinx.ext.autodoc and has been only slightly adapted for use in
# subclasses here.

#    :copyright: Copyright 2007-2011 by the Sphinx team, see AUTHORS.
#    :license: BSD, see LICENSE for details.

import re
from sphinx.ext.autodoc import Documenter, FunctionDocumenter
from sphinx.domains.python import PyModulelevel, _pseudo_parse_arglist
from sphinx import addnodes
from sphinx.locale import _

yaml_sig_re = re.compile('yaml:\s*(.*)')


class PyYAMLFunction(PyModulelevel):
    def handle_signature(self, sig, signode):
        """Transform a Python signature into RST nodes.

        Return (fully qualified name of the thing, classname if any).

        If inside a class, the current class name is handled intelligently:
        * it is stripped from the displayed name if present
        * it is added to the full name (return value) if not present
        """
        name_prefix = None
        name = sig
        arglist = None
        retann = None

        # determine module and class name (if applicable), as well as full name
        modname = self.options.get(
            'module', self.env.temp_data.get('py:module'))
        classname = self.env.temp_data.get('py:class')

        fullname = name

        signode['module'] = modname
        signode['class'] = classname
        signode['fullname'] = fullname

        sig_prefix = self.get_signature_prefix(sig)
        if sig_prefix:
            signode += addnodes.desc_annotation(sig_prefix, sig_prefix)

        if name_prefix:
            signode += addnodes.desc_addname(name_prefix, name_prefix)

        anno = self.options.get('annotation')

        signode += addnodes.desc_name(name, name)
        if not arglist:
            if self.needs_arglist():
                # for callables, add an empty parameter list
                signode += addnodes.desc_parameterlist()
            if retann:
                signode += addnodes.desc_returns(retann, retann)
            if anno:
                signode += addnodes.desc_annotation(' ' + anno, ' ' + anno)
            return fullname, name_prefix

        _pseudo_parse_arglist(signode, arglist)
        if retann:
            signode += addnodes.desc_returns(retann, retann)
        if anno:
            signode += addnodes.desc_annotation(' ' + anno, ' ' + anno)
        return fullname, name_prefix

    def get_index_text(self, modname, name_cls):
        return _('%s (in module %s)') % (name_cls[0], modname)


class YAMLFunctionDocumenter(FunctionDocumenter):
    priority = FunctionDocumenter.priority + 10
    objtype = 'yamlfunction'
    directivetype = 'yamlfunction'

    @classmethod
    def can_document_member(cls, member, membername, isattr, parent):
        if not FunctionDocumenter.can_document_member(member, membername,
                                                      isattr, parent):
            return False
        if member.__doc__ is not None and yaml_sig_re.match(member.__doc__):
            return True
        return False

    def _find_signature(self, encoding=None):
        docstrings = Documenter.get_doc(self, encoding, 2)
        if len(docstrings) != 1:
            return
        doclines = docstrings[0]
        setattr(self, '__new_doclines', doclines)
        if not doclines:
            return
        # match first line of docstring against signature RE
        match = yaml_sig_re.match(doclines[0])
        if not match:
            return
        name = match.group(1)
        # ok, now jump over remaining empty lines and set the remaining
        # lines as the new doclines
        i = 1
        while i < len(doclines) and not doclines[i].strip():
            i += 1
        setattr(self, '__new_doclines', doclines[i:])
        return name

    def get_doc(self, encoding=None, ignore=1):
        lines = getattr(self, '__new_doclines', None)
        if lines is not None:
            return [lines]
        return Documenter.get_doc(self, encoding, ignore)

    def format_signature(self):
        result = self._find_signature()
        self._name = result
        return ''

    def format_name(self):
        return self._name


def setup(app):
    app.add_autodocumenter(YAMLFunctionDocumenter)
    app.add_directive_to_domain('py', 'yamlfunction', PyYAMLFunction)
