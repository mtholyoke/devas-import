#!/usr/bin/env bash

echo "Running all MHC datasets"

DATA_ROOT=/mars/g/rch3/r/mdyar
TODAY=$(date "+%Y-%m-%d")
NEMO_ROOT=cj@nemo.mtholyoke.edu:/home/cj/datafiles
SCRIPT_ROOT=/home/jproctor/devas-import

echo "Starting Mossbauer"
MOSS_DIR=$DATA_ROOT/data_Moss
MOSS_LOG=$MOSS_DIR/nightly-logs/mossbauer-$TODAY.log
MOSS_REMOTE=www-data@mossbauer.mtholyoke.edu:/var/www/mossbauer.mtholyoke.edu/data_Moss
echo "### $(date) - starting processing" > $MOSS_LOG
python2.7 $SCRIPT_ROOT/process_mossbauer_files.py -i $MOSS_DIR/data -o $MOSS_DIR/to-DEVAS/mossbauer -m $MOSS_DIR/mlogbook.xlsx >> $MOSS_LOG 2>&1
echo "### $(date) - finished processing, starting rsync to nemo" >> $MOSS_LOG
rsync -av $MOSS_DIR/to-DEVAS/ $NEMO_ROOT/Mossbauer/MHC/ >> $MOSS_LOG 2>&1
echo "### $(date) - finished rsync to nemo, starting rsync to mossbauer" >> $MOSS_LOG
rsync -av $MOSS_DIR/data/ $MOSS_REMOTE/data/ >> $MOSS_LOG 2>&1
rsync -av $MOSS_DIR/mlogbook.xlsx $MOSS_REMOTE/mlogbook.xlsx >> $MOSS_LOG 2>&1
echo "### $(date) - finished rsync to mossbauer" >> $MOSS_LOG
echo "Finished Mossbauer"

echo "Starting Raman"
RAMAN_DIR=$DATA_ROOT/data_Raman
RAMAN_LOG=$RAMAN_DIR/nightly-logs/raman-$TODAY.log
echo "### $(date) - starting processing" > $RAMAN_LOG
python2.7 $SCRIPT_ROOT/process_raman_files.py -i $RAMAN_DIR/spectra -o $RAMAN_DIR/to-DEVAS/raman -m $RAMAN_DIR/rlogbook.xlsx >> $RAMAN_LOG 2>&1
echo "### $(date) - finished processing, starting rsync" >> $RAMAN_LOG
rsync -av $RAMAN_DIR/to-DEVAS/ $NEMO_ROOT/Raman/MHC/ >> $RAMAN_LOG 2>&1
echo "### $(date) - finished rsync" >> $RAMAN_LOG
echo "Finished Raman"

echo "Starting ChemLIBS"
CHEMLIBS_DIR=$DATA_ROOT/MHC.LIBS/DATA
CHEMLIBS_LOG=$CHEMLIBS_DIR/nightly-logs/chemlibs-$TODAY.log
echo "### $(date) - starting processing" > $CHEMLIBS_LOG
python2.7 $SCRIPT_ROOT/process_mhc_files.py -i $CHEMLIBS_DIR/PREPROCESSED_NO_BLR -o $CHEMLIBS_DIR/to-DEVAS/prepro_no_blr -m $CHEMLIBS_DIR/COMPOSITIONS/Millennium_COMPS.xlsx >> $CHEMLIBS_LOG 2>&1
echo "### $(date) - finished processing, starting rsync" >> $CHEMLIBS_LOG
rsync -av $CHEMLIBS_DIR/to-DEVAS/ $NEMO_ROOT/LIBS/MHC/ >> $CHEMLIBS_LOG 2>&1
echo "### $(date) - finished rsync" >> $CHEMLIBS_LOG
echo "Finished ChemLIBS"

echo "Starting SuperLIBS 5120"
SUPERLIBS_DIR=$DATA_ROOT/MHC.SuperLIBS/SAMPLE_RUNS
SUPERLIBS_LOG=$SUPERLIBS_DIR/nightly-logs/MHC_5120-$TODAY.log
echo "### $(date) - starting processing" > $SUPERLIBS_LOG
python2.7 $SCRIPT_ROOT/process_superlibs_files.py -i $SUPERLIBS_DIR/PREPROCESSED_NO_BLR/MHC_SuperLIBS_5120 -o $SUPERLIBS_DIR/to-DEVAS/MHC_5120/prepro_no_blr -m $CHEMLIBS_DIR/COMPOSITIONS/Millennium_COMPS.xlsx >> $SUPERLIBS_LOG 2>&1
echo "### $(date) - finished processing, starting rsync" >> $SUPERLIBS_LOG
rsync -av $SUPERLIBS_DIR/to-DEVAS/MHC_5120/ $NEMO_ROOT/SuperLIBS/MHC_5120/ >> $SUPERLIBS_LOG 2>&1
echo "### $(date) - finished rsync" >> $SUPERLIBS_LOG
echo "Finished SuperLIBS 5120"

echo "Server refresh:"
echo "$(wget -O- --method=POST http://nemo.p/nightly-refresh 2>&1)"

echo "Finished running all MHC datasets"
