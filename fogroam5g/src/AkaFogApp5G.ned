package fogroam5g;

import inet.applications.contract.IApp;

//
// Fog node F_j, co-located with gNB j (single FIFO CPU). Phase A: M1 -> M2 to the cloud,
// M3 -> M4 to the vehicle; phase B: M5 -> M6 without the cloud. The fog node keeps a
// short-lived record of each pending phase-A session (vehicle address and port), keyed by
// the request identifier (vehicle, session) that M2 and M3 carry, until M3 arrives.
//
simple AkaFogApp5G like IApp
{
    parameters:
        @class(fogroam5g::AkaFogApp5G);
        @display("i=block/app");
        int localPort = default(4000);
        int cloudPort = default(4000);
        string cloudModule = default("cloud");
        int m2Bits;
        int m4Bits;
        int m6Bits = default(0);
        double cF1 @unit(s);                        // computation between M1 and M2
        double cF2 @unit(s);                        // computation between M3 and M4
        double cFH @unit(s) = default(0s);          // computation between M5 and M6
        double measureStart @unit(s) = default(300s);
        double measureEnd @unit(s) = default(898s);
    gates:
        input socketIn @labels(UdpControlInfo/up);
        output socketOut @labels(UdpControlInfo/down);
}
