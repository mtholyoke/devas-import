#!/usr/bin/env bash
set -e

# User settings
REMOTE_PREPROCESSED=http://pds-geosciences.wustl.edu/msl/msl-m-chemcam-libs-4_5-rdr-v1/mslccm_1xxx/
MASTER_FILE=msl_ccam_obs.csv

MSL_DIR=/srv/nfs/common/spectra/MSL_PDS
CCS_DATA_DIR=$MSL_DIR/ccs_data
CCS_PREFIX=$CCS_DATA_DIR/ccs
CCS_ORIGINALS=$CCS_DATA_DIR/original
MODELS_PREDS_DIR=$MSL_DIR/models_predictions
MOC_DIR=$MODELS_PREDS_DIR/moc

LIBS_DATA_DIR=/srv/nfs/common/spectra/LIBS
LIBS_MIX_FILE=$LIBS_DATA_DIR/mhc_doping+mhc_big+lanl_400+public_caltargets.npz
LANL_FILE=$LIBS_DATA_DIR/lanl_new.hdf5

# Download Masterfile, processed spectra, & MOC predictions
starttime=$(date +%s)
echo "$starttime: Starting MSL data downloads..."
lftp $REMOTE_PREPROCESSED <<EOF
 get -c document/$MASTER_FILE  -o $CCS_DATA_DIR/$MASTER_FILE
 mirror -c -I 'cl5_*ccs_*.csv' --no-empty-dirs data $CCS_ORIGINALS
 mirror -c -I '*.csv' data/moc $MOC_DIR
EOF
endtime=$(date +%s)
echo "$endtime: Download finished after $((endtime - starttime)) seconds."

# Add the new CCS files to the server-readable data
python2.7 process_msl_files.py -o $CCS_PREFIX -i $CCS_ORIGINALS \
    -m $CCS_DATA_DIR/$MASTER_FILE
echo "$(date +%s): Added new CCS files to ${CCS_PREFIX}.xxx.hdf5"

# Predict the new shots
python2.7 web_model.py -o $MODELS_PREDS_DIR --ccs-dir $CCS_DATA_DIR \
    --model standard --lanl-file $LANL_FILE
echo "$(date +%s): Predicted compositions for new CCS files"

python2.7 web_model.py -o $MODELS_PREDS_DIR --ccs-dir $CCS_DATA_DIR  \
    --model mixed --libs-mix-file $LIBS_MIX_FILE
echo "$(date +%s): Predicted compositions for new CCS files with Mixed model"

python2.7 web_model.py -o $MODELS_PREDS_DIR --ccs-dir $CCS_DATA_DIR \
    --model moc --moc-dir $MOC_DIR
echo "$(date +%s): Predicted compositions for new CCS files with MOC model"

python2.7 web_model.py -o $MODELS_PREDS_DIR --ccs-dir $CCS_DATA_DIR \
    --model dust
echo "$(date +%s): Predicted dust shots for new CCS files with the Dust Classifier"
