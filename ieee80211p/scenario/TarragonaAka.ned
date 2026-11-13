//
// Tarragona (Spain) city-centre scenario for evaluating the authentication
// and key agreement protocols over IEEE 802.11p (Veins 5.3.1, SUMO 1.20).
//
import org.car2x.veins.base.connectionManager.ConnectionManager;
import org.car2x.veins.base.modules.BaseWorldUtility;
import org.car2x.veins.modules.mobility.traci.TraCIScenarioManagerForker;
import org.car2x.veins.modules.obstacle.ObstacleControl;
import org.car2x.veins.modules.world.annotations.AnnotationManager;
import org.car2x.veins.nodes.Car;
import org.car2x.veins.modules.application.aka.FogRSU;
import org.car2x.veins.modules.application.aka.CloudServer;

channel Backhaul extends ned.DatarateChannel
{
    datarate = 1Gbps;
}

network TarragonaAka
{
    parameters:
        double playgroundSizeX @unit(m);
        double playgroundSizeY @unit(m);
        double playgroundSizeZ @unit(m);
        int numRsu = default(4);
        double backhaulDelay @unit(s) = default(10ms);
        @display("bgb=dropUnit($playgroundSizeX),dropUnit($playgroundSizeY)");
    submodules:
        obstacles: ObstacleControl;
        annotations: AnnotationManager;
        connectionManager: ConnectionManager;
        world: BaseWorldUtility {
            playgroundSizeX = parent.playgroundSizeX;
            playgroundSizeY = parent.playgroundSizeY;
            playgroundSizeZ = parent.playgroundSizeZ;
        }
        manager: TraCIScenarioManagerForker;
        rsu[numRsu]: FogRSU;
        cloud: CloudServer;
        node[0]: Car;
    connections allowunconnected:
        for i=0..numRsu-1 {
            rsu[i].backhaul <--> Backhaul { delay = parent.backhaulDelay; } <--> cloud.port++;
        }
}
