//
// Messages used to emulate the authentication protocols (the proposed
// two-phase scheme and the scheme of [12]) over IEEE 802.11p and the
// fog-to-cloud wired backhaul.
//
import veins.modules.messages.BaseFrame1609_4;

namespace veins;

// Over-the-air frames
//   1 = M1 (V->F, phase A)      4 = M4 (F->V, phase A)
//   5 = M5 (V->F, phase B)      6 = M6 (F->V, phase B)
//  10 = fog advertisement {FID_j, P_Fj}
packet AkaFrame extends BaseFrame1609_4 {
    int msgType;
    long sessionId;
    long vehicleMac;
    long rsuMac;
    int rsuIndex;
    simtime_t sessionStart;   // time at which V_i started the session
    simtime_t genTime;        // generation time of this frame
}

// Wired backhaul messages: M2 (F->CS) and M3 (CS->F)
packet AkaBackhaul {
    int msgType;              // 2 = M2, 3 = M3
    long sessionId;
    long vehicleMac;
    int rsuIndex;
    simtime_t sessionStart;
    simtime_t genTime;
}
