#!/bin/bash
# Downloads the additional sources of the 5G NR simulation into $SIM/src:
# INET 4.5.2 and Simu5G 1.2.2 (the release for OMNeT++ 6.0.x and INET 4.5).
# OMNeT++ 6.0.3, SUMO 1.20.0 and Veins 5.3.1 are fetched by fetch.sh.
set -x
SIM=${SIM:-$(cd "$(dirname "$0")/.." && pwd)}
mkdir -p "$SIM/src" && cd "$SIM/src"
[ -d omnetpp-6.0.3 ] || [ -f omnetpp-6.0.3.tgz ] || "$SIM/build/fetch.sh"
git clone -q --depth 1 -b v4.5.2 https://github.com/inet-framework/inet inet4.5
git clone -q --depth 1 -b v1.2.2 https://github.com/Unipisa/Simu5G simu5g
echo FETCH5G_DONE
