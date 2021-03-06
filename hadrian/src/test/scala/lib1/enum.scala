// Copyright (C) 2014  Open Data ("Open Data" refers to
// one or more of the following companies: Open Data Partners LLC,
// Open Data Research LLC, or Open Data Capital LLC.)
// 
// This file is part of Hadrian.
// 
// Licensed under the Hadrian Personal Use and Evaluation License (PUEL);
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
// 
//     http://raw.githubusercontent.com/opendatagroup/hadrian/master/LICENSE
// 
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

package test.scala.lib1.enum

import scala.collection.JavaConversions._

import org.junit.runner.RunWith

import org.scalatest.FlatSpec
import org.scalatest.junit.JUnitRunner
import org.scalatest.Matchers

import com.opendatagroup.hadrian.jvmcompiler._
import com.opendatagroup.hadrian.errors._
import test.scala._

@RunWith(classOf[JUnitRunner])
class Lib1EnumSuite extends FlatSpec with Matchers {
  "basic access" must "convert to string" taggedAs(Lib1, Lib1Enum) in {
    val engine = PFAEngine.fromYaml("""
input: {type: enum, name: Test, symbols: ["A", "B", "C"]}
output: string
action:
  enum.toString: input
""").head
    engine.action(engine.fromJson(""""A"""", engine.inputType)) should be ("A")
    engine.action(engine.fromJson(""""B"""", engine.inputType)) should be ("B")
    engine.action(engine.fromJson(""""C"""", engine.inputType)) should be ("C")
    evaluating { engine.fromJson(""""D"""", engine.inputType) } should produce [org.apache.avro.AvroTypeException]
  }

  it must "convert to int" taggedAs(Lib1, Lib1Enum) in {
    val engine = PFAEngine.fromYaml("""
input: {type: enum, name: Test, symbols: ["A", "B", "C"]}
output: int
action:
  enum.toInt: input
""").head
    engine.action(engine.fromJson(""""A"""", engine.inputType)) should be (0)
    engine.action(engine.fromJson(""""B"""", engine.inputType)) should be (1)
    engine.action(engine.fromJson(""""C"""", engine.inputType)) should be (2)
  }

  it must "return numSymbols" taggedAs(Lib1, Lib1Enum) in {
    val engine = PFAEngine.fromYaml("""
input: {type: enum, name: Test, symbols: ["A", "B", "C"]}
output: int
action:
  enum.numSymbols: input
""").head
    engine.action(engine.fromJson(""""A"""", engine.inputType)) should be (3)
    engine.action(engine.fromJson(""""B"""", engine.inputType)) should be (3)
    engine.action(engine.fromJson(""""C"""", engine.inputType)) should be (3)
  }

}
