package org.car2x.veins.modules.application.aka;

import org.car2x.veins.base.modules.*;
import org.car2x.veins.modules.nic.Nic80211p;

// RSU with a co-located fog node application and a wired backhaul port
module FogRSU
{
    parameters:
        string nicType = default("Nic80211p");
        @display("i=veins/sign/yellowdiamond;is=vs");
    gates:
        input veinsradioIn;
        inout backhaul;
    submodules:
        appl: AkaFogRsuApp {
            parameters:
                @display("p=60,50");
        }
        nic: <nicType> like org.car2x.veins.modules.nic.INic80211p {
            parameters:
                @display("p=60,166");
        }
        mobility: BaseMobility {
            parameters:
                @display("p=130,172;i=block/cogwheel");
        }
    connections:
        nic.upperLayerOut --> appl.lowerLayerIn;
        nic.upperLayerIn <-- appl.lowerLayerOut;
        nic.upperControlOut --> appl.lowerControlIn;
        nic.upperControlIn <-- appl.lowerControlOut;
        veinsradioIn --> nic.radioIn;
        appl.backhaul <--> backhaul;
}
