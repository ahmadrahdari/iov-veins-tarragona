#!/usr/bin/env python3
"""Markdown tables of the README (section Results) from analysis/summary5g.json.

usage: readme5g.py summary5g.json
"""
import json, sys
S = json.load(open(sys.argv[1]))
Ns = [20, 40, 60, 80, 100, 120]
NAME = {'Proposed': 'FogRoam (A+B)', 'ProposedA': 'FogRoam (A only)', 'Baseline': 'Chen et al.',
        'ProposedHO': 'FogRoam (A+B)', 'BaselineHO': 'Chen et al.'}
f = lambda x, d=2: '–' if x != x else f'{x:.{d}f}'
print('| N | Scheme | Latency (ms) | Phase A (ms) | Phase B (ms) | Phase B share | Loss (95 % interval) | Success | CS load (msg/s) |')
print('|---|--------|-------------:|-------------:|-------------:|--------------:|-----:|--------:|----------------:|')
for n in Ns:
    for c in ('Proposed', 'ProposedA', 'Baseline'):
        s = S[f'{c}-{n}']
        print(f"| {n} | {NAME[c]} | {s['lat_ms']:.2f} ± {s['lat_ms_ci']:.2f} | {f(s['latA_ms'])} | {f(s['latB_ms'])} | "
              f"{100*s['fracB']:.1f} % | {100*s['plr_pooled']:.2f} % ({100*s['plr_lo']:.2f}–{100*s['plr_hi']:.2f}) | "
              f"{100*s['succ']:.1f} % | {s['cloud_rate']:.3f} |")
red = [1 - S[f'Proposed-{n}']['lat_ms'] / S[f'Baseline-{n}']['lat_ms'] for n in Ns]
cs = [1 - S[f'Proposed-{n}']['cloud_rate'] / S[f'Baseline-{n}']['cloud_rate'] for n in Ns]
print(f"\nCompared with the baseline, FogRoam reduces the mean authentication latency by {100*min(red):.1f}–{100*max(red):.1f} % "
      f"(mean {100*sum(red)/len(red):.1f} %) and the load of the cloud server by {100*min(cs):.1f}–{100*max(cs):.1f} % "
      f"(mean {100*sum(cs)/len(cs):.1f} %).\n")
P = [S[f'Proposed-{n}'] for n in Ns]
avg = lambda k: sum(p[k] for p in P) / len(P)
print(f"Radio KPIs averaged over all runs of `Proposed`: uplink SINR {avg('sinr_ul'):.1f} dB, downlink SINR {avg('sinr_dl'):.1f} dB, "
      f"uplink CQI {avg('cqi_ul'):.1f}, downlink CQI {avg('cqi_dl'):.1f}, first-transmission block error rate "
      f"{100*avg('bler1_ul'):.1f} % (uplink) and {100*avg('bler1_dl'):.1f} % (downlink), residual MAC loss after HARQ "
      f"{100*avg('macloss_ul'):.2f} % (uplink) and {100*avg('macloss_dl'):.2f} % (downlink), CAM delivery ratio "
      f"{100*avg('cam_pdr'):.2f} % with a mean delay of {avg('cam_ms'):.2f} ms.\n")
print('Handover-triggered sessions (`ProposedHO`, `BaselineHO`; a session starts when the vehicle joins, when its serving '
      'gNB changes, and when its last phase A is older than 300 s):\n')
print('| N | Scheme | Latency (ms) | After handover (ms) | Phase B share | Loss | Success | CS load (msg/s) |')
print('|---|--------|-------------:|--------------------:|--------------:|-----:|--------:|----------------:|')
for n in Ns:
    for c in ('ProposedHO', 'BaselineHO'):
        s = S[f'{c}-{n}']
        ho = s['latBho_ms'] if c == 'ProposedHO' else s['latAho_ms']
        hoci = s['latBho_ms_ci'] if c == 'ProposedHO' else s['latAho_ms_ci']
        print(f"| {n} | {NAME[c]} | {s['lat_ms']:.2f} ± {s['lat_ms_ci']:.2f} | {ho:.2f} ± {hoci:.2f} | {100*s['fracB']:.1f} % | "
              f"{100*s['plr_pooled']:.2f} % | {100*s['succ']:.1f} % | {s['cloud_rate']:.3f} |")
print('\nPhase-A re-validation interval with handover-triggered sessions, 60 vehicles:\n')
print('| Interval | Phase B share | Latency (ms) | CS load (msg/s) |')
print('|---------:|--------------:|-------------:|----------------:|')
for c, iv in (('ProposedHO150', 150), ('ProposedHO', 300), ('ProposedHO600', 600)):
    s = S[f'{c}-60']
    print(f"| {iv} s | {100*s['fracB']:.1f} % | {s['lat_ms']:.2f} | {s['cloud_rate']:.3f} |")
