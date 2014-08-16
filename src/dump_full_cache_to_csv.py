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

def dump_cache(cache, tag):
    extension = "{tag}_{num_requests:0>7}.csv".format(
            tag=tag[:-len(".csv")], num_requests=cache.num_requests)

    info_order = ["tau", "theta0", "theta1"]
    info_file = open("csv/cache_dump/cache_dump_info_" + extension, "w")
    info_writer = csv.writer(info_file)
    info_writer.writerow(["tau", "theta0", "theta1"])
    info_writer.writerow([cache.tau[0], cache.theta[0], cache.theta[1]])
    info_file.close()

    order = ['row', 'is_evicted', 'depth', 'rank', 'value', 'value_order']
    datapoint = {key: None for key in order}
    datapoint['row'] = 0
    csv_file = open("csv/cache_dump/cache_dump_" + extension, "w")
    writer = csv.writer(csv_file)
    writer.writerow(order)

    nodes = []
    for node in cache.full_cache.values():
        try:
            node.recompute_expected_value()
        except:
            pass
        nodes.append(node)

    try:
        nodes.sort(key=lambda node: node.expected_value)
    except:
        nodes.sort(key=lambda node: node.get_expected_value())
    nodes.reverse()

    for value_order, node in enumerate(nodes):
        datapoint['row'] += 1
        try:
            is_evicted = node.is_evicted()
            depth = node.depth
            rank = node.freq_rank
            value = node.get_expected_value()
        except:
            is_evicted = node.is_evicted
            depth = node.depth
            rank = node.rank
            node.recompute_expected_value()
            value = node.expected_value
        datapoint['is_evicted'] = int(is_evicted)
        datapoint['depth'] = depth
        datapoint['rank'] = rank
        datapoint['value'] = value
        datapoint['value_order'] = value_order + 1
        writer.writerow([datapoint[key] for key in order])
    csv_file.close()

