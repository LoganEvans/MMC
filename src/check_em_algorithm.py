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

import numpy as np
import time
from pprint import pprint
from empirical_cache_hits import *
import scipy.stats as stats

class XZ(object):
    def __init__(self, x, true_z=None):
        self.x = x
        self.true_z = true_z
        self.z = None
        self.H_0 = None
        self.H_1 = None

    def __str__(self):
        return ("x: {self.x} z: {self.z} true_z: {self.true_z}"
                "".format(self=self))

    def set_z(self, tau, theta_0, theta_1):
        num = tau * theta_0 * (1 - theta_0)**self.H_0
        denom = []
        denom.append(num)
        denom.append((1 - tau) * theta_1 * (1 - theta_1)**self.H_1)
        self.z = num / sum(denom)


def idx_to_cdf(p, idx):
    return 1 - (1 - p) ** (idx + 1)

def cdf_to_idx(p, cdf):
    # This uses the formula:
    # cdf = 1 - (1 - p) ** (k + 1)
    # log(cdf - 1) = (k + 1) log(1 - p)
    # k = -1 + log(cdf - 1) / log(1 - p)
    try:
        return int(np.around(-1 + np.log(1 - cdf) / np.log(1 - p), decimals=0))
    except ValueError:
        return -1

def gen_sample(domain, tau, theta_0, theta_1, n=None, burn=1000):
    irm = list(np.random.permutation(domain))
    sdd = irm[:]

    def one_ob():
        cdf = np.random.uniform(0, 1)
        if np.random.uniform(0, 1) < tau:
            idx = cdf_to_idx(theta_0, cdf)
            ob = XZ(sdd[idx], true_z=1)
            ob.H_0 = idx
            sdd.insert(0, sdd.pop(idx))
        else:
            idx = cdf_to_idx(theta_1, cdf)
            ob = XZ(irm[idx], true_z=0)
            ob.H_0 = sdd.index(ob.x)
            #ob.H_1 = idx
        return ob

    for i in xrange(burn):
        one_ob()
    if n is None:
        yield one_ob()
    else:
        for _ in xrange(n):
            yield one_ob()

def estimate_irm(obs):
    mapping = {}
    for ob in obs:
        if not ob.z:
            ob.z = 0.5
        if ob.x in mapping:
            #mapping[ob.x] += 1 - ob.z
            mapping[ob.x] += 1 - ob.z
        else:
            #mapping[ob.x] = 1 - ob.z
            mapping[ob.x] = 1 - ob.z
    return zip(*sorted(mapping.items(), key=lambda a: -a[1]))[0]

def assign_all_H_1(obs):
    irm = estimate_irm(obs)
    for ob in obs:
        ob.H_1 = irm.index(ob.x)

def estimate_tau(obs):
    return sum([ob.z for ob in obs]) / len(obs)

def estimate_theta_0(obs, tau=None):
    if tau is None:
        tau = estimate_tau(obs)
    num = len(obs) * tau
    acc = 0.0
    for ob in iter(obs):
        acc += ob.z * ob.H_0
    return num / (num + acc)

def estimate_theta_1(obs, tau=None):
    if tau is None:
        tau = estimate_tau(obs)
    num = len(obs) * (1 - tau)
    acc = 0.0
    for ob in iter(obs):
        acc += (1 - ob.z) * ob.H_1
    return num / (num + acc)

def EM(obs):
    tau = 0.5
    theta_0 = 0.1
    theta_1 = 0.1
    while True:
        print tau, theta_0, theta_1
        assign_all_H_1(obs)
        # E step
        for ob in obs:
            ob.set_z(tau, theta_0, theta_1)
        tau = estimate_tau(obs)
        theta_0 = estimate_theta_0(obs, tau)
        theta_1 = estimate_theta_1(obs, tau)
        time.sleep(0.0005)



if __name__ == '__main__':
    sample = list(gen_sample(range(10000), 0.5, 0.03, 0.05, 5000, 1000))
    EM(sample)

