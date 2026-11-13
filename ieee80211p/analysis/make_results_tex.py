#!/usr/bin/env python3
"""Write the results paragraph (sim_results.tex) of the paper from summary.json."""
import json, sys
S = json.load(open(sys.argv[1]))
out = sys.argv[2]
Ns = [20, 40, 60, 80, 100, 120]
g = lambda c, n, k: S[f'{c}-{n}'][k]
P, A, C = 'Proposed', 'ProposedA', 'Baseline'
lo, hi = Ns[0], Ns[-1]
red_cloud = [1 - g(P, n, 'cloud') / g(C, n, 'cloud') for n in Ns]
red_lat = [1 - g(P, n, 'lat_ms') / g(C, n, 'lat_ms') for n in Ns]
fracB = [g(P, n, 'fracB') for n in Ns]
txt = rf"""% SIM-RESULTS-BEGIN
\emph{{Results:}} Fig.~\ref{{fig:sim}} shows the results. The packet loss rate grows with the number of vehicles for all schemes, from about {100*g(C,lo,'plr'):.1f}\% with {lo} vehicles to {100*min(g(P,hi,'plr'),g(A,hi,'plr'),g(C,hi,'plr')):.1f}--{100*max(g(P,hi,'plr'),g(A,hi,'plr'),g(C,hi,'plr')):.1f}\% with {hi} vehicles, because the V2V beacons increasingly load the channel and buildings block many links (Fig.~\ref{{fig:map}}). The differences between the schemes stay within the variation across seeds, i.e., the slightly larger messages of the proposed protocol do not increase the losses. The end-to-end delay of a protocol frame is dominated by channel access and transmission at 6~Mbps: it is {g(C,lo,'e2e_ms'):.3f}--{g(C,hi,'e2e_ms'):.3f}~ms for \cite{{chen2024provably}}, whose messages are the shortest, {g(P,lo,'e2e_ms'):.3f}--{g(P,hi,'e2e_ms'):.3f}~ms for our protocol, and {g(A,lo,'e2e_ms'):.3f}--{g(A,hi,'e2e_ms'):.3f}~ms when only phase~A is used. The short messages $M_5$ and $M_6$ of phase~B thus reduce the air time of our protocol, and all values remain far below the latency budget of vehicular safety applications. The authentication latency is dominated by computation and by the backhaul round trip. Phase~A takes {g(P,lo,'latA_ms'):.1f}--{g(P,hi,'latA_ms'):.1f}~ms, more than the {g(C,lo,'lat_ms'):.1f}--{g(C,hi,'lat_ms'):.1f}~ms of \cite{{chen2024provably}}, because of its additional point multiplications. However, phase~B needs only {g(P,lo,'latB_ms'):.1f}--{g(P,hi,'latB_ms'):.1f}~ms, and since it handles {100*min(fracB):.0f}\% of the authentications, the mean latency of our protocol is {g(P,lo,'lat_ms'):.1f}--{g(P,hi,'lat_ms'):.1f}~ms, i.e., {100*min(red_lat):.1f}--{100*max(red_lat):.1f}\% lower than that of \cite{{chen2024provably}}, while providing all the security properties of Table~\ref{{tab:features}}. Moreover, phase~B removes {100*min(red_cloud):.0f}--{100*max(red_cloud):.0f}\% of the messages processed by $\CS$ and of the backhaul traffic, i.e., the cloud processes about seven times fewer authentication messages. The success rate of the sessions, which mainly reflects vehicles leaving the coverage of their fog node, is similar for all schemes ({100*g(P,hi,'succ'):.1f}\%, {100*g(A,hi,'succ'):.1f}\%, and {100*g(C,hi,'succ'):.1f}\% with {hi} vehicles).

%FIG_SIMRES%
% SIM-RESULTS-END
"""
open(out, 'w').write(txt)
print(txt)
