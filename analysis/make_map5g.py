#!/usr/bin/env python3
"""Figure of the Tarragona scenario of the 5G NR simulation.

(a) road network and building footprints processed by SUMO, with the four gNB sites and
    their co-located fog nodes;
(b) serving cells of the vehicles at one instant, recorded by the simulation itself
    (run with "--**.app[*].snapshotTime=600s", scalars akaSnapX, akaSnapY, akaSnapFog).

The panels have no titles; the sub-captions are set in LaTeX below the figure.

usage: make_map5g.py <net.xml> <poly.xml> <snapshot.sca> <out.png> [dpi]
"""
import sys, re, collections, xml.etree.ElementTree as ET
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection, PolyCollection
from matplotlib.lines import Line2D

NET, POLY, SCA, OUT = sys.argv[1:5]
DPI = int(sys.argv[5]) if len(sys.argv) > 5 else 300

root = ET.parse(NET).getroot()
xmin, ymin, xmax, ymax = map(float, root.find('location').get('convBoundary').split(','))
lanes = [[tuple(map(float, p.split(','))) for p in ln.get('shape').split()]
         for e in root.iter('edge') if e.get('function') != 'internal' for ln in e.iter('lane')]
buildings = []
for p in ET.parse(POLY).getroot().iter('poly'):
    pts = [tuple(map(float, q.split(','))) for q in p.get('shape').split()]
    if len(pts) >= 3:
        buildings.append(np.array(pts))

# OMNeT++ -> SUMO coordinates (Veins margin of 25 m, y axis flipped)
to_sumo = lambda x, y: (x - 25 + xmin, ymax + 25 - y)
gnb_omnet = [(1749, 997), (2675, 1356), (975, 1356), (2098, 717)]   # gnb[0..3] in omnetpp.ini
gnb = np.array([to_sumo(x, y) for x, y in gnb_omnet])

snap = collections.defaultdict(dict)
for line in open(SCA):
    m = re.match(r'scalar (\S+) (akaSnap\w+) (\S+)', line)
    if m:
        snap[m.group(1)][m.group(2)] = float(m.group(3))
veh = [(to_sumo(v['akaSnapX'], v['akaSnapY']), int(v['akaSnapFog'])) for v in snap.values()]
print(len(veh), 'vehicles;', collections.Counter(c for _, c in veh))

COL = ['#2A78D6', '#EB6834', '#1BAF7A', '#9B59B6']   # validated categorical palette
plt.rcParams.update({'font.family': 'serif', 'font.size': 8, 'mathtext.fontset': 'cm'})
fig, axs = plt.subplots(1, 2, figsize=(7.16, 2.12), constrained_layout=True)
for k, ax in enumerate(axs):
    ax.add_collection(PolyCollection(buildings, facecolor='#d9d6cf', edgecolor='#bdb9b0', linewidth=0.2, rasterized=True))
    ax.add_collection(LineCollection(lanes, colors='#6f6f6f' if k == 0 else '#a5a5a5', linewidths=0.45, rasterized=True))
    ax.set_xlim(xmin - 20, xmax + 20)
    ax.set_ylim(ymin - 20, ymax + 20)
    ax.set_aspect('equal')
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_color('#999999')
        s.set_linewidth(0.6)

# (a) network, gNB sites and fog nodes
ax = axs[0]
ax.scatter(gnb[:, 0], gnb[:, 1], marker='^', s=46, c='#2A78D6', edgecolors='black', linewidths=0.6, zorder=5)
for j, (x, y) in enumerate(gnb):
    ax.annotate(f'$\\mathsf{{F}}_{j + 1}$ / gNB$_{j + 1}$', (x, y), xytext=(5, 5), textcoords='offset points', fontsize=7.5,
                bbox=dict(boxstyle='round,pad=0.15', fc='white', ec='none', alpha=0.85), zorder=6)
ax.plot([xmax - 560, xmax - 60], [ymin + 60, ymin + 60], color='black', lw=1.2)
ax.text(xmax - 310, ymin + 95, '500 m', ha='center', fontsize=7)

# (b) serving cells
ax = axs[1]
for c in range(len(gnb)):
    pts = [p for p, f in veh if f == c]
    if pts:
        ax.add_collection(LineCollection([[p, gnb[c]] for p in pts], colors=COL[c], linewidths=0.45, alpha=0.55, zorder=3))
        a = np.array(pts)
        ax.scatter(a[:, 0], a[:, 1], s=8, c=COL[c], edgecolors='white', linewidths=0.3, zorder=5)
    ax.scatter([gnb[c, 0]], [gnb[c, 1]], marker='^', s=52, c=COL[c], edgecolors='black', linewidths=0.6, zorder=6)
    ax.annotate(f'gNB$_{c + 1}$', gnb[c], xytext=(5, -9), textcoords='offset points', fontsize=7,
                bbox=dict(boxstyle='round,pad=0.12', fc='white', ec='none', alpha=0.8), zorder=7)
lost = [p for p, f in veh if f < 0]
if lost:
    a = np.array(lost)
    ax.scatter(a[:, 0], a[:, 1], s=8, c='#222222', zorder=5)
h = [Line2D([0], [0], marker='^', ls='', mfc='#bbbbbb', mec='black', ms=6, label='gNB with fog node'),
     Line2D([0], [0], marker='o', ls='', mfc='#777777', mec='white', ms=4, label='vehicle (NR UE)'),
     Line2D([0], [0], color='#777777', lw=1.0, label='link to serving gNB')]
ax.legend(handles=h, loc='upper right', fontsize=6, frameon=True, framealpha=0.9, edgecolor='#cccccc', handlelength=1.2, borderaxespad=0.25, borderpad=0.3, labelspacing=0.25)
fig.savefig(OUT, dpi=DPI)
print('saved', OUT)
