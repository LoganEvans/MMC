#!/usr/bin/env bash

wget http://skuld.cs.umass.edu/traces/storage/Financial1.spc.bz2
bzip2 -d Financial1.spc.bz2

wget http://skuld.cs.umass.edu/traces/storage/Financial2.spc.bz2
bzip2 -d Financial2.spc.bz2

wget http://skuld.cs.umass.edu/traces/storage/WebSearch1.spc.bz2
bzip2 -d WebSearch1.spc.bz2

wget http://skuld.cs.umass.edu/traces/storage/WebSearch2.spc.bz2
bzip2 -d WebSearch2.spc.bz2

wget http://skuld.cs.umass.edu/traces/storage/WebSearch3.spc.bz2
bzip2 -d WebSearch3.spc.bz2

wget http://skuld.cs.umass.edu/traces/cpumem/reduced-rept-acroread.100000000.bz2
bzip2 -d reduced-rept-acroread.100000000.bz2
mv reduced-rept-acroread.100000000 acroread.kvmtrace

wget http://skuld.cs.umass.edu/traces/cpumem/reduced-rept-cc1.100000000.bz2
bzip2 -d reduced-rept-cc1.100000000.bz2
mv reduced-rept-cc1.100000000 cc1.kvmtrace

