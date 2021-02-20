#!/usr/bin/env bash
set -e

# User settings
REMOTE_PREPROCESSED=ftp://pds-geosciences.wustl.edu/msl/msl-m-chemcam-libs-4_5-rdr-v1/mslccm_1xxx/
MASTER_FILE=msl_ccam_obs.csv

MSL_DIR=/mars/g/rch3/r/mdyar/MSL_PDS
CCS_DATA_DIR=$MSL_DIR/ccs_data
CCS_PREFIX=$CCS_DATA_DIR/ccs
CCS_ORIGINALS=$CCS_DATA_DIR/original

# Download Masterfile, processed spectra, & MOC predictions
starttime=$(date +%s)
echo "$starttime: Starting MSL data downloads..."
/usr/bin/lftp $REMOTE_PREPROCESSED <<EOF
 get -c document/$MASTER_FILE  -o $CCS_DATA_DIR/$MASTER_FILE
 mirror -c -I 'cl5_*ccs_*.csv' --no-empty-dirs data $CCS_ORIGINALS
EOF
endtime=$(date +%s)
echo "$endtime: Download finished after $((endtime - starttime)) seconds."

# Add the new CCS files to the server-readable data
python2.7 process_msl_files.py -o $CCS_PREFIX -i $CCS_ORIGINALS -m $CCS_DATA_DIR/$MASTER_FILE
echo "$(date +%s): Added new CCS files to ${CCS_PREFIX}.xxx.hdf5"
