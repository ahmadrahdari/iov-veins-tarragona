package fogroam5g;

import inet.applications.contract.IApp;

//
// Vehicle V_i (NR UE). It authenticates with the fog node co-located with its serving gNB,
// which it reads from its NR physical layer, and sends CAMs to that fog node.
//
// Session triggers (authTrigger):
//  - "timer": every authInterval +- authJitter (re-keying and handovers, as in the paper);
//  - "handover": when the vehicle joins, when its serving gNB changes, and when its last
//    phase A is older than phaseAValidity (phase-A re-validation).
// With useHandover = true (FogRoam), phase A is run when the vehicle joins and whenever its
// last phase A is older than phaseAValidity, and phase B otherwise; with useHandover = false
// (FogRoam restricted to phase A, or the protocol of Chen et al.), every session is a full run.
//
simple AkaVehicleApp5G like IApp
{
    parameters:
        @class(fogroam5g::AkaVehicleApp5G);
        @display("i=block/app");
        int localPort = default(4000);
        int fogPort = default(4000);
        string fogModule = default("fog");          // fog node j is <fogModule>[j], at gNB j
        int m1Bits;                                 // size of M1 (phase A or full run)
        int m5Bits = default(0);                    // size of M5 (phase B)
        double cV1 @unit(s);                        // computation before sending M1
        double cV2 @unit(s);                        // computation after receiving M4
        double cH1 @unit(s) = default(0s);          // computation before sending M5
        double cH2 @unit(s) = default(0s);          // computation after receiving M6
        bool useHandover = default(false);          // phase B available (FogRoam)
        double phaseAValidity @unit(s) = default(300s);
        // vehicles of SUMO type "ext" enter from the map edge and were already authenticated by a
        // fog node outside the area: their last phase A is uniform in the past phaseAValidity
        bool edgeEntryHandover = default(false);
        string authTrigger = default("timer");      // "timer" or "handover"
        double authInterval @unit(s) = default(30s);
        double authJitter @unit(s) = default(7.5s);
        double hoCheckInterval @unit(s) = default(0.1s);   // polling of the serving gNB ("handover")
        double sessionTimeout @unit(s) = default(1s);
        double camInterval @unit(s) = default(0.1s);       // CAM period (0 = no CAMs)
        int camBits = default(2000);
        double measureStart @unit(s) = default(300s);
        double measureEnd @unit(s) = default(898s);
        double snapshotTime @unit(s) = default(-1s);       // records position and fog node (map figure)
    gates:
        input socketIn @labels(UdpControlInfo/up);
        output socketOut @labels(UdpControlInfo/down);
}
