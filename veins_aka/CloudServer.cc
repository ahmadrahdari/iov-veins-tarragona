#include "veins/modules/application/aka/CloudServer.h"

using namespace veins;

Define_Module(veins::CloudServer);

void CloudServer::initialize()
{
    m3Bits = par("m3Bits");
    cCS = par("cCS");
}

void CloudServer::handleMessage(cMessage* msg)
{
    if (msg->isSelfMessage()) {
        AkaBackhaul* m3 = static_cast<AkaBackhaul*>(msg->getContextPointer());
        int port = m3->getRsuIndex();
        m3->setGenTime(simTime());
        send(m3, "port$o", port);
        delete msg;
        return;
    }
    AkaBackhaul* m2 = check_and_cast<AkaBackhaul*>(msg);
    // verify C2 (F_j) and A_i (V_i), compute R3, Z_FC, Z_VC, SK, d1, N_c
    AkaBackhaul* m3 = new AkaBackhaul("M3");
    m3->setBitLength(m3Bits);
    m3->setMsgType(3);
    m3->setSessionId(m2->getSessionId());
    m3->setVehicleMac(m2->getVehicleMac());
    m3->setRsuIndex(m2->getArrivalGate()->getIndex());
    m3->setSessionStart(m2->getSessionStart());
    simtime_t start = std::max(simTime(), cpuBusyUntil);
    cpuBusyUntil = start + cCS;
    cMessage* job = new cMessage("cloudJob");
    job->setContextPointer(m3);
    scheduleAt(cpuBusyUntil, job);
    processed++;
    delete m2;
}

void CloudServer::finish()
{
    recordScalar("akaProcessed", processed);
}
