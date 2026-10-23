#pragma once

#include "veins/modules/application/ieee80211p/DemoBaseApplLayer.h"
#include "veins/modules/application/aka/AkaMessages_m.h"

namespace veins {

/**
 * Vehicle V_i: discovers fog nodes through RSU advertisements and
 * periodically authenticates with the fog node in range (re-keying and
 * handover). With the proposed scheme, the full cloud-assisted phase A is
 * run when the vehicle joins and whenever its last phase A is older than
 * phaseAValidity; all other authentications use the cloud-free phase B.
 * With the scheme of [12], every authentication is a full run.
 * The vehicle also broadcasts V2V beacons (BSMs).
 */
class VEINS_API AkaVehicleApp : public DemoBaseApplLayer {
public:
    ~AkaVehicleApp() override;
    void initialize(int stage) override;
    void finish() override;

protected:
    void onWSM(BaseFrame1609_4* wsm) override;
    void handleSelfMsg(cMessage* msg) override;
    bool inWindow(simtime_t t) const { return t >= measureStart && t <= measureEnd; }

    // parameters
    int m1Bits = 0, m5Bits = 0;
    bool useHandover = false;
    simtime_t cV1, cV2, cH1, cH2, phaseAValidity;
    simtime_t authInterval, authJitter, sessionTimeout, advValidity, measureStart, measureEnd;

    // fog node currently in range
    long rsuMac = -1;
    int rsuIndex = -1;
    simtime_t lastAdv = -1;
    simtime_t lastPhaseA = -1;     // completion time of the last phase A

    // current session
    bool busy = false;
    int curPhase = 0;              // 1 = phase A, 2 = phase B
    long sessionCounter = 0;
    long curSession = -1;
    simtime_t curStart;
    long sessionRsu = -1;

    cMessage* authEvt = nullptr;
    cMessage* sendEvt = nullptr;
    cMessage* doneEvt = nullptr;
    cMessage* timeoutEvt = nullptr;

    // statistics (only sessions started inside the measurement window)
    // index 0 = phase A (or full run of [12]), 1 = phase B
    long sentReq[2] = {0, 0}, recvResp[2] = {0, 0};
    long started[2] = {0, 0}, completed[2] = {0, 0}, timedOut[2] = {0, 0};
    double sumAuthLatency[2] = {0, 0}, sumRespDelay[2] = {0, 0};
    long handovers = 0;
    cOutVector authLatencyVec;
};

} // namespace veins
