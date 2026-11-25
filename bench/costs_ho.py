#!/usr/bin/env python3
"""Cost of one handover in phase B of FogRoam and in the handover schemes [34]-[36] of the paper
(Table VII), at the 128-bit level and on the platform of Table V.

Primitive times: Tpm, Th as in sim_delays5g.py (bench256.c); Te (exponentiation in G of a Type-A
pairing, |q| = 1536, |r| = 256), Tbp (Tate pairing), and Tc (Chebyshev map, 1536-bit modulus) from
"bench_pairing.c 128", which measures them in the same process as Tpm on secp256r1; we scale the
mean of their ratios to Tpm over 3 runs to the Tpm of Table V. The symmetric pairing of [35] needs
a 1536-bit field at the 128-bit level.
Operation counts (vehicle / fog nodes), point additions neglected:
  [34] Xie et al.     3Th / 2Tpm + 7Th         (handover phase AN1-AN2, as counted in [34], Table III)
  [35] Mohammed et al. Te + Tbp + Th / 5Te + Tbp + Th
                       (GenVehPK2 / GenHC at the old fog node: 2Te + Th, GenToken and GenFogPK2 at
                        the new one: 3Te + Tbp)
  [36] Son et al.     5Th / 6Tc + 10Th        (O_i, L, SK, N, Z / ES_j: 3Tc + 3Th, ES_j+1: 3Tc + 7Th)
Sizes (bits): identity 64, hash and random value 256, timestamp 32, EC point 512 (Section VII-B),
pairing-group element 3072, Chebyshev value 1536.
"""
import json
from sim_delays5g import Tpm, Th
ratio = dict(Te=(395.644 + 377.002 + 389.036) / 3, Tbp=(126.164 + 132.951 + 129.911) / 3,
             Tc=(6.523 + 6.502 + 6.653) / 3)    # bench_pairing.c 128, CPU time, 3 runs of 10 rounds
Te, Tbp, Tc = (ratio[k] * Tpm for k in ('Te', 'Tbp', 'Tc'))
ID, H, T, P, G, C = 64, 256, 32, 512, 3072, 1536
rows = {
 'xie2023provable':  dict(veh=3 * Th, fog=2 * Tpm + 7 * Th,
                          air=H + H + T,                       # {PID_i, N2, T4}; the report AC is payload
                          interfog='one ledger record per handover', fog_storage_per_vehicle=ID + 4 * H + P + T),  # ledger record {RID_t, PID_i, K, N1, l_t, J_t, T3}
 'mohammed2024hafc': dict(veh=Te + Tbp + Th, fog=5 * Te + Tbp + Th,
                          air=2 * G,                           # HC2 and the token D_{i+1,2}
                          interfog=G,                          # HC1
                          fog_storage_per_vehicle=2 * G),      # PK_f1 and SK
 'son2025seamless':  dict(veh=5 * Th, fog=6 * Tc + 10 * Th,
                          air=(ID + H + H + T) + (2 * H + H + T),          # {ID, AID, O_i, T7}, {L, N, T10}
                          interfog=(ID + C + H + H + T) + (C + ID + H + T),  # {ID, R, AID, O_i, T8}, {K, O_j, T9}
                          fog_storage_per_vehicle=H + ID + T),  # (AID, RID, ET)
 'FogRoam B':        dict(veh=None, fog=None, air=(P + ID + H + T) + (P + H + T), interfog=0, fog_storage=2 * H + H * 1001),
}
from sim_delays5g import c, ty, tx
rows['FogRoam B']['veh'] = c(pm=3, h=6, sed=1, mm=ty)
rows['FogRoam B']['fog'] = c(pm=3, h=6, sed=1, mm=tx)
for k, v in rows.items():
    v['total'] = v['veh'] + v['fog']
    print(f"{k:18s} veh {v['veh']:.3f} ms  fog {v['fog']:.3f} ms  total {v['total']:.3f} ms  air {v['air']}  inter-fog {v['interfog']}  "
          f"storage {v.get('fog_storage_per_vehicle', v.get('fog_storage'))}")
print(f'Te {Te:.3f} ms, Tbp {Tbp:.3f} ms, Tc {Tc:.4f} ms')
print('inter-fog record of [34]:', H + T + ID + H + P + T, 'bits')
json.dump(dict(T=dict(Tpm=Tpm, Th=Th, Te=Te, Tbp=Tbp, Tc=Tc), rows=rows), open('costs_ho.json', 'w'), indent=1)
