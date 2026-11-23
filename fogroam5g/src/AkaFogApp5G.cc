#include "AkaFogApp5G.h"

#include "AkaMessages5G_m.h"
#include "inet/common/packet/Packet.h"
#include "inet/networklayer/common/L3AddressResolver.h"
#include "inet/networklayer/common/L3AddressTag_m.h"
#include "inet/transportlayer/common/L4PortTag_m.h"

using namespace omnetpp;

namespace fogroam5g {

Define_Module(AkaFogApp5G);

AkaFogApp5G::~AkaFogApp5G()
{
    // computations still running at the end of the simulation
    for (cMessage *job : jobs) {
        delete static_cast<Job *>(job->getContextPointer());
        cancelAndDelete(job);
    }
}

void AkaFogApp5G::initialize(int stage)
{
    if (stage == inet::INITSTAGE_LOCAL) {
        localPort = par("localPort");
        cloudPort = par("cloudPort");
        m2Bits = par("m2Bits");
        m4Bits = par("m4Bits");
        m6Bits = par("m6Bits");
        cF1 = par("cF1");
        cF2 = par("cF2");
        cFH = par("cFH");
        measureStart = par("measureStart");
        measureEnd = par("measureEnd");
        reqDelayVec[0].setName("akaReqDelayA");
        reqDelayVec[1].setName("akaReqDelayB");
        camDelayVec.setName("akaCamDelay");
    }
    else if (stage == inet::INITSTAGE_APPLICATION_LAYER) {
        socket.setOutputGate(gate("socketOut"));
        socket.setCallback(this);
        socket.bind(localPort);
        cloudAddr = inet::L3AddressResolver().resolve(par("cloudModule").stringValue());
    }
}

simtime_t AkaFogApp5G::cpuSchedule(simtime_t cost)
{
    simtime_t start = std::max(simTime(), cpuBusyUntil);
    cpuBusyUntil = start + cost;
    return cpuBusyUntil;
}

void AkaFogApp5G::schedule(const inet::Ptr<AkaPacket>& msg, const char *name, const inet::L3Address& dest, int port, simtime_t cost)
{
    cMessage *job = new cMessage("fogJob");
    job->setContextPointer(new Job{msg, name, dest, port});
    jobs.insert(job);
    scheduleAt(cpuSchedule(cost), job);
}

void AkaFogApp5G::handleMessage(cMessage *msg)
{
    if (msg->isSelfMessage()) {
        Job *job = static_cast<Job *>(msg->getContextPointer());
        int type = job->msg->getMsgType();
        if ((type == 4 || type == 6) && inWindow(job->msg->getSessionStart()))
            sentResp[type == 6 ? 1 : 0]++;
        // the generation time is that of the transmission, after the computation
        job->msg->setGenTime(simTime());
        socket.sendTo(new inet::Packet(job->name.c_str(), job->msg), job->dest, job->port);
        jobs.erase(msg);
        delete job;
        delete msg;
    }
    else if (socket.belongsToSocket(msg))
        socket.processMessage(msg);
    else
        delete msg;
}

void AkaFogApp5G::socketDataArrived(inet::UdpSocket *, inet::Packet *packet)
{
    auto m = packet->peekAtFront<AkaPacket>();
    int type = m->getMsgType();
    inet::L3Address src = packet->getTag<inet::L3AddressInd>()->getSrcAddress();
    int srcPort = packet->getTag<inet::L4PortInd>()->getSrcPort();
    double delay = (simTime() - m->getGenTime()).dbl();

    auto reply = [&](int replyType, int bits) {
        auto chunk = inet::makeShared<AkaPacket>();
        chunk->setChunkLength(inet::B(bits / 8));
        chunk->setMsgType(replyType);
        chunk->setSessionId(m->getSessionId());
        chunk->setVehicleId(m->getVehicleId());
        chunk->setFogIndex(getParentModule()->getIndex());
        chunk->setSessionStart(m->getSessionStart());
        return chunk;
    };

    if (type == 20) {   // CAM
        if (inWindow(m->getGenTime())) {
            camRecv++;
            sumCamDelay += delay;
            camDelayVec.record(delay);
        }
    }
    else if (type == 1 || type == 5) {
        int k = type == 5 ? 1 : 0;
        if (inWindow(m->getSessionStart())) {
            recvReq[k]++;
            sumReqDelay[k] += delay;
            reqDelayVec[k].record(delay);
        }
        if (type == 1) {
            // Q1, K1, C1, VID_i not revoked, k_ij, sigma_1, x2, R2, Q2, K2, C2; then M2 to CS
            pending[{m->getVehicleId(), m->getSessionId()}] = Pending{src, srcPort, simTime()};
            schedule(reply(2, m2Bits), "M2", cloudAddr, cloudPort, cF1);
        }
        else {
            // Q4, K3, C3, VID_i not revoked, k_ik, sigma_4, x5, R5, Z, SK', d5; then M6
            schedule(reply(6, m6Bits), "M6", src, srcPort, cFH);
        }
    }
    else if (type == 3) {
        auto it = pending.find({m->getVehicleId(), m->getSessionId()});
        if (it != pending.end()) {
            // Z_FC, h_2, SK from N_f, d_1, d_3; then M4 to V_i
            schedule(reply(4, m4Bits), "M4", it->second.vehicleAddr, it->second.vehiclePort, cF2);
            pending.erase(it);
        }
        else
            lostRecords++;
    }
    // records of sessions whose M3 never arrived expire after a timeout
    for (auto it = pending.begin(); it != pending.end();) {
        if (simTime() - it->second.created > 2)
            it = pending.erase(it);
        else
            ++it;
    }
    delete packet;
}

void AkaFogApp5G::socketErrorArrived(inet::UdpSocket *, inet::Indication *indication)
{
    delete indication;
}

void AkaFogApp5G::finish()
{
    const char *ph[2] = {"A", "B"};
    for (int k = 0; k < 2; k++) {
        std::string p = ph[k];
        recordScalar(("akaRecvReq" + p).c_str(), recvReq[k]);
        recordScalar(("akaSentResp" + p).c_str(), sentResp[k]);
        recordScalar(("akaSumReqDelay" + p).c_str(), sumReqDelay[k]);
    }
    recordScalar("akaCamRecv", camRecv);
    recordScalar("akaSumCamDelay", sumCamDelay);
    recordScalar("akaLostRecords", lostRecords);
}

} // namespace fogroam5g
