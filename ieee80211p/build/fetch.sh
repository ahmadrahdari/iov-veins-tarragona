#!/bin/bash
# Downloads the sources of flex, Xerces-C, OMNeT++ 6.0.3, Veins 5.3.1, and SUMO 1.20.0
# into $SIM/src (default: the parent folder of this script's folder).
set -x
SIM=${SIM:-$(cd "$(dirname "$0")/.." && pwd)}
mkdir -p "$SIM/src" && cd "$SIM/src"
curl -sSL -o flex-2.6.4.tar.gz https://github.com/westes/flex/releases/download/v2.6.4/flex-2.6.4.tar.gz
git clone -q --depth 1 -b v3.2.5 https://github.com/apache/xerces-c xerces-c
git clone -q --depth 1 -b veins-5.3.1 https://github.com/sommer/veins veins
curl -sSL -o omnetpp-6.0.3.tgz https://github.com/omnetpp/omnetpp/releases/download/omnetpp-6.0.3/omnetpp-6.0.3-linux-x86_64.tgz
git clone -q --depth 1 --filter=blob:none --no-checkout -b v1_20_0 https://github.com/eclipse-sumo/sumo sumo \
  && (cd sumo && git sparse-checkout set --no-cone '/*' '!/tests/' '!/docs/' && git checkout -q v1_20_0)
echo FETCH_DONE
