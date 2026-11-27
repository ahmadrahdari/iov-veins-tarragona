# 5G NR simulation of FogRoam (Tarragona, Spain)

Simu5G/INET/Veins/SUMO/OMNeT++ simulation used in the paper
*"FogRoam: Cloud-Free Handover Authentication for B5G Vehicular Networks"*. The B5G
architecture of the paper is simulated with 5G settings: the FogRoam authentication protocol
runs over a 5G NR standalone radio access network. Vehicles are NR user equipments driven by SUMO, every
fog node is co-located with a gNB, and the cloud server is reached over a backhaul link.
Three configurations are compared:

| Configuration | Protocol |
|---------------|----------|
| `Proposed`  | FogRoam: phase A (cloud-assisted, messages M1–M4) and phase B (cloud-free handover, messages M5–M6) |
| `ProposedA` | FogRoam restricted to phase A |
| `Baseline`  | the protocol of Chen et al. analysed in the paper (messages M1–M4) |
| `ProposedHO`, `BaselineHO` | as `Proposed` and `Baseline`, but sessions are triggered by the mobility: when a vehicle joins, at every change of its serving gNB, and when its last phase A (full run) is older than 300 s |
| `ProposedHO150`, `ProposedHO600` | `ProposedHO` with a phase-A re-validation interval of 150 s and 600 s |

## Software

| Component | Version | Role |
|-----------|---------|------|
| OMNeT++   | 6.0.3 (Cmdenv only) | discrete-event simulator |
| INET      | 4.5.2 | IPv4, UDP, SCTP (X2), PPP links |
| Simu5G    | 1.2.2 | 5G NR user plane: PDCP, RLC, MAC (HARQ, scheduling, link adaptation), PHY and channel models, handover |
| Veins     | 5.3.1 (`veins_inet` subproject) | coupling with SUMO over TraCI |
| SUMO      | 1.20.0 | road traffic |
| Xerces-C  | 3.2.5 | required by SUMO |

Simu5G 1.2.2 is the Simu5G release for OMNeT++ 6.0.x and INET 4.5. No source file of
OMNeT++, INET, Simu5G, Veins or SUMO is modified; all protocol logic is in `fogroam5g/`.

```bash
build/fetch.sh       # OMNeT++, SUMO, Veins, Xerces-C, flex          -> ./src
build/fetch5g.sh     # INET 4.5.2 and Simu5G 1.2.2                   -> ./src
build/build.sh       # builds OMNeT++, SUMO and Veins (no root rights needed)
build/build5g.sh     # builds INET (required features only), Simu5G, veins_inet and fogroam5g
```

The scripts use the repository folder as `$SIM`; set `SIM=/other/path` to change it.
`build5g.sh` takes about 20 minutes on two cores (`JOBS=N` changes the number of jobs).
A build made from scratch with these scripts gives scalar results identical to those of the
build used for the results below.

## Mapping of the protocol entities to the 5G system

| Protocol entity | Simulation module | Notes |
|-----------------|-------------------|-------|
| Vehicle V_i | `simu5g.nodes.cars.NRCar` with `AkaVehicleApp5G` | NR UE; mobility from SUMO (`VeinsInetMobility`) |
| Fog node F_j | `StandardHost fog[j]` with `AkaFogApp5G`, co-located with `gnb[j]` | reached through the user-plane function of the edge site (5 µs links) |
| Cloud server CS | `StandardHost cloud` with `AkaCloudApp5G` | 1 Gbps backhaul with 10 ms delay |
| Messages M1, M5 | UDP datagrams in the NR uplink | scheduling request, grant, HARQ |
| Messages M4, M6 | UDP datagrams in the NR downlink | |
| Messages M2, M3 | UDP datagrams between F_j and CS | wired |

The fog node of a vehicle is the one at its serving gNB, which the vehicle reads from its NR
physical layer (`LtePhyUe::getMasterId()`); when the UE is handed over to another gNB, its
next authentication is run with the fog node of the new cell. With `Proposed` this is a
phase B run (cloud-free) as long as the last phase A of the vehicle is not older than 300 s.

## Scenario

* Road network and building footprints of the city centre of Tarragona
  (OpenStreetMap extract `map/tarragona.osm.xml`, 41.104–41.126 N, 1.229–1.264 E),
  converted with `netconvert` and `polyconvert` by `map/prepare_map.sh`.
  The simulated area is 3.7 km × 2.0 km.
* 4 gNB sites with co-located fog nodes (Plaça de la Imperial Tàrraco, Rambla Nova,
  Avinguda de Roma, Avinguda de Catalunya), X2 full mesh between the gNBs.
* 20, 40, 60, 80, 100 and 120 vehicles on random routes (`randomTrips.py`, minimum trip
  length 1200 m). Vehicles of SUMO type `ext` enter from the map edge and were authenticated
  by a fog node outside the area before (their last phase A is uniform in the past 300 s).
* Every vehicle authenticates with the fog node of its serving cell every 30 ± 7.5 s. With
  `Proposed`, phase A is run when the vehicle joins and whenever its last phase A is older
  than 300 s, and phase B otherwise. A session fails if it is not completed within 1 s.
  With the `...HO` configurations (`authTrigger = "handover"`), a vehicle instead starts a
  session when it joins, when its serving gNB changes, and when its last phase A is older
  than `phaseAValidity`; the latency of the sessions that follow a handover is recorded
  separately (`latAho_ms`, `latBho_ms` in `analysis/summary5g.json`).
* Every vehicle sends a 250-byte cooperative awareness message (CAM) to its fog node at
  10 Hz as background uplink traffic.
* Message sizes (bits) and processing delays (ms) are set in `scenario/omnetpp.ini` at the 128-bit
  security level (secp256r1, SHA-256, AES-256, 256-bit field for the polynomial shares), from the
  operation counts of Table V of the paper and the execution times measured with `bench/bench256.c`
  (`cd bench && python3 sim_delays5g.py` prints the delays, `python3 costs128.py` the sizes). Fog nodes and CS process the messages in
  FIFO order.
* 900 s per run, statistics collected after a 300 s warm-up, 10 seeds per configuration
  (95 % confidence intervals of the mean over the seeds, Student t).

### Radio access network

| Parameter | Value |
|-----------|-------|
| Radio access | 5G NR standalone, one carrier, FDD |
| Carrier | 2.1 GHz (band n1), 20 MHz, 30 kHz subcarrier spacing (numerology 1, 0.5 ms slots), 51 resource blocks per direction |
| Transmit power | gNB 46 dBm, vehicle 23 dBm |
| Antennas | gNB 18 dBi at 25 m, omnidirectional; vehicle 3 dBi at 1.5 m (3GPP TR 37.885) |
| Noise figure | gNB 5 dB, vehicle 9 dB (3GPP TR 37.885) |
| Path loss | 3GPP TR 38.901 urban macro-cell (UMa) with distance-dependent LOS probability |
| Shadowing and fading | log-normal shadowing (50 m correlation distance), Jakes fast fading |
| Interference | inter-cell interference in both directions (all gNBs use the same carrier) |
| Link adaptation | NR CQI/MCS tables (`NRAmc`), target BLER 0.01, CSI report every 40 ms |
| HARQ | 8 processes, up to 3 retransmissions |
| RLC | unacknowledged mode, reassembly timer 50 ms |
| Scheduler | proportional fair in both directions |
| Mobility management | attachment to the strongest gNB, handover with 50 ms interruption, X2 |

Deviations from the Simu5G defaults, and why:

* `dynamic_los`, `downlink_interference` and `uplink_interference` are enabled, since by
  default Simu5G treats every link as NLOS and ignores the other cells.
* `targetBler = 0.01` and `blerShift = 5` as in the NR scenarios shipped with Simu5G.
* `fbPeriod = 40` (CSI report every 40 ms instead of 6 ms) to keep the run time acceptable.
* The RLC UM reassembly timer is 50 ms instead of 1 s. With the default, every residual
  HARQ failure stalls the uplink of that vehicle for up to 1 s, which no NR configuration
  for delay-sensitive traffic uses (t-Reassembly in 3GPP TS 38.331 is at most 200 ms).
* Simu5G models an FDD carrier by default. Its TDD option divides every slot into downlink
  and uplink symbols; it produced multi-second uplink stalls in this scenario and is not used.

## Running

```bash
cd scenario
./run.sh Proposed 0              # one run; run numbers 0..59 = 6 densities x 10 seeds
python3 runset.py 20,40,60,80,100,120 2     # Proposed, ProposedA and Baseline, 2 in parallel, resumable
./campaign.sh                    # all runs of the paper in the order in which they were made
cd ..
python3 analysis/parse5g.py results analysis/summary5g.json analysis/summary5g.csv
python3 analysis/make_fig5g.py analysis/summary5g.json figs/results5g.png
python3 analysis/make_tex5g.py analysis/summary5g.json fig_sim.tex
```

The scenario figure (`figs/tarragona_sim5g.png`) shows the serving gNB of every vehicle at
t = 600 s, after the 300 s warm-up, recorded by the simulation itself.
`results/snapshot/Proposed-N100-r0-t600.sca` is a copy of `scenario/snapshot600/Proposed-N100-r0.sca`
written by

```bash
cd scenario
./run.sh Proposed 40 --sim-time-limit=601s --result-dir=snapshot600 "--**.app[*].snapshotTime=600s"
cd ..
python3 analysis/make_map5g.py scenario/tarragona_center.net.xml scenario/tarragona_center.poly.xml \
  results/snapshot/Proposed-N100-r0-t600.sca figs/tarragona_sim5g.png
```

`snapshotTime` is off by default and draws no random numbers, so it does not change any result.

`runset.py` writes the results to `scenario/results/` (copy them to `results/` or pass that
folder to `parse5g.py`). SUMO is started by the simulation itself (`VeinsInetManagerForker`).
A 900 s run takes about 4 minutes for 20 vehicles, 25 minutes for 100 vehicles and 35 minutes
for 120 vehicles on one core of an Intel Xeon at 2.1 GHz (two runs in parallel on two cores);
the 320 runs of `campaign.sh` take about 80 core-hours. `runset.py` takes an optional time budget in minutes as
fourth argument and only starts runs that are expected to finish within it; with
`LARGE_FIRST=1` it starts the longest runs first. A run counts as complete only when its log
in `scenario/runlogs/` reports that the 900 s time limit was reached.

The fog-node application records the delay of every received request and CAM as output
vectors (`akaReqDelayA`, `akaReqDelayB`, `akaCamDelay`). Vector recording is off by default;
`./run.sh Proposed 0 "--**.app[*].aka*.vector-recording=true"` enables it, and
`analysis/vecstats.py <file.vec>` prints their percentiles.

## Metrics

* **Authentication latency**: time from the start of a session at the vehicle to the
  establishment of the session key, including processing, radio access and backhaul delays.
* **Packet loss rate**: fraction of the over-the-air protocol messages (M1, M4, M5, M6)
  that are not received by their destination, over all messages of the ten seeds, with
  its 95 % Wilson interval (only a few messages are lost per run).
* **End-to-end delay**: time from the transmission of an over-the-air protocol message by
  the application of the sender to its reception by that of the receiver.
* **Cloud load**: number of messages M2 processed by the cloud server per second.
* **Success ratio**: fraction of the started sessions that are completed within 1 s.
* Radio KPIs recorded by Simu5G: SINR, CQI, HARQ error rates, MAC packet loss.

## Results

Results of the campaign at the 128-bit level (320 runs). Mean over ten seeds (latency: mean ± 95 % confidence
interval of the mean, Student t; loss: all messages of the ten seeds, with the 95 % Wilson interval, since fewer
than ten protocol messages are lost per run on average). `analysis/summary5g.json` and `analysis/summary5g.csv`
contain all metrics, `figs/results5g.png` the figure and `figs/tarragona_sim5g.png` the scenario
(`python3 analysis/readme5g.py analysis/summary5g.json` prints the tables below).

| N | Scheme | Latency (ms) | Phase A (ms) | Phase B (ms) | Phase B share | Loss (95 % interval) | Success | CS load (msg/s) |
|---|--------|-------------:|-------------:|-------------:|--------------:|-----:|--------:|----------------:|
| 20 | FogRoam (A+B) | 12.94 ± 0.12 | 31.67 | 9.73 | 85.3 % | 0.11 % (0.06–0.21) | 99.8 % | 0.098 |
| 20 | FogRoam (A only) | 31.25 ± 0.10 | 31.25 | – | 0.0 % | 0.09 % (0.04–0.18) | 99.8 % | 0.664 |
| 20 | Chen et al. | 30.71 ± 0.12 | 30.71 | – | 0.0 % | 0.20 % (0.12–0.33) | 99.6 % | 0.666 |
| 40 | FogRoam (A+B) | 13.32 ± 0.16 | 31.70 | 10.12 | 85.1 % | 0.15 % (0.10–0.22) | 99.7 % | 0.197 |
| 40 | FogRoam (A only) | 31.51 ± 0.15 | 31.51 | – | 0.0 % | 0.18 % (0.13–0.26) | 99.6 % | 1.328 |
| 40 | Chen et al. | 30.91 ± 0.13 | 30.91 | – | 0.0 % | 0.18 % (0.13–0.26) | 99.6 % | 1.325 |
| 60 | FogRoam (A+B) | 13.09 ± 0.08 | 32.23 | 10.10 | 86.4 % | 0.22 % (0.17–0.29) | 99.6 % | 0.270 |
| 60 | FogRoam (A only) | 31.69 ± 0.10 | 31.69 | – | 0.0 % | 0.20 % (0.15–0.27) | 99.6 % | 1.996 |
| 60 | Chen et al. | 31.07 ± 0.05 | 31.07 | – | 0.0 % | 0.16 % (0.12–0.22) | 99.7 % | 1.999 |
| 80 | FogRoam (A+B) | 13.47 ± 0.06 | 32.45 | 10.36 | 85.9 % | 0.22 % (0.17–0.27) | 99.6 % | 0.374 |
| 80 | FogRoam (A only) | 31.84 ± 0.06 | 31.84 | – | 0.0 % | 0.21 % (0.16–0.26) | 99.6 % | 2.659 |
| 80 | Chen et al. | 31.23 ± 0.10 | 31.23 | – | 0.0 % | 0.23 % (0.18–0.28) | 99.5 % | 2.664 |
| 100 | FogRoam (A+B) | 13.26 ± 0.15 | 32.32 | 10.12 | 85.8 % | 0.17 % (0.13–0.21) | 99.7 % | 0.471 |
| 100 | FogRoam (A only) | 31.76 ± 0.05 | 31.76 | – | 0.0 % | 0.16 % (0.12–0.20) | 99.7 % | 3.324 |
| 100 | Chen et al. | 31.14 ± 0.07 | 31.14 | – | 0.0 % | 0.18 % (0.14–0.23) | 99.6 % | 3.327 |
| 120 | FogRoam (A+B) | 13.06 ± 0.22 | 32.30 | 10.07 | 86.5 % | 0.18 % (0.15–0.23) | 99.6 % | 0.537 |
| 120 | FogRoam (A only) | 31.80 ± 0.13 | 31.80 | – | 0.0 % | 0.20 % (0.16–0.24) | 99.6 % | 3.992 |
| 120 | Chen et al. | 31.08 ± 0.07 | 31.08 | – | 0.0 % | 0.20 % (0.16–0.24) | 99.6 % | 3.994 |

Compared with the baseline, FogRoam reduces the mean authentication latency by 56.9–58.0 % (mean 57.5 %) and the load of the cloud server by 85.1–86.6 % (mean 85.9 %).

Radio KPIs averaged over all runs of `Proposed`: uplink SINR 21.5 dB, downlink SINR 43.7 dB, uplink CQI 11.6, downlink CQI 14.3, first-transmission block error rate 18.8 % (uplink) and 2.0 % (downlink), residual MAC loss after HARQ 0.30 % (uplink) and 0.00 % (downlink), CAM delivery ratio 99.45 % with a mean delay of 8.57 ms.

Handover-triggered sessions (`ProposedHO`, `BaselineHO`; a session starts when the vehicle joins, when its serving gNB changes, and when its last phase A is older than 300 s):

| N | Scheme | Latency (ms) | After handover (ms) | Phase B share | Loss | Success | CS load (msg/s) |
|---|--------|-------------:|--------------------:|--------------:|-----:|--------:|----------------:|
| 20 | FogRoam (A+B) | 18.49 ± 0.51 | 15.29 ± 0.64 | 79.6 % | 0.51 % | 99.0 % | 0.100 |
| 20 | Chen et al. | 34.44 ± 0.79 | 35.31 ± 1.00 | 0.0 % | 0.94 % | 98.1 % | 0.492 |
| 40 | FogRoam (A+B) | 18.53 ± 0.56 | 15.54 ± 0.74 | 80.8 % | 0.63 % | 98.7 % | 0.203 |
| 40 | Chen et al. | 34.24 ± 0.40 | 35.02 ± 0.50 | 0.0 % | 0.91 % | 98.2 % | 0.990 |
| 60 | FogRoam (A+B) | 18.47 ± 0.44 | 15.40 ± 0.57 | 80.8 % | 0.83 % | 98.3 % | 0.285 |
| 60 | Chen et al. | 34.49 ± 0.38 | 35.28 ± 0.46 | 0.0 % | 1.08 % | 97.9 % | 1.403 |
| 80 | FogRoam (A+B) | 18.92 ± 0.26 | 15.97 ± 0.35 | 81.2 % | 0.96 % | 98.1 % | 0.393 |
| 80 | Chen et al. | 34.91 ± 0.36 | 35.63 ± 0.39 | 0.0 % | 1.13 % | 97.8 % | 2.008 |
| 100 | FogRoam (A+B) | 19.68 ± 0.41 | 16.39 ± 0.54 | 77.9 % | 0.82 % | 98.4 % | 0.505 |
| 100 | Chen et al. | 34.95 ± 0.41 | 35.98 ± 0.51 | 0.0 % | 1.03 % | 98.0 % | 2.173 |
| 120 | FogRoam (A+B) | 19.23 ± 0.36 | 15.95 ± 0.46 | 79.0 % | 0.96 % | 98.1 % | 0.564 |
| 120 | Chen et al. | 34.73 ± 0.43 | 35.58 ± 0.50 | 0.0 % | 0.94 % | 98.1 % | 2.546 |

Phase-A re-validation interval with handover-triggered sessions, 60 vehicles:

| Interval | Phase B share | Latency (ms) | CS load (msg/s) |
|---------:|--------------:|-------------:|----------------:|
| 150 s | 69.7 % | 20.71 | 0.517 |
| 300 s | 80.8 % | 18.47 | 0.285 |
| 600 s | 83.2 % | 18.22 | 0.239 |

![Results](figs/results5g.png)

## Layout

```
fogroam5g/   OMNeT++ project (src/): AkaVehicleApp5G, AkaFogApp5G, AkaCloudApp5G, AkaMessages5G.msg,
             network Tarragona5G; build with build/build5g.sh
scenario/    omnetpp.ini, address plan, SUMO inputs, run.sh, runset.py
map/         OpenStreetMap extract and prepare_map.sh
analysis/    parse5g.py (aggregation), report5g.py and readme5g.py (numbers of the paper and of this README),
             make_fig5g.py and make_tex5g.py (result figures), make_map5g.py (scenario figure), vecstats.py
bench/       bench256.c (operation timings at the 128-bit level), ops128.json (measured times),
             sim_delays5g.py and costs128.py (costs, message sizes, and processing delays of Tables V and VI),
             bench_pairing.c and costs_ho.py (pairing, Chebyshev, and handover costs of Table VII)
build/       fetch.sh, build.sh, fetch5g.sh, build5g.sh
results/     OMNeT++ scalar results of all 320 runs of the 128-bit campaign (.sca.gz); snapshot/ for the scenario figure
figs/        result and scenario figures
```

## Earlier IEEE 802.11p version

The GitHub repository also contains, in `ieee80211p/`, an earlier simulation of the same
scenario with Veins and IEEE 802.11p roadside units instead of a 5G NR network. With
802.11p, FogRoam reduces the authentication latency by 63–68 % and the load of the cloud
server by 71–77 % compared with the baseline, at packet loss rates of 2.3–6.9 %.
