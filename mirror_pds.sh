#!/usr/bin/env bash
set -e

# User settings
REMOTE_PREPROCESSED=ftp://pds-geosciences.wustl.edu/msl/msl-m-chemcam-libs-4_5-rdr-v1/mslccm_1xxx/
MASTER_FILE=msl_ccam_obs.csv

MSL_DIR=/mars/g/rch3/r/mdyar/MSL_PDS
CCS_DATA_DIR=$MSL_DIR/ccs_data
CCS_PREFIX=$CCS_DATA_DIR/ccs
CCS_ORIGINALS=$CCS_DATA_DIR/original

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
EOF
endtime=$(date +%s)
echo "### $(date) - Download finished after $((endtime - starttime)) seconds, starting processing." >> MSL_LOG

