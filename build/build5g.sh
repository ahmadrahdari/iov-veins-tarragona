#!/bin/bash
# Builds INET 4.5.2 (only the features needed by Simu5G), Simu5G 1.2.2, the veins_inet
# subproject of Veins 5.3.1 and the FogRoam 5G modules on top of the OMNeT++ 6.0.3 / SUMO /
# Veins installation made by build.sh. No source file of these frameworks is modified.
SIM=${SIM:-$(cd "$(dirname "$0")/.." && pwd)}
S=$SIM/src; LOG=$SIM/logs
JOBS=${JOBS:-2}
mkdir -p $LOG
[ -f $S/veins/src/libveins.so ] || $SIM/build/build.sh || exit 1
cd $S/omnetpp-6.0.3 && source setenv -f > /dev/null
export LD_LIBRARY_PATH=$SIM/local/lib:$LD_LIBRARY_PATH

# INET 4.5.2: IPv4, UDP, TCP, SCTP (X2), PPP and Ethernet links, mobility, visualisation base
cd $S/inet4.5 && export INET_ROOT=$PWD INET_PROJ=$PWD PATH=$PWD/bin:$PATH
opp_featuretool disable -f all > $LOG/inet_features.log 2>&1
opp_featuretool enable -f Clock Ethernet Ieee8021as Ieee8021d Ieee8021q Ieee8021r Ieee8022 Ipv4 Mobility \
  PhysicalLayerCommon PhysicalLayerWiredCommon PhysicalLayerWirelessCommon Ppp ProtocolElement Queueing Sctp \
  TcpCommon TcpInet Tun Udp VirtualInterface VisualizationCommon VisualizationCanvas >> $LOG/inet_features.log 2>&1
make makefiles > $LOG/inet_make.log 2>&1 && make MODE=release -j$JOBS >> $LOG/inet_make.log 2>&1 \
  || { echo "INET build failed"; exit 1; }

# Simu5G 1.2.2 (its Makefile expects INET in ../inet4.5)
cd $S/simu5g && make makefiles > $LOG/simu5g_make.log 2>&1 && make MODE=release -j$JOBS >> $LOG/simu5g_make.log 2>&1 \
  || { echo "Simu5G build failed"; exit 1; }

# veins_inet (SUMO-driven mobility for INET nodes)
rm -rf $S/veins_inet && cp -r $S/veins/subprojects/veins_inet $S/veins_inet && cd $S/veins_inet
./configure --with-veins=$S/veins --with-inet=$S/inet4.5 > $LOG/veins_inet_make.log 2>&1 \
  && make MODE=release -j$JOBS >> $LOG/veins_inet_make.log 2>&1 || { echo "veins_inet build failed"; exit 1; }

# FogRoam modules
cd $SIM/fogroam5g && make makefiles ROOT=$S VEINS_PROJ=$S/veins > $LOG/fogroam5g_make.log 2>&1 \
  && make MODE=release -j$JOBS >> $LOG/fogroam5g_make.log 2>&1 || { echo "fogroam5g build failed"; exit 1; }
echo BUILD5G_DONE
