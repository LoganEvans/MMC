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

from bintrees import FastRBTree
from index_rbtree.rbtree import RBTree
from pprint import pprint
import numpy as np
import collections
import csv
import time
from dump_full_cache_to_csv import dump_cache

class Node(object):
    def __init__(self, cache):
        self.cache = cache
        self.page_key = None
        self.is_evicted = None
        self.is_purged = None
        self._expected_value = None
        self._hit_count = 0.0
        self.stack_key = None
        self.ranker_key = None

    @property
    def expected_value(self):
        if self._expected_value is None:
            self.recompute_expected_value()
        return self._expected_value

    def recompute_expected_value(self, depth=None, rank=None):
        tau = self.cache.tau
        theta = self.cache.theta
        depth = depth or self.depth
        rank = rank or self.rank
        value = tau[0] * theta[0] * (1.0 - theta[0])**depth
        value += tau[1] * theta[1] * (1.0 - theta[1])**rank
        self._expected_value = value

    @property
    def depth(self):
        try:
            return self.cache.stack.index(self.stack_key)
        except KeyError:
            return 1.0 / self.cache.theta[0]

    def restack(self):
        self.cache.stack.discard(self.stack_key)
        self.stack_key = self.new_stack_key()
        self.cache.stack[self.stack_key] = self

    def rerank(self):
        self.cache.ranker.discard(self.ranker_key)
        self.ranker_key = self.new_ranker_key()
        self.cache.ranker[self.ranker_key] = self

    @property
    def hit_count(self):
        return self._hit_count

    @hit_count.setter
    def hit_count(self, new_hit_count):
        if self.is_purged:
            return
        self._hit_count = new_hit_count
        self.rerank()

    def new_stack_key(self):
        key = self.cache.generation
        self.cache.generation -= 1
        return key

    def new_ranker_key(self):
        gen_key = self.cache.generation
        self.cache.generation -= 1
        return (-self.hit_count, gen_key)

    @property
    def rank(self):
        try:
            return self.cache.ranker.index(self.ranker_key)
        except KeyError:
            return 1.0 / self.cache.theta[1]

    def purge(self):
        self.rank_purge_memo = self.rank
        self.cache.stack.discard(self.stack_key)
        self.stack_key = None
        self.cache.ranker.discard(self.ranker_key)
        self.ranker_key = None
        self.is_purged = True
        del self.cache.full_cache[self.page_key]


class Record(object):
    def __init__(self, cache, node):
        self.cache = cache
        self.node = node
        self.depth = node.depth
        self.rank_memo = node.rank
        self._Z = self.cache.calculate_Z(self.depth, node.rank)
        self.was_hit = cache.was_hit

    @property
    def Z(self):
        return self._Z

    @Z.setter
    def Z(self, new_Z):
        self._Z = new_Z

class MMCPolicy(object):
    def __init__(self, cache_entries_limit, ghost_entries_limit,
                 trace_size_limit, csv_suffix="_mmc.csv", draw_dump=False):
        self.full_cache = FastRBTree()
        self.was_hit = None
        self.was_ghost_hit = None
        self.num_hits = 0
        self.num_requests = 0
        self.cache_entries_limit = cache_entries_limit
        self.ghost_entries_limit = ghost_entries_limit
        self.trace_size_limit = trace_size_limit
        self.trace = collections.deque()
        self.stack = RBTree()
        self.ranker = RBTree()
        self.generation = 0
        # During startup, this will act like an LRU.
        self.startup = True
        self.EM_period = 50 * int(np.ceil(np.log(trace_size_limit)))
        self.countdown_to_EM = trace_size_limit // 2
        self.tau = [0.5, 0.5]
        self.theta = [0.5, 0.5]
        self.acc_tau = [0.0]
        self.acc_theta = [0.0, 0.0]
        self.num_in_cache = 0
        self.num_in_full_cache = 0
        self.csv_suffix = csv_suffix
        self.draw_dump = draw_dump

        self.ts_order = [
                'row', 'hit', 'ghost_hit', 'tau',
                'theta0', 'theta1', 'Z', 'depth', 'rank']
        self.ts_datapoint = {key: None for key in self.ts_order}
        self.ts_datapoint['row'] = 0
        self.ts_file = open("csv/mmc" + self.csv_suffix, "w")
        self.ts_writer = csv.writer(self.ts_file)
        self.ts_writer.writerow(self.ts_order)

        self.evict_order = [
                'row', 'depth', 'rank', 'value', 'Z', 'tau']
        self.evict_datapoint = {key: None for key in self.evict_order}
        self.evict_datapoint['row'] = 0
        self.evict_file = open("csv/mmc_evict" + self.csv_suffix, "w")
        self.evict_writer = csv.writer(self.evict_file)
        self.evict_writer.writerow(self.evict_order)

        self.purge_order = ['row', 'depth', 'rank', 'value', 'Z']
        self.purge_datapoint = {key: None for key in self.purge_order}
        self.purge_datapoint['row'] = 0
        self.purge_file = open("csv/mmc_purge" + self.csv_suffix, "w")
        self.purge_writer = csv.writer(self.purge_file)
        self.purge_writer.writerow(self.purge_order)

    def request(self, page):
        self.num_requests += 1
        self.was_hit = False
        self.was_ghost_hit = False
        node = self.get_node(page)
        if node:
            self.was_ghost_hit = True
            if not node.is_evicted:
                self.num_hits += 1
                self.was_hit = True
            node.hit_count += 1.0 - self.calculate_Z(node.depth, node.rank)
        else:
            node = Node(self)
            node.hit_count = self.tau[1]
            node.page_key = page
            self.full_cache[page] = node

        if not self.was_hit:
            self.num_in_cache += 1
        if not self.was_ghost_hit:
            self.num_in_full_cache += 1

        node.is_evicted = node.is_purged = False
        record = Record(self, node)
        self.add_trace_record(record)

        if len(self.trace) > self.trace_size_limit:
            popped_record = self.trace.popleft()
            self.update_tau_and_theta_accs(record, increment=True)
            self.update_tau_and_theta_accs(popped_record, increment=False)
            self.refresh_params()
            popped_record.node.hit_count -= 1.0 - popped_record.Z

        node.restack()
        node.rerank()

        self.countdown_to_EM -= 1
        if self.countdown_to_EM == 0:
            self.EM_algorithm(delta=0.00001)
            self.countdown_to_EM = self.EM_period
            self.startup = False

        if (
          self.num_in_cache > self.cache_entries_limit or
          self.num_in_full_cache >
          self.cache_entries_limit + self.ghost_entries_limit
        ):
            self.pageout()
        if self.draw_dump:
            dump_cache(self, self.csv_suffix)

    def add_trace_record(self, record):
        self.ts_datapoint['row'] = self.num_requests
        if self.was_hit:
            self.ts_datapoint['hit'] = 1
        else:
            self.ts_datapoint['hit'] = 0

        if self.was_ghost_hit:
            self.ts_datapoint['ghost_hit'] = 1
        else:
            self.ts_datapoint['ghost_hit'] = 0

        self.ts_datapoint['tau'] = self.tau[0]
        self.ts_datapoint['theta0'] = self.theta[0]
        self.ts_datapoint['theta1'] = self.theta[1]
        depth = record.depth
        self.ts_datapoint['depth'] = depth
        self.ts_datapoint['rank'] = record.node.rank
        self.ts_datapoint['Z'] = record.Z
        self.ts_writer.writerow(
                [self.ts_datapoint[key] for key in self.ts_order])
        self.ts_file.flush()
        self.trace.append(record)

    def pageout(self):
        min_node = None
        min_node_value = None
        min_ghost = None
        min_ghost_value = None

        for depth, node in enumerate(self.stack.values()):
            node.depth_memo = depth

        for rank, node in enumerate(self.ranker.values()):
            node.recompute_expected_value(depth=node.depth_memo, rank=rank)
            value = node.expected_value
            if not node.is_evicted:
                if min_node is None or value < min_node_value:
                    min_node = node
                    min_node_value = value
            if min_ghost is None or value < min_ghost_value:
                min_ghost = node
                min_ghost_value = value

        if self.num_in_cache > self.cache_entries_limit:
            self.evict(min_node)

        if (
          self.num_in_full_cache >
          self.cache_entries_limit + self.ghost_entries_limit
        ):
            self.purge(min_ghost)

    def EM_algorithm(self, delta):
        def abs_sum():
            return abs(self.tau[0]) + abs(self.theta[0]) + abs(self.theta[1])
        before = delta + 4.0
        i = 0
        # We need to detect if we're in a "nonsense" local optimum. The
        # algorithm will optimize to the global maximum if we aren't in one of
        # these cases.
        if (self.startup or
            self.tau[0] == 0.0 or
            self.tau[0] == 1.0 or
            self.theta[0] == 0.0 or
            self.theta[0] == 0.0
        ):
            use_hard_Z = True
        else:
            use_hard_Z = False

        while abs(before - abs_sum()) > delta:
            before = abs_sum()
            hard_Z = 0.5 if use_hard_Z and i == 0 else None
            self.E_step(hard_Z=hard_Z)
            i += 1
            self.M_step()
            # Since we are rearranging the ranks, it's possible that we can
            # get into a situation where the ranks shift in a cycle such
            # that the tau delta is always exeeded. I've only seen this limit
            # hit when the trace size is very small (e.g. 10).
            if i > 50:
                break

    def E_step(self, hard_Z=None):
        """Treat self.tau and self.theta as constants."""
        for node in self.full_cache.values():
            node._hit_count = 0.0

        for record in self.trace:
            if hard_Z is None:
                if record.node.is_purged:
                    rank = record.node.rank_purge_memo
                else:
                    rank = record.node.rank
                record._Z = self.calculate_Z(record.depth, rank)
            else:
                record._Z = hard_Z
            record.node._hit_count += (1.0 - record._Z)

        new_ranker = RBTree()
        for node in self.full_cache.values():
            node.ranker_key = node.new_ranker_key()
            new_ranker[node.ranker_key] = node
        self.ranker = new_ranker

    def M_step(self):
        """Treat Record.Z as constant."""
        self.acc_tau = [0.0]
        self.acc_theta = [0.0, 0.0]
        for record in self.trace:
            self.update_tau_and_theta_accs(record, increment=True)
        self.refresh_params()

    def calculate_Z(self, depth, rank):
        numerator = (
                self.tau[0] *
                self.theta[0] *
                (1 - self.theta[0])**depth)
        denominator = (
                numerator +
                self.tau[1] *
                self.theta[1] *
                (1 - self.theta[1])**rank)
        try:
            return float(numerator) / denominator
        except ZeroDivisionError as err:
            # This can happen when a node falls off the trace and rank and
            # depth become greater than the limits.
            return self.tau[0]

    def refresh_params(self):
        R = len(self.trace)
        self.tau[0] = self.acc_tau[0] / R
        self.tau[1] = 1.0 - self.tau[0]

        try:
            self.theta[0] = ((R * self.tau[0]) /
                             (R * self.tau[0] + self.acc_theta[0]))
        except ZeroDivisionError:
            self.theta[0] = 1.0 / len(self.full_cache)

        try:
            self.theta[1] = ((R * self.tau[1]) /
                             (R * self.tau[1] + self.acc_theta[1]))
        except ZeroDivisionError:
            self.theta[1] = 1.0 / len(self.full_cache)

    def _update_tau_and_theta_accs(self, Z, depth, rank, increment=True):
        if increment:
            self.acc_tau[0] += Z
            self.acc_theta[0] += Z * depth
            self.acc_theta[1] += (1.0 - Z) * rank
        else:
            self.acc_tau[0] -= Z
            self.acc_theta[0] -= Z * depth
            self.acc_theta[1] -= (1.0 - Z) * rank
            self.acc_theta = [max(0.0, acc) for acc in self.acc_theta]

    def update_tau_and_theta_accs(self, record, increment=True):
        depth = record.depth

        if record.node.is_purged:
            rank = record.node.rank_purge_memo
        else:
            rank = record.node.rank

        self._update_tau_and_theta_accs(record.Z, depth, rank, increment)

    def evict(self, node):
        self.evict_datapoint['row'] += 1
        self.evict_datapoint['depth'] = node.depth
        self.evict_datapoint['rank'] = node.rank
        self.evict_datapoint['value'] = node.expected_value
        self.evict_datapoint['Z'] = self.calculate_Z(
                node.depth, node.rank)
        self.evict_datapoint['tau'] = self.tau[0]
        self.evict_writer.writerow(
                [self.evict_datapoint[key] for key in self.evict_order])
        self.evict_file.flush()
        self.num_in_cache -= 1
        node.is_evicted = True

    def purge(self, node):
        self.purge_datapoint['row'] += 1
        self.purge_datapoint['depth'] = node.depth
        self.purge_datapoint['rank'] = node.rank
        self.purge_datapoint['value'] = node.expected_value
        self.purge_datapoint['Z'] = self.calculate_Z(
                node.depth, node.rank)
        self.purge_writer.writerow(
                [self.purge_datapoint[key] for key in self.purge_order])
        self.purge_file.flush()
        self.num_in_full_cache -= 1
        node.purge()

    @property
    def cache_list(self):
        return filter(lambda node: not node.is_evicted, self.full_cache_list)

    @property
    def full_cache_list(self):
        return list(self.full_cache.values())

    def hit_rate(self):
        return float(self.num_hits) / self.num_requests

    def get_node(self, page):
        try:
            node = self.full_cache[page]
            return node
        except KeyError:
            return None

