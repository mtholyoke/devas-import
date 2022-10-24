#!/usr/bin/env bash
set -e

# User settings
REMOTE_PREPROCESSED=ftp://pds-geosciences.wustl.edu/msl/msl-m-chemcam-libs-4_5-rdr-v1/mslccm_1xxx/
MASTER_FILE=msl_ccam_obs.csv

MSL_DIR=/mars/g/rch3/r/mdyar/MSL_PDS
CCS_DATA_DIR=$MSL_DIR/ccs_data
CCS_PREFIX=$CCS_DATA_DIR/ccs
CCS_ORIGINALS=$CCS_DATA_DIR/original
MODELS_PREDS_DIR=$MSL_DIR/models_predictions
MOC_DIR=$MODELS_PREDS_DIR/moc

TODAY=$(date "+%Y-%m-%d")
NEMO_ROOT=cj@nemo.mtholyoke.edu:/home/cj/datafiles
MSL_LOG=$MSL_DIR/nightly-logs/msl-$TODAY.log

# Download Masterfile, processed spectra, & MOC predictions
echo "Running MSL-PDS dataset"
starttime=$(date +%s)
echo "### $(date) - Starting MSL data downloads" > MSL_LOG
/usr/bin/lftp $REMOTE_PREPROCESSED <<EOF
 get -c document/$MASTER_FILE  -o $CCS_DATA_DIR/$MASTER_FILE
 mirror -c -I 'cl5_*ccs_*.csv' --no-empty-dirs data $CCS_ORIGINALS
 mirror -c -I '*.csv' data/moc $MOC_DIR
EOF
endtime=$(date +%s)
echo "### $(date) - Download finished after $((endtime - starttime)) seconds, starting processing." >> MSL_LOG

# Add the new CCS files to the server-readable data
python2.7 process_msl_files.py -o $CCS_PREFIX -i $CCS_ORIGINALS -m $CCS_DATA_DIR/$MASTER_FILE
echo "### $(date) - Added new CCS files to ${CCS_PREFIX}.xxx.hdf5, starting rsync" >> $MSL_LOG
rsync -av $SUPERLIBS_DIR/to-DEVAS/MHC_18K/ $NEMO_ROOT/SuperLIBS/MHC_18K/ >> $MSL_LOG 2>&1
echo "### $(date) - finished rsync" >> $MSL_LOG

# # Predict the new shots
#
# LIBS_DATA_DIR=/mars/g/rch3/r/mdyar/jproctor-test/LIBS
# LIBS_MIX_FILE=$LIBS_DATA_DIR/mhc_doping+mhc_big+lanl_400+public_caltargets.npz
# LANL_FILE=$LIBS_DATA_DIR/lanl_new.hdf5
#
# python2.7 web_model.py -o $MODELS_PREDS_DIR --ccs-dir $CCS_DATA_DIR --model standard --lanl-file $LANL_FILE
# echo "$(date +%s): Predicted compositions for new CCS files"
#
# python2.7 web_model.py -o $MODELS_PREDS_DIR --ccs-dir $CCS_DATA_DIR  --model mixed --libs-mix-file $LIBS_MIX_FILE
# echo "$(date +%s): Predicted compositions for new CCS files with Mixed model"
#
# python2.7 web_model.py -o $MODELS_PREDS_DIR --ccs-dir $CCS_DATA_DIR --model moc --moc-dir $MOC_DIR
# echo "$(date +%s): Predicted compositions for new CCS files with MOC model"
#
# python2.7 web_model.py -o $MODELS_PREDS_DIR --ccs-dir $CCS_DATA_DIR --model dust
# echo "$(date +%s): Predicted dust shots for new CCS files with the Dust Classifier"

