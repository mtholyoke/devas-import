#!/usr/bin/env bash

echo "Testing Raman"

DATA_ROOT=/mars/g/rch3/r/mdyar
TODAY=$(date "+%Y-%m-%d")
NEMO_ROOT=cj@nemo.mtholyoke.edu:/home/cj/datafiles
SCRIPT_ROOT=/home/jproctor/devas-import

echo "Starting Raman"
RAMAN_DIR=$DATA_ROOT/data_Raman
RAMAN_LOG=$RAMAN_DIR/nightly-logs/raman-$TODAY-test.log
echo "### $(date) - starting processing" > $RAMAN_LOG
python2.7 $SCRIPT_ROOT/process_raman_files.py -i $RAMAN_DIR/spectra -o $RAMAN_DIR/to-DEVAS/raman -m $RAMAN_DIR/rlogbook.xlsx >> $RAMAN_LOG 2>&1
echo "### $(date) - finished processing, skipping rsync" >> $RAMAN_LOG
# echo "### $(date) - finished processing, starting rsync" >> $RAMAN_LOG
# rsync -av $RAMAN_DIR/to-DEVAS/ $NEMO_ROOT/Raman/MHC/ >> $RAMAN_LOG 2>&1
# echo "### $(date) - finished rsync" >> $RAMAN_LOG
echo "Finished Raman"

echo "Finished running all datasets"
