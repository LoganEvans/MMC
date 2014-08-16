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
import numpy as np
import scipy.stats as stats
from MMC import Cache, TraceMixin, StackDepthMixin, FrequencyMixin
from MMC import StackTraceMixin, MMCPolicyOne, debug
from pprint import pprint
#debug.do_show = False

class TestCache(unittest.TestCase):
    def setUp(self):
        class CacheTest(Cache):
            def pageout(self): pass
        self.uut = CacheTest()

    def test_request_no_hits(self):
        for page in range(20):
            self.uut.request(page)
        self.assertEqual(len(self.uut.cache_list), 20)

    def test_request_with_hits(self):
        for page in range(20):
            self.uut.request(page)
        self.assertEqual(len(self.uut.cache_list), 20)
        for page in range(10, 30):
            self.uut.request(page)
        self.assertEqual(len(self.uut.cache_list), 30)

class TestTraceMixin(unittest.TestCase):
    def setUp(self):
        class TraceMixinTest(Cache, TraceMixin):
            def __init__(self, trace_size_limit):
                Cache.__init__(self)
                TraceMixin.__init__(self, trace_size_limit)
            def pageout(self):
                pass
        self.uut = TraceMixinTest(trace_size_limit=100)

    def test_request(self):
        for page in range(1, 201):
            self.uut.request(page)
            self.assertEqual(min(page, 100), len(self.uut.trace))

class TestStackDepthMixin(unittest.TestCase):
    def setUp(self):
        class StackDepthMixinTest(Cache, StackDepthMixin, TraceMixin):
            def __init__(self):
                Cache.__init__(self)
                StackDepthMixin.__init__(self)
                # Including this to give the test more chances to fail.
                TraceMixin.__init__(self, trace_size_limit=10)
            def pageout(self):
                pass
        self.uut = StackDepthMixinTest()

    def test_request(self):
        for page in range(100):
            self.uut.request(page)
        self.assertEqual(len(self.uut.cache_list), 100)
        self.assertEqual(len(self.uut.stack), 100)

    def test_depth(self):
        for page in [1, 2, 1]:
            self.uut.request(page)
        self.assertEqual(len(self.uut.cache_list), 2)
        self.assertEqual(len(self.uut.stack), 2)
        self.assertEqual(self.uut.depth(1), 0)
        self.assertEqual(self.uut.depth(2), 1)

    def test_depth_random(self):
        slow_stack = []
        for _ in range(1000):
            page = np.random.randint(0, 50)
            if page in slow_stack:
                self.assertEqual(self.uut.depth(page), slow_stack.index(page))
                slow_stack.insert(0, slow_stack.pop(slow_stack.index(page)))
            else:
                self.assertEqual(None, self.uut.depth(page))
                slow_stack.insert(0, page)
            self.uut.request(page)
            self.assertEqual(len(slow_stack), len(self.uut.cache_list))

    def test_top_of_stack_prev_depth(self):
        slow_stack = []
        for _ in range(1000):
            page = np.random.randint(0, 50)
            if page in slow_stack:
                prev_depth = slow_stack.index(page)
                self.assertEqual(self.uut.depth(page), slow_stack.index(page))
                slow_stack.insert(0, slow_stack.pop(slow_stack.index(page)))
            else:
                prev_depth = None
                self.assertEqual(None, self.uut.depth(page))
                slow_stack.insert(0, page)
            self.uut.request(page)
            self.assertEqual(prev_depth, self.uut.top_of_stack_prev_depth())
            self.assertEqual(len(slow_stack), len(self.uut.cache_list))

class TestStackTraceMixin(unittest.TestCase):
    def setUp(self):
        class StackTraceMixinTest(Cache, StackTraceMixin):
            def __init__(self):
                Cache.__init__(self)
                StackTraceMixin.__init__(self, trace_size_limit=10)
            def pageout(self):
                pass
        self.uut = StackTraceMixinTest()

    def test_request(self):
        for page in range(1, 201):
            self.uut.request(page)
            self.assertEqual(min(page, 10), len(self.uut.trace))

    def test_depth_record(self):
        slow_stack = []
        for _ in range(1000):
            page = np.random.randint(0, 50)
            if page in slow_stack:
                prev_depth = slow_stack.index(page)
                self.assertEqual(self.uut.depth(page), slow_stack.index(page))
                slow_stack.insert(0, slow_stack.pop(slow_stack.index(page)))
            else:
                prev_depth = None
                self.assertEqual(None, self.uut.depth(page))
                slow_stack.insert(0, page)
            self.uut.request(page)
            self.assertEqual(prev_depth, self.uut.top_of_stack_prev_depth())
            self.assertEqual(prev_depth, self.uut.trace[-1].get_depth())
            self.assertEqual(len(slow_stack), len(self.uut.cache_list))

def pnode(node):
    print "{0:>4} ({1:>.2f}): {2:>6} <{3:>6}> {4:>6}".format(
            node.freq_rank, node.get_hit_count(),
            node.prev_node.get_page_key() if node.prev_node else 0.0,
            node.get_page_key(),
            node.next_node.get_page_key() if node.next_node else 0.0)

def plist(uut):
    print "len(uut.cache):", len(uut.cache_list)
    print "Forward:"
    node = uut.freq_list_head
    while node:
        pnode(node)
        node = node.next_node
   #print "Backward:"
   #node = uut.freq_list_tail
   #while node:
   #    pnode(node)
   #    node = node.prev_node

class TestFrequencyMixin(unittest.TestCase):
    def setUp(self):
        class FrequencyMixinTest(
                Cache, FrequencyMixin, StackDepthMixin, TraceMixin):
            def __init__(self):
                Cache.__init__(self)
                FrequencyMixin.__init__(self)
                StackDepthMixin.__init__(self)
                # Including this to give the test more chances to fail.
                TraceMixin.__init__(self, trace_size_limit=10)
            def pageout(self):
                pass
        self.uut = FrequencyMixinTest()

    def test_request(self):
        for page in range(100):
            self.uut.request(page)
        self.assertEqual(len(self.uut.cache_list), 100)

    def test_frequency(self):
        check = []
        for _ in range(1000):
            page = np.random.randint(0, 50)
            check.append(page)
            self.uut.request(page)
            self.assertEqual(
                    float(check.count(page)) / len(check),
                    self.uut.frequency(page))

    def test_frequency_rank(self):
        check = []
        self.uut.request(2)
        self.uut.request(2)
        for page in range(3, 50):
            self.uut.request(page)
            self.assertEqual(
                    self.uut.get_node(page).get_frequency_rank(),
                    page - 2)
            for _ in range(1, page):
                self.uut.request(page)
            self.assertEqual(
                    self.uut.get_node(page).get_frequency_rank(), 0)

    def test_reorder_rank(self):
        def assertion():
            pages = [node.get_page_key() for node in self.uut.cache_list]
            len_head = 0
            head = self.uut.freq_list_head
            while head:
                len_head += 1
                self.assertEqual(head.freq_rank, len_head - 1)
                head = head.next_node
            self.assertEqual(len_head, len(pages))
            len_tail = 0
            tail = self.uut.freq_list_tail
            len_full_cache = len(self.uut.full_cache_list)
            while tail:
                len_tail += 1
                self.assertEqual(tail.freq_rank, len_full_cache - len_tail)
                tail = tail.prev_node
            self.assertEqual(len_tail, len(pages))

        unif = stats.uniform(0, 50)
        for _ in range(5000):
            page = int(np.floor(unif.rvs()))
            self.uut.request(page)
            assertion()

class TestMMCPolicyOne(unittest.TestCase):
    def setUp(self):
        self.uut = MMCPolicyOne(
                cache_size_limit=1000, full_cache_size_limit=1000,
                trace_size_limit=500)

    def test_run_EM_algorithm(self):
        for _ in range(1000):
            page = np.random.randint(0, 50)
            self.uut.request(page)
        self.uut.run_EM_algorithm(3)
        self.assertTrue(0.0 <= self.uut.tau[0] and self.uut.tau[0] <= 1.0)
        self.assertAlmostEqual(self.uut.tau[0], 1.0 - self.uut.tau[1], places=10)
        self.assertTrue(0.0 <= self.uut.theta[0] and self.uut.theta[0] <= 1.0)
        self.assertTrue(0.0 <= self.uut.theta[1] and self.uut.theta[1] <= 1.0)

    def test_update_record_runs(self):
        for _ in range(1000):
            page = np.random.randint(0, 50)
            self.uut.request(page)
        self.uut.run_EM_algorithm(3)
        self.uut.update_expected_values()
        for node in self.uut.cache_list:
            self.assertTrue(0.0 <= node.get_expected_value() and
                            node.get_expected_value() <= 1.0)

    def test_correct_callback_is_last(self):
        self.assertEqual(
                MMCPolicyOne.request_page_callback,
                self.uut.request_page_callbacks[-1])

    def test_pageout_maintains_size(self):
        self.uut = MMCPolicyOne(
                cache_size_limit=10, full_cache_size_limit=20,
                trace_size_limit=15)
        g = stats.geom(0.05)
        # Fill up the cache.
        for page in range(100):
            self.uut.request(page)

        # Request some cache hits and some cache misses.
        for page in range(5) + range(100, 105):
            self.uut.request(page)
            self.assertEqual(len(self.uut.cache_list), 10)
            self.assertEqual(len(self.uut.full_cache), 20)
            self.assertEqual(len(self.uut.trace), 15)

    def test_purge_works(self):
        for page in range(10):
            self.uut.request(page)

        self.assertEqual(10, len(self.uut.full_cache))
        self.assertEqual(10, len(self.uut.stack))
        self.assertTrue(10 in self.uut.full_cache)

        self.uut.trigger_purge_node_callbacks(self.uut.full_cache.pop(5))
        self.assertEqual(len(self.uut.full_cache), len(self.uut.stack))

