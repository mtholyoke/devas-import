#!/usr/bin/env bash

CRONMASTER=jproctor@mtholyoke.edu
WORK_DIR=$(dirname $0)
TODAY=$(date +%D)

cd "$WORK_DIR"

./mirror_pds.sh > daily_pds.log 2>&1
if [[ $? -ne 0 ]]; then
  mail -s "MSL daily download failed on $TODAY" $CRONMASTER <daily_pds.log
fi

./process_all.py > daily_mhc.log 2>&1
if [[ $? -ne 0 ]]; then
  mail -s "MHC daily rsync failed on $TODAY" $CRONMASTER <daily_mhc.log
fi

# Regardless of failure or success, keep the logs around until tomorrow.
