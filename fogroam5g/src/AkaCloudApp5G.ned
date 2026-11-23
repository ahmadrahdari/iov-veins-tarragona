package fogroam5g;

import inet.applications.contract.IApp;

//
// Cloud server CS: processes M2 and returns M3 to the fog node (single FIFO CPU).
//
simple AkaCloudApp5G like IApp
{
    parameters:
        @class(fogroam5g::AkaCloudApp5G);
        @display("i=block/app");
        int localPort = default(4000);
        int m3Bits;
        double cCS @unit(s);
        double measureStart @unit(s) = default(300s);
        double measureEnd @unit(s) = default(898s);
    gates:
        input socketIn @labels(UdpControlInfo/up);
        output socketOut @labels(UdpControlInfo/down);
}
