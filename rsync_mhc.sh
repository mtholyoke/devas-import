#!/usr/bin/env bash
set -e

REMOTE_SERVER=rover.mtholyoke.edu
REMOTE_USER=tommy
RSYNC='rsync -e ssh -zrlv --inplace'
PYTHON='python2.7 -W i'

# LIBS -------------------

LIBS_LOCAL_DIR=/srv/nfs/common/spectra/LIBS/MHC
LIBS_REMOTE_DIR=/mnt/research-space/MHC.LIBS/DATA

echo "Syncing LIBS files..."
remote_addr="$REMOTE_USER@$REMOTE_SERVER:$LIBS_REMOTE_DIR"
$RSYNC "$remote_addr/prepro_no_blr*" "$LIBS_LOCAL_DIR/"
echo "  done."

# SuperLIBS -------------------

SUPERLIBS_LOCAL_DIR=/srv/nfs/common/spectra/SuperLIBS/MHC
SUPERLIBS_REMOTE_DIR='/mnt/research-space/MHC.SUPERLIBS/SAMPLE\ RUNS'

echo "Syncing SuperLIBS files..."
remote_addr="$REMOTE_USER@$REMOTE_SERVER:$SUPERLIBS_REMOTE_DIR"
$RSYNC "$remote_addr/prepro_no_blr*" "$SUPERLIBS_LOCAL_DIR/"
echo "  done."

# Raman ------------------

RAMAN_LOCAL_DIR=/srv/nfs/common/spectra/Raman/MHC
RAMAN_REMOTE_DIR=/mnt/research-space/rdata

echo "Syncing Raman files..."
remote_addr="$REMOTE_USER@$REMOTE_SERVER:$RAMAN_REMOTE_DIR"
$RSYNC "$remote_addr/raman*" "$RAMAN_LOCAL_DIR/"
echo "  done."

# Mossbauer ------------------

MOSS_LOCAL_DIR=/srv/nfs/common/spectra/Mossbauer/MHC
MOSS_REMOTE_DIR=/mnt/research-space/mdata

echo "Syncing Mossbauer files..."
remote_addr="$REMOTE_USER@$REMOTE_SERVER:$MOSS_REMOTE_DIR"
$RSYNC "$remote_addr/mossbauer*" "$MOSS_LOCAL_DIR/"
echo "  done."

# XRF ------------------

XRF_LOCAL_DIR=/srv/nfs/common/spectra/XRF
XRF_REMOTE_DIR=/mnt/research-space/xdata

echo "Syncing XRF files..."
remote_addr="$REMOTE_USER@$REMOTE_SERVER:$XRF_REMOTE_DIR"
$RSYNC "$remote_addr/tracer_17_csv/*" "$XRF_LOCAL_DIR/original"
$RSYNC "$remote_addr/olympus_17_csv/*" "$XRF_LOCAL_DIR/original"
$RSYNC "$remote_addr/$XRF_MASTER_FILE" "$XRF_LOCAL_DIR"
echo "  done."

echo "Processing new XRF files..."
# TODO: instead of deleting, move to a backup dir. Then, if the python
#       script fails, we can roll back.
rm -f $XRF_LOCAL_DIR/xrf*
$PYTHON process_xrf_files.py -o $XRF_LOCAL_DIR/xrf \
	-i $XRF_LOCAL_DIR/original -m $XRF_LOCAL_DIR/$XRF_MASTER_FILE \
	-m2 $LIBS_LOCAL_DIR/$LIBS_COMP_FILE
echo "  done."
