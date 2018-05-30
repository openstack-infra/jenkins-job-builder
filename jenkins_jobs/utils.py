#!/usr/bin/env python
# Copyright (C) 2015 Hewlett-Packard Development Company, L.P.
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

# functions that don't fit in well elsewhere

import codecs
import fnmatch
import locale
import os.path
from six.moves import input


def wrap_stream(stream, encoding='utf-8'):

    try:
        stream_enc = stream.encoding
    except AttributeError:
        stream_enc = locale.getpreferredencoding()

    if hasattr(stream, 'buffer'):
        stream = stream.buffer

    if str(stream_enc).lower() == str(encoding).lower():
        return stream

    return codecs.EncodedFile(stream, encoding, stream_enc)


def recurse_path(root, excludes=None):
    if excludes is None:
        excludes = []

    basepath = os.path.realpath(root)
    pathlist = [basepath]

    patterns = [e for e in excludes if os.path.sep not in e]
    absolute = [e for e in excludes if os.path.isabs(e)]
    relative = [e for e in excludes if os.path.sep in e and
                not os.path.isabs(e)]
    for root, dirs, files in os.walk(basepath, topdown=True):
        # sort in-place to ensure dirnames are visited in alphabetical order
        # a predictable order makes it easier to use the retain_anchors option
        dirs.sort()
        dirs[:] = [
            d for d in dirs
            if not any([fnmatch.fnmatch(d, pattern) for pattern in patterns])
            if not any([fnmatch.fnmatch(os.path.abspath(os.path.join(root, d)),
                                        path)
                        for path in absolute])
            if not any([fnmatch.fnmatch(os.path.relpath(os.path.join(root, d)),
                                        path)
                        for path in relative])
        ]
        pathlist.extend([os.path.join(root, path) for path in dirs])

    return pathlist


def confirm(question):
    answer = input('%s (Y/N): ' % question).upper().strip()
    return answer == 'Y'
