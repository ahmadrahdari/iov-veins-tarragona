#include "veins/modules/application/aka/AkaFogRsuApp.h"

using namespace veins;

Define_Module(veins::AkaFogRsuApp);

enum { FOG_ADV_EVT = 200, FOG_SEND_M2, FOG_SEND_RESP };

AkaFogRsuApp::~AkaFogRsuApp()
{
    cancelAndDelete(advEvt);
}

void AkaFogRsuApp::initialize(int stage)
{
    DemoBaseApplLayer::initialize(stage);
    if (stage == 0) {
        m2Bits = par("m2Bits");
        m4Bits = par("m4Bits");
        m6Bits = par("m6Bits");
        advBits = par("advBits");
        cF1 = par("cF1");
        cF2 = par("cF2");
        cFH = par("cFH");
        advInterval = par("advInterval");
        measureStart = par("measureStart");
        measureEnd = par("measureEnd");
        backhaulOut = gate("backhaul$o");
        advEvt = new cMessage("fogAdvertisement", FOG_ADV_EVT);
        scheduleAt(simTime() + uniform(0, advInterval.dbl()), advEvt);
    }
}

simtime_t AkaFogRsuApp::cpuSchedule(simtime_t cost)
{
    simtime_t start = std::max(simTime(), cpuBusyUntil);
    cpuBusyUntil = start + cost;
    return cpuBusyUntil;
}

void AkaFogRsuApp::handleMessage(cMessage* msg)
{
    if (msg->getArrivalGate() == gate("backhaul$i")) {
        AkaBackhaul* m3 = check_and_cast<AkaBackhaul*>(msg);
        // compute Z_FC, SK, verify d1, compute d3, then send M4 to V_i
        AkaFrame* m4 = new AkaFrame("M4");
        populateWSM(m4, m3->getVehicleMac());
        m4->addBitLength(m4Bits);
        m4->setMsgType(4);
        m4->setSessionId(m3->getSessionId());
        m4->setVehicleMac(m3->getVehicleMac());
        m4->setRsuMac(myId);
        m4->setRsuIndex(getParentModule()->getIndex());
        m4->setSessionStart(m3->getSessionStart());
        cMessage* job = new cMessage("fogJobM4", FOG_SEND_RESP);
        job->setContextPointer(m4);
        scheduleAt(cpuSchedule(cF2), job);
        delete m3;
        return;
    }
    DemoBaseApplLayer::handleMessage(msg);
}

void AkaFogRsuApp::onWSM(BaseFrame1609_4* wsm)
{
    AkaFrame* f = dynamic_cast<AkaFrame*>(wsm);
    if (!f || f->getRecipientAddress() != myId) return;
    if (f->getMsgType() == 1) {
        if (inWindow(f->getSessionStart())) {
            recvReq[0]++;
            sumReqDelay[0] += (simTime() - f->getGenTime()).dbl();
        }
        // compute Q1, K1, decrypt C1, verify sigma_1, R2, Q2, K2, C2, then send M2 to CS
        AkaBackhaul* m2 = new AkaBackhaul("M2");
        m2->setBitLength(m2Bits);
        m2->setMsgType(2);
        m2->setSessionId(f->getSessionId());
        m2->setVehicleMac(f->getVehicleMac());
        m2->setRsuIndex(getParentModule()->getIndex());
        m2->setSessionStart(f->getSessionStart());
        cMessage* job = new cMessage("fogJobM2", FOG_SEND_M2);
        job->setContextPointer(m2);
        scheduleAt(cpuSchedule(cF1), job);
    }
    else if (f->getMsgType() == 5) {
        if (inWindow(f->getSessionStart())) {
            recvReq[1]++;
            sumReqDelay[1] += (simTime() - f->getGenTime()).dbl();
        }
        // compute Q4, K3, decrypt C3, k_ik, verify sigma_4, R5, Z, SK', d5, then send M6
        AkaFrame* m6 = new AkaFrame("M6");
        populateWSM(m6, f->getVehicleMac());
        m6->addBitLength(m6Bits);
        m6->setMsgType(6);
        m6->setSessionId(f->getSessionId());
        m6->setVehicleMac(f->getVehicleMac());
        m6->setRsuMac(myId);
        m6->setRsuIndex(getParentModule()->getIndex());
        m6->setSessionStart(f->getSessionStart());
        cMessage* job = new cMessage("fogJobM6", FOG_SEND_RESP);
        job->setContextPointer(m6);
        scheduleAt(cpuSchedule(cFH), job);
    }
}

void AkaFogRsuApp::handleSelfMsg(cMessage* msg)
{
    switch (msg->getKind()) {
    case FOG_ADV_EVT: {
        AkaFrame* adv = new AkaFrame("FogAdv");
        populateWSM(adv);
        adv->addBitLength(advBits);
        adv->setMsgType(10);
        adv->setRsuMac(myId);
        adv->setRsuIndex(getParentModule()->getIndex());
        adv->setGenTime(simTime());
        sendDown(adv);
        scheduleAt(simTime() + advInterval, advEvt);
        break;
    }
    case FOG_SEND_M2: {
        AkaBackhaul* m2 = static_cast<AkaBackhaul*>(msg->getContextPointer());
        m2->setGenTime(simTime());
        send(m2, backhaulOut);
        delete msg;
        break;
    }
    case FOG_SEND_RESP: {
        AkaFrame* r = static_cast<AkaFrame*>(msg->getContextPointer());
        r->setGenTime(simTime());
        if (inWindow(r->getSessionStart())) sentResp[r->getMsgType() == 6 ? 1 : 0]++;
        sendDown(r);
        delete msg;
        break;
    }
    default:
        DemoBaseApplLayer::handleSelfMsg(msg);
        break;
    }
}

void AkaFogRsuApp::finish()
{
    DemoBaseApplLayer::finish();
    const char* ph[2] = {"A", "B"};
    for (int k = 0; k < 2; k++) {
        recordScalar((std::string("akaRecvReq") + ph[k]).c_str(), recvReq[k]);
        recordScalar((std::string("akaSentResp") + ph[k]).c_str(), sentResp[k]);
        recordScalar((std::string("akaSumReqDelay") + ph[k]).c_str(), sumReqDelay[k]);
    }
}
