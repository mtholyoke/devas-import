#!/usr/bin/env bash

DATA_ROOT=/mars/g/rch3/r/mdyar
TODAY=$(date "+%Y-%m-%d")
NEMO_ROOT=cj@nemo.mtholyoke.edu:/home/cj/datafiles
SCRIPT_ROOT=/home/jproctor/devas-import
CHEMLIBS_DIR=$DATA_ROOT/MHC.LIBS/DATA

echo "Starting SuperLIBS 5120"
SUPERLIBS_DIR=$DATA_ROOT/MHC.SuperLIBS/SAMPLE_RUNS
SUPERLIBS_LOG=$SUPERLIBS_DIR/nightly-logs/MHC_5120-$TODAY-test.log
echo "### $(date) - starting processing" > $SUPERLIBS_LOG
python2.7 $SCRIPT_ROOT/process_superlibs_files.py -i $SUPERLIBS_DIR/PREPROCESSED_NO_BLR/MHC_SuperLIBS_5120 -o $SUPERLIBS_DIR/to-DEVAS/MHC_5120/prepro_no_blr -m $CHEMLIBS_DIR/COMPOSITIONS/Millennium_COMPS.xlsx >> $SUPERLIBS_LOG
echo "### $(date) - finished processing" >> $SUPERLIBS_LOG
# echo "### $(date) - finished processing, starting rsync" >> $SUPERLIBS_LOG
# rsync -av $SUPERLIBS_DIR/to-DEVAS/MHC_5120/ $NEMO_ROOT/SuperLIBS/MHC_5120/ >> $SUPERLIBS_LOG 2>&1
# echo "### $(date) - finished rsync" >> $SUPERLIBS_LOG
echo "Finished SuperLIBS 5120"

# echo "Starting SuperLIBS 10K"
# SUPERLIBS_DIR=$DATA_ROOT/MHC.SuperLIBS/SAMPLE_RUNS
# SUPERLIBS_LOG=$SUPERLIBS_DIR/nightly-logs/MHC_10K-$TODAY-test.log
# echo "### $(date) - starting processing" > $SUPERLIBS_LOG
# python2.7 $SCRIPT_ROOT/process_superlibs_10k_files.py -i $SUPERLIBS_DIR/PREPROCESSED_NO_BLR/MHC_SuperLIBS_10K -o $SUPERLIBS_DIR/to-DEVAS/MHC_10K/prepro_no_blr -m $CHEMLIBS_DIR/COMPOSITIONS/Millennium_COMPS.xlsx >> $SUPERLIBS_LOG
# echo "### $(date) - finished processing" >> $SUPERLIBS_LOG
# # echo "### $(date) - finished processing, starting rsync" >> $SUPERLIBS_LOG
# # rsync -av $SUPERLIBS_DIR/to-DEVAS/MHC_10K/ $NEMO_ROOT/SuperLIBS/MHC_10K/ >> $SUPERLIBS_LOG 2>&1
# # echo "### $(date) - finished rsync" >> $SUPERLIBS_LOG
# echo "Finished SuperLIBS 10K"

# echo "Starting SuperLIBS 18K"
# SUPERLIBS_DIR=$DATA_ROOT/MHC.SuperLIBS/SAMPLE_RUNS
# SUPERLIBS_LOG=$SUPERLIBS_DIR/nightly-logs/MHC_18K-$TODAY-test.log
# echo "### $(date) - starting processing" > $SUPERLIBS_LOG
# python2.7 $SCRIPT_ROOT/process_superlibs_18k_files.py -i $SUPERLIBS_DIR/PREPROCESSED_NO_BLR/MHC_SuperLIBS_18K -o $SUPERLIBS_DIR/to-DEVAS/MHC_18K/prepro_no_blr -m $CHEMLIBS_DIR/COMPOSITIONS/Millennium_COMPS.xlsx >> $SUPERLIBS_LOG
# echo "### $(date) - finished processing" >> $SUPERLIBS_LOG
# # echo "### $(date) - finished processing, starting rsync" >> $SUPERLIBS_LOG
# # rsync -av $SUPERLIBS_DIR/to-DEVAS/MHC_18K/ $NEMO_ROOT/SuperLIBS/MHC_T18K/ >> $SUPERLIBS_LOG 2>&1
# # echo "### $(date) - finished rsync" >> $SUPERLIBS_LOG
# echo "Finished SuperLIBS 18K"

