#include "veins/modules/application/aka/AkaVehicleApp.h"

using namespace veins;

Define_Module(veins::AkaVehicleApp);

enum { AKA_AUTH_EVT = 100, AKA_SEND_REQ, AKA_DONE, AKA_TIMEOUT };

AkaVehicleApp::~AkaVehicleApp()
{
    cancelAndDelete(authEvt);
    cancelAndDelete(sendEvt);
    cancelAndDelete(doneEvt);
    cancelAndDelete(timeoutEvt);
}

void AkaVehicleApp::initialize(int stage)
{
    DemoBaseApplLayer::initialize(stage);
    if (stage == 0) {
        m1Bits = par("m1Bits");
        m5Bits = par("m5Bits");
        cV1 = par("cV1");
        cV2 = par("cV2");
        cH1 = par("cH1");
        cH2 = par("cH2");
        useHandover = par("useHandover");
        phaseAValidity = par("phaseAValidity");
        authInterval = par("authInterval");
        authJitter = par("authJitter");
        sessionTimeout = par("sessionTimeout");
        advValidity = par("advValidity");
        measureStart = par("measureStart");
        measureEnd = par("measureEnd");
        authEvt = new cMessage("authEvt", AKA_AUTH_EVT);
        sendEvt = new cMessage("sendRequest", AKA_SEND_REQ);
        doneEvt = new cMessage("skEstablished", AKA_DONE);
        timeoutEvt = new cMessage("sessionTimeout", AKA_TIMEOUT);
        authLatencyVec.setName("authLatency");
        scheduleAt(simTime() + uniform(0, authInterval.dbl()), authEvt);
    }
}

void AkaVehicleApp::onWSM(BaseFrame1609_4* wsm)
{
    AkaFrame* f = dynamic_cast<AkaFrame*>(wsm);
    if (!f) return;
    if (f->getMsgType() == 10) { // fog advertisement {FID_j, P_Fj}
        rsuMac = f->getRsuMac();
        rsuIndex = f->getRsuIndex();
        lastAdv = simTime();
        return;
    }
    int expected = (curPhase == 2) ? 6 : 4;
    if (f->getMsgType() == expected && f->getRecipientAddress() == myId && busy && f->getSessionId() == curSession) {
        int k = curPhase - 1;
        if (inWindow(curStart)) {
            recvResp[k]++;
            sumRespDelay[k] += (simTime() - f->getGenTime()).dbl();
        }
        cancelEvent(timeoutEvt);
        scheduleAt(simTime() + (curPhase == 2 ? cH2 : cV2), doneEvt);
    }
}

void AkaVehicleApp::handleSelfMsg(cMessage* msg)
{
    switch (msg->getKind()) {
    case AKA_AUTH_EVT: {
        if (!busy && rsuMac >= 0 && simTime() - lastAdv <= advValidity) {
            busy = true;
            bool phaseAValid = lastPhaseA >= 0 && simTime() - lastPhaseA <= phaseAValidity;
            curPhase = (useHandover && phaseAValid) ? 2 : 1;
            curSession = ++sessionCounter;
            curStart = simTime();
            if (inWindow(curStart)) {
                started[curPhase - 1]++;
                if (sessionRsu >= 0 && sessionRsu != rsuMac) handovers++;
            }
            sessionRsu = rsuMac;
            // phase A: R1, Q1, K1, k_ij, sigma_1, A_i, C1 ; phase B: R4, Q4, K3, k_ik, sigma_4, C3
            scheduleAt(simTime() + (curPhase == 2 ? cH1 : cV1), sendEvt);
        }
        scheduleAt(simTime() + authInterval + uniform(-authJitter.dbl(), authJitter.dbl()), authEvt);
        break;
    }
    case AKA_SEND_REQ: {
        AkaFrame* req = new AkaFrame(curPhase == 2 ? "M5" : "M1");
        populateWSM(req, sessionRsu);
        req->addBitLength(curPhase == 2 ? m5Bits : m1Bits);
        req->setMsgType(curPhase == 2 ? 5 : 1);
        req->setSessionId(curSession);
        req->setVehicleMac(myId);
        req->setRsuMac(sessionRsu);
        req->setRsuIndex(rsuIndex);
        req->setSessionStart(curStart);
        req->setGenTime(simTime());
        sendDown(req);
        if (inWindow(curStart)) sentReq[curPhase - 1]++;
        scheduleAt(simTime() + sessionTimeout, timeoutEvt);
        break;
    }
    case AKA_DONE: {
        int k = curPhase - 1;
        if (curPhase == 1) lastPhaseA = simTime();
        if (inWindow(curStart)) {
            completed[k]++;
            double lat = (simTime() - curStart).dbl();
            sumAuthLatency[k] += lat;
            authLatencyVec.record(lat);
        }
        busy = false;
        break;
    }
    case AKA_TIMEOUT: {
        if (inWindow(curStart)) timedOut[curPhase - 1]++;
        busy = false;
        break;
    }
    default:
        DemoBaseApplLayer::handleSelfMsg(msg);
        break;
    }
}

void AkaVehicleApp::finish()
{
    DemoBaseApplLayer::finish();
    const char* ph[2] = {"A", "B"};
    for (int k = 0; k < 2; k++) {
        recordScalar((std::string("akaSentReq") + ph[k]).c_str(), sentReq[k]);
        recordScalar((std::string("akaRecvResp") + ph[k]).c_str(), recvResp[k]);
        recordScalar((std::string("akaStarted") + ph[k]).c_str(), started[k]);
        recordScalar((std::string("akaCompleted") + ph[k]).c_str(), completed[k]);
        recordScalar((std::string("akaTimedOut") + ph[k]).c_str(), timedOut[k]);
        recordScalar((std::string("akaSumAuthLatency") + ph[k]).c_str(), sumAuthLatency[k]);
        recordScalar((std::string("akaSumRespDelay") + ph[k]).c_str(), sumRespDelay[k]);
    }
    recordScalar("akaHandovers", handovers);
}
