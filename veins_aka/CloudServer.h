#pragma once

#include "veins/veins.h"
#include "veins/modules/application/aka/AkaMessages_m.h"

namespace veins {

/** Cloud server CS: receives M2, computes, and returns M3 (single FIFO CPU). */
class VEINS_API CloudServer : public cSimpleModule {
protected:
    void initialize() override;
    void handleMessage(cMessage* msg) override;
    void finish() override;
    int m3Bits = 0;
    simtime_t cCS, cpuBusyUntil = 0;
    long processed = 0;
};

} // namespace veins
