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
import locale


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
