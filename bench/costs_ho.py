#!/usr/bin/env python3
"""Cost of one handover in phase B of FogRoam and in the handover schemes [34]-[36] of the paper
(Table VII), at the 80-bit level and on the platform of Table V.

Primitive times: Tpm, Th as in sim_delays5g.py (bench.c); Te (exponentiation in G of a Type-A
pairing), Tbp (Tate pairing), and Tc (Chebyshev map) from bench_pairing.c, which measures them
in the same process as Tpm; we scale their ratios to Tpm to the Tpm of Table V.
Operation counts (vehicle / fog nodes), point additions neglected:
  [34] Xie et al.     3Th / 2Tpm + 7Th         (handover phase AN1-AN2, as counted in [34], Table III)
  [35] Mohammed et al. Te + Tbp + Th / 5Te + Tbp + Th
                       (GenVehPK2 / GenHC at the old fog node: 2Te + Th, GenToken and GenFogPK2 at
                        the new one: 3Te + Tbp)
  [36] Son et al.     5Th / 6Tc + 10Th        (O_i, L, SK, N, Z / ES_j: 3Tc + 3Th, ES_j+1: 3Tc + 7Th)
Sizes (bits): identity 64, hash and random value 160, timestamp 32, EC point 320 (Section VII-B),
pairing-group element 1024, Chebyshev value 512.
"""
import json
Tpm, Th = 0.1717, 0.00052
ratio = dict(Te=7.597, Tbp=3.863, Tc=0.296)          # bench_pairing.c, CPU time, 10 rounds
Te, Tbp, Tc = (ratio[k] * Tpm for k in ('Te', 'Tbp', 'Tc'))
ID, H, T, P, G, C = 64, 160, 32, 320, 1024, 512
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
 'FogRoam B':        dict(veh=0.547, fog=0.799, air=1088, interfog=0, fog_storage=320 + 160 * 1001),
}
for k, v in rows.items():
    print(f"{k:18s} veh {v['veh']:.3f} ms  fog {v['fog']:.3f} ms  air {v['air']}  inter-fog {v['interfog']}  "
          f"storage {v.get('fog_storage_per_vehicle', v.get('fog_storage'))}")
print(f'Te {Te:.3f} ms, Tbp {Tbp:.3f} ms, Tc {Tc:.4f} ms')
json.dump(dict(T=dict(Tpm=Tpm, Th=Th, Te=Te, Tbp=Tbp, Tc=Tc), rows=rows), open('costs_ho.json', 'w'), indent=1)
