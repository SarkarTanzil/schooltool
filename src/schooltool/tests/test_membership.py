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
Unit tests for schooltool.membership

$Id: test_model.py 153 2003-10-16 12:33:50Z mg $
"""

import unittest
from persistence import Persistent
from zope.interface import implements
from zope.interface.verify import verifyObject
from schooltool.interfaces import IGroupMember, IFacet, IFaceted
from schooltool.interfaces import IEventConfigurable
from schooltool.tests.utils import LocatableEventTargetMixin
from schooltool.tests.utils import EventServiceTestMixin

__metaclass__ = type

class P(Persistent):
    pass

class MemberStub(LocatableEventTargetMixin):
    implements(IGroupMember, IFaceted)

    def __init__(self, parent=None, name='does not matter'):
        LocatableEventTargetMixin.__init__(self, parent, name)
        self.__facets__ = {}
        self.added = None
        self.removed = None

    def notifyAdd(self, group, name):
        self.added = group

    def notifyRemove(self, group):
        self.removed = group

class GroupStub(LocatableEventTargetMixin):
    deleted = None

    def __delitem__(self, key):
        self.deleted = key


class TestURIs(unittest.TestCase):

    def testURIGroup(self):
        from schooltool.interfaces import URIGroup
        from schooltool.component import inspectSpecificURI
        inspectSpecificURI(URIGroup)

    def testURIMember(self):
        from schooltool.interfaces import URIMember
        from schooltool.component import inspectSpecificURI
        inspectSpecificURI(URIMember)


class TestMemberMixin(unittest.TestCase):

    def test_notifyAdd(self):
        from schooltool.membership import MemberMixin
        member = MemberMixin()
        group = P()
        member.notifyAdd(group, 1)
        self.assertEqual(list(member.groups()), [group])
        self.assertEqual(member.__parent__, group)
        self.assertEqual(member.__name__, '1')
        member.notifyAdd(P(), '2')
        self.assertEqual(member.__parent__, group)
        self.assertEqual(member.__name__, '1')

    def test_notifyRemove(self):
        from schooltool.membership import MemberMixin
        member = MemberMixin()
        group = object()
        other = object()
        for parent in (group, other):
            member.__parent__ = parent
            member.__name__ = 'spam'
            member._groups = {group: '1'}
            member.notifyRemove(group)
            self.assertEqual(list(member.groups()), [])
            self.assertRaises(KeyError, member.notifyRemove, group)
            if parent == group:
                self.assertEqual(member.__parent__, None)
                self.assertEqual(member.__name__, None)
            else:
                self.assertEqual(member.__parent__, other)
                self.assertEqual(member.__name__, 'spam')

    def testQueryLinks(self):
        from schooltool.membership import MemberMixin
        from schooltool.interfaces import IQueryLinks, URIGroup, URIMember
        from schooltool.interfaces import ISpecificURI
        member = MemberMixin()
        verifyObject(IQueryLinks, member)
        self.assertEqual(member.listLinks(), [])
        group = P()
        member.notifyAdd(group, 1)

        for role in (URIGroup, ISpecificURI):
            links = member.listLinks(role)
            self.assertEqual(len(links), 1, str(role))
            self.assertEqual(links[0].role, URIGroup)
            self.assertEqual(links[0].title, "Membership")
            self.assertEqual(links[0].name, 1)
            self.assert_(links[0].traverse() is group)

        class URIFoo(URIGroup):
            "http://example.com/ns/foo"

        for role in (URIMember, URIFoo):
            links = member.listLinks(role)
            self.assertEqual(links, [], str(role))


class TestGroupMixin(unittest.TestCase):

    def test(self):
        from schooltool.interfaces import IQueryLinks
        from schooltool.membership import GroupMixin
        group = GroupMixin()
        verifyObject(IQueryLinks, group)

    def test_add(self):
        from schooltool.membership import GroupMixin
        group = GroupMixin()
        member = MemberStub()
        key = group.add(member)
        self.assertEqual(member, group[key])
        self.assertEqual(member.added, group)
        self.assertRaises(TypeError, group.add, "not a member")

    def test_remove(self):
        from schooltool.membership import GroupMixin
        group = GroupMixin()
        member = MemberStub()
        key = group.add(member)
        del group[key]
        self.assertRaises(KeyError, group.__getitem__, key)
        self.assertRaises(KeyError, group.__delitem__, key)
        self.assertEqual(member.removed, group)

    def test_items(self):
        from schooltool.membership import GroupMixin
        group = GroupMixin()
        self.assertEquals(list(group.keys()), [])
        self.assertEquals(list(group.values()), [])
        self.assertEquals(list(group.items()), [])
        member = MemberStub()
        key = group.add(member)
        self.assertEquals(list(group.keys()), [key])
        self.assertEquals(list(group.values()), [member])
        self.assertEquals(list(group.items()), [(key, member)])

    def testQueryLinks(self):
        from schooltool.membership import GroupMixin
        from schooltool.interfaces import IQueryLinks, URIGroup, URIMember
        from schooltool.interfaces import ISpecificURI
        group = GroupMixin()
        verifyObject(IQueryLinks, group)
        self.assertEqual(group.listLinks(), [])
        member = MemberStub()
        key = group.add(member)

        for role in (URIMember, ISpecificURI):
            links = group.listLinks(role)
            self.assertEqual(len(links), 1, str(role))
            self.assertEqual(links[0].role, URIMember)
            self.assertEqual(links[0].title, "Membership")
            self.assert_(links[0].traverse() is member)

        class URIFoo(URIMember):
            "http://example.com/ns/foo"

        for role in (URIGroup, URIFoo):
            links = group.listLinks(role)
            self.assertEqual(links, [], str(role))


class TestMembershipRelationship(unittest.TestCase):

    def test(self):
        from schooltool.membership import Membership
        # XXX unfinished


class TestMemberLink(EventServiceTestMixin, unittest.TestCase):

    def test(self):
        from schooltool.membership import MemberLink
        from schooltool.interfaces import URIMember, IRemovableLink

        member = object()
        parent = object()
        link = MemberLink(parent, member, 'name')
        self.assertEqual(link.title, 'Membership')
        self.assertEqual(link.name, 'name')
        self.assert_(link.traverse() is member)
        self.assert_(link.role is URIMember)
        self.assert_(link.__parent__ is parent)
        verifyObject(IRemovableLink, link)

    def test_unlink(self):
        from schooltool.membership import MemberLink
        from schooltool.interfaces import IMemberRemovedEvent
        member = MemberStub(self.serviceManager)
        group = GroupStub(self.serviceManager)
        link = MemberLink(group, member, 'foo')
        link.unlink()
        self.assertEqual(group.deleted, 'foo')
        self.assertEquals(len(self.eventService.events), 1)
        e = self.eventService.events[0]
        self.assert_(group.events, [e])
        self.assert_(member.events, [e])
        self.assert_(IMemberRemovedEvent.isImplementedBy(e))
        self.assert_(e.member is member)
        self.assert_(e.group is group)


class TestGroupLink(EventServiceTestMixin, unittest.TestCase):

    def test(self):
        from schooltool.membership import GroupLink
        from schooltool.interfaces import URIGroup, IRemovableLink

        group = object()
        parent = object()
        link = GroupLink(parent, group, 'name')
        self.assertEqual(link.title, 'Membership')
        self.assertEqual(link.name, 'name')
        self.assert_(link.traverse() is group)
        self.assert_(link.role is URIGroup)
        self.assert_(link.__parent__ is parent)
        verifyObject(IRemovableLink, link)

    def test_unlink(self):
        from schooltool.membership import GroupLink
        from schooltool.interfaces import IMemberRemovedEvent
        member = MemberStub(self.serviceManager)
        group = GroupStub(self.serviceManager)
        link = GroupLink(member, group, 'foo')
        link.unlink()
        self.assertEqual(group.deleted, 'foo')
        self.assertEquals(len(self.eventService.events), 1)
        e = self.eventService.events[0]
        self.assert_(group.events, [e])
        self.assert_(member.events, [e])
        self.assert_(IMemberRemovedEvent.isImplementedBy(e))
        self.assert_(e.member is member)
        self.assert_(e.group is group)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestGroupMixin))
    suite.addTest(unittest.makeSuite(TestMembershipRelationship))
    suite.addTest(unittest.makeSuite(TestMemberMixin))
    suite.addTest(unittest.makeSuite(TestURIs))
    suite.addTest(unittest.makeSuite(TestMemberLink))
    suite.addTest(unittest.makeSuite(TestGroupLink))
    return suite

if __name__ == '__main__':
    unittest.main()
