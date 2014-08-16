# Copyright: Eric Casteleijn (MIT liscense)
# Source:
# http://code.activestate.com/recipes/576532-adaptive-replacement-cache-in-python/

from collections import deque
import csv

class ARCPolicy(object):
    def __init__(self, size, csv_suffix=".csv"):
        self.c = size
        self.p = 0
        self.t1 = deque()
        self.t2 = deque()
        self.b1 = deque()
        self.b2 = deque()

        self.hits = 0
        self.requests = 0
        self.ts_order = [
                'row', 'hit', 't1', 'b1', 't2', 'b2', 'p',
                'len_t1', 'len_b1', 'len_t2', 'len_b2']
        self.ts_datapoint = {key: None for key in self.ts_order}
        self.ts_datapoint['row'] = 0
        self.ts_file = open("csv/arc" + csv_suffix, "w")
        self.ts_writer = csv.writer(self.ts_file)
        self.ts_writer.writerow(self.ts_order)

    def hit_rate(self):
        return float(self.hits) / self.requests

    def replace(self, page):
        if (
          self.t1 and
          ((page in self.b2 and len(self.t1) == self.p) or
           (len(self.t1) > self.p))
        ):
            old = self.t1.pop()
            self.b1.appendleft(old)
        else:
            old = self.t2.pop()
            self.b2.appendleft(old)

    def request(self, page):
        self.requests += 1
        self.ts_datapoint['row'] += 1
        self.ts_datapoint['t1'] = 0
        self.ts_datapoint['b1'] = 0
        self.ts_datapoint['t2'] = 0
        self.ts_datapoint['b2'] = 0
        self._request(page)
        self.ts_datapoint['hit'] = max(
                self.ts_datapoint['t1'], self.ts_datapoint['t2'])
        self.ts_datapoint['ghost_hit'] = max(
                self.ts_datapoint['b1'], self.ts_datapoint['b2'])
        if self.ts_datapoint['hit']:
            self.hits += 1
        self.ts_datapoint['hit_rate'] = self.hit_rate()
        self.ts_datapoint['p'] = self.p
        self.ts_datapoint['len_t1'] = len(self.t1)
        self.ts_datapoint['len_b1'] = len(self.b1)
        self.ts_datapoint['len_t2'] = len(self.t2)
        self.ts_datapoint['len_b2'] = len(self.b2)
        self.ts_writer.writerow(
                [self.ts_datapoint[key] for key in self.ts_order])
        self.ts_file.flush()

    def _request(self, page):
        if page in self.t1:
            self.ts_datapoint['t1'] = 1
            self.t1.remove(page)
            self.t2.appendleft(page)
            return
        if page in self.t2:
            self.ts_datapoint['t2'] = 1
            self.t2.remove(page)
            self.t2.appendleft(page)
            return
        if page in self.b1:
            self.ts_datapoint['b1'] = 1
            self.p = min(self.c, self.p + max(len(self.b2) / len(self.b1) , 1))
            self.replace(page)
            self.b1.remove(page)
            self.t2.appendleft(page)
            #print "%s:: t1:%s b1:%s t2:%s b2:%s p:%s" % (
            #    repr(func)[10:30], len(self.t1),len(self.b1),len(self.t2),
            #    len(self.b2), self.p)
            return
        if page in self.b2:
            self.ts_datapoint['b2'] = 1
            self.p = max(0, self.p - max(len(self.b1) / len(self.b2), 1))
            self.replace(page)
            self.b2.remove(page)
            self.t2.appendleft(page)
            #print "%s:: t1:%s b1:%s t2:%s b2:%s p:%s" % (
            #   repr(func)[10:30], len(self.t1),len(self.b1),len(self.t2),
            #   len(self.b2), self.p)
            return
        if len(self.t1) + len(self.b1) == self.c:
            if len(self.t1) < self.c:
                self.b1.pop()
                self.replace(page)
            else:
                self.t1.pop()
        else:
            total = (len(self.t1) + len(self.b1) +
                     len(self.t2) + len(self.b2))
            if total >= self.c:
                if total == (2 * self.c):
                    self.b2.pop()
                self.replace(page)
        self.t1.appendleft(page)

