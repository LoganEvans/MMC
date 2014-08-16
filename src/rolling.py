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
import collections
from scipy import stats
import time

def estimate_z(tau, theta, idx):
    def func(i):
        return tau[i] * theta[i] * (1 - theta[i])**idx
    return func(0) / (func(0) + func(1))

def generate(tau, theta):
    f = [stats.geom(theta[0]), stats.geom(theta[1])]
    while True:
        if np.random.uniform(0, 1) < tau[0]:
            dist = 0
        else:
            dist = 1
        yield f[dist].rvs(1)[0]

def roll(n, tau, theta):
    trace = collections.deque()
    gen = generate(tau, theta)
    tau_acc = [0.0, 0.0]
    theta_acc = [0.0, 0.0]

    def tau_hat():
        return [tau_acc[0] / n, tau_acc[1] / n]
    def theta_hat():
        return [(n * tau_hat()[0]) / theta_acc[0],
                (n * tau_hat()[1]) / theta_acc[1]]

    j = 0
    while True:
        j += 1
        X = next(gen)
        if j < n:
            Z = estimate_z(tau, theta, X)
        else:
            Z = estimate_z(tau_hat(), theta_hat(), X)
        trace.append((X, Z))
        tau_acc[0] += Z
        tau_acc[1] += 1 - Z
        theta_acc[0] += X * Z
        theta_acc[1] += X * (1 - Z)
        if j >= n:
            discard_X, discard_Z = trace.popleft()
            tau_acc[0] -= discard_Z
            tau_acc[1] -= 1 - discard_Z
            theta_acc[0] -= discard_X * discard_Z
            theta_acc[1] -= discard_X * (1 - discard_Z)
        if j % 10000 == 0:
            print "j:", j
            print "tau:", tau_hat()
            print "theta_hat:", theta_hat()
            print "theta_acc:", theta_acc


if __name__ == '__main__':
    roll(3000, [0.3, 0.7], [0.1, 0.01])

