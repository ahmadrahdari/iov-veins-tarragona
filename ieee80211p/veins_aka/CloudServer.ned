package org.car2x.veins.modules.application.aka;

// Cloud server: processes M2 and returns M3 (single FIFO CPU)
simple CloudServer
{
    parameters:
        @class(veins::CloudServer);
        @display("i=device/server2");
        int m3Bits;
        double cCS @unit(s);
        double measureStart @unit(s) = default(25s);
        double measureEnd @unit(s) = default(148s);
    gates:
        inout port[];
}
