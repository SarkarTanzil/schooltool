#
# SchoolTool - common information systems platform for school administration
# Copyright (c) 2003 Shuttleworth Foundation
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
"""
Unit tests for schooltool.app

$Id$
"""

import unittest
from persistence import Persistent
from zope.interface import implements
from zope.interface.verify import verifyObject
from schooltool.interfaces import IApplication, IEventService
from schooltool.interfaces import IApplicationObjectContainer
from schooltool.interfaces import ILocation
from schooltool.tests.utils import EqualsSortedMixin

class P(Persistent):
    pass

class Location(Persistent):
    __slots__ = '__parent__', '__name__'
    implements(ILocation)

    def __init__(self):
        self.__parent__ = None
        self.__name__ = None

class TestApplication(unittest.TestCase, EqualsSortedMixin):
    def test(self):
        from schooltool.app import Application
        a = Application()
        verifyObject(IApplication, a)
        verifyObject(IEventService, a.eventService)

    def testRoots(self):
        from schooltool.app import Application
        a = Application()
        self.assertEqual(list(a.getRoots()), [])
        root1 = P()
        a.addRoot(root1)
        self.assertEqual(list(a.getRoots()), [root1])
        root2 = P()
        a.addRoot(root2)
        self.assertEqualsSorted(list(a.getRoots()), [root1, root2])

    def testAppObjectContainers(self):
        from schooltool.app import Application
        a = Application()
        self.assertEqual(a.keys(), [])
        self.assertRaises(KeyError, a.__getitem__, 'people')
        self.assertRaises(TypeError, a.__setitem__, 'people', P())
        location = Location()
        a['people'] = location
        self.assertEqual(a.keys(), ['people'])
        self.assertEqual(a['people'], location)
        self.assertEqual(location.__name__, 'people')
        self.assert_(location.__parent__ is a, 'location.__parent__ is a')


class TestApplicationObjectContainer(unittest.TestCase):
    def test(self):
        from schooltool.app import ApplicationObjectContainer
        factory = lambda: None
        a = ApplicationObjectContainer(factory)
        verifyObject(IApplicationObjectContainer, a)

    def testDoingStuffToContents(self):
        from schooltool.app import ApplicationObjectContainer
        factory = lambda: Location()
        a = ApplicationObjectContainer(factory)
        def case1():
            return None, a.new()
        def case2():
            name = 'whatever something'
            return name, a.new(name)

        for case in case1, case2:
            desiredname, obj = case()
            name = obj.__name__
            if desiredname:
                self.assertEqual(name, desiredname)
            self.assert_(obj.__parent__ is a, 'obj.__parent__ is a')
            self.assert_(a[name] is obj, 'a[name] is obj')
            self.assertEqual(a.keys(), [name])
            del a[name]
            self.assertRaises(KeyError, a.__getitem__, name)
            self.assertEqual(obj.__name__, None)
            self.assertEqual(obj.__parent__, None)

    def testNameCollision(self):
        from schooltool.app import ApplicationObjectContainer
        factory = lambda: Location()
        a = ApplicationObjectContainer(factory)
        a.new('foo')
        self.assertRaises(KeyError, a.new, 'foo')

        for count in 1, 2, 3, 4, 5, 6, 7, 8:
          a.new()

    def testAnotherContainerTakesResponsibility(self):
        from schooltool.app import ApplicationObjectContainer
        factory = lambda: Location()
        a = ApplicationObjectContainer(factory)
        obj = a.new()
        name = obj.__name__
        self.assert_(obj.__parent__ is a)
        parent = P()
        obj.__parent__ = parent
        del a[name]
        self.assert_(obj.__parent__ is parent)
        self.assertEqual(obj.__name__, name)

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestApplication))
    suite.addTest(unittest.makeSuite(TestApplicationObjectContainer))
    return suite

if __name__ == '__main__':
    unittest.main()
