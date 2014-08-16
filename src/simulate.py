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

import sys
import time
from mmc import MMCPolicy
from mmc_rw import MMCRWPolicy
from arc import ARCPolicy
from lru import LRUPolicy
from min_policy import MINPolicy
from dump_full_cache_to_csv import dump_cache
import numpy as np

def spc_trace(fname, lower, upper):
    burned = 0
    yielded = 0
    with open(fname, 'r') as fin:
        while True:
            next_line = fin.readline()
            if not next_line:
                raise StopIteration
            else:
                asu, lba, size, opcode, timestamp = next_line.split(',')
                asu = int(asu)
                lba = int(lba)
                size = int(size)
                timestamp = float(timestamp)
                for i in range(size / 512):
                    if burned < lower:
                        burned += 1
                    elif yielded < upper - lower:
                        yield int(lba + i), opcode
                        yielded += 1
                    else:
                        raise StopIteration


def synthetic_trace(count, tau, theta):
    domain = list(range(100000))
    np.random.seed(0)
    irm = list(np.random.permutation(domain))
    sdd = irm[:]

    def cdf_to_idx(p, cdf):
        try:
            return int(np.around(-1 + np.log(1 - cdf) /
                       np.log(1 - p), decimals=0))
        except ValueError:
            return -1

    for i in xrange(count):
        cdf = np.random.uniform(0, 1)
        if np.random.uniform(0, 1) < tau:
            idx = cdf_to_idx(theta[0], cdf)
            page = sdd[idx]
        else:
            idx = cdf_to_idx(theta[1], cdf)
            page = irm[idx]
        sdd.insert(0, sdd.pop(sdd.index(page)))
        yield page


def simulate(request_generator, mmc=None, arc=None, lru=None, mmc_rw=None,
             tag=None):
    def p():
        print ('{5}: i: {0:>6} mmc: {1:>6.4f} mmc_rw: {2:>6.4f} '
               'arc: {3:>6.4f} lru: {4:>6.4f}\r'
               ''.format(
                    i,
                    mmc.hit_rate() if mmc else -1.0,
                    mmc_rw.hit_rate() if mmc_rw else -1.0,
                    arc.hit_rate() if arc else -1.0,
                    lru.hit_rate() if lru else -1.0,
                    tag
            )),
        sys.stdout.flush()
    last_time = time.time()
    seq = 0
    for i, page_opcode in enumerate(request_generator):
        if seq > 10000:
            break
        page, opcode = page_opcode
      # if i < 50000:
      #     continue
      # seq += 1
      # if seq > 1000000:
      #     break
        if mmc:
            mmc.request(page)
        if mmc_rw:
            mmc_rw.request(page, opcode)
        if arc:
            arc.request(page)
        if lru:
            lru.request(page)
        if time.time() > last_time + 0.1:
            last_time = time.time()
            p()
    p()
    print
    if mmc:
        print mmc.tau, mmc.theta


spc_files = [
    "../traces/short.spc",
    "../traces/short2.spc",
    "../traces/Financial1.spc",
    "../traces/Financial2.spc",
    "../traces/Financial1.spc",
    "../traces/Financial1.spc",
    "../traces/WebSearch1.spc",
    "../traces/WebSearch2.spc",
    "../traces/WebSearch3.spc"]

def run_min(entries, get_trace, csv_suffix):
    min_ = MINPolicy(entries, get_trace(), csv_suffix)
    last_time = time.time()
    for i, page_opcode in enumerate(get_trace()):
        if time.time() > last_time + 0.1:
            last_time = time.time()
            print '2', i, '\r',
            sys.stdout.flush()

        page, opcode = page_opcode
        min_.request(page)

if __name__ == '__main__':
    entries = 445
    ghost = entries
    trace = 4 * entries
    #trace = 2000
    #limit = 2000
    base = 0
    limit = 1000000
    file_choice = 4
    tag = "{0}_{1}_{2}_{3}".format(entries, ghost, trace, file_choice)
    csv_suffix = "_{0}.csv".format(tag)
    mmc = MMCPolicy(
            cache_entries_limit=entries, ghost_entries_limit=ghost,
            trace_size_limit=trace, csv_suffix=csv_suffix,
            draw_dump=True)
   #mmc_rw = MMCRWPolicy(
   #        cache_entries_limit=entries, ghost_entries_limit=ghost,
   #        trace_size_limit=trace, csv_suffix=csv_suffix)
    arc = ARCPolicy(entries, csv_suffix=csv_suffix)
    lru = LRUPolicy(entries, csv_suffix=csv_suffix)

    get_trace = lambda: spc_trace(spc_files[file_choice], base, base + limit)
    #run_min(entries, get_trace, csv_suffix)
    simulate(get_trace(), mmc=mmc, arc=arc, lru=lru, mmc_rw=None,
             tag=tag)
   #simulate(
   #        synthetic_trace(count=20000, tau=0.35, theta=[0.02, 0.002]),
   #        mmc=mmc, arc=arc, lru=lru, tag=tag)

   #mmc.EM_algorithm(delta=0.00001)
   #dump_cache(mmc, tag)

