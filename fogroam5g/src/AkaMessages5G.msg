//
// Payload of the UDP datagrams that emulate the messages of the authentication
// protocols (FogRoam phases A and B, and the protocol of Chen et al.) and the
// background CAMs. The chunk length is set to the size of the emulated message.
//
//   1 = M1 (V->F, phase A)      2 = M2 (F->CS)      3 = M3 (CS->F)
//   4 = M4 (F->V, phase A)      5 = M5 (V->F, phase B)
//   6 = M6 (F->V, phase B)     20 = CAM (V->F)
//
import inet.common.INETDefs;
import inet.common.packet.chunk.Chunk;

namespace fogroam5g;

class AkaPacket extends inet::FieldsChunk
{
    int msgType;
    long sessionId;             // session counter of the vehicle
    int vehicleId;              // module id of the vehicle
    int fogIndex;               // fog node of the session
    omnetpp::simtime_t sessionStart;   // time at which V_i started the session
    omnetpp::simtime_t genTime;        // time at which this message was sent
}
