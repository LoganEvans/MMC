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

from abc import ABCMeta, abstractmethod, abstractproperty
from collections import deque
from pprint import pprint, pformat
from simulate import *
import matplotlib.pyplot as plt
import math
import numpy as np
import random
import sys
import time
import bintrees
import index_rbtree.rbtree

class LinkedNode(object):
    def __init__(self, value, index_counter=None):
        self.value = value
        self.insert(None, None)
        self.set_index_counter(index_counter)

    def __str__(self):
        return "Node({0})".format(self.value)

    def remove(self):
        if self.prev_node:
            self.prev_node.next_node = self.next_node

        if self.next_node:
            self.next_node.prev_node = self.prev_node

    def insert(self, prev_node, next_node):
        self.prev_node = prev_node
        if self.prev_node:
            self.prev_node.next_node = self

        self.next_node = next_node
        if self.next_node:
            self.next_node.prev_node = self

    def set_index_counter(self, index_counter):
        self.index_counter = index_counter

    def get_index_counter(self):
        return self.index_counter

    def __eq__(self, other):
        if isinstance(other, LinkedNode):
            return self.value == other.value
        else:
            return self.value == other

    def __ne__(self, other):
        if isinstance(other, LinkedNode):
            return self.value != other.value
        else:
            return self.value != other

    def __lt__(self, other):
        if isinstance(other, LinkedNode):
            return self.value < other.value
        else:
            return self.value < other

    def __le__(self, other):
        if isinstance(other, LinkedNode):
            return self.value <= other.value
        else:
            return self.value <= other

    def __gt__(self, other):
        if isinstance(other, LinkedNode):
            return self.value > other.value
        else:
            return self.value > other

    def __ge__(self, other):
        if isinstance(other, LinkedNode):
            return self.value >= other.value
        else:
            return self.value >= other

    def __nonzero__(self):
        return True


class LinkedNodeLRU2(LinkedNode):
    def __init__(self, value, index_counter=None):
        LinkedNode.__init__(self, value, inex_counter)


class LinkedList(object):
    def __init__(self):
        self.head = None
        self.tail = None

    def __str__(self):
        vals = []
        node = self.head
        while node:
            vals.append(str(node))
            node = node.next_node
        return " -> ".join(vals)

    def __nonzero__(self):
        return bool(self.head)

    def remove_node(self, node):
        if node is None:
            return

        if node is self.head:
            self.head = self.head.next_node
            self.head.prev_node = None

        if node is self.tail:
            self.tail = self.tail.prev_node
            self.tail.next_node = None

        node.remove()

    def _push_node(self, node):
        """Adds the value to the tail of the list."""
        node.insert(self.tail, None)
        self.tail = node
        self.tail.next_node = None
        if not self.head:
            self.head = self.tail

    def push_node(self, node):
        self._push_node(node)

    def _pop_node(self):
        """Removes and returns the item at the tail of the list."""
        node = self.tail
        if node and node.prev_node:
            node.prev_node.next_node = None
            self.tail = node.prev_node
        else:
            self.head = None
            self.tail = None

        if node:
            node.insert(None, None)
        return node

    def pop_node(self):
        return self._pop_node()

    def _unshift_node(self, node):
        """Adds the value to the head of the list."""
        node.insert(None, self.head)
        self.head = node
        if not self.tail:
            self.tail = self.head

    def unshift_node(self, node):
        self._unshift_node( node)

    def _shift_node(self):
        """Removes and returns the item at the head of the list."""
        node = self.head
        if node and node.next_node:
            node.next_node.prev_node = None
            self.head = node.next_node
        else:
            self.head = None
            self.tail = None

        if node:
            node.insert(None, None)
        return node

    def shift_node(self):
        return self._shift_node()

    def clear(self):
        node = self.head
        while node:
            node = self._pop_node()


class Cache(LinkedList):
    def __init__(self):
        LinkedList.__init__(self)
        self.lut = bintrees.FastRBTree()
        self.stack = LinkedList()
        self.indexer = index_rbtree.rbtree.RBTree()
        self.index_counter = 0

    def __len__(self):
        return len(self.lut)

    def insert(self, value):
        self.index_counter -= 1
        node = LinkedNode(value, index_counter=self.index_counter)
        self.stack.unshift_node(node)
        self.lut[value] = node
        self.indexer[self.index_counter] = node

    def find_node(self, value):
        try:
            return self.lut[value]
        except KeyError:
            return None

    def find(self, value, requeue=False):
        node = self.find_node(value)
        if requeue and node:
            self.index_counter -= 1
            LinkedList.remove_node(self, node)
            self.indexer.discard(node.get_index_counter())
            node.set_index_counter(self.index_counter)
            self._unshift_node(node)
            self.indexer[self.index_counter] = node
        if node:
            return node.value

    def index(self, value):
        try:
            node = self.lut[value]
            return self.indexer.index(node.get_index_counter())
        except KeyError:
            return -1

    def remove(self, value):
        node = self.lut.pop(value)
        self.indexer.discard(node.get_index_counter())
        self.remove_node(node)

    def clear(self):
        self.stack.clear()
        self.indexer.clear()
        self.lut.clear()

    def push_node(self, node):
        self.index_counter -= 1
        node.set_index_counter(self.index_counter)
        self.indexer[self.index_counter] = node
        LinkedList.push_node(self, node)
        self.lut[node.value] = node

    def push(self, value):
        self.index_counter -= 1
        node = LinkedNode(value, self.index_counter)
        self.push_node(node)

    def pop_node(self):
        node = LinkedList.pop_node(self)
        self.lut.discard(node.value)
        self.indexer.discard(node.get_index_counter())
        return node

    def pop(self):
        node = self._pop_node()
        if node:
            return node.value

    def unshift_node(self, node):
        self.index_counter -= 1
        node.set_index_counter(self.index_counter)
        LinkedList.unshift_node(self, node)
        self.lut[node.value] = node
        self.indexer[self.index_counter] = node

    def unshift(self, value):
        self.index_counter -= 1
        node = LinkedNode(value, self.index_counter)
        self.unshift_node(node)

    def shift_node(self):
        node = LinkedList.shift_node(self)
        self.lut.discard(node.value)
        self.indexer.discard(node.get_index_counter())
        return node

    def shift(self):
        node = self._shift_node()
        if node:
            return node.value

    def clear(self):
        LinkedList.clear(self)
        self.lut.clear()
        self.indexer.clear()


class PageoutPolicy(object):
    __metaclass__ = ABCMeta
    def __init__(self, cache_size):
        self.cache_size = cache_size
        self.cache = Cache()

    @abstractmethod
    def request(self, val):
        """Returns True if val is in the cache; False otherwise."""


class Grapher(object):
    def __init__(self):
        self.observations = []

    def add_observation(self, observation):
        self.observations.append(observation)

    def graph(self, sort=False, cumulative=False, bin_proportion=0.01,
              xlim=None, ylim=None, xlab=None, ylab=None):
        if sort:
            sorter = {}
            for val in self.observations:
                if val in sorter:
                    sorter[val] += 1
                else:
                    sorter[val] = 1
            sorter = sorter.items()
            sorter.sort(key=lambda item: item[1], reverse=True)
            mocked = []
            index = 0
            for key, val in sorter:
                mocked += [index for _ in xrange(val)]
                index += 1
            sorted_data = mocked
        else:
            sorted_data = sorted(self.observations)

        fix, ax = plt.subplots()
        pmf, bins, patches = plt.hist(
                sorted_data,
                bins=get_proportional_bins(bin_proportion, sorted_data),
                normed=True,
                cumulative=cumulative,
                histtype='step')
        if xlab:
            plt.xlabel(xlab)
        if ylab:
            plt.ylabel(ylab)
        xdelta = sorted_data[-1] - sorted_data[0]
        if xlim:
            ax.set_xlim(
                    left=xlim[0],
                    right=xlim[1])
        else:
            ax.set_xlim(
                    left=sorted_data[0] - 0.01 * xdelta,
                    right=sorted_data[-1] + 0.01 * xdelta)

        if ylim:
            ax.set_ylim(bottom=ylim[0], top=ylim[1])
        else:
            ax.set_ylim(bottom=0.0, top=1.01 * max(pmf))

        plt.show()

def get_proportional_bins(proportion, sorted_data):
    bin_edges = []
    step = len(sorted_data) * proportion
    cut = step
    covered = 0.0
    while covered < 1.0:
        if int(np.ceil(cut)) < len(sorted_data):
            bin_edges.append(sorted_data[int(np.floor(cut))])
        else:
            bin_edges.append(sorted_data[-1] + 1)
        cut += step
        covered += proportion
    return sorted(set(bin_edges))


class SDDTraceGrapher(PageoutPolicy, Grapher):
    """Finds the last time the page was requested and notes how long ago that
    was. This is not a real caching policy.

    """
    def __init__(self, cache_size=None):
        PageoutPolicy.__init__(self, cache_size)
        Grapher.__init__(self)
        self.cache = Cache()
        self.num_requests = 0

    def request(self, val):
        self.num_requests += 1
        depth = self.cache.index(val)

        if depth > -1:
            self.add_observation(depth)
            self.cache.find(val, requeue=True)
        else:
            self.cache.unshift(val)

        return depth > 0

    def get_cdf(self):
        sorted_obs = deque(sorted(self.observations))
        length = float(len(sorted_obs))
        cdf = []

        cdf = []
        acc = 0.0
        for val in range(0, sorted_obs[-1]):
            while sorted_obs and val == sorted_obs[0]:
                sorted_obs.popleft()
                acc += 1
            cdf.append(acc / self.num_requests)
        return cdf


class IRMTraceGrapher(PageoutPolicy, Grapher):
    def __init__(self, cache_size=None):
        PageoutPolicy.__init__(self, cache_size)
        Grapher.__init__(self)
        self.cache = Cache()

    def request(self, val):
        self.add_observation(val)
        return False


class DistanceGrapher(PageoutPolicy, Grapher):
    def __init__(self, cache_size=None):
        PageoutPolicy.__init__(self, cache_size)
        Grapher.__init__(self)
        self.cache = Cache()

    def request(self, val):
        if val not in self.cache.lut:
            self.cache.unshift(val)

        try:
            prev_key = self.cache.lut.prev_key(val)
        except KeyError:
            prev_key = None

        try:
            succ_key = self.cache.lut.succ_key(val)
        except KeyError:
            succ_key = None

        if not prev_key and not succ_key:
            return False
        elif not prev_key:
            self.add_observation(abs(val - succ_key))
        elif not succ_key:
            self.add_observation(abs(val - prev_key))
        else:
            min_distance = min(abs(val - prev_key), abs(val - succ_key))
            self.add_observation(min_distance)

        return False

if __name__ == '__main__':
    sdd = SDDTraceGrapher()
    last_time = time.time()
    filechoice = 3
    base = 0
    limit = 1000000
    for i, page_opcode in enumerate(spc_trace(spc_files[filechoice],
                                              base, base + limit)):
        page, opcode = page_opcode
        sdd.request(page)
        if time.time() > last_time + 0.1:
            last_time = time.time()
            print i, '\r',
            sys.stdout.flush()
    #print sdd.get_cdf()
    #sdd.graph()

