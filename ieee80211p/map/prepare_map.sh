#!/bin/bash
# Regenerates the SUMO inputs of the Tarragona scenario from the OSM extract.
# The options are those recorded in the headers of the generated files.
set -e
SUMO_HOME=${SUMO_HOME:-/path/to/sumo}
netconvert --osm-files tarragona.osm.xml -o tarragona.net.xml --output.street-names \
  --simple-projection --geometry.remove --roundabouts.guess --ramps.guess \
  --tls.discard-simple --tls.join --tls.guess-signals --tls.default-type actuated \
  --keep-edges.by-vclass passenger --remove-edges.isolated --junctions.join \
  --osm.elevation false
netconvert --sumo-net-file tarragona.net.xml -o tarragona_center.net.xml --output.street-names \
  --keep-edges.in-boundary 500,700,2900,2200 --keep-edges.components 1 \
  --remove-edges.isolated --offset.disable-normalization --no-turnarounds
polyconvert --net-file tarragona_center.net.xml --osm-files tarragona.osm.xml \
  --type-file $SUMO_HOME/data/typemap/osmPolyconvert.typ.xml \
  --prune.in-net --prune.in-net.offsets 30,30,30,30 -o tarragona_center.poly.xml
# Routes: 1.5 N random trips within the first 20 s, keep the first N valid vehicles.
for N in 20 40 60 80 100 120; do
  P=$(python3 -c "print(round(20/(1.5*$N),4))")
  python3 $SUMO_HOME/tools/randomTrips.py -n tarragona_center.net.xml \
    -o trips_$N.xml -r rou_$N.xml --prefix v --fringe-factor 2 --min-distance 1200 \
    --validate --end 20 --period $P --trip-attributes 'departLane="best" departSpeed="max"'
  python3 - "$N" <<'PY'
import sys, re
n = int(sys.argv[1]); s = open(f'rou_{n}.xml').read()
veh = re.findall(r'<vehicle .*?</vehicle>', s, re.S)
head = s[:s.index('<vehicle ')]
open(f'tarragona_N{n}.rou.xml', 'w').write(head + '\n'.join(veh[:n]) + '\n</routes>\n')
PY
done
