#!/bin/bash
# usage: ./run.sh <Config> <runnumber> [extra opp_run options]
#   Config: see omnetpp.ini;  run numbers 0..59 = 6 densities x 10 seeds (r = 10*index(N) + seed)
# Paths default to the layout made by build/fetch5g.sh and build/build5g.sh and can be
# overridden with the environment variables below.
HERE=$(cd "$(dirname "$0")" && pwd)
SIM=${SIM:-$(cd "$HERE/.." && pwd)}
OMNETPP=${OMNETPP_ROOT:-$SIM/src/omnetpp-6.0.3}
VEINS=${VEINS_ROOT:-$SIM/src/veins}
SUMO=${SUMO_HOME:-$SIM/src/sumo}
INET=${INET_ROOT:-$SIM/src/inet4.5}
SIMU5G=${SIMU5G_ROOT:-$SIM/src/simu5g}
VINET=${VEINS_INET_ROOT:-$SIM/src/veins_inet}
APP=${FOGROAM5G_ROOT:-$SIM/fogroam5g}
export PATH=$OMNETPP/bin:$SUMO/bin:$PATH SUMO_HOME=$SUMO
export LD_LIBRARY_PATH=$OMNETPP/lib:${LOCAL_LIB:-$SIM/local/lib}:$LD_LIBRARY_PATH
cd "$HERE"
CFG=$1; RUN=$2; shift 2
opp_run -u Cmdenv -c $CFG -r $RUN \
  -n "$APP/src:$SIMU5G/src:$INET/src:$VEINS/src/veins:$VINET/src/veins_inet" \
  -x "$(tr '\n' ';' < $INET/.nedexclusions)" \
  -l $INET/src/INET -l $SIMU5G/src/simu5g -l $VEINS/src/veins -l $VINET/src/veins_inet -l $APP/src/fogroam5g \
  --image-path="$VEINS/images:$SIMU5G/images" "$@" omnetpp.ini
