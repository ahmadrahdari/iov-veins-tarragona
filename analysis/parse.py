#!/usr/bin/env python3
"""Aggregate Veins scalar results of the authentication protocols.

Metrics per configuration and number of vehicles N (mean over seeds):
  plr      packet loss rate of the over-the-air protocol frames
           (M1, M4 for phase A / full runs; M5, M6 for phase B)
  e2e_ms   mean end-to-end delay of the received protocol frames
  lat_ms   mean authentication latency (session start -> session key)
  latA_ms, latB_ms  latency of phase A and phase B sessions
  succ     fraction of started sessions that completed
  fracB    fraction of sessions that used phase B
"""
import glob, re, sys, collections, statistics, json

def parse_sca(path):
    d = collections.defaultdict(float)
    for line in open(path):
        if not line.startswith('scalar '):
            continue
        parts = line.split()
        mod, name, val = parts[1], parts[2], parts[3]
        if not name.startswith('aka'):
            continue
        try:
            v = float(val)
        except ValueError:
            continue
        role = 'cloud' if '.cloud' in mod else ('rsu' if '.rsu[' in mod else 'veh')
        d[(role, name)] += v
    return d

def metrics(d):
    g = lambda r, n: d[(r, n)]
    sent = sum(g('veh', 'akaSentReq' + p) + g('rsu', 'akaSentResp' + p) for p in 'AB')
    recv = sum(g('rsu', 'akaRecvReq' + p) + g('veh', 'akaRecvResp' + p) for p in 'AB')
    delay = sum(g('rsu', 'akaSumReqDelay' + p) + g('veh', 'akaSumRespDelay' + p) for p in 'AB')
    comp = {p: g('veh', 'akaCompleted' + p) for p in 'AB'}
    lat = {p: g('veh', 'akaSumAuthLatency' + p) for p in 'AB'}
    started = sum(g('veh', 'akaStarted' + p) for p in 'AB')
    m = dict(
        plr=1 - recv / sent if sent else float('nan'),
        e2e_ms=1e3 * delay / recv if recv else float('nan'),
        lat_ms=1e3 * (lat['A'] + lat['B']) / (comp['A'] + comp['B']) if comp['A'] + comp['B'] else float('nan'),
        latA_ms=1e3 * lat['A'] / comp['A'] if comp['A'] else float('nan'),
        latB_ms=1e3 * lat['B'] / comp['B'] if comp['B'] else float('nan'),
        succ=(comp['A'] + comp['B']) / started if started else float('nan'),
        fracB=g('veh', 'akaStartedB') / started if started else float('nan'),
        sessions=started, frames=sent, handovers=g('veh', 'akaHandovers'),
        cloud=g('cloud', 'akaProcessed'),
    )
    return m

res = collections.defaultdict(list)
for f in sorted(glob.glob(sys.argv[1] + '/*.sca')):
    mm = re.search(r'(\w+)-N(\d+)-r(\d+)\.sca$', f)
    if mm:
        res[(mm.group(1), int(mm.group(2)))].append(metrics(parse_sca(f)))
out = {}
for (cfg, N), runs in sorted(res.items()):
    keys = runs[0].keys()
    agg = {k: statistics.mean(r[k] for r in runs) for k in keys}
    for k in ('plr', 'e2e_ms', 'lat_ms'):
        agg[k + '_sd'] = statistics.stdev(r[k] for r in runs) if len(runs) > 1 else 0.0
    agg['runs'] = len(runs)
    out[f'{cfg}-{N}'] = agg
    print(f"{cfg:9s} N={N:3d} runs={len(runs)} PLR={agg['plr']*100:6.3f}%  E2E={agg['e2e_ms']:6.3f} ms  "
          f"lat={agg['lat_ms']:6.2f} (A {agg['latA_ms']:6.2f}, B {agg['latB_ms']:6.2f}) ms  succ={agg['succ']*100:6.2f}%  "
          f"B={agg['fracB']*100:5.1f}%  sess={agg['sessions']:.0f} cloud={agg['cloud']:.0f}")
if len(sys.argv) > 2:
    json.dump(out, open(sys.argv[2], 'w'), indent=1)
