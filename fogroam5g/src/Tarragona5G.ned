package fogroam5g;

import inet.networklayer.configurator.ipv4.Ipv4NetworkConfigurator;
import inet.networklayer.ipv4.RoutingTableRecorder;
import inet.node.inet.Router;
import inet.node.inet.StandardHost;
import ned.DatarateChannel;
import org.car2x.veins.subprojects.veins_inet.VeinsInetManagerForker;
import simu5g.common.binder.Binder;
import simu5g.common.carrierAggregation.CarrierAggregation;
import simu5g.nodes.NR.gNodeB;
import simu5g.nodes.Upf;
import simu5g.nodes.cars.NRCar;
import simu5g.world.radio.LteChannelControl;

//
// 5G NR standalone network of the Tarragona scenario: numFog gNBs, each with a co-located fog
// node behind the user-plane function of the edge site (5 us links), an X2 full mesh between
// the gNBs, and the cloud server behind a 1 Gbps backhaul with 10 ms delay. Vehicles (NR UEs)
// are created and removed by the Veins manager, which starts SUMO.
//
network Tarragona5G
{
    parameters:
        double playgroundSizeX @unit(m);
        double playgroundSizeY @unit(m);
        double playgroundSizeZ @unit(m);
        int numFog = default(4);
        @display("bgb=3700,2000");
    types:
        channel EdgeLink extends DatarateChannel
        {
            datarate = 10Gbps;
            delay = 5us;
        }
        channel Backhaul extends DatarateChannel
        {
            datarate = 1Gbps;
            delay = 10ms;
        }
    submodules:
        routingRecorder: RoutingTableRecorder {
            @display("p=100,100;is=s");
        }
        configurator: Ipv4NetworkConfigurator {
            @display("p=100,200");
        }
        veinsManager: VeinsInetManagerForker {
            @display("p=100,300;is=s");
        }
        channelControl: LteChannelControl {
            @display("p=100,400;is=s");
        }
        binder: Binder {
            @display("p=100,500;is=s");
        }
        carrierAggregation: CarrierAggregation {
            @display("p=100,600;is=s");
        }
        upf: Upf {
            @display("p=1850,200");
        }
        edgeRouter: Router {
            @display("p=2150,200");
        }
        cloud: StandardHost {
            @display("p=2450,100;i=device/server2");
        }
        gnb[numFog]: gNodeB {
            @display("is=vl");
        }
        fog[numFog]: StandardHost {
            @display("i=device/server");
        }
        car[0]: NRCar;
    connections allowunconnected:
        upf.filterGate <--> EdgeLink <--> edgeRouter.pppg++;
        edgeRouter.pppg++ <--> Backhaul <--> cloud.pppg++;
        for i=0..numFog-1 {
            upf.pppg++ <--> EdgeLink <--> gnb[i].ppp;
            edgeRouter.pppg++ <--> EdgeLink <--> fog[i].pppg++;
        }
        // X2 full mesh; the interface of gnb[i] towards gnb[j] is x2ppp<k>, k = index of the
        // x2 gate, as used by the connectAddress parameters in omnetpp.ini
        for i=0..numFog-1, for j=i+1..numFog-1 {
            gnb[i].x2++ <--> EdgeLink <--> gnb[j].x2++;
        }
}
