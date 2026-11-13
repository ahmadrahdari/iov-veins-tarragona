#!/usr/bin/env python3
"""Computation and communication costs at the 80-bit (secp160r1, SHA-1) and the 128-bit
(secp256r1, SHA-256) security level, from the operation times measured in one session
(ops_session2.json: 10 alternating runs of bench160/bench256, OpenSSL 3.0.13, Xeon 2.10 GHz)."""
import json
ops = json.load(open('ops_session2.json'))
ty, tx = 100, 1000
def T(level):
    o = ops[level]
    return dict(pm=o['Tpm'], pa=o['Tpa'], h=o['Th'], sed=o['Tsed'], mm=o['f_1000'] / 1000)  # mm: one Horner step
def c(t, pm=0, pa=0, h=0, sed=0, mm=0):
    return pm * t['pm'] + pa * t['pa'] + h * t['h'] + sed * t['sed'] + mm * t['mm']
OPS = {   # (vehicle, fog node, cloud server) operation counts, unchanged by the revision of phase A
 'oursA': (dict(pm=3, h=9, sed=2, mm=ty), dict(pm=4, h=8, sed=2, mm=tx), dict(pm=4, h=7, sed=1)),
 'oursB': (dict(pm=3, h=5, sed=1, mm=ty), dict(pm=3, h=5, sed=1, mm=tx), None),
 'chen':  (dict(pm=2, h=4), dict(pm=1, h=10), dict(h=8)),
 'ma':    (dict(pm=3, h=4), dict(pm=4, h=4), dict(pm=8, h=9)),
 'wazid': (dict(h=6), dict(h=14), dict(h=6)),
 'eft':   (dict(pm=3, pa=1, h=11), dict(pm=3, pa=1, h=12), dict(pm=3, h=15)),
}
comp = {}
for lvl in ('160', '256'):
    t = T(lvl); comp[lvl] = {}
    for k, ents in OPS.items():
        v = [c(t, **e) if e is not None else None for e in ents]
        comp[lvl][k] = v + [sum(x for x in v if x is not None)]
# communication: element sizes (bits) per level
SZ = {'160': dict(h=160, P=320, ID=64, T=32), '256': dict(h=256, P=512, ID=64, T=32)}
def bits(lvl, h=0, P=0, ID=0, T=0):
    s = SZ[lvl]; return h * s['h'] + P * s['P'] + ID * s['ID'] + T * s['T']
MSG = {   # bits sent by (vehicle, fog node, cloud server); h = hash-sized value (hash, nonce, masked value)
 # FogRoam phase A (revised): M1={R1,C1,s1,tau,T1}, M2={FID,R1,R2,C2,tau,T2}, M3={R3,Nf,d1,T3}, M4={R3,d3,T4}
 'oursA': (dict(P=1, ID=1, h=2, T=1), [dict(ID=1, P=2, ID2=0, h=1, T=1, C=1), dict(P=1, h=1, T=1)], dict(P=1, h=2, T=1)),
}
def ours_bits(lvl):
    s = SZ[lvl]
    m1 = s['P'] + s['ID'] + 2 * s['h'] + s['T']                 # R1, C1 (=|ID|), sigma1, tau
    m2 = s['ID'] + 2 * s['P'] + s['ID'] + s['h'] + s['T']       # FID, R1, R2, C2 (=|ID|), tau
    m3 = s['P'] + 2 * s['h'] + s['T']                           # R3, Nf, d1
    m4 = s['P'] + s['h'] + s['T']                               # R3, d3
    m5 = s['P'] + s['ID'] + s['h'] + s['T']                     # R4, C3, sigma4
    m6 = s['P'] + s['h'] + s['T']                               # R5, d5
    return dict(A=(m1, m2 + m4, m3), B=(m5, m6, 0), msgs=(m1, m2, m3, m4, m5, m6))
def comm(lvl):
    s = SZ[lvl]; o = ours_bits(lvl)
    chen = (s['h'] + s['P'] + s['h'] + s['T'],                    # M1 = {RID, P, F, T1}
            (4 * s['h'] + s['T']) + (2 * s['h'] + s['T']),       # M2 = {W, X, Y, D, T2}, M4 = {N, J, T4}
            2 * s['h'] + s['T'])                                 # M3 = {L, Z, T3}
    ma = (s['P'] + 2 * s['h'] + s['T'], 6 * s['P'] + 5 * s['h'] + 3 * s['T'], 3 * s['P'] + 2 * s['h'] + s['T'])  # Ma et al.'s own formulas
    wazid = (s['ID'] + 2 * s['h'] + s['T'],                       # {TID_V, MVF1, MVF2, T}
             (s['ID'] + 2 * s['h'] + s['T']) + (3 * s['h'] + s['T']),   # to V_i; {TID_FS, MFC1, MFC2, T} to CS
             3 * s['h'] + s['T'])                                # {TID_FS, MFC3, MFC4, T}
    eft = (s['h'] + s['P'] + (s['ID'] + s['h']) + s['h'] + s['T'],                                   # V -> F
           (2 * s['h'] + 2 * s['P'] + 2 * (s['ID'] + s['h']) + s['h'] + s['T']) + (s['h'] + 2 * s['P'] + s['h']),  # F -> CS, F -> V
           2 * s['h'] + s['P'] + 2 * s['h'])                     # CS -> F
    d = dict(oursA=o['A'], oursB=o['B'], chen=chen, ma=ma, wazid=wazid, eft=eft)
    return {k: list(v) + [sum(v)] for k, v in d.items()}, o['msgs']
out = dict(comp=comp, comm={l: comm(l)[0] for l in SZ}, msgs={l: comm(l)[1] for l in SZ}, T={l: T(l) for l in SZ})
json.dump(out, open('costs2.json', 'w'), indent=1)
for lvl in ('160', '256'):
    print(f'== {lvl}-bit  (Tpm {T(lvl)["pm"]:.4f}, Th {T(lvl)["h"]:.5f}, Tsed {T(lvl)["sed"]:.5f}, Horner step {T(lvl)["mm"]:.6f} ms)')
    for k in OPS:
        v = comp[lvl][k]; b = out['comm'][lvl][k]
        print(f"  {k:6s} comp V {v[0]:.3f} F {v[1]:.3f} CS {('%.3f' % v[2]) if v[2] is not None else '  -  '} total {v[3]:.3f} ms | comm V {b[0]} F {b[1]} CS {b[2]} total {b[3]}")
    print('  messages M1..M6:', comm(lvl)[1])
# processing delays for the simulation (80-bit level, as in the comparison with [10])
t = T('160')
sim = {'Proposed': dict(cV1=c(t, pm=2, h=6, sed=2, mm=ty), cV2=c(t, pm=1, h=3), cH1=c(t, pm=2, h=3, sed=1, mm=ty), cH2=c(t, pm=1, h=2),
                        cF1=c(t, pm=3, h=4, sed=2, mm=tx), cF2=c(t, pm=1, h=4), cFH=c(t, pm=3, h=5, sed=1, mm=tx), cCS=c(t, pm=4, h=7, sed=1)),
       'Chen': dict(cV1=c(t, pm=2, h=2), cV2=c(t, h=2), cF1=c(t, pm=1, h=5), cF2=c(t, h=5), cCS=c(t, h=8))}
print('sim delays (ms):', {k: {a: round(b, 4) for a, b in d.items()} for k, d in sim.items()})
json.dump(sim, open('sim_delays2.json', 'w'), indent=1)
