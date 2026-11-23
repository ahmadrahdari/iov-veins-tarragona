#ifndef FOGROAM5G_AKAFOGAPP5G_H
#define FOGROAM5G_AKAFOGAPP5G_H

#include <map>
#include <set>
#include "inet/common/INETDefs.h"
#include "inet/networklayer/common/L3Address.h"
#include "inet/transportlayer/contract/udp/UdpSocket.h"
#include "AkaMessages5G_m.h"

namespace fogroam5g {

/**
 * Fog node F_j co-located with gNB j (single FIFO CPU). Phase A relays the session to the
 * cloud (M1 -> M2, M3 -> M4); phase B is answered locally (M5 -> M6). It also receives the
 * CAMs of the vehicles in its cell.
 */
class AkaFogApp5G : public omnetpp::cSimpleModule, public inet::UdpSocket::ICallback
{
  public:
    ~AkaFogApp5G() override;

  protected:
    int numInitStages() const override { return inet::NUM_INIT_STAGES; }
    void initialize(int stage) override;
    void handleMessage(omnetpp::cMessage *msg) override;
    void finish() override;

    void socketDataArrived(inet::UdpSocket *socket, inet::Packet *packet) override;
    void socketErrorArrived(inet::UdpSocket *socket, inet::Indication *indication) override;
    void socketClosed(inet::UdpSocket *socket) override {}

    bool inWindow(omnetpp::simtime_t t) const { return t >= measureStart && t <= measureEnd; }
    omnetpp::simtime_t cpuSchedule(omnetpp::simtime_t cost);
    void schedule(const inet::Ptr<AkaPacket>& msg, const char *name, const inet::L3Address& dest, int port, omnetpp::simtime_t cost);

    struct Pending {                      // pending phase-A session, until M3 arrives
        inet::L3Address vehicleAddr;
        int vehiclePort;
        omnetpp::simtime_t created;
    };
    struct Job {                          // message to be sent when its computation ends
        inet::Ptr<AkaPacket> msg;
        std::string name;
        inet::L3Address dest;
        int port;
    };
    std::set<omnetpp::cMessage *> jobs;

    int localPort = 0, cloudPort = 0, m2Bits = 0, m4Bits = 0, m6Bits = 0;
    omnetpp::simtime_t cF1, cF2, cFH, measureStart, measureEnd, cpuBusyUntil = 0;
    inet::UdpSocket socket;
    inet::L3Address cloudAddr;
    std::map<std::pair<int, long>, Pending> pending;   // key: (vehicle, session)

    // index 0 = phase A (M1 received, M4 sent), 1 = phase B (M5 received, M6 sent)
    long recvReq[2] = {0, 0}, sentResp[2] = {0, 0};
    double sumReqDelay[2] = {0, 0};
    long camRecv = 0, lostRecords = 0;
    double sumCamDelay = 0;
    omnetpp::cOutVector reqDelayVec[2], camDelayVec;
};

} // namespace fogroam5g

#endif
