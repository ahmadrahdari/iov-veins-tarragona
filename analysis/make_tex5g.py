#!/usr/bin/env python3
"""Generate the pgfplots figure of the paper (Fig. "fig:sim") from summary5g.json.

usage: make_tex5g.py summary5g.json fig_sim.tex

Panel (a) shows the loss rate over the messages of all seeds with its 95 % Wilson interval
(markers only, slightly offset); panels (b)-(d) show the mean over the seeds with the
standard deviation across seeds. Panel labels are placed below the axes and the legend
below the figure, as in the paper.
"""
import json, sys

S = json.load(open(sys.argv[1]))
out = sys.argv[2]
Ns = [20, 40, 60, 80, 100, 120]
cfgs = [('Proposed', r'{\protocol} ($\mathsf{A}{+}\mathsf{B}$)', 'cA', 'mark=*', 'solid', -2.5),
        ('ProposedA', r'{\protocol} ($\mathsf{A}$ only)', 'cB', 'mark=square*', 'dashed', 0.0),
        ('Baseline', r'\cite{chen2024provably}', 'cC', 'mark=triangle*', 'densely dotted', 2.5)]

AX = r'''\begin{axis}[width=4.75cm, height=3.9cm, xmin=10, xmax=130, xtick={20,40,60,80,100,120},
  tick label style={font=\scriptsize}, label style={font=\scriptsize}, xlabel={Number of vehicles},
  ymajorgrids, grid style={black!12}, axis line style={black!45}, tick style={black!45},
  legend style={font=\scriptsize, draw=none, fill=none}, ylabel={%s}, title={(%s)}, title style={font=\scriptsize, at={(0.5,0)}, anchor=north, yshift=-27pt}%s]'''


def series(key, sd=None, scale=1.0, marks_only=False):
    lines = []
    for cfg, name, col, mark, style, dx in cfgs:
        pts = []
        for n in Ns:
            r = S[f'{cfg}-{n}']
            y = r[key] * scale
            if marks_only:   # asymmetric 95 % interval
                lo, hi = (r[key] - r['plr_lo']) * scale, (r['plr_hi'] - r[key]) * scale
                pts.append(f'({n + dx:g},{y:.4f}) += (0,{hi:.4f}) -= (0,{lo:.4f})')
            else:
                e = r.get(sd, 0.0) * scale
                pts.append(f'({n},{y:.4f}) +- (0,{e:.4f})')
        look = f'{col}, only marks, {mark}, mark size=1.8pt' if marks_only else \
               f'{col}, {style}, line width=1pt, {mark}, mark size=1.8pt, mark options={{solid}}'
        lines.append(f'\\addplot[{look}, error bars/.cd, y dir=both, y explicit, error bar style={{line width=0.5pt,solid}}] coordinates {{{" ".join(pts)}}};')
        lines.append(f'\\addlegendentry{{{name}}}')
    return '\n'.join(lines)


def panel(label, ylabel, key, sd=None, scale=1.0, extra='', marks_only=False, legend=False):
    body = (AX % (ylabel, label, extra)) + '\n' + series(key, sd, scale, marks_only) + '\n'
    return body + ('' if legend else '\\legend{}\n') + '\\end{axis}'


pa = panel('a', r'Packet loss rate (\%)', 'plr_pooled', scale=100.0, extra=', ymin=0, ymax=1', marks_only=True)
pb = panel('b', 'End-to-end delay (ms)', 'e2e_ms', 'e2e_ms_ci', extra=', ymin=0, legend to name=simleg', legend=True)
pc = panel('c', 'Authentication latency (ms)', 'lat_ms', 'lat_ms_ci', extra=', ymin=0')
pd = panel('d', r'$\CS$ load (msg/s)', 'cloud_rate', 'cloud_rate_ci', extra=', ymin=0')
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
\node[anchor=north, inner sep=1pt] at (9.0cm,-1.2cm) {\pgfplotslegendfromname{simleg}};
\end{tikzpicture}
\vspace{-10pt}
\caption{Simulation results of the 5G NR scenario in Tarragona: (a) packet loss rate of the protocol messages over the three seeds with 95\%% Wilson intervals, (b) mean end-to-end delay of the protocol messages, (c) mean authentication latency, and (d) messages processed by $\CS$ per second. Error bars in (b)--(d) show the standard deviation over three seeds.}
\label{fig:sim}
\end{figure*}
''' % (pa, pb, pc, pd)
open(out, 'w').write(fig)
print('written', out)
