#!/usr/bin/env python3
"""Computation (Table V), communication (Fig. 7), and storage (Table VI) costs of the paper at the
128-bit level: secp256r1, SHA-256, AES-256, and a 256-bit field for the polynomial shares.
Operation times as in sim_delays5g.py (means of 5 runs of bench256.c, ops128.json)."""
import json
from sim_delays5g import Tpm, Tpa, Th, Tsed, Tmm, ty, tx
def c(pm=0, pa=0, h=0, sed=0, mm=0):
    return pm * Tpm + pa * Tpa + h * Th + sed * Tsed + mm * Tmm
OPS = {   # (vehicle, fog node, cloud server) operation counts
 'oursA': (dict(pm=3, h=8, sed=1, mm=ty), dict(pm=4, h=9, sed=2, mm=tx), dict(pm=4, h=8, sed=1)),
 'oursB': (dict(pm=3, h=6, sed=1, mm=ty), dict(pm=3, h=6, sed=1, mm=tx), None),
 'chen':  (dict(pm=2, h=2), dict(pm=1, h=10), dict(h=8)),
 'ma':    (dict(pm=3, h=4), dict(pm=4, h=4), dict(pm=8, h=9)),
 'wazid': (dict(h=6), dict(h=14), dict(h=6)),
 'eft':   (dict(pm=3, pa=1, h=10), dict(pm=3, pa=1, h=12), dict(pm=3, h=15)),
}
comp = {}
for k, ents in OPS.items():
    v = [c(**e) if e is not None else None for e in ents]
    comp[k] = v + [sum(x for x in v if x is not None)]
# sizes (bits): hash outputs, random numbers, and field elements 256, points 512, identities 64, timestamps 32
h, P, ID, T = 256, 512, 64, 32
m1 = P + ID + 2 * h + T          # M1 = {R1, C1 (=|ID|), sigma_1, tau_i, T1}
m2 = ID + 2 * P + ID + h + T     # M2 = {FID_j, R1, R2, C2 (=|ID|), tau_i, T2}
m3 = P + 2 * h + T               # M3 = {R3, N_f, d1, T3}
m4 = P + h + T                   # M4 = {R3, d3, T4}
m5 = P + ID + h + T              # M5 = {R4, C3 (=|ID|), sigma_4, T5}
m6 = P + h + T                   # M6 = {R5, d5, T6}
comm = {   # bits sent by (vehicle, fog node, cloud server)
 'oursA': (m1, m2 + m4, m3),
 'oursB': (m5, m6, 0),
 'chen':  (h + P + h + T, (4 * h + T) + (2 * h + T), 2 * h + T),
 'ma':    (P + 2 * h + T, 6 * P + 5 * h + 3 * T, 3 * P + 2 * h + T),
 'wazid': (ID + 2 * h + T, (ID + 2 * h + T) + (3 * h + T), 3 * h + T),
 'eft':   (h + P + (ID + h) + h + T,
           (2 * h + 2 * P + 2 * (ID + h) + h + T) + (h + 2 * P + h),
           2 * h + P + 2 * h),
}
comm = {k: list(v) + [sum(v)] for k, v in comm.items()}
# storage (bits): vehicle b_i, TV_i (8), Cred_i = (nu_i (128), sk_i, k_ic, t_y+1 coefficients);
# fog node sk_j, k_jc, t_x+1 coefficients; CS sk_c, (ID, pk, k) per entity, (t_x+1)(t_y+1) coefficients
veh = h + 8 + 128 + h + h + h * (ty + 1)
fog = h + h + h * (tx + 1)
cs_entry = ID + P + h
f_bits = h * (tx + 1) * (ty + 1)
storage = dict(vehicle=veh, fog=fog, cs_entry=cs_entry, cs_f_bits=f_bits,
               vehicle_KiB=veh / 8 / 1024, fog_KiB=fog / 8 / 1024, cs_f_MiB=f_bits / 8 / 2**20,
               chen=dict(vehicle=3 * h, fog=3 * h, cs='256+64N_F'))
renewal_bits = h * (ty + 1) + 128     # AE of the t_y+1 coefficients of psi_i with a 128-bit tag
out = dict(T=dict(Tpm=Tpm, Tpa=Tpa, Th=Th, Tsed=Tsed, Tmm=Tmm), comp=comp, comm=comm,
           msgs=dict(M1=m1, M2=m2, M3=m3, M4=m4, M5=m5, M6=m6), storage=storage, renewal_bits=renewal_bits)
json.dump(out, open('costs128.json', 'w'), indent=1)
for k, v in comp.items():
    print(f"{k:6s} " + "  ".join('--' if x is None else f'{x:.3f}' for x in v))
for k, v in comm.items():
    print(f"{k:6s} bits {v}")
print('messages', out['msgs'])
print('storage', storage, 'renewal', renewal_bits)
