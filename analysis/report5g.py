#!/usr/bin/env python3
"""Numbers quoted in the paper, from analysis/summary5g.json.

usage: report5g.py summary5g.json
"""
import json, sys, math
S = json.load(open(sys.argv[1]))
Ns = [20, 40, 60, 80, 100, 120]
g = lambda c, n, k: S.get(f'{c}-{n}', {}).get(k, float('nan'))
rng = lambda v: f'{min(v):.1f}-{max(v):.1f}'
pct = lambda v: f'{100*min(v):.1f}-{100*max(v):.1f} % (mean {100*sum(v)/len(v):.1f} %)'
have = lambda c: all(f'{c}-{n}' in S for n in Ns)
if have('Proposed') and have('Baseline'):
    print('runs per point:', {c: [g(c, n, 'runs') for n in Ns] for c in ('Proposed', 'ProposedA', 'Baseline') if have(c)})
    for n in Ns:
        print(f"N={n:3d} lat P {g('Proposed',n,'lat_ms'):6.2f}+-{g('Proposed',n,'lat_ms_ci'):.2f}  A {g('Proposed',n,'latA_ms'):6.2f}  B {g('Proposed',n,'latB_ms'):6.2f}"
              f"  Bho {g('Proposed',n,'latBho_ms'):6.2f}  Aonly {g('ProposedA',n,'lat_ms'):6.2f}  Chen {g('Baseline',n,'lat_ms'):6.2f}+-{g('Baseline',n,'lat_ms_ci'):.2f}"
              f"  Chen_ho {g('Baseline',n,'latAho_ms'):6.2f}  fracB {g('Proposed',n,'fracB'):.3f} hoFracB {g('Proposed',n,'hoFracB'):.3f}"
              f"  cloud P {g('Proposed',n,'cloud_rate'):.3f} C {g('Baseline',n,'cloud_rate'):.3f}  e2e {g('Proposed',n,'e2e_ms'):.2f}/{g('Baseline',n,'e2e_ms'):.2f}"
              f"  UL {g('Proposed',n,'ulA_ms'):.2f}/{g('Proposed',n,'ulB_ms'):.2f} DL {g('Proposed',n,'dlA_ms'):.2f}  plr {100*g('Proposed',n,'plr_pooled'):.2f}/{100*g('ProposedA',n,'plr_pooled'):.2f}/{100*g('Baseline',n,'plr_pooled'):.2f} %"
              f"  succ {100*min(g(c,n,'succ') for c in ('Proposed','ProposedA','Baseline') if have(c)):.2f}")
    red = [1 - g('Proposed', n, 'lat_ms') / g('Baseline', n, 'lat_ms') for n in Ns]
    cs = [1 - g('Proposed', n, 'cloud_rate') / g('Baseline', n, 'cloud_rate') for n in Ns]
    print('latency reduction', pct(red)); print('cloud reduction', pct(cs))
    print('latency FogRoam', rng([g('Proposed', n, 'lat_ms') for n in Ns]), 'Chen', rng([g('Baseline', n, 'lat_ms') for n in Ns]),
          'phase A', rng([g('Proposed', n, 'latA_ms') for n in Ns]), 'phase B', rng([g('Proposed', n, 'latB_ms') for n in Ns]),
          'phase B after handover', rng([g('Proposed', n, 'latBho_ms') for n in Ns]))
    print('fracB', pct([g('Proposed', n, 'fracB') for n in Ns]), 'hoFracB', pct([g('Proposed', n, 'hoFracB') for n in Ns]))
    print('e2e all', rng([g(c, n, 'e2e_ms') for c in ('Proposed', 'ProposedA', 'Baseline') if have(c) for n in Ns]),
          'UL', rng([g(c, n, k) for c in ('Proposed', 'ProposedA', 'Baseline') if have(c) for n in Ns for k in ('ulA_ms', 'ulB_ms') if not math.isnan(g(c, n, k))]),
          'DL', rng([g(c, n, k) for c in ('Proposed', 'ProposedA', 'Baseline') if have(c) for n in Ns for k in ('dlA_ms', 'dlB_ms') if not math.isnan(g(c, n, k))]))
    print('plr pooled', rng([100 * g(c, n, 'plr_pooled') for c in ('Proposed', 'ProposedA', 'Baseline') if have(c) for n in Ns]), '%, max lost/run',
          max(g(c, n, 'lost') / g(c, n, 'runs') for c in ('Proposed', 'ProposedA', 'Baseline') if have(c) for n in Ns))
if have('ProposedHO') and have('BaselineHO'):
    print('--- handover-triggered sessions')
    for n in Ns:
        print(f"N={n:3d} runs {g('ProposedHO',n,'runs')}  lat P {g('ProposedHO',n,'lat_ms'):6.2f}  Bho {g('ProposedHO',n,'latBho_ms'):6.2f}+-{g('ProposedHO',n,'latBho_ms_ci'):.2f}"
              f"  Chen_ho {g('BaselineHO',n,'latAho_ms'):6.2f}+-{g('BaselineHO',n,'latAho_ms_ci'):.2f}  Chen all {g('BaselineHO',n,'lat_ms'):6.2f}  fracB {g('ProposedHO',n,'fracB'):.3f}"
              f"  cloud P {g('ProposedHO',n,'cloud_rate'):.3f} C {g('BaselineHO',n,'cloud_rate'):.3f}  sessions/veh/min {g('ProposedHO',n,'sessions')/n/((898-300)/60):.2f}")
    print('cloud reduction HO', pct([1 - g('ProposedHO', n, 'cloud_rate') / g('BaselineHO', n, 'cloud_rate') for n in Ns]))
    print('latency reduction HO (all sessions)', pct([1 - g('ProposedHO', n, 'lat_ms') / g('BaselineHO', n, 'lat_ms') for n in Ns]))
    print('handover latency reduction', pct([1 - g('ProposedHO', n, 'latBho_ms') / g('BaselineHO', n, 'latAho_ms') for n in Ns]))
for c in ('ProposedHO150', 'ProposedHO', 'ProposedHO600'):
    if f'{c}-60' in S:
        print(f"{c:14s} N=60 runs {g(c,60,'runs')} fracB {g(c,60,'fracB'):.3f}+-{g(c,60,'fracB_ci'):.3f} lat {g(c,60,'lat_ms'):.2f} cloud {g(c,60,'cloud_rate'):.3f}")
