#!/bin/bash
# Builds flex, Xerces-C, OMNeT++ (Cmdenv only), SUMO, and Veins with the AKA modules
# without root rights. Sources in $SIM/src, installed libraries in $SIM/local.
SIM=${SIM:-$(cd "$(dirname "$0")/.." && pwd)}
S=$SIM/src; L=$SIM/local; LOG=$SIM/logs
mkdir -p $L $LOG
export PATH=$L/bin:$PATH
cd $S
if [ ! -x $L/bin/flex ]; then
  tar xzf flex-2.6.4.tar.gz && cd flex-2.6.4 && ./configure --prefix=$L > $LOG/flex.log 2>&1 \
    && make -j2 >> $LOG/flex.log 2>&1 && make install >> $LOG/flex.log 2>&1; cd $S
fi
if [ ! -f $L/lib/libxerces-c.so ]; then
  mkdir -p xerces-c/build && cd xerces-c/build && cmake .. -DCMAKE_INSTALL_PREFIX=$L -DCMAKE_BUILD_TYPE=Release \
    -Dnetwork=OFF -Dtranscoder=iconv > $LOG/xerces.log 2>&1 && make -j2 >> $LOG/xerces.log 2>&1 \
    && make install >> $LOG/xerces.log 2>&1; cd $S
fi
# OMNeT++ 6.0.3 (command-line environment only)
[ -d omnetpp-6.0.3 ] || tar xzf omnetpp-6.0.3.tgz
cd $S/omnetpp-6.0.3 && source setenv -f > /dev/null
./configure WITH_QTENV=no WITH_OSG=no WITH_OSGEARTH=no WITH_PARSIM=no PREFER_CLANG=no > $LOG/omnet_configure.log 2>&1
make -j2 MODE=release base > $LOG/omnet_make.log 2>&1 || { echo "OMNeT++ build failed"; exit 1; }
# SUMO 1.20.0
mkdir -p $S/sumo/build/cmake-build && cd $S/sumo/build/cmake-build
cmake ../.. -DCMAKE_BUILD_TYPE=Release -DXercesC_INCLUDE_DIR=$L/include -DXercesC_LIBRARY=$L/lib/libxerces-c.so \
  -DCHECK_OPTIONAL_LIBS=OFF -DENABLE_JAVA_BINDINGS=OFF -DENABLE_CS_BINDINGS=OFF -DENABLE_PYTHON_BINDINGS=OFF > $LOG/sumo_cmake.log 2>&1
make -j2 sumo netconvert duarouter polyconvert > $LOG/sumo_make.log 2>&1 || { echo "SUMO build failed"; exit 1; }
# Veins 5.3.1 with the protocol modules
mkdir -p $S/veins/src/veins/modules/application/aka
cp $SIM/veins_aka/* $S/veins/src/veins/modules/application/aka/
cd $S/veins && ./configure > $LOG/veins_configure.log 2>&1 && make -j2 MODE=release > $LOG/veins_make.log 2>&1 \
  || { echo "Veins build failed"; exit 1; }
echo BUILD_DONE
