package org.car2x.veins.modules.application.aka;

import org.car2x.veins.modules.application.ieee80211p.DemoBaseApplLayer;

// Fog node attached to an RSU: phase A relays M1/M4 over the air and M2/M3
// over the backhaul; phase B (M5/M6) is answered locally without the cloud
simple AkaFogRsuApp extends DemoBaseApplLayer
{
    parameters:
        @class(veins::AkaFogRsuApp);
        int m2Bits;
        int m4Bits;
        int m6Bits = default(0);
        int advBits = default(384);               // FID_j || P_Fj
        double cF1 @unit(s);                      // computation between M1 and M2
        double cF2 @unit(s);                      // computation between M3 and M4
        double cFH @unit(s) = default(0s);        // computation between M5 and M6
        double advInterval @unit(s) = default(0.5s);
        double measureStart @unit(s) = default(25s);
        double measureEnd @unit(s) = default(148s);
    gates:
        inout backhaul;
}
