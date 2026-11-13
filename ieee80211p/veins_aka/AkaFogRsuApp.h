#pragma once

#include "veins/modules/application/ieee80211p/DemoBaseApplLayer.h"
#include "veins/modules/application/aka/AkaMessages_m.h"

namespace veins {

/** Fog node F_j co-located with an RSU (single FIFO CPU). */
class VEINS_API AkaFogRsuApp : public DemoBaseApplLayer {
public:
    ~AkaFogRsuApp() override;
    void initialize(int stage) override;
    void finish() override;
    void handleMessage(cMessage* msg) override;

protected:
    void onWSM(BaseFrame1609_4* wsm) override;
    void handleSelfMsg(cMessage* msg) override;
    simtime_t cpuSchedule(simtime_t cost);
    bool inWindow(simtime_t t) const { return t >= measureStart && t <= measureEnd; }

    int m2Bits = 0, m4Bits = 0, m6Bits = 0, advBits = 0;
    simtime_t cF1, cF2, cFH, advInterval, measureStart, measureEnd;
    simtime_t cpuBusyUntil = 0;
    cMessage* advEvt = nullptr;
    cGate* backhaulOut = nullptr;

    // index 0 = phase A (M1 received, M4 sent), 1 = phase B (M5 received, M6 sent)
    long recvReq[2] = {0, 0}, sentResp[2] = {0, 0};
    double sumReqDelay[2] = {0, 0};
};

} // namespace veins
