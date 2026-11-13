# Costs (ms) of every scheme from the averaged benchmark (bench/results.txt: 5 x 20 rounds,
# OpenSSL 3.0.13, Intel Xeon 2.10 GHz) and the operation counts of the authentication phases.
Tpm, Tpa, Th, Tsed, Tmm = 0.1717, 0.00042, 0.00052, 0.00060, 0.00028   # Tmm = one Horner step
ty, tx = 100, 1000
def c(pm=0, pa=0, h=0, sed=0, mm=0): return pm*Tpm + pa*Tpa + h*Th + sed*Tsed + mm*Tmm
rows = {
 'FogRoam-A': (c(3,0,9,2,ty), c(4,0,8,2,tx), c(4,0,7,1)),
 'FogRoam-B': (c(3,0,5,1,ty), c(3,0,5,1,tx), 0),
 'Chen2024': (c(2,0,4), c(1,0,10), c(0,0,8)),
 'Ma2019':   (c(3,0,4), c(4,0,4), c(8,0,9)),
 'Wazid2019':(c(0,0,6), c(0,0,14), c(0,0,6)),
 'Eftekhari2021':(c(3,1,11), c(3,1,12), c(3,0,15)),
}
for k, (v, f, s) in rows.items():
    print(f"{k:14s} V {v:.3f}  F {f:.3f}  CS {s:.3f}  total {v+f+s:.3f}")
sim = {
 'Proposed': dict(cV1=c(2,0,6,2,ty), cV2=c(1,0,3), cH1=c(2,0,3,1,ty), cH2=c(1,0,2),
                  cF1=c(3,0,4,2,tx), cF2=c(1,0,4), cFH=c(3,0,5,1,tx), cCS=c(4,0,7,1)),
 'Baseline': dict(cV1=c(2,0,2), cV2=c(0,0,2), cF1=c(1,0,5), cF2=c(0,0,5), cCS=c(0,0,8)),
}
for k, d in sim.items(): print(k, {a: round(b, 4) for a, b in d.items()})
print('share eval V %.4f F %.4f' % (ty*Tmm, tx*Tmm))
