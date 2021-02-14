#!/usr/bin/env bash

echo "Running all MHC datasets"

DATA_ROOT=/home/jproctor
TODAY=$(date "+%Y-%m-%d")
NEMO_ROOT=cj@nemo.mtholyoke.edu:/home/cj/datafiles
SCRIPT_ROOT=/home/jproctor/devas-import

echo "Starting ChemLIBS"
CHEMLIBS_DIR=$DATA_ROOT/ChemLIBS
CHEMLIBS_LOG=$CHEMLIBS_DIR/logs/chemlibs-$TODAY.log
echo "### $(date) - starting processing" > $CHEMLIBS_LOG
python2.7 $SCRIPT_ROOT/process_mhc_files.py -i $CHEMLIBS_DIR/PREPROCESSED_NO_BLR -o $CHEMLIBS_DIR/to-DEVAS/prepro_no_blr -m $CHEMLIBS_DIR/Millennium_COMPS.xlsx >> $CHEMLIBS_LOG 2>&1
echo "### $(date) - finished processing, starting rsync" >> $CHEMLIBS_LOG
# rsync -av $CHEMLIBS_DIR/to-DEVAS/ $NEMO_ROOT/LIBS/MHC/ >> $CHEMLIBS_LOG 2>&1
echo "### $(date) - finished rsync" >> $CHEMLIBS_LOG
echo "Finished ChemLIBS"

echo "Finished running all MHC datasets"
