#!/usr/bin/env python3
"""Generate the pgfplots figure and the results text for the paper from summary.json."""
import json, sys

S = json.load(open(sys.argv[1]))
out = sys.argv[2]
Ns = [20, 40, 60, 80, 100, 120]
cfgs = [('Proposed', 'Ours (A+B)', 'cA', 'mark=*', 'solid'),
        ('ProposedA', 'Ours (A only)', 'cB', 'mark=square*', 'dashed'),
        ('Baseline', r'\cite{chen2024provably}', 'cC', 'mark=triangle*', 'densely dotted')]

def series(key, scale=1.0, sd=None):
    lines = []
    for cfg, name, col, mark, style in cfgs:
        pts = []
        for n in Ns:
            k = f'{cfg}-{n}'
            if k not in S:
                continue
            y = S[k][key] * scale
            e = S[k].get(sd, 0.0) * scale if sd else 0.0
            pts.append(f'({n},{y:.4f}) +- (0,{e:.4f})')
        lines.append(f'\\addplot[{col}, {style}, line width=1pt, {mark}, mark size=1.8pt, mark options={{solid}}, error bars/.cd, y dir=both, y explicit, error bar style={{line width=0.5pt,solid}}] coordinates {{{" ".join(pts)}}};')
        lines.append(f'\\addlegendentry{{{name}}}')
    return '\n'.join(lines)

ax = r'''\begin{axis}[width=4.75cm, height=4.1cm, xmin=10, xmax=130, xtick={20,40,60,80,100,120},
  tick label style={font=\scriptsize}, label style={font=\scriptsize}, xlabel={Number of vehicles},
  ymajorgrids, grid style={black!12}, axis line style={black!45}, tick style={black!45},
  legend style={font=\scriptsize, draw=none, fill=none}, %s]'''

def plot(key, ylabel, extra, sd=None, scale=1.0, legend=False):
    leg = '' if legend else r'\legend{}'
    return (ax % (f'ylabel={{{ylabel}}}, ' + extra)) + '\n' + series(key, scale, sd) + '\n' + leg + '\n\\end{axis}'

fig = r'''\begin{figure*}[!t]
\centering
\definecolor{cA}{HTML}{2A78D6}\definecolor{cB}{HTML}{EB6834}\definecolor{cC}{HTML}{1BAF7A}
\pgfplotsset{every axis legend/.append style={legend columns=3, /tikz/every even column/.append style={column sep=8pt}}}
\begin{tikzpicture}
\begin{scope}
%s
\end{scope}
\begin{scope}[xshift=4.6cm]
%s
\end{scope}
\begin{scope}[xshift=9.2cm]
%s
\end{scope}
\begin{scope}[xshift=13.8cm]
%s
\end{scope}
\end{tikzpicture}
\caption{Simulation results in Tarragona: (a) packet loss rate of the protocol frames, (b) mean end-to-end delay of the protocol frames, (c) mean authentication latency, and (d) messages processed by $\CS$ per second. Error bars show the standard deviation over three seeds.}
\label{fig:sim}
\end{figure*}
'''
pa = plot('plr', 'Packet loss rate (\\%)', r'title={(a)}, title style={font=\scriptsize, yshift=-4pt}, legend to name=simleg', 'plr_sd', 100.0, legend=True)
pb = plot('e2e_ms', 'End-to-end delay (ms)', r'title={(b)}, title style={font=\scriptsize, yshift=-4pt}', 'e2e_ms_sd')
pc = plot('lat_ms', 'Authentication latency (ms)', r'title={(c)}, title style={font=\scriptsize, yshift=-4pt}', 'lat_ms_sd')
# cloud load: messages per second over the 123 s measurement window
for k in S:
    S[k]['cloud_rate'] = S[k]['cloud'] / 150.0
pd = plot('cloud_rate', '$\\CS$ load (msg/s)', r'title={(d)}, title style={font=\scriptsize, yshift=-4pt}')
body = fig % (pa, pb, pc, pd)
body = body.replace(r'\end{tikzpicture}', r'\node[anchor=north] at (9.0cm,-1.0cm) {\pgfplotslegendfromname{simleg}};' + '\n' + r'\end{tikzpicture}')
open(out, 'w').write(body)
print('written', out)
