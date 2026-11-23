#ifndef FOGROAM5G_AKACLOUDAPP5G_H
#define FOGROAM5G_AKACLOUDAPP5G_H

#include <set>
#include "inet/common/INETDefs.h"
#include "inet/networklayer/common/L3Address.h"
#include "inet/transportlayer/contract/udp/UdpSocket.h"
#include "AkaMessages5G_m.h"

namespace fogroam5g {

/** Cloud server CS: receives M2, computes, and returns M3 to the fog node (single FIFO CPU). */
class AkaCloudApp5G : public omnetpp::cSimpleModule, public inet::UdpSocket::ICallback
{
  public:
    ~AkaCloudApp5G() override;

  protected:
    int numInitStages() const override { return inet::NUM_INIT_STAGES; }
    void initialize(int stage) override;
    void handleMessage(omnetpp::cMessage *msg) override;
    void finish() override;

    void socketDataArrived(inet::UdpSocket *socket, inet::Packet *packet) override;
    void socketErrorArrived(inet::UdpSocket *socket, inet::Indication *indication) override;
    void socketClosed(inet::UdpSocket *socket) override {}

    struct Job {
        inet::Ptr<AkaPacket> msg;
        inet::L3Address dest;
        int port;
    };

    int localPort = 0, m3Bits = 0;
    omnetpp::simtime_t cCS, cpuBusyUntil = 0, measureStart, measureEnd;
    inet::UdpSocket socket;
    std::set<omnetpp::cMessage *> jobs;
    long processed = 0;       // all messages M2
    long processedWin = 0;    // messages M2 of sessions started in the measurement window
};

} // namespace fogroam5g

#endif
