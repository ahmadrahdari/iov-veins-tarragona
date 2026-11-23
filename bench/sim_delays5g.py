#!/usr/bin/env python3
"""Operation counts of Table V of the paper and the processing delays of the 5G simulation.

Operation times (ms) at the 80-bit level (secp160r1, SHA-1, AES-128, 160-bit modulus), averaged
over 100 rounds of bench/bench.c (OpenSSL 3.0.13, Intel Xeon 2.10 GHz), as in the paper.
Counts exclude the one-time login of the vehicle (password check and unlocking of Cred_i) and
include the derivation of the exported session key h_ses(SK) by every party.
"""
import json
Tpm, Tpa, Th, Tsed, Tmm = 0.1717, 0.00042, 0.00052, 0.00060, 0.00028
ty, tx = 100, 1000
def c(pm=0, pa=0, h=0, sed=0, mm=0):
    return pm * Tpm + pa * Tpa + h * Th + sed * Tsed + mm * Tmm
# processing steps of the simulation (ms)
steps = {
 'Proposed': dict(
   cV1=c(pm=2, h=4, sed=1, mm=ty),   # x1, R1, Q1, K1, k_ij, sigma_1, tau_i, C1
   cV2=c(pm=1, h=4),                 # Z_VC, h_2, SK, d_3, h_ses(SK)
   cH1=c(pm=2, h=3, sed=1, mm=ty),   # x4, R4, Q4, K3, k_ik, sigma_4, C3
   cH2=c(pm=1, h=3),                 # Z, SK', d_5, h_ses(SK')
   cF1=c(pm=3, h=4, sed=2, mm=tx),   # Q1, K1, D(C1), k_ij, sigma_1, x2, R2, Q2, K2, C2
   cF2=c(pm=1, h=5),                 # Z_FC, h_2, mask of N_f, d_1, d_3, h_ses(SK)
   cFH=c(pm=3, h=6, sed=1, mm=tx),   # Q4, K3, D(C3), k_ik, sigma_4, x5, R5, Z, SK', d_5, h_ses(SK')
   cCS=c(pm=4, h=8, sed=1)),         # Q2, K2, D(C2), tau_i, x3, R3, Z_FC, Z_VC, h_2, SK, d_1, N_f, h_ses(SK)
 'Baseline': dict(                   # Chen et al.
   cV1=c(pm=2),                      # P_i, Q_i (PV_i and TV_i belong to the login)
   cV2=c(h=2),                       # J_i, SK
   cF1=c(pm=1, h=5),                 # b_j, Q_i, W_i, Y_i, X_i, D
   cF2=c(h=5),                       # r_5, SK, Z_i, J_i, N_i
   cCS=c(h=8)),
}
p, b = steps['Proposed'], steps['Baseline']
table = {
 'FogRoam A': (p['cV1'] + p['cV2'], p['cF1'] + p['cF2'], p['cCS']),
 'FogRoam B': (p['cH1'] + p['cH2'], p['cFH'], 0.0),
 'Chen': (b['cV1'] + b['cV2'], b['cF1'] + b['cF2'], b['cCS']),
}
for k, (v, f, cs) in table.items():
    print(f'{k:10s} V {v:.3f}  F {f:.3f}  CS {cs:.3f}  total {v + f + cs:.3f} ms')
print('omnetpp.ini (ms):')
for cfg, d in steps.items():
    print(' ', cfg, ' '.join(f'{a}={x:.4f}ms' for a, x in d.items()))
json.dump({cfg: {a: round(x, 4) for a, x in d.items()} for cfg, d in steps.items()}, open('sim_delays5g.json', 'w'), indent=1)
