"""
Copyright (c) 2014, Logan P. Evans <loganpevans@gmail.com>
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
this list of conditions and the following disclaimer in the documentation
and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""

import unittest
from empirical_cache_hits import LinkedNode, LinkedList, Cache
from index_rbtree.rbtree import RBTree
from numpy import random


class TestRBTree(unittest.TestCase):
    def setUp(self):
        self.uut = RBTree()
        random.seed(0)

    def test_inserts(self):
        to_add = set()
        for _ in range(1000):
            to_add.add(random.randint(0, 1000000))
        for val in to_add:
            self.uut[val] = None

        size = len(self.uut)
        self.assertEqual(size, len(to_add))
        for val in to_add:
            self.uut.pop(val)
            size -= 1
            self.assertEqual(len(self.uut), size)
        self.assertEqual(len(self.uut), 0)

    def test_index(self):
        to_add = set()
        for _ in range(1000):
            to_add.add(random.randint(0, 1000000))
        for val in to_add:
            self.uut[val] = None

        for index, val in enumerate(sorted(to_add)):
            self.assertEqual(index, self.uut.index(val))

    def test_discard(self):
        to_add = set()
        for _ in range(1000):
            to_add.add(random.randint(0, 1000000))
        for val in to_add:
            self.uut[val] = None

        sorted_list = sorted(to_add)
        while self.uut:
            index = random.randint(0, len(sorted_list))
            element = sorted_list[index]
            self.assertEqual(index, self.uut.index(element))
            self.uut.discard(element)
            sorted_list.remove(element)


class TestLinkedList(unittest.TestCase):
    def setUp(self):
        self.uut = LinkedList()

    def test_head(self):
        self.assertEqual(self.uut.head, None)
        x = LinkedNode(4)
        y = LinkedNode(4)
        z = LinkedNode(6)
        self.uut.push_node(x)
        self.assertEqual(x, y)
        self.assertEqual(self.uut.head, x)
        self.assertEqual(self.uut.head, y)

        self.uut.unshift_node(z)
        self.assertEqual(self.uut.head, 6)

    def test_tail(self):
        self.assertEqual(self.uut.head, None)
        x = LinkedNode(4)
        y = LinkedNode(4)
        z = LinkedNode(6)
        self.uut.unshift_node(x)
        self.assertEqual(x, y)
        self.assertEqual(self.uut.tail, x)
        self.assertEqual(self.uut.tail, y)

        self.uut.push_node(z)
        self.assertEqual(self.uut.tail, 6)

    def test_push(self):
        for x in range(10):
            self.uut.push_node(LinkedNode(x))

    def test_unshift(self):
        for x in range(10):
            self.uut.unshift_node(LinkedNode(x))

    def test_empty(self):
        self.assertFalse(bool(self.uut))
        self.uut.push_node(LinkedNode(1))
        self.assertTrue(bool(self.uut))

    def test_pop_node(self):
        expected = list(range(10))
        for x in expected:
            self.uut.push_node(LinkedNode(x))

        self.assertTrue(bool(self.uut))

        while self.uut:
            self.assertEqual(expected[-1], self.uut.pop_node().value)
            expected = expected[:-1]

        self.assertFalse(bool(self.uut))

        for x in range(-10, 11):
            self.uut.unshift_node(LinkedNode(x))
            self.assertEqual(x, self.uut.pop_node().value)

            self.uut.push_node(LinkedNode(x))
            self.assertEqual(x, self.uut.pop_node().value)

    def test_shift_node(self):
        expected = list(range(10))
        for x in expected:
            # Place on the back...
            self.uut.push_node(LinkedNode(x))

        self.assertTrue(bool(self.uut))

        while self.uut:
            # Read from the front...
            self.assertEqual(expected[0], self.uut.shift_node().value)
            expected = expected[1:]

        self.assertFalse(bool(self.uut))
        # We aren't testing Cache.clear() here...
        self.uut = Cache()

        for x in range(-10, 11):
            self.uut.unshift_node(LinkedNode(x))
            self.assertEqual(x, self.uut.shift_node().value)

            self.uut.push_node(LinkedNode(x))
            self.assertEqual(x, self.uut.shift_node().value)


class TestCache(unittest.TestCase):
    def setUp(self):
        self.uut = Cache()

    def tearDown(self):
        if self.uut.head:
            self.assertEqual(None, self.uut.head.prev_node)

        if self.uut.tail:
            self.assertEqual(None, self.uut.tail.next_node)

    def test_push(self):
        for x in range(10):
            self.uut.push(x)

    def test_unshift(self):
        for x in range(10):
            self.uut.unshift(x)

    def test_empty(self):
        self.assertFalse(bool(self.uut))
        self.uut.push(1)
        self.assertTrue(bool(self.uut))

    def test_pop(self):
        expected = list(range(10))
        for x in expected:
            self.uut.push(x)

        self.assertTrue(bool(self.uut))

        while self.uut:
            self.assertEqual(expected[-1], self.uut.pop())
            expected = expected[:-1]

        self.assertFalse(bool(self.uut))

        for x in range(-10, 11):
            self.uut.unshift(x)
            self.assertEqual(x, self.uut.pop())

            self.uut.push(x)
            self.assertEqual(x, self.uut.pop())

    def test_shift(self):
        expected = list(range(10))
        for x in expected:
            # Place on the back...
            self.uut.push(x)

        self.assertTrue(bool(self.uut))

        while self.uut:
            # Read from the front...
            self.assertEqual(expected[0], self.uut.shift())
            expected = expected[1:]

        self.assertFalse(bool(self.uut))
        # We aren't testing Cache.clear() here...
        self.uut = Cache()

        for x in range(-10, 11):
            self.uut.unshift(x)
            self.assertEqual(x, self.uut.shift())

            self.uut.push(x)
            self.assertEqual(x, self.uut.shift())

    def test_insert(self):
        expected = list(range(10))

    def test_find(self):
        for x in range(2, 10, 2):
            self.uut.unshift(x)

        for x in range(1, 10):
            if x % 2:
                self.assertFalse(self.uut.find(x))
            else:
                self.assertTrue(self.uut.find(x))

    def test_requeue(self):
        for x in range(0, 10):
            self.uut.push(x)

        for x in range(2, 10):
            self.uut.unshift(-1)
            self.uut.find(x, requeue=True)
            self.assertTrue(self.uut.shift(), x)
            self.uut.shift()

    def test_remove(self):
        for x in range(10):
            for y in range(10):
                self.uut.push(y)
            print x, y, self.uut
            self.uut.remove(x)
            while self.uut:
                popped = self.uut.pop()
                self.assertNotEqual(x, popped)

    def test_clear(self):
        for x in range(10):
            self.uut.push(x)
        self.uut.clear()
        self.assertFalse(bool(self.uut))
        self.assertEqual(len(self.uut), 0)
        self.assertRaises(self.uut.shift())
        self.assertRaises(self.uut.pop())

