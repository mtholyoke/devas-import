#!/usr/bin/env bash

export PYTHONPATH=/home/cj/superman:$PYTHONPATH

CRONMASTER=ccarey@cs.umass.edu
WORK_DIR=$(dirname $0)
today=$(date +%D)

cd "$WORK_DIR"

./mirror_pds.sh >daily_pds.log 2>&1
if [[ $? -ne 0 ]]; then
  mail -s "MSL daily download failed on $today" $CRONMASTER <daily_pds.log
fi

./rsync_mhc.sh >daily_mhc.log 2>&1
if [[ $? -ne 0 ]]; then
  mail -s "MHC daily rsync failed on $today" $CRONMASTER <daily_mhc.log
fi

# Regardless of failure or success, keep the logs around until tomorrow.
