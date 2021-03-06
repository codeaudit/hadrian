#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
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
# See: string the License for the specific language governing permissions and
# limitations under the License.

import unittest
import math
import struct

from titus.genpy import PFAEngine
from titus.errors import *

class TestLib1Rand(unittest.TestCase):
    def testInt(self):
        engine1, = PFAEngine.fromYaml('''
input: "null"
output: int
randseed: 12345
action: {rand.int: []}
''')
        self.assertEqual(engine1.action(None), -358114921)
        self.assertEqual(engine1.action(None), -2103807398)
        self.assertEqual(engine1.action(None), 1396751321)

        engine2, = PFAEngine.fromYaml('''
input: "null"
output: int
randseed: 12345
action: {rand.int: [5, 10]}
''')
        self.assertEqual(engine2.action(None), 7)
        self.assertEqual(engine2.action(None), 5)
        self.assertEqual(engine2.action(None), 9)

    def testLong(self):
        engine1, = PFAEngine.fromYaml('''
input: "null"
output: long
randseed: 12345
action: {rand.long: []}
''')
        self.assertEqual(engine1.action(None), 4292285838037326215)
        self.assertEqual(engine1.action(None), 6551146165133617474)
        self.assertEqual(engine1.action(None), -5650950641291792112)

        engine2, = PFAEngine.fromYaml('''
input: "null"
output: long
randseed: 12345
action: {rand.long: [5, 10]}
''')
        self.assertEqual(engine2.action(None), 7)
        self.assertEqual(engine2.action(None), 5)
        self.assertEqual(engine2.action(None), 9)

    def testFloat(self):
        engine, = PFAEngine.fromYaml('''
input: "null"
output: float
randseed: 12345
action: {rand.float: [5, 10]}
''')
        self.assertAlmostEqual(engine.action(None), 7.08309936273, places=5)
        self.assertAlmostEqual(engine.action(None), 5.05084584729, places=5)
        self.assertAlmostEqual(engine.action(None), 9.12603254627, places=5)

    def testDouble(self):
        engine, = PFAEngine.fromYaml('''
input: "null"
output: double
randseed: 12345
action: {rand.double: [5, 10]}
''')
        self.assertAlmostEqual(engine.action(None), 7.08309936273, places=5)
        self.assertAlmostEqual(engine.action(None), 5.05084584729, places=5)
        self.assertAlmostEqual(engine.action(None), 9.12603254627, places=5)

    def testString(self):
        engine1, = PFAEngine.fromYaml('''
input: "null"
output: string
randseed: 12345
action: {rand.string: [10]}
''')
        self.assertEqual(engine1.action(None), u"姾ȳ눿䂂侔⧕穂⋭᫘嶄")
        self.assertEqual(engine1.action(None), u"祩▩睿䲩컲Ꮉ퍣夅泚 ")
        self.assertEqual(engine1.action(None), u"魍⤉䧇ԕ䥖탺퍬ꃒÀ쬘")

        engine2, = PFAEngine.fromYaml('''
input: "null"
output: string
randseed: 12345
action: {rand.string: [10, {string: "abcdefghijklmnopqrstuvwxyz0123456789"}]}
''')
        self.assertEqual(engine2.action(None), "oa3kngufep")
        self.assertEqual(engine2.action(None), "ugtm8d9osf")
        self.assertEqual(engine2.action(None), "zgmam890a7")

        engine3, = PFAEngine.fromYaml('''
input: "null"
output: string
randseed: 12345
action: {rand.string: [10, 33, 127]}
''')
        self.assertEqual(engine3.action(None), "H!n=C3V0,I")
        self.assertEqual(engine3.action(None), "U1UB{)|GP.")
        self.assertEqual(engine3.action(None), "d2A#@{}f!y")

    def testBytes(self):
        engine1, = PFAEngine.fromYaml('''
input: "null"
output: bytes
randseed: 12345
action: {rand.bytes: [10]}
''')
        self.assertEqual(engine1.action(None), "j\x02\xd3L^1\x90)\x1fn")
        self.assertEqual(engine1.action(None), "\x8f,\x8dZ\xf5\x17\xfai\x81%")
        self.assertEqual(engine1.action(None), "\xb80W\x06V\xf7\xfa\xbe\x00\xf0")

        engine2, = PFAEngine.fromYaml('''
input: "null"
output: bytes
randseed: 12345
action: {rand.bytes: [10, {base64: "YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5"}]}

''')
        self.assertEqual(engine2.action(None), "oa3kngufep")
        self.assertEqual(engine2.action(None), "ugtm8d9osf")
        self.assertEqual(engine2.action(None), "zgmam890a7")

        engine3, = PFAEngine.fromYaml('''
input: "null"
output: bytes
randseed: 12345
action: {rand.bytes: [10, 33, 127]}
''')
        self.assertEqual(engine3.action(None), "H!n=C3V0,I")
        self.assertEqual(engine3.action(None), "U1UB{)|GP.")
        self.assertEqual(engine3.action(None), "d2A#@{}f!y")

    def testUUID(self):
        engine1, = PFAEngine.fromYaml('''
input: "null"
output: string
randseed: 12345
action: {rand.uuid: []}
''')
        self.assertEqual(engine1.action(None), "6aa79987-bb91-4029-8d1f-cd8778e7d340bbcd")
        self.assertEqual(engine1.action(None), "4c73a942-daea-45e5-8ee8-452ec40a3193ca54")
        self.assertEqual(engine1.action(None), "90e5e945-6fac-4296-85f8-dfc9e3b11fcff454")

        engine2, = PFAEngine.fromYaml('''
input: "null"
output: string
action: {s.substr: [{rand.uuid: []}, 14, 15]}
''')
        for i in xrange(1000):
            self.assertEqual(engine2.action(None), "4")

        engine3, = PFAEngine.fromYaml('''
input: "null"
output: string
action: {s.substr: [{rand.uuid: []}, 19, 20]}
''')
        for i in xrange(1000):
            self.assertEqual(engine3.action(None), "8")

    def testGaussian(self):
        engine, = PFAEngine.fromYaml('''
input: "null"
output: double
randseed: 12345
action: {rand.gaussian: [10, 2]}
''')
        self.assertAlmostEqual(engine.action(None), 9.75239840882, places=5)
        self.assertAlmostEqual(engine.action(None), 10.143049927, places=5)
        self.assertAlmostEqual(engine.action(None), 10.7667383886, places=5)

if __name__ == "__main__":
    unittest.main()
