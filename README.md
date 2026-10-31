# V2X simulation of FogRoam (Tarragona, Spain)

Veins/SUMO/OMNeT++ simulation used in the paper
*"FogRoam: Forward-Secure Authentication with Cloud-Free Handover for 6G Vehicular Networks"* to
compare the packet loss rate, the end-to-end delay, and the authentication latency of three configurations:

| Configuration | Protocol |
|---------------|----------|
| `Proposed`  | FogRoam: phase A (cloud-assisted, messages M1–M4) and phase B (cloud-free handover, messages M5–M6) |
| `ProposedA` | FogRoam restricted to phase A |
| `Baseline`  | the fog-based protocol of Chen et al. analysed in the paper (reference [11]; messages M1–M4) |

## Software

| Component | Version |
|-----------|---------|
| OMNeT++   | 6.0.3 (Cmdenv only) |
| Veins     | 5.3.1 |
| SUMO      | 1.20.0 |
| Xerces-C  | 3.2.5 (required by SUMO) |

```bash
build/fetch.sh     # downloads the sources into ./src
build/build.sh     # builds flex, Xerces-C, OMNeT++, SUMO and Veins (no root rights needed)
```

`build.sh` copies the protocol modules of `veins_aka/` to
`src/veins/src/veins/modules/application/aka/` before building Veins.
Both scripts use the repository folder as `$SIM`; set `SIM=/other/path` to change it.

## Scenario

* Road network and building footprints of the city centre of Tarragona
  (OpenStreetMap extract `map/tarragona.osm.xml`, 41.104–41.126 N, 1.229–1.264 E),
  converted with `netconvert` and `polyconvert` by `map/prepare_map.sh`.
  The simulated area is 3.7 km × 2.0 km.
* 4 fog nodes with co-located RSUs (Plaça de la Imperial Tàrraco, Rambla Nova,
  Avinguda de Roma, Avinguda de Catalunya) connected to the cloud server by a
  1 Gbps backhaul with 10 ms delay.
* 20, 40, 60, 80, 100, and 120 vehicles on random routes (`randomTrips.py`, minimum
  trip length 1200 m); IEEE 802.11p at 6 Mbps and 20 mW; free-space path loss with
  building shadowing (`SimpleObstacleShadowing`).
* Every vehicle broadcasts 250-byte V2V beacons at 10 Hz and authenticates with the
  fog node in range every 2 ± 0.5 s. With `Proposed`, phase A is run when the
  vehicle joins and whenever its last phase A is older than 20 s, and phase B
  otherwise.
* Message sizes (bits) and processing delays (ms) are set in `scenario/omnetpp.ini`
  from the operation counts of each scheme and the execution times measured with
  `bench/bench.c` (polynomial degrees t_x = 1000, t_y = 100); see *Operation costs*.
* 150 s per run, statistics collected after a 25 s warm-up, 3 seeds per configuration.

## Running

```bash
cd scenario
./run.sh Proposed 0      # one run; run numbers 0..17 = 6 densities x 3 seeds
./runall.sh              # all runs of the three configurations (JOBS=4 ./runall_par.sh runs them in parallel)
cd ..
python3 analysis/parse.py scenario/results analysis/summary.json
python3 analysis/make_tex.py analysis/summary.json fig_sim.tex
```

Veins starts SUMO itself (`TraCIScenarioManagerForker`).

## Operation costs

`bench/bench.c` measures, with OpenSSL 3, the execution time of a point multiplication and a
point addition on secp160r1, a SHA-1 hash, an AES-128 encryption (including the key
schedule), and one Horner step (160-bit modular multiplication and addition). The paper
uses the mean of five runs (`bench/results.txt`, Intel Xeon at 2.10 GHz); `bench/costs.py`
combines them with the operation counts of every scheme and prints the computation costs
of the paper and the processing delays of `scenario/omnetpp.ini`.

```bash
gcc -O2 bench/bench.c -o bench/bench -lcrypto -lm
for i in 1 2 3 4 5; do bench/bench; done > bench/results.txt
python3 bench/costs.py
```

## Metrics

* **Packet loss rate**: fraction of the over-the-air protocol frames (M1, M4, M5, M6)
  that are not received by their destination.
* **End-to-end delay**: time from the transmission of a protocol frame by the
  application layer of the sender to its reception by that of the receiver.
* **Authentication latency**: time from the start of a session at the vehicle to the
  establishment of the session key, including processing and backhaul delays.
* **Cloud load**: number of messages processed by the cloud server per second.

## Layout

```
veins_aka/   Veins modules: vehicle, fog node/RSU, cloud server, message definitions
scenario/    network (NED), omnetpp.ini, radio and obstacle configuration, SUMO inputs
map/         OpenStreetMap extract and prepare_map.sh
analysis/    parse.py (aggregation), make_tex.py (paper figure), make_map.py (scenario figure)
bench/       bench.c (operation timings), results.txt, costs.py (costs and processing delays)
build/       fetch.sh, build.sh
results/     OMNeT++ scalar results of all 54 runs (.sca)
figs/        scenario figure of the paper
```

The scenario figure is drawn from a SUMO trace of the 100-vehicle scenario:

```bash
cd scenario
sumo -n tarragona_center.net.xml -r tarragona_N100.rou.xml -a tarragona_center.poly.xml \
     --fcd-output ../figs/fcd_N100.xml --fcd-output.attributes x,y,angle,speed \
     --end 61 --step-length 0.1 --time-to-teleport -1
cd ..
python3 analysis/make_map.py scenario/tarragona_center.net.xml scenario/tarragona_center.poly.xml \
        figs/fcd_N100.xml figs/tarragona_sim.png 60
```

`results/` contains the raw results of the runs reported in the paper, and
`analysis/summary.json` the aggregated values; running `parse.py` and `make_tex.py`
on them reproduces the simulation figure of the paper.
