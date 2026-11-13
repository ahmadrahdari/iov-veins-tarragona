#!/usr/bin/env python3
"""Quick percentile statistics of the diagnostic vectors in a .vec file."""
import sys, collections
ids={}; data=collections.defaultdict(list)
for line in open(sys.argv[1]):
    p=line.split()
    if not p: continue
    if p[0]=='vector': ids[p[1]]=p[3]
    elif p[0] in ids:
        data[ids[p[0]]].append(float(p[3]))
for name,v in sorted(data.items()):
    v.sort(); n=len(v); q=lambda f: 1e3*v[min(n-1,int(f*n))]
    print(f"{name:14s} n={n:6d}  min={q(0):7.2f}  p50={q(.5):7.2f}  p90={q(.9):7.2f}  p99={q(.99):8.2f}  max={1e3*v[-1]:9.2f}  mean={1e3*sum(v)/n:7.2f} ms")
