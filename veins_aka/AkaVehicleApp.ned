package org.car2x.veins.modules.application.aka;

import org.car2x.veins.modules.application.ieee80211p.DemoBaseApplLayer;

// Vehicle side of the authentication protocol emulation (also sends V2V beacons)
simple AkaVehicleApp extends DemoBaseApplLayer
{
    parameters:
        @class(veins::AkaVehicleApp);
        int m1Bits;                               // size of M1 (phase A)
        int m5Bits = default(0);                  // size of M5 (phase B)
        double cV1 @unit(s);                      // computation before sending M1
        double cV2 @unit(s);                      // computation after receiving M4
        double cH1 @unit(s) = default(0s);        // computation before sending M5
        double cH2 @unit(s) = default(0s);        // computation after receiving M6
        bool useHandover = default(false);        // phase B available (proposed scheme)
        double phaseAValidity @unit(s) = default(20s); // phase A repeated after this period
        double authInterval @unit(s) = default(2s);
        double authJitter @unit(s) = default(0.5s);
        double sessionTimeout @unit(s) = default(1s);
        double advValidity @unit(s) = default(1.2s);
        double measureStart @unit(s) = default(25s);
        double measureEnd @unit(s) = default(148s);
}
