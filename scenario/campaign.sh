#!/bin/bash
# Order of the runs of the revised campaign (resumable: finished runs are skipped).
# The configurations of Fig. 9 come first, then the handover-triggered sessions.
cd "$(dirname "$0")"
ALL=20,40,60,80,100,120
python3 runset.py $ALL 2 Proposed,Baseline,ProposedA 0 0-2
python3 runset.py $ALL 2 Proposed,Baseline,ProposedA 0 3-9
python3 runset.py $ALL 2 ProposedHO,BaselineHO 0 0-4
python3 runset.py 60 2 ProposedHO150,ProposedHO600 0 0-9
python3 runset.py $ALL 2 ProposedHO,BaselineHO 0 5-9
echo CAMPAIGN_DONE
