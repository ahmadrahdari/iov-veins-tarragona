#!/usr/bin/env python3
"""Figure of the Tarragona scenario: (a) road network and buildings processed by
SUMO with the fog nodes/RSUs, (b) snapshot of the V2I/V2V simulation.

Links in (b) are drawn when the received power predicted by the propagation
models configured in Veins (free-space path loss with exponent 2 and building
shadowing of 9 dB per wall and 0.4 dB per metre) exceeds the -93 dBm needed for
6 Mbps on a -98 dBm noise floor.
"""
import sys, math, xml.etree.ElementTree as ET
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.path import Path
from matplotlib.collections import LineCollection, PolyCollection

NET, POLY, FCD, OUT = sys.argv[1:5]
T_SNAP = float(sys.argv[5]) if len(sys.argv) > 5 else 60.0

# ---------------- network ----------------
root = ET.parse(NET).getroot()
loc = root.find('location').get('convBoundary').split(',')
xmin, ymin, xmax, ymax = map(float, loc)
lanes = []
for e in root.iter('edge'):
    if e.get('function') == 'internal':
        continue
    for ln in e.iter('lane'):
        pts = [tuple(map(float, p.split(','))) for p in ln.get('shape').split()]
        lanes.append(pts)
buildings = []
for p in ET.parse(POLY).getroot().iter('poly'):
    pts = [tuple(map(float, q.split(','))) for q in p.get('shape').split()]
    if len(pts) >= 3:
        buildings.append(np.array(pts))

# RSU positions: OMNeT++ -> SUMO coordinates (Veins margin of 25 m, y axis flipped)
rsu_omnet = [(1749, 997), (2675, 1356), (975, 1356), (2098, 717)]
rsu_names = ['$\\mathsf{F}_1$', '$\\mathsf{F}_2$', '$\\mathsf{F}_3$', '$\\mathsf{F}_4$']
rsu = np.array([(x - 25 + xmin, ymax + 25 - y) for x, y in rsu_omnet])

# ---------------- vehicles at T_SNAP ----------------
veh = []
for ev, el in ET.iterparse(FCD, events=('start',)):
    if el.tag == 'timestep':
        t = float(el.get('time'))
        if t > T_SNAP + 1e-6:
            break
        cur = (abs(t - T_SNAP) < 1e-6)
    elif el.tag == 'vehicle' and cur:
        veh.append((float(el.get('x')), float(el.get('y'))))
veh = np.array(veh)

# ---------------- propagation ----------------
segs = []   # building walls
paths = []
bbox = []
for b in buildings:
    cl = np.vstack([b, b[:1]])
    for k in range(len(cl) - 1):
        segs.append((cl[k][0], cl[k][1], cl[k + 1][0], cl[k + 1][1]))
    paths.append(Path(cl))
    bbox.append((b[:, 0].min(), b[:, 1].min(), b[:, 0].max(), b[:, 1].max()))
segs = np.array(segs)
bbox = np.array(bbox)
lam = 3e8 / 5.89e9

def walls_and_inside(p, q):
    # number of walls crossed by segment pq and metres travelled inside buildings
    x1, y1, x2, y2 = segs.T
    d1x, d1y = q[0] - p[0], q[1] - p[1]
    d2x, d2y = x2 - x1, y2 - y1
    den = d1x * d2y - d1y * d2x
    with np.errstate(divide='ignore', invalid='ignore'):
        t = ((x1 - p[0]) * d2y - (y1 - p[1]) * d2x) / den
        u = ((x1 - p[0]) * d1y - (y1 - p[1]) * d1x) / den
    walls = int(np.sum((den != 0) & (t > 0) & (t < 1) & (u >= 0) & (u <= 1)))
    if walls == 0:
        return 0, 0.0
    L = math.hypot(d1x, d1y)
    n = max(2, int(L / 2.0))
    pts = np.column_stack([np.linspace(p[0], q[0], n), np.linspace(p[1], q[1], n)])
    lo = np.minimum(p, q); hi = np.maximum(p, q)
    cand = np.where((bbox[:, 2] >= lo[0]) & (bbox[:, 0] <= hi[0]) & (bbox[:, 3] >= lo[1]) & (bbox[:, 1] <= hi[1]))[0]
    inside = np.zeros(n, bool)
    for c in cand:
        inside |= paths[c].contains_points(pts)
    return walls, inside.mean() * L

def rx_dbm(p, q, h_tx=1.895, h_rx=1.895):
    d = max(1.0, math.dist(p, q))
    d3 = math.hypot(d, h_tx - h_rx)
    loss = 20 * math.log10(4 * math.pi * d3 / lam)
    w, m = walls_and_inside(p, q)
    return 13.0 - loss - 9.0 * w - 0.4 * m

THR = -93.0
v2i, v2v = [], []
for v in veh:
    for r in rsu:
        if math.dist(v, r) < 1200 and rx_dbm(v, r, 1.895, 6.0) >= THR:
            v2i.append((v, r))
for a in range(len(veh)):
    for b in range(a + 1, len(veh)):
        if math.dist(veh[a], veh[b]) < 600 and rx_dbm(veh[a], veh[b]) >= THR:
            v2v.append((veh[a], veh[b]))
print(f'{len(veh)} vehicles, {len(v2i)} V2I links, {len(v2v)} V2V links')

# ---------------- figure ----------------
cA, cB, cC = '#2A78D6', '#EB6834', '#1BAF7A'
plt.rcParams.update({'font.family': 'serif', 'font.size': 8, 'mathtext.fontset': 'cm'})
fig, axs = plt.subplots(1, 2, figsize=(7.16, 2.3), constrained_layout=True)
for k, ax in enumerate(axs):
    ax.add_collection(PolyCollection(buildings, facecolor='#d9d6cf', edgecolor='#bdb9b0', linewidth=0.2, rasterized=True))
    ax.add_collection(LineCollection(lanes, colors='#6f6f6f' if k == 0 else '#9a9a9a', linewidths=0.45, rasterized=True))
    ax.set_xlim(xmin - 20, xmax + 20); ax.set_ylim(ymin - 20, ymax + 20)
    ax.set_aspect('equal'); ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_color('#999999'); s.set_linewidth(0.6)
# (a) network and fog nodes
ax = axs[0]
ax.scatter(rsu[:, 0], rsu[:, 1], marker='^', s=46, c=cA, edgecolors='black', linewidths=0.6, zorder=5)
for (x, y), nm in zip(rsu, rsu_names):
    ax.annotate(nm + ' / RSU', (x, y), xytext=(5, 5), textcoords='offset points', fontsize=7.5,
                bbox=dict(boxstyle='round,pad=0.15', fc='white', ec='none', alpha=0.85), zorder=6)
ax.plot([xmax - 560, xmax - 60], [ymin + 60, ymin + 60], color='black', lw=1.2)
ax.text(xmax - 310, ymin + 95, '500 m', ha='center', fontsize=7)
ax.set_title('(a) Road network and buildings of Tarragona (SUMO)', fontsize=8)
# (b) snapshot
ax = axs[1]
ax.add_collection(LineCollection([[a, b] for a, b in v2v], colors=cB, linewidths=0.5, alpha=0.8, zorder=3))
ax.add_collection(LineCollection([[a, b] for a, b in v2i], colors=cA, linewidths=0.8, zorder=4))
ax.scatter(veh[:, 0], veh[:, 1], s=7, c='#222222', zorder=5, linewidths=0)
ax.scatter(rsu[:, 0], rsu[:, 1], marker='^', s=46, c=cA, edgecolors='black', linewidths=0.6, zorder=6)
ax.set_title(f'(b) V2I/V2V links with {len(veh)} vehicles at $t={T_SNAP:.0f}$ s (Veins)', fontsize=8)
from matplotlib.lines import Line2D
h = [Line2D([0], [0], marker='^', ls='', mfc=cA, mec='black', ms=6, label='fog node / RSU'),
     Line2D([0], [0], marker='o', ls='', mfc='#222222', mec='none', ms=3.5, label='vehicle'),
     Line2D([0], [0], color=cA, lw=1.2, label='V2I link'),
     Line2D([0], [0], color=cB, lw=1.0, label='V2V link')]
ax.legend(handles=h, loc='upper left', fontsize=6.5, frameon=True, framealpha=0.9, edgecolor='#cccccc', handlelength=1.4)
fig.savefig(OUT, dpi=int(sys.argv[6]) if len(sys.argv) > 6 else 300)
print('saved', OUT)
