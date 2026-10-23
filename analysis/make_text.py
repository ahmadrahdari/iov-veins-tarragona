#!/usr/bin/env python3
"""Print the key numbers used in the results paragraph of the paper."""
import json, sys
S = json.load(open(sys.argv[1]))
Ns = [20, 40, 60, 80, 100, 120]
def g(c, n, k): return S[f'{c}-{n}'][k]
for k in ('plr', 'e2e_ms', 'lat_ms', 'latA_ms', 'latB_ms', 'succ', 'fracB', 'cloud'):
    for c in ('Proposed', 'ProposedA', 'Baseline'):
        vals = [g(c, n, k) for n in Ns if f'{c}-{n}' in S]
        print(f'{k:8s} {c:9s} ' + ' '.join(f'{v:9.4f}' for v in vals))
P, A, C = 'Proposed', 'ProposedA', 'Baseline'
n0, n1 = Ns[0], Ns[-1]
print('PLR range proposed %.2f-%.2f, chen %.2f-%.2f, A-only %.2f-%.2f' % (100*g(P,n0,'plr'),100*g(P,n1,'plr'),100*g(C,n0,'plr'),100*g(C,n1,'plr'),100*g(A,n0,'plr'),100*g(A,n1,'plr')))
print('E2E range proposed %.3f-%.3f, chen %.3f-%.3f, A-only %.3f-%.3f' % (g(P,n0,'e2e_ms'),g(P,n1,'e2e_ms'),g(C,n0,'e2e_ms'),g(C,n1,'e2e_ms'),g(A,n0,'e2e_ms'),g(A,n1,'e2e_ms')))
print('lat proposed %.1f-%.1f (A %.1f-%.1f, B %.1f-%.1f), chen %.1f-%.1f, A-only %.1f-%.1f' % (g(P,n0,'lat_ms'),g(P,n1,'lat_ms'),g(P,n0,'latA_ms'),g(P,n1,'latA_ms'),g(P,n0,'latB_ms'),g(P,n1,'latB_ms'),g(C,n0,'lat_ms'),g(C,n1,'lat_ms'),g(A,n0,'lat_ms'),g(A,n1,'lat_ms')))
red = [1 - g(P,n,'cloud')/g(C,n,'cloud') for n in Ns]
print('cloud load reduction vs chen: %.1f%%-%.1f%%' % (100*min(red), 100*max(red)))
print('lat reduction vs chen: ' + ' '.join('%.1f%%' % (100*(1-g(P,n,'lat_ms')/g(C,n,'lat_ms'))) for n in Ns))
print('fracB: ' + ' '.join('%.1f%%' % (100*g(P,n,'fracB')) for n in Ns))
print('succ P/C/A @120: %.2f %.2f %.2f' % (100*g(P,n1,'succ'), 100*g(C,n1,'succ'), 100*g(A,n1,'succ')))
