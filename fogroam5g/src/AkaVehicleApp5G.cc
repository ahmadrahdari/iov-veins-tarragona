#include "AkaVehicleApp5G.h"

#include "AkaMessages5G_m.h"
#include "inet/common/ModuleAccess.h"
#include "inet/common/packet/Packet.h"
#include "inet/networklayer/common/L3AddressResolver.h"
#include "stack/phy/layer/LtePhyUe.h"
#include "veins_inet/VeinsInetMobility.h"

using namespace omnetpp;

namespace fogroam5g {

Define_Module(AkaVehicleApp5G);

AkaVehicleApp5G::~AkaVehicleApp5G()
{
    cancelAndDelete(authEvt);
    cancelAndDelete(sendEvt);
    cancelAndDelete(doneEvt);
    cancelAndDelete(timeoutEvt);
    cancelAndDelete(camEvt);
    cancelAndDelete(snapEvt);
}

void AkaVehicleApp5G::initialize(int stage)
{
    if (stage == inet::INITSTAGE_LOCAL) {
        localPort = par("localPort");
        fogPort = par("fogPort");
        fogModule = par("fogModule").stdstringValue();
        m1Bits = par("m1Bits");
        m5Bits = par("m5Bits");
        cV1 = par("cV1");
        cV2 = par("cV2");
        cH1 = par("cH1");
        cH2 = par("cH2");
        useHandover = par("useHandover");
        phaseAValidity = par("phaseAValidity");
        std::string trigger = par("authTrigger").stdstringValue();
        if (trigger != "timer" && trigger != "handover")
            throw cRuntimeError("authTrigger must be \"timer\" or \"handover\"");
        handoverTrigger = trigger == "handover";
        authInterval = par("authInterval");
        authJitter = par("authJitter");
        hoCheckInterval = par("hoCheckInterval");
        sessionTimeout = par("sessionTimeout");
        camInterval = par("camInterval");
        camBits = par("camBits");
        measureStart = par("measureStart");
        measureEnd = par("measureEnd");
        snapshotTime = par("snapshotTime");
        authEvt = new cMessage("authEvt");
        sendEvt = new cMessage("sendRequest");
        doneEvt = new cMessage("skEstablished");
        timeoutEvt = new cMessage("sessionTimeout");
        camEvt = new cMessage("cam");
        snapEvt = new cMessage("snapshot");
        authLatencyVec.setName("akaAuthLatency");
    }
    else if (stage == inet::INITSTAGE_APPLICATION_LAYER) {
        cModule *host = inet::getContainingNode(this);
        nrPhy = check_and_cast<LtePhyUe *>(host->getSubmodule("cellularNic")->getSubmodule("nrPhy"));
        mobility = check_and_cast<veins::VeinsInetMobility *>(host->getSubmodule("mobility"));
        fogAddr.assign(numFog(), inet::L3Address());
        socket.setOutputGate(gate("socketOut"));
        socket.setCallback(this);
        socket.bind(localPort);
        // first session trigger: a random phase of the authentication period, or the polling of
        // the serving gNB
        if (handoverTrigger)
            scheduleAt(simTime() + uniform(0, hoCheckInterval.dbl()), authEvt);
        else
            scheduleAt(simTime() + uniform(0, authInterval.dbl()), authEvt);
        if (par("edgeEntryHandover").boolValue() && mobility->getVehicleCommandInterface()->getTypeId() == "ext") {
            edgeEntry = true;
            phaseADone = true;
            lastPhaseA = simTime() - uniform(0, phaseAValidity.dbl());
        }
        if (camInterval > 0)
            scheduleAt(simTime() + uniform(0, camInterval.dbl()), camEvt);
        if (snapshotTime >= simTime())
            scheduleAt(snapshotTime, snapEvt);   // draws no random number
    }
}

int AkaVehicleApp5G::numFog() const
{
    return getSystemModule()->getSubmoduleVectorSize(fogModule.c_str());
}

int AkaVehicleApp5G::servingFog() const
{
    // gNB j has macNodeId j + 1; the master id is 0 while the UE is not attached
    int master = nrPhy->getMasterId();
    int fog = master - 1;
    return (master >= 1 && fog < (int)fogAddr.size()) ? fog : -1;
}

inet::L3Address AkaVehicleApp5G::fogAddress(int fog)
{
    if (fogAddr[fog].isUnspecified())
        fogAddr[fog] = inet::L3AddressResolver().resolve((fogModule + "[" + std::to_string(fog) + "]").c_str());
    return fogAddr[fog];
}

void AkaVehicleApp5G::handleMessage(cMessage *msg)
{
    if (msg == authEvt) {
        if (handoverTrigger) {
            checkTriggers();
            scheduleAt(simTime() + hoCheckInterval, authEvt);
        }
        else {
            if (!busy) {
                int fog = servingFog();
                if (fog >= 0)
                    startSession(fog);
                else if (inWindow(simTime()))
                    skippedDetached++;
            }
            scheduleAt(simTime() + authInterval + uniform(-authJitter.dbl(), authJitter.dbl()), authEvt);
        }
    }
    else if (msg == sendEvt)
        sendRequest();
    else if (msg == doneEvt) {
        int k = curPhase - 1;
        if (curPhase == 1) {
            lastPhaseA = simTime();
            phaseADone = true;
        }
        authFog = curFog;
        if (inWindow(curStart)) {
            double lat = (simTime() - curStart).dbl();
            completed[k]++;
            sumAuthLatency[k] += lat;
            if (curHandover) {
                completedHo[k]++;
                sumAuthLatencyHo[k] += lat;
            }
            authLatencyVec.record(lat);
        }
        busy = false;
    }
    else if (msg == timeoutEvt) {
        if (inWindow(curStart))
            timedOut[curPhase - 1]++;
        busy = false;
    }
    else if (msg == camEvt) {
        sendCam();
        scheduleAt(simTime() + camInterval, camEvt);
    }
    else if (msg == snapEvt) {
        inet::Coord pos = mobility->getCurrentPosition();
        snapX = pos.x;
        snapY = pos.y;
        snapFog = servingFog();
        snapTaken = true;
    }
    else if (socket.belongsToSocket(msg))
        socket.processMessage(msg);
    else
        delete msg;
}

void AkaVehicleApp5G::checkTriggers()
{
    if (busy)
        return;
    int fog = servingFog();
    if (fog < 0)
        return;
    bool revalidate = phaseADone && simTime() - lastPhaseA > phaseAValidity;
    // joining, a change of the serving gNB (also after a failed session), or phase-A re-validation
    if (fog != authFog || revalidate)
        startSession(fog);
}

void AkaVehicleApp5G::startSession(int fog)
{
    busy = true;
    bool phaseAValid = phaseADone && simTime() - lastPhaseA <= phaseAValidity;
    curPhase = (useHandover && phaseAValid) ? 2 : 1;
    curSession = ++sessionCounter;
    curStart = simTime();
    curFog = fog;
    curHandover = prevFog >= 0 && prevFog != fog;
    int k = curPhase - 1;
    if (inWindow(curStart)) {
        started[k]++;
        if (curHandover) {
            handovers++;
            handoversPh[k]++;
        }
        else if (prevFog < 0 && edgeEntry)
            entryHandoversPh[k]++;   // arrives from a fog node outside the area
    }
    prevFog = fog;
    // phase A: x1, R1, Q1, K1, k_ij, sigma_1, tau_i, C1; phase B: x4, R4, Q4, K3, k_ik, sigma_4, C3
    scheduleAt(simTime() + (curPhase == 2 ? cH1 : cV1), sendEvt);
}

void AkaVehicleApp5G::sendRequest()
{
    bool b = curPhase == 2;
    auto chunk = inet::makeShared<AkaPacket>();
    chunk->setChunkLength(inet::B((b ? m5Bits : m1Bits) / 8));
    chunk->setMsgType(b ? 5 : 1);
    chunk->setSessionId(curSession);
    chunk->setVehicleId(getId());
    chunk->setFogIndex(curFog);
    chunk->setSessionStart(curStart);
    chunk->setGenTime(simTime());
    socket.sendTo(new inet::Packet(b ? "M5" : "M1", chunk), fogAddress(curFog), fogPort);
    if (inWindow(curStart))
        sentReq[curPhase - 1]++;
    scheduleAt(simTime() + sessionTimeout, timeoutEvt);
}

void AkaVehicleApp5G::sendCam()
{
    int fog = servingFog();
    if (fog < 0)
        return;
    auto chunk = inet::makeShared<AkaPacket>();
    chunk->setChunkLength(inet::B(camBits / 8));
    chunk->setMsgType(20);
    chunk->setVehicleId(getId());
    chunk->setFogIndex(fog);
    chunk->setGenTime(simTime());
    socket.sendTo(new inet::Packet("CAM", chunk), fogAddress(fog), fogPort);
    if (inWindow(simTime()))
        camSent++;
}

void AkaVehicleApp5G::socketDataArrived(inet::UdpSocket *, inet::Packet *packet)
{
    auto m = packet->peekAtFront<AkaPacket>();
    int expected = curPhase == 2 ? 6 : 4;
    if (busy && m->getMsgType() == expected && m->getSessionId() == curSession && timeoutEvt->isScheduled()) {
        int k = curPhase - 1;
        if (inWindow(curStart)) {
            recvResp[k]++;
            sumRespDelay[k] += (simTime() - m->getGenTime()).dbl();
        }
        cancelEvent(timeoutEvt);
        // phase A: Z_VC, h_2, SK, d_3, session key; phase B: Z, SK', d_5, session key
        scheduleAt(simTime() + (curPhase == 2 ? cH2 : cV2), doneEvt);
    }
    delete packet;
}

void AkaVehicleApp5G::socketErrorArrived(inet::UdpSocket *, inet::Indication *indication)
{
    delete indication;
}

void AkaVehicleApp5G::finish()
{
    const char *ph[2] = {"A", "B"};
    for (int k = 0; k < 2; k++) {
        std::string p = ph[k];
        recordScalar(("akaSentReq" + p).c_str(), sentReq[k]);
        recordScalar(("akaRecvResp" + p).c_str(), recvResp[k]);
        recordScalar(("akaStarted" + p).c_str(), started[k]);
        recordScalar(("akaCompleted" + p).c_str(), completed[k]);
        recordScalar(("akaTimedOut" + p).c_str(), timedOut[k]);
        recordScalar(("akaSumAuthLatency" + p).c_str(), sumAuthLatency[k]);
        recordScalar(("akaSumRespDelay" + p).c_str(), sumRespDelay[k]);
        recordScalar(("akaCompletedHo" + p).c_str(), completedHo[k]);
        recordScalar(("akaSumAuthLatencyHo" + p).c_str(), sumAuthLatencyHo[k]);
        recordScalar(("akaHandovers" + p).c_str(), handoversPh[k]);
        recordScalar(("akaEntryHandovers" + p).c_str(), entryHandoversPh[k]);
    }
    recordScalar("akaHandovers", handovers);
    recordScalar("akaEdgeEntry", edgeEntry ? 1 : 0);
    recordScalar("akaSkippedDetached", skippedDetached);
    recordScalar("akaCamSent", camSent);
    if (snapTaken) {
        recordScalar("akaSnapX", snapX);
        recordScalar("akaSnapY", snapY);
        recordScalar("akaSnapFog", snapFog);
    }
}

} // namespace fogroam5g
