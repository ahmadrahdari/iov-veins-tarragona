#ifndef FOGROAM5G_AKAVEHICLEAPP5G_H
#define FOGROAM5G_AKAVEHICLEAPP5G_H

#include <vector>
#include "inet/common/INETDefs.h"
#include "inet/networklayer/common/L3Address.h"
#include "inet/transportlayer/contract/udp/UdpSocket.h"

class LtePhyUe;
namespace veins { class VeinsInetMobility; }

namespace fogroam5g {

/**
 * Vehicle V_i: authenticates with the fog node of its serving gNB (phase A, phase B, or a
 * full run of the protocol of Chen et al.) and sends CAMs to it. Statistics are collected
 * for the sessions started inside [measureStart, measureEnd].
 */
class AkaVehicleApp5G : public omnetpp::cSimpleModule, public inet::UdpSocket::ICallback
{
  public:
    ~AkaVehicleApp5G() override;

  protected:
    int numInitStages() const override { return inet::NUM_INIT_STAGES; }
    void initialize(int stage) override;
    void handleMessage(omnetpp::cMessage *msg) override;
    void finish() override;

    void socketDataArrived(inet::UdpSocket *socket, inet::Packet *packet) override;
    void socketErrorArrived(inet::UdpSocket *socket, inet::Indication *indication) override;
    void socketClosed(inet::UdpSocket *socket) override {}

    bool inWindow(omnetpp::simtime_t t) const { return t >= measureStart && t <= measureEnd; }
    int servingFog() const;                 // fog index of the serving gNB, -1 if detached
    inet::L3Address fogAddress(int fog);
    void startSession(int fog);
    void sendRequest();
    void sendCam();
    void checkTriggers();
    int numFog() const;

    // parameters
    int localPort = 0, fogPort = 0, m1Bits = 0, m5Bits = 0, camBits = 0;
    bool useHandover = false, handoverTrigger = false;
    omnetpp::simtime_t cV1, cV2, cH1, cH2, phaseAValidity, authInterval, authJitter, hoCheckInterval;
    omnetpp::simtime_t sessionTimeout, camInterval, measureStart, measureEnd, snapshotTime;
    std::string fogModule;

    inet::UdpSocket socket;
    LtePhyUe *nrPhy = nullptr;
    veins::VeinsInetMobility *mobility = nullptr;
    std::vector<inet::L3Address> fogAddr;

    // protocol state
    omnetpp::simtime_t lastPhaseA = -1;     // completion time of the last phase A
    bool phaseADone = false;                // a phase A has been completed (possibly outside the area)
    bool edgeEntry = false;                 // vehicle entered from the map edge (SUMO type "ext")
    int prevFog = -1;                       // fog node of the previous session (statistics)
    int authFog = -1;                       // fog node of the last completed session ("handover")
    bool busy = false;
    int curPhase = 0;                       // 1 = phase A or full run, 2 = phase B
    bool curHandover = false;               // the session follows a change of fog node
    int curFog = -1;
    long sessionCounter = 0, curSession = -1;
    omnetpp::simtime_t curStart;

    omnetpp::cMessage *authEvt = nullptr, *sendEvt = nullptr, *doneEvt = nullptr;
    omnetpp::cMessage *timeoutEvt = nullptr, *camEvt = nullptr, *snapEvt = nullptr;

    // statistics; index 0 = phase A (or full run), 1 = phase B
    long sentReq[2] = {0, 0}, recvResp[2] = {0, 0};
    long started[2] = {0, 0}, completed[2] = {0, 0}, timedOut[2] = {0, 0};
    double sumAuthLatency[2] = {0, 0}, sumRespDelay[2] = {0, 0};
    long completedHo[2] = {0, 0};           // completed sessions that follow a handover
    double sumAuthLatencyHo[2] = {0, 0};
    long handovers = 0, handoversPh[2] = {0, 0}, entryHandoversPh[2] = {0, 0};
    long skippedDetached = 0, camSent = 0;
    bool snapTaken = false;
    double snapX = 0, snapY = 0;
    int snapFog = -1;
    omnetpp::cOutVector authLatencyVec;
};

} // namespace fogroam5g

#endif
