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

echo "Server refresh:"
echo "$(wget -O- --method=POST http://nemo.p/nightly-refresh 2>&1)"

echo "Finished running all datasets"
