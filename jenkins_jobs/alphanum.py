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

"""
Sorts using alphanum algorithm which can be explained as:

Normal sort:    ['a', 'a1', 'a10', 'a2']
Alphanum sort:  ['a', 'a1', 'a2', 'a10']

It can sortof many kinds of objects, using name attribe if possible,
otherwise it will try to use str().

How to use:

from alphanum import AlphanumSort

sorted( foo, key=AlphanumSort)

"""
import re


re_chunk = re.compile(r"([\D]+|[\d]+)")
re_letters = re.compile(r"\D+")
re_numbers = re.compile(r"\d+")


def getchunk(item):
    itemchunk = re_chunk.match(item)

    # Subtract the matched portion from the original string
    # if there was a match, otherwise set it to ""
    item = (item[itemchunk.end():] if itemchunk else "")
    # Don't return the match object, just the text
    itemchunk = (itemchunk.group() if itemchunk else "")

    return (itemchunk, item)


def cmp(a, b):
    return (a > b) - (a < b)


def alphanum(a, b):
    a = a.name if hasattr(a, 'name') else str(a)
    b = b.name if hasattr(b, 'name') else str(b)

    n = 0

    while (n == 0):
        # Get a chunk and the original string with the chunk subtracted
        (ac, a) = getchunk(a)
        (bc, b) = getchunk(b)

        # Both items contain only letters
        if (re_letters.match(ac) and re_letters.match(bc)):
            n = cmp(ac, bc)
        else:
            # Both items contain only numbers
            if (re_numbers.match(ac) and re_numbers.match(bc)):
                n = cmp(int(ac), int(bc))
            # item has letters and one item has numbers, or one item is empty
            else:
                n = cmp(ac, bc)
                # Prevent deadlocks
                if (n == 0):
                    n = 1
    return n


class AlphanumSort(object):
    def __init__(self, obj, *args):
        self.obj = obj

    def __lt__(self, other):
        return alphanum(self.obj, other.obj) < 0

    def __gt__(self, other):
        return alphanum(self.obj, other.obj) > 0

    def __eq__(self, other):
        return alphanum(self.obj, other.obj) == 0

    def __le__(self, other):
        return alphanum(self.obj, other.obj) <= 0

    def __ge__(self, other):
        return alphanum(self.obj, other.obj) >= 0

    def __ne__(self, other):
        return alphanum(self.obj, other.obj) != 0


if __name__ == "__main__":

    mylist = ['a2', 'a1', 'a10', 'a']
    assert sorted(mylist, key=AlphanumSort) == ['a', 'a1', 'a2', 'a10']
