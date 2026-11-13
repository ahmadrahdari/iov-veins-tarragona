#!/usr/bin/env python3
"""Aggregate the scalar results of the 5G NR (Simu5G) simulations.

usage: parse5g.py <results-dir> [summary.json] [summary.csv]

Metrics per configuration and number of vehicles N (mean over the seeds):
  lat_ms      mean authentication latency (session start -> session key), all sessions
  latA_ms     latency of phase A sessions (full runs of the baseline)
  latB_ms     latency of phase B sessions
  ulA_ms, ulB_ms   delay of the request (M1 / M5) from the vehicle to the fog node
  dlA_ms, dlB_ms   delay of the response (M4 / M6) from the fog node to the vehicle
  plr         loss rate of the over-the-air protocol messages (M1, M4, M5, M6)
  plr_ul, plr_dl   the same for the uplink (M1, M5) and the downlink (M4, M6)
  plr_pooled  loss rate over the messages of all seeds, with its 95 % Wilson interval
              [plr_lo, plr_hi]; lost = number of lost messages in all seeds
  e2e_ms      mean delay of the received over-the-air protocol messages
  succ        fraction of started sessions that completed
  fracB       fraction of started sessions that used phase B
  cloud       messages M2 processed by CS for sessions started in the measurement window
  cloud_rate  cloud divided by the length of the measurement window (msg/s)
  handovers   sessions run with a fog node other than that of the previous session
  hoFracB     fraction of phase B sessions that are handovers between two fog nodes of the
              area (the others are re-keying); hoFracB_entry also counts the first session
              of a vehicle that entered from the map edge
  cam_pdr, cam_ms  delivery ratio and delay of the background CAMs (vehicle -> fog node)
  sinr_ul, sinr_dl, cqi_ul, cqi_dl, bler1_ul, bler1_dl, harq_ul, harq_dl,
  macloss_ul, macloss_dl   radio KPIs (mean over the vehicles and cells)
"""
import glob, re, sys, collections, statistics, json, math

NAN = float('nan')
RADIO = {  # scalar name -> (key, level)
    'rcvdSinrUl:mean': 'sinr_ul', 'rcvdSinrDl:mean': 'sinr_dl',
    'averageCqiUl:mean': 'cqi_ul', 'averageCqiDl:mean': 'cqi_dl',
    'harqErrorRate_1st_Ul:mean': 'bler1_ul', 'harqErrorRate_1st_Dl:mean': 'bler1_dl',
    'harqErrorRateUl:mean': 'harq_ul', 'harqErrorRateDl:mean': 'harq_dl',
    'macPacketLossUl:mean': 'macloss_ul', 'macPacketLossDl:mean': 'macloss_dl',
}


def parse_sca(path):
    d = collections.defaultdict(float)
    radio = collections.defaultdict(list)
    for line in open(path):
        if not line.startswith('scalar '):
            continue
        parts = line.rstrip('\n').split(' ')
        mod, name, val = ' '.join(parts[1:-2]), parts[-2], parts[-1]
        try:
            v = float(val)
        except ValueError:
            continue
        if name.startswith('aka'):
            role = 'cloud' if '.cloud.' in mod else ('fog' if '.fog[' in mod else 'veh')
            d[(role, name)] += v
        elif name in RADIO and not math.isnan(v):
            if '.car[' in mod and '.cellularNic.nr' not in mod and name.startswith(('harq', 'macPacket', 'averageCqi')):
                continue  # idle LTE stack of the dual-stack NIC
            radio[RADIO[name]].append(v)
    return d, radio


def ratio(a, b, scale=1.0):
    return scale * a / b if b else NAN


def metrics(d, radio):
    g = lambda r, n: d[(r, n)]
    sent_ul = sum(g('veh', 'akaSentReq' + p) for p in 'AB')
    recv_ul = sum(g('fog', 'akaRecvReq' + p) for p in 'AB')
    sent_dl = sum(g('fog', 'akaSentResp' + p) for p in 'AB')
    recv_dl = sum(g('veh', 'akaRecvResp' + p) for p in 'AB')
    delay = sum(g('fog', 'akaSumReqDelay' + p) + g('veh', 'akaSumRespDelay' + p) for p in 'AB')
    comp = {p: g('veh', 'akaCompleted' + p) for p in 'AB'}
    lat = {p: g('veh', 'akaSumAuthLatency' + p) for p in 'AB'}
    started = sum(g('veh', 'akaStarted' + p) for p in 'AB')
    m = dict(
        lat_ms=ratio(lat['A'] + lat['B'], comp['A'] + comp['B'], 1e3),
        latA_ms=ratio(lat['A'], comp['A'], 1e3),
        latB_ms=ratio(lat['B'], comp['B'], 1e3),
        ulA_ms=ratio(g('fog', 'akaSumReqDelayA'), g('fog', 'akaRecvReqA'), 1e3),
        ulB_ms=ratio(g('fog', 'akaSumReqDelayB'), g('fog', 'akaRecvReqB'), 1e3),
        dlA_ms=ratio(g('veh', 'akaSumRespDelayA'), g('veh', 'akaRecvRespA'), 1e3),
        dlB_ms=ratio(g('veh', 'akaSumRespDelayB'), g('veh', 'akaRecvRespB'), 1e3),
        plr=1 - ratio(recv_ul + recv_dl, sent_ul + sent_dl),
        plr_ul=1 - ratio(recv_ul, sent_ul),
        plr_dl=1 - ratio(recv_dl, sent_dl),
        e2e_ms=ratio(delay, recv_ul + recv_dl, 1e3),
        succ=ratio(comp['A'] + comp['B'], started),
        succA=ratio(comp['A'], g('veh', 'akaStartedA')),
        succB=ratio(comp['B'], g('veh', 'akaStartedB')),
        fracB=ratio(g('veh', 'akaStartedB'), started),
        fracBc=ratio(comp['B'], comp['A'] + comp['B']),
        sessions=started, startedA=g('veh', 'akaStartedA'), startedB=g('veh', 'akaStartedB'),
        frames=sent_ul + sent_dl,
        cloud=g('cloud', 'akaProcessedWin'),
        cloud_rate=ratio(g('cloud', 'akaProcessedWin'), g('cloud', 'akaWindow')),
        handovers=g('veh', 'akaHandovers'),
        handoversA=g('veh', 'akaHandoversA'), handoversB=g('veh', 'akaHandoversB'),
        entryA=g('veh', 'akaEntryHandoversA'), entryB=g('veh', 'akaEntryHandoversB'),
        hoFracB=ratio(g('veh', 'akaHandoversB'), g('veh', 'akaStartedB')),
        hoFracB_entry=ratio(g('veh', 'akaHandoversB') + g('veh', 'akaEntryHandoversB'), g('veh', 'akaStartedB')),
        edge_entries=g('veh', 'akaEdgeEntry'),
        detached=g('veh', 'akaSkippedDetached'),
        cam_pdr=ratio(g('fog', 'akaCamRecv'), g('veh', 'akaCamSent')),
        cam_ms=ratio(g('fog', 'akaSumCamDelay'), g('fog', 'akaCamRecv'), 1e3),
    )
    for k in sorted(set(RADIO.values())):
        m[k] = statistics.mean(radio[k]) if radio[k] else NAN
    return m


def main():
    res = collections.defaultdict(list)
    for f in sorted(glob.glob(sys.argv[1] + '/*.sca')):
        mm = re.search(r'(\w+)-N(\d+)-r(\d+)\.sca$', f)
        if mm:
            d, radio = parse_sca(f)
            if not d.get(('cloud', 'akaWindow')):
                print(f'skipping {f}: no results (run not finished)', file=sys.stderr)
                continue
            res[(mm.group(1), int(mm.group(2)))].append(metrics(d, radio))
    out = {}
    for (cfg, N), runs in sorted(res.items()):
        clean = lambda k: [r[k] for r in runs if not math.isnan(r[k])]
        agg = {k: (statistics.mean(clean(k)) if clean(k) else NAN) for k in runs[0]}
        for k in ('lat_ms', 'latA_ms', 'latB_ms', 'plr', 'e2e_ms', 'succ', 'cloud_rate', 'fracB'):
            vals = clean(k)
            agg[k + '_sd'] = statistics.stdev(vals) if len(vals) > 1 else 0.0
        agg['runs'] = len(runs)
        # loss pooled over the seeds with a 95 % Wilson interval: only a few protocol messages
        # are lost per run, so the standard deviation of the per-seed rates is not informative
        n = sum(r['frames'] for r in runs)
        k = sum(r['plr'] * r['frames'] for r in runs if not math.isnan(r['plr']))
        p, z = (k / n if n else NAN), 1.96
        if n:
            c = (p + z * z / (2 * n)) / (1 + z * z / n)
            h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
            agg.update(plr_pooled=p, plr_lo=c - h, plr_hi=c + h, lost=k)
        out[f'{cfg}-{N}'] = agg
        print(f"{cfg:9s} N={N:3d} runs={len(runs)} lat={agg['lat_ms']:6.2f} (A {agg['latA_ms']:6.2f}, B {agg['latB_ms']:6.2f}) ms  "
              f"UL {agg['ulA_ms']:5.2f}/{agg['ulB_ms']:5.2f} DL {agg['dlA_ms']:5.2f}/{agg['dlB_ms']:5.2f} ms  "
              f"PLR={agg['plr']*100:5.2f}%  succ={agg['succ']*100:6.2f}%  B={agg['fracB']*100:5.1f}%  "
              f"sess={agg['sessions']:.0f} cloud={agg['cloud']:.0f} ({agg['cloud_rate']:.3f}/s)  "
              f"CAM {agg['cam_pdr']*100:5.2f}% {agg['cam_ms']:5.2f} ms  SINR UL {agg['sinr_ul']:4.1f} dB")
    if len(sys.argv) > 2:
        json.dump(out, open(sys.argv[2], 'w'), indent=1)
    if len(sys.argv) > 3:
        keys = [k for k in next(iter(out.values()))] if out else []
        with open(sys.argv[3], 'w') as f:
            f.write('config,N,' + ','.join(keys) + '\n')
            for name, agg in out.items():
                cfg, N = name.rsplit('-', 1)
                f.write(f'{cfg},{N},' + ','.join(f'{agg[k]:.6g}' for k in keys) + '\n')


if __name__ == '__main__':
    main()
