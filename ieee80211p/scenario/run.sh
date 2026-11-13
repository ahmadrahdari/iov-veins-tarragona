#!/bin/bash
# usage: ./run.sh <Config> <runnumber|all>
HERE=$(cd $(dirname $0); pwd)
SIM=${SIM:-$(cd "$HERE/.." && pwd)}   # folder with src/ and local/ made by build/fetch.sh and build/build.sh
source $SIM/src/omnetpp-6.0.3/setenv -f > /dev/null
export PATH=$SIM/src/sumo/bin:$PATH LD_LIBRARY_PATH=$SIM/local/lib:$LD_LIBRARY_PATH SUMO_HOME=$SIM/src/sumo
VEINS=$SIM/src/veins
cd $HERE
opp_run -u Cmdenv -c $1 ${2:+-r $2} -n .:$VEINS/src/veins -l $VEINS/src/veins --image-path=$VEINS/images omnetpp.ini
