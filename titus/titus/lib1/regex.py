#!/usr/bin/env python

# Copyright (C) 2014  Open Data ("Open Data" refers to
# one or more of the following companies: Open Data Partners LLC,
# Open Data Research LLC, or Open Data Capital LLC.)
#
# This file is part of Hadrian.
#
# Licensed under the Hadrian Personal Use and Evaluation License (PUEL);
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://raw.githubusercontent.com/opendatagroup/hadrian/master/LICENSE
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from titus.fcn import Fcn
from titus.fcn import LibFcn
from titus.signature import Sig
from titus.signature import Sigs
from titus.datatype import *
from titus.errors import *
from titus.util import callfcn, negativeIndex, checkRange, startEnd
import titus.P as P

import sys
import ctypes

provides = {}
def provide(fcn):
    provides[fcn.name] = fcn

prefix = "re."

####################################################################

## try to import clib (give warning if user doesnt have it)
## wrap clib for either ubuntu linux or mac after checking system
#    - works on sys.platform -> darwin, sys.platform -> linux2
## expose clib regex functionality to Regexer

# this class holds info about clib regex compile settings
# for use in the future to dynamically wrap clibs regex
class RegexSpecs(object):
    def __init__(self):
        system = sys.platform
        if system == "linux2":
            # tested on
            self.libname = "libc.so.6"
            self._linux2Specs()
            self.importSuccessfull = True
        elif system == "darwin":
            # tested on
            self.libname = "libc.dylib"
            self._darwinSpecs()
            self.importSuccessfull = True
        else:
            self.importSuccessfull = False

    def _darwinSpecs(self):
        self.multilineFlag = 1
        self.posixExtendedSyntaxFlag = 1
        self.numNullPointersBefore_re_nsub = 1
        self.numNullPointersAfter_re_nsub = 2
        self.field_re_nsub = ("re_nsub", ctypes.c_size_t)
        self.field_rm_so = ("rm_so", ctypes.c_ulong)
        self.field_rm_co = ("rm_co", ctypes.c_ulong)

    def _linux2Specs(self):
        self.multilineFlag = 1
        self.posixExtendedSyntaxFlag = 1
        self.numNullPointersBefore_re_nsub = 6
        self.numNullPointersAfter_re_nsub = 1
        self.field_re_nsub = ("re_nsub", ctypes.c_size_t)
        self.field_rm_so = ("rm_so", ctypes.c_int)
        self.field_rm_co = ("rm_co", ctypes.c_int)
        self.importSuccessfull = True

# get clib regex specs for the wrapper
clibSpecs = RegexSpecs()

class Regexer(object):
    # this block is here to run only when titus evaluates a pfa regex function
    if not clibSpecs.importSuccessfull:
        raise ImportError("clib unavailable")
    else:
        # define the uninstantiated regex_t class
        regex_t_fields = []
        for i in range(0, clibSpecs.numNullPointersBefore_re_nsub):
            regex_t_fields.append( ("unusedname", ctypes.c_void_p) )
        regex_t_fields.append(clibSpecs.field_re_nsub)
        for i in range(0, clibSpecs.numNullPointersAfter_re_nsub):
            regex_t_fields.append( ("unusedname", ctypes.c_void_p) )
        global Regex_t
        Regex_t = type("Regex_t", (ctypes.Structure,), {"_fields_": regex_t_fields})
        # define the uninstantiated regmatch_t class
        regmatch_t_fields = [clibSpecs.field_rm_so, clibSpecs.field_rm_co]
        global Regmatch_t
        Regmatch_t = type("Regmatch_t", (ctypes.Structure,), {"_fields_": regmatch_t_fields})
        # actually import the clibrary
        global libc
        libc = ctypes.cdll.LoadLibrary(clibSpecs.libname)

    def __init__(self, haystack, pattern):
        # haystack and pattern come in as type(haystack) == unicode
        self.haystack = haystack
        # keep track of haystack unicode indexes
        self.haystack_indices = utf8ByteIndexes(str(haystack))
        # compile pattern into regex_t object
        regex_t = Regex_t()
        try:
            comp = libc.regcomp(ctypes.byref(regex_t), pattern.encode("utf-8"), clibSpecs.posixExtendedSyntaxFlag)
        except UnicodeDecodeError:
            comp = libc.regcomp(ctypes.byref(regex_t), pattern, clibSpecs.posixExtendedSyntaxFlag)

        if (comp != 0):
            raise PFARuntimeException("bad pattern")
        self.regex_t = regex_t

        self.numGroups = int(self.regex_t.re_nsub) + 1
        self.groupArray = (Regmatch_t * self.numGroups)()
        self.indexOffset = 0

    def search(self, start):
        ex = libc.regexec(ctypes.byref(self.regex_t), self.haystack[start:],
                          self.numGroups, self.groupArray, 0)
        self.indexOffset = start
        if (ex != 0) or (start >= len(self.haystack)):
            return False
        else:
            return True

    def groupsFound(self):
        # count results in group array that arent (-1, -1)
        numFound = 0
        for i in range(0, self.numGroups):
            if self.groupArray[i].rm_so != -1:
                numFound += 1
        return numFound

    def getRegion(self):
        return Region(self.groupArray, self.indexOffset)

    def free(self):
        # free after every use!
        libc.regfree(ctypes.byref(self.regex_t))

# region class (for use similar to joni in scala)
class Region(object):
    def __init__(self, groupArray, indexOffset):
        beg = []
        end = []
        for i in range(0, len(groupArray)):
            if groupArray[i].rm_so != -1:
                beg.append(int(groupArray[i].rm_so) + indexOffset)
                end.append(int(groupArray[i].rm_co) + indexOffset)
        self.beg = beg
        self.end = end

def utf8ByteIndexes(s):
    out = []
    cumulative = 0
    for i in xrange(len(s)):
        out.append(cumulative)
        c = ord(s[i])
        if   (c <=     0x7f): cumulative += 1
        elif (c <=    0x7ff): cumulative += 2
        elif (c <=   0xffff): cumulative += 3
        elif (c <= 0x1fffff): cumulative += 4
        else:
            raise Exception
    return out

def convert(haystack, pattern, paramType0):
    if paramType0 == "string":
        return haystack.encode("utf-8"), pattern.encode("utf-8"), lambda x: x.decode("utf-8")
    else:
        return haystack, pattern, lambda x: x

############################################################# Index
class Index(LibFcn):
    name = prefix + "index"
    sig = Sigs([Sig([{"haystack": P.String()}, {"pattern": P.String()}], P.Array(P.Int())),
               Sig([{"haystack": P.Bytes()},  {"pattern": P.Bytes()}],  P.Array(P.Int()))])
    def __call__(self, state, scope, paramTypes, haystack, pattern):
        haystack, pattern, to = convert(haystack, pattern, paramTypes[0])
        re = Regexer(haystack, pattern)
        if re.search(0):
            region = re.getRegion()
            out = [region.beg[0], region.end[0]]
        else:
            out = []
        re.free()
        return out
provide(Index())

############################################################# Contains
class Contains(LibFcn):
    name = prefix + "contains"
    sig = Sigs([Sig([{"haystack": P.String()}, {"pattern": P.String()}], P.Boolean()),
                Sig([{"haystack": P.Bytes()},  {"pattern": P.Bytes()}],  P.Boolean())])
    def __call__(self, state, scope, paramTypes, haystack, pattern):
        haystack, pattern, to = convert(haystack, pattern, paramTypes[0])
        re = Regexer(haystack, pattern)
        out = re.search(0)
        re.free()
        return out
provide(Contains())

############################################################# Count
class Count(LibFcn):
    name = prefix + "count"
    sig = Sigs([Sig([{"haystack": P.String()}, {"pattern": P.String()}], P.Int()),
                Sig([{"haystack": P.Bytes()},  {"pattern": P.Bytes()}],  P.Int())])
    def __call__(self, state, scope, paramTypes, haystack, pattern):
        haystack, pattern, to = convert(haystack, pattern, paramTypes[0])
        re = Regexer(haystack, pattern)
        total = 0
        found = re.search(0)
        region = re.getRegion()
        start = region.end[0]
        while found:
            total += 1
            found = re.search(start)
            region = re.getRegion()
            start = region.end[0]
        re.free()
        return total
provide(Count())

############################################################# Rindex
class RIndex(LibFcn):
    name = prefix + "rIndex"
    sig = Sigs([Sig([{"haystack": P.String()}, {"pattern": P.String()}], P.Array(P.Int())),
                Sig([{"haystack": P.Bytes()}, {"pattern": P.Bytes()}], P.Array(P.Int()))])
    def __call__(self, state, scope, paramTypes, haystack, pattern):
        haystack, pattern, to = convert(haystack, pattern, paramTypes[0])
        re = Regexer(haystack, pattern)
        found = re.search(0)
        region = re.getRegion()
        start = 0
        if found:
            while found:
                region = re.getRegion()
                start = region.end[0]
                found = re.search(start)
            out = [region.beg[0], region.end[0]]
        else:
            out = []
        re.free()
        return out
provide(RIndex())

############################################################# Groups
class Groups(LibFcn):
    name = prefix + "groups"
    sig = Sigs([Sig([{"haystack": P.String()}, {"pattern": P.String()}], P.Array(P.Array(P.Int()))),
                Sig([{"haystack": P.Bytes()}, {"pattern": P.Bytes()}], P.Array(P.Array(P.Int())))])
    def __call__(self, state, scope, paramTypes, haystack, pattern):
        haystack, pattern, to = convert(haystack, pattern, paramTypes[0])
        re = Regexer(haystack, pattern)
        found = re.search(0)
        region = re.getRegion()
        start = region.end[0]
        out = []
        if found:
            for i in range(0, re.groupsFound()):
                out.append([region.beg[i], region.end[i]])
        else:
            out = []
        re.free()
        return out
provide(Groups())

############################################################# IndexAll
class IndexAll(LibFcn):
    name = prefix + "indexAll"
    sig = Sigs([Sig([{"haystack": P.String()}, {"pattern": P.String()}], P.Array(P.Array(P.Int()))),
                Sig([{"haystack": P.Bytes()}, {"pattern": P.Bytes()}], P.Array(P.Array(P.Int())))])
    def __call__(self, state, scope, paramTypes, haystack, pattern):
        haystack, pattern, to = convert(haystack, pattern, paramTypes[0])
        re = Regexer(haystack, pattern)
        found = re.search(0)
        region = re.getRegion()
        start = region.end[0]
        out = []
        if found:
            while found:
                region = re.getRegion()
                start = region.end[0]
                found = re.search(start)
                out.append([region.beg[0], region.end[0]])
        else:
            out = []
        re.free()
        return out
provide(IndexAll())

############################################################# FindAll
class FindAll(LibFcn):
    name = prefix + "findAll"
    sig = Sigs([Sig([{"haystack": P.String()}, {"pattern": P.String()}], P.Array(P.String())),
                Sig([{"haystack": P.Bytes()}, {"pattern": P.Bytes()}], P.Array(P.Bytes()))])
    def __call__(self, state, scope, paramTypes, haystack, pattern):
        haystack, pattern, to = convert(haystack, pattern, paramTypes[0])
        re = Regexer(haystack, pattern)
        found = re.search(0)
        region = re.getRegion()
        start = region.end[0]
        out = []
        if found:
            while found:
                region = re.getRegion()
                start = region.end[0]
                out.append(to(haystack[region.beg[0]:region.end[0]]))
                found = re.search(start)
        else:
            out = []
        re.free()
        return out
provide(FindAll())

############################################################# FindFirst
class FindFirst(LibFcn):
    name = prefix + "findFirst"
    sig = Sigs([Sig([{"haystack": P.String()}, {"pattern": P.String()}], P.String()),
                Sig([{"haystack": P.Bytes()}, {"pattern": P.Bytes()}], P.Bytes())])
    def __call__(self, state, scope, paramTypes, haystack, pattern):
        haystack, pattern, to = convert(haystack, pattern, paramTypes[0])
        re = Regexer(haystack, pattern)
        found = re.search(0)
        if found:
            region = re.getRegion()
            out = to(haystack[region.beg[0]:region.end[0]])
        else:
            out = None
        re.free()
        return out
provide(FindFirst())

############################################################# FindGroupsFirst
class FindGroupsFirst(LibFcn):
    name = prefix + "findGroupsFirst"
    sig = Sigs([Sig([{"haystack": P.String()}, {"pattern": P.String()}], P.Array(P.String())),
                Sig([{"haystack": P.Bytes()}, {"pattern": P.Bytes()}], P.Array(P.Bytes()))])
    def __call__(self, state, scope, paramTypes, haystack, pattern):
        haystack, pattern, to = convert(haystack, pattern, paramTypes[0])
        re = Regexer(haystack, pattern)
        start = 0
        found = re.search(start)
        out = []
        region = re.getRegion()
        if (found):
            for i in range(0,re.groupsFound()):
                out.append(to(haystack[region.beg[i]:region.end[i]]))
        else:
            out = []
        re.free()
        return out
provide(FindGroupsFirst())

############################################################# FindGroupsAll
class FindGroupsAll(LibFcn):
    name = prefix + "findGroupsAll"
    sig = Sigs([Sig([{"haystack": P.String()}, {"pattern": P.String()}], P.Array(P.Array(P.String()))),
                Sig([{"haystack": P.Bytes()}, {"pattern": P.Bytes()}], P.Array(P.Array(P.Bytes())))])
    def __call__(self, state, scope, paramTypes, haystack, pattern):
        haystack, pattern, to = convert(haystack, pattern, paramTypes[0])
        re = Regexer(haystack, pattern)
        start = 0
        found = re.search(start)
        region = re.getRegion()
        out = []
        if found:
            while found:
                region = re.getRegion()
                groupList = []
                for i in range(0, re.groupsFound()):
                    groupList.append(to(haystack[region.beg[i]:region.end[i]]))
                out.append(groupList)
                start = region.end[0]
                found = re.search(start)
        else:
            out = []
        re.free()
        return out
provide(FindGroupsAll())

############################################################# GroupsAll
class GroupsAll(LibFcn):
    name = prefix + "groupsAll"
    sig = Sigs([Sig([{"haystack": P.String()}, {"pattern": P.String()}], P.Array(P.Array(P.Array(P.Int())))),
                Sig([{"haystack": P.Bytes()}, {"pattern": P.Bytes()}], P.Array(P.Array(P.Array(P.Int()))))])
    def __call__(self, state, scope, paramTypes, haystack, pattern):
        haystack, pattern, to = convert(haystack, pattern, paramTypes[0])
        re = Regexer(haystack, pattern)
        start = 0
        found = re.search(start)
        region = re.getRegion()
        out = []
        if found:
            while found:
                region = re.getRegion()
                groupList = []
                for i in range(0, re.groupsFound()):
                    groupList.append([region.beg[i], region.end[i]])
                out.append(groupList)
                start = region.end[0]
                found = re.search(start)
        else:
            out = []
        re.free()
        return out
provide(GroupsAll())

############################################################# ReplaceFirst
class ReplaceFirst(LibFcn):
    name = prefix + "replaceFirst"
    sig = Sigs([Sig([{"haystack": P.String()}, {"pattern": P.String()}, {"replacement": P.String()}], P.String()),
                Sig([{"haystack": P.Bytes()}, {"pattern": P.Bytes()}, {"replacement": P.Bytes()}], P.Bytes())])
    def __call__(self, state, scope, paramTypes, haystack, pattern, replacement):
        haystack, pattern, to = convert(haystack, pattern, paramTypes[0])
        re = Regexer(haystack, pattern)
        found = re.search(0)
        region = re.getRegion()
        if found:
            out = to(haystack[:region.beg[0]]) + replacement + to(haystack[region.end[0]:])
        else:
            out = to(haystack)
        re.free()
        return out
provide(ReplaceFirst())

############################################################# ReplaceLast
class ReplaceLast(LibFcn):
    name = prefix + "replaceLast"
    sig = Sigs([Sig([{"haystack": P.String()}, {"pattern": P.String()}, {"replacement": P.String()}], P.String()),
                Sig([{"haystack": P.Bytes()}, {"pattern": P.Bytes()}, {"replacement": P.Bytes()}], P.Bytes())])
    def __call__(self, state, scope, paramTypes, haystack, pattern, replacement):
        haystack, pattern, to = convert(haystack, pattern, paramTypes[0])
        re = Regexer(haystack, pattern)
        found = re.search(0)
        region = re.getRegion()
        start = 0
        if found:
            while found:
                region = re.getRegion()
                start = region.end[0]
                found = re.search(start)
            out = to(haystack[:region.beg[0]]) + replacement + to(haystack[region.end[0]:])
        else:
            out = to(haystack)
        re.free()
        return out
provide(ReplaceLast())

############################################################# Split
class Split(LibFcn):
    name = prefix + "split"
    sig = Sigs([Sig([{"haystack": P.String()}, {"pattern": P.String()}], P.Array(P.String())),
                Sig([{"haystack": P.Bytes()}, {"pattern": P.Bytes()}], P.Array(P.Bytes()))])
    def __call__(self, state, scope, paramTypes, haystack, pattern):
        haystack, pattern, to = convert(haystack, pattern, paramTypes[0])
        re = Regexer(haystack, pattern)
        out = []
        start = 0
        found = re.search(start)
        region = re.getRegion()
        beg = 0
        end = region.beg[0]
        if (end == 0):
            flag = True
        else:
            flag = False
        if found:
            while found:
                out.append(to(haystack[beg:end]))
                beg = region.end[0]
                found = re.search(beg)
                region = re.getRegion()
                end = region.beg[0]
            if beg != len(haystack):
                out.append(to(haystack[beg:]))
            if flag:
                out = out[1:]
        else:
            out = to(haystack)
        re.free()
        return out
provide(Split())

############################################################# ReplaceAll
class ReplaceAll(LibFcn):
    name = prefix + "replaceAll"
    sig = Sigs([Sig([{"haystack": P.String()}, {"pattern": P.String()}, {"replacement": P.String()}], P.String()),
                Sig([{"haystack": P.Bytes()}, {"pattern": P.Bytes()}, {"replacement": P.Bytes()}], P.Bytes())])
    def __call__(self, state, scope, paramTypes, haystack, pattern, replacement):
        haystack, pattern, to = convert(haystack, pattern, paramTypes[0])
        re = Regexer(haystack, pattern)
        found = re.search(0)
        region = re.getRegion()
        beg = 0
        end = region.beg[0]
        out = ""
        if found:
            while found:
                out = out + to(haystack[beg:end]) + replacement
                beg = region.end[0]
                found = re.search(beg)
                region = re.getRegion()
                end = region.beg[0]
            if beg != len(haystack):
                out = out + to(haystack[beg:])
        else:
            out = haystack.decode("utf-8")
        re.free()
        return out
provide(ReplaceAll())
