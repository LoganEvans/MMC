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

import csv
import collections
import sys
import time
from bintrees import FastRBTree

class MINPolicy(object):
    def __init__(self, cache_size_limit, trace, csv_suffix=".csv"):
        self.cache_size_limit = cache_size_limit
        self.cache = {}
        self.hits = 0.0
        self.requests = 0.0
        self.ts_order = ['row', 'hit']
        self.ts_datapoint = {key: None for key in self.ts_order}
        self.ts_datapoint['row'] = 0
        self.ts_file = open("csv/min" + csv_suffix, "w")
        self.ts_writer = csv.writer(self.ts_file)
        self.ts_writer.writerow(self.ts_order)

        self.clairvoyance = FastRBTree()

        self.precog = FastRBTree()
        last_time = time.time()
        for i, page_opcode in enumerate(trace):
            if time.time() > last_time + 0.1:
                last_time = time.time()
                print '1', i, '\r',
            sys.stdout.flush()
            page, _ = page_opcode
            try:
                self.precog[page].append(i)
            except KeyError:
                self.precog[page] = collections.deque()
                self.precog[page].append(i)

            known_max = i
        known_max += 2
        for times in self.precog.values():
            times.append(known_max)
            known_max += 1
        print
        print 'Done loading.'

    def hit_rate(self):
        return self.hits / self.requests

    def request(self, page):
        self.requests += 1
        if page in self.cache:
            was_hit = True
            self.hits += 1
        else:
            was_hit = False

        self.cache[page] = self.precog[page].popleft()
        # This happens on startup.
        if self.cache[page] < self.requests:
            self.cache[page] = self.precog[page].popleft()
        self.clairvoyance[self.cache[page]] = page
        self.ts_datapoint['row'] += 1

        if was_hit:
            self.ts_datapoint['hit'] = 1
        else:
            self.ts_datapoint['hit'] = 0

        self.ts_writer.writerow(
                [self.ts_datapoint[key] for key in self.ts_order])
        self.ts_file.flush()

        if len(self.cache) > self.cache_size_limit:
            next_use, page = self.clairvoyance.pop_max()
            del self.cache[page]

