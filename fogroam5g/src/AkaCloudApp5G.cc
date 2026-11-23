#include "AkaCloudApp5G.h"

#include "inet/common/packet/Packet.h"
#include "inet/networklayer/common/L3AddressTag_m.h"
#include "inet/transportlayer/common/L4PortTag_m.h"

using namespace omnetpp;

namespace fogroam5g {

Define_Module(AkaCloudApp5G);

AkaCloudApp5G::~AkaCloudApp5G()
{
    for (cMessage *job : jobs) {
        delete static_cast<Job *>(job->getContextPointer());
        cancelAndDelete(job);
    }
}

void AkaCloudApp5G::initialize(int stage)
{
    if (stage == inet::INITSTAGE_LOCAL) {
        localPort = par("localPort");
        m3Bits = par("m3Bits");
        cCS = par("cCS");
        measureStart = par("measureStart");
        measureEnd = par("measureEnd");
    }
    else if (stage == inet::INITSTAGE_APPLICATION_LAYER) {
        socket.setOutputGate(gate("socketOut"));
        socket.setCallback(this);
        socket.bind(localPort);
    }
}

void AkaCloudApp5G::handleMessage(cMessage *msg)
{
    if (msg->isSelfMessage()) {
        Job *job = static_cast<Job *>(msg->getContextPointer());
        job->msg->setGenTime(simTime());
        socket.sendTo(new inet::Packet("M3", job->msg), job->dest, job->port);
        jobs.erase(msg);
        delete job;
        delete msg;
    }
    else if (socket.belongsToSocket(msg))
        socket.processMessage(msg);
    else
        delete msg;
}

void AkaCloudApp5G::socketDataArrived(inet::UdpSocket *, inet::Packet *packet)
{
    auto m2 = packet->peekAtFront<AkaPacket>();
    if (m2->getMsgType() == 2) {
        // Q2, K2, C2, k_ic, tau_i, x3, R3, Z_FC, Z_VC, h_2, SK, d_1, N_f; then M3 to F_j
        auto m3 = inet::makeShared<AkaPacket>();
        m3->setChunkLength(inet::B(m3Bits / 8));
        m3->setMsgType(3);
        m3->setSessionId(m2->getSessionId());
        m3->setVehicleId(m2->getVehicleId());
        m3->setFogIndex(m2->getFogIndex());
        m3->setSessionStart(m2->getSessionStart());
        cMessage *job = new cMessage("cloudJob");
        job->setContextPointer(new Job{m3, packet->getTag<inet::L3AddressInd>()->getSrcAddress(),
                                       packet->getTag<inet::L4PortInd>()->getSrcPort()});
        jobs.insert(job);
        simtime_t start = std::max(simTime(), cpuBusyUntil);
        cpuBusyUntil = start + cCS;
        scheduleAt(cpuBusyUntil, job);
        processed++;
        if (m2->getSessionStart() >= measureStart && m2->getSessionStart() <= measureEnd)
            processedWin++;
    }
    delete packet;
}

void AkaCloudApp5G::socketErrorArrived(inet::UdpSocket *, inet::Indication *indication)
{
    delete indication;
}

void AkaCloudApp5G::finish()
{
    recordScalar("akaProcessed", processed);
    recordScalar("akaProcessedWin", processedWin);
    recordScalar("akaWindow", (measureEnd - measureStart).dbl());
}

} // namespace fogroam5g
