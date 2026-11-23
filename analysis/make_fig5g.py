#!/usr/bin/env python3
"""Draw the four result panels of the 5G NR simulation from summary5g.json.

Panel (a) shows the loss rate pooled over the seeds with its 95 % Wilson interval, the other
panels the mean over the seeds with the standard deviation across seeds.

usage: make_fig5g.py summary5g.json out.png
"""
import json, sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

S = json.load(open(sys.argv[1]))
Ns = [20, 40, 60, 80, 100, 120]
CFGS = [('Proposed', 'FogRoam (A+B)', '#2A78D6', 'o', '-'),
        ('ProposedA', 'FogRoam (A only)', '#EB6834', 's', '--'),
        ('Baseline', 'Chen et al.', '#1BAF7A', '^', ':')]
PANELS = [('plr_pooled', None, 100.0, 'Packet loss rate (%)', '(a) loss of the protocol messages'),
          ('e2e_ms', 'e2e_ms_ci', 1.0, 'End-to-end delay (ms)', '(b) delay of the protocol messages'),
          ('lat_ms', 'lat_ms_ci', 1.0, 'Authentication latency (ms)', '(c) authentication latency'),
          ('cloud_rate', 'cloud_rate_ci', 1.0, 'CS load (msg/s)', '(d) messages processed by CS')]

plt.rcParams.update({'font.size': 9, 'axes.spines.top': False, 'axes.spines.right': False})
fig, axes = plt.subplots(1, 4, figsize=(13.5, 3.4))
for ax, (key, sd, scale, ylabel, title) in zip(axes, PANELS):
    for i, (cfg, name, col, mark, ls) in enumerate(CFGS):
        xs = [n for n in Ns if f'{cfg}-{n}' in S]
        if not xs:
            continue
        ys = [S[f'{cfg}-{n}'][key] * scale for n in xs]
        if sd is None:   # pooled loss rate with its 95 % Wilson interval
            es = [[(S[f'{cfg}-{n}'][key] - S[f'{cfg}-{n}']['plr_lo']) * scale for n in xs],
                  [(S[f'{cfg}-{n}']['plr_hi'] - S[f'{cfg}-{n}'][key]) * scale for n in xs]]
        else:
            es = [S[f'{cfg}-{n}'].get(sd, 0.0) * scale for n in xs]
        line = ls
        if sd is None:   # estimates of a rare event: markers only, slightly offset so that the intervals do not overlap
            xs = [x + (i - 1) * 2.5 for x in xs]
            line = 'none'
        ax.errorbar(xs, ys, yerr=es, color=col, marker=mark, ls=line, lw=2, ms=6, capsize=2.5,
                    elinewidth=0.8, markeredgecolor='white', markeredgewidth=0.8, label=name)
    ax.set_xlabel('Number of vehicles')
    ax.set_ylabel(ylabel)
    # panel label below the axis, as in the paper (no titles above the panels)
    ax.text(0.5, -0.30, title.split(' ')[0], transform=ax.transAxes, ha='center', va='top', fontsize=9)
    ax.set_xticks(Ns)
    ax.set_xlim(10, 130)
    ax.set_ylim(bottom=0)
    if key == 'plr_pooled':
        ax.set_ylim(0, 1.0)
    ax.grid(axis='y', color='#000000', alpha=0.1, lw=0.6)
    for s in ('left', 'bottom'):
        ax.spines[s].set_color('#777777')
    ax.tick_params(colors='#555555')
handles, labels = axes[2].get_legend_handles_labels()
fig.legend(handles, labels, loc='lower center', ncol=3, frameon=False, bbox_to_anchor=(0.5, 0.0))
fig.subplots_adjust(left=0.05, right=0.99, top=0.97, bottom=0.33, wspace=0.32)
fig.savefig(sys.argv[2], dpi=200)
print('written', sys.argv[2])
