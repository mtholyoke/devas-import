# devas-import

Scripts for aggregating and preprocessing data for [Superman](https://github.com/all-umass/superman) service running at http://nemo.mtholyoke.edu and [Specx](https://github.com/mtholyoke/specx) service running at https://mossbauer.mtholyoke.edu.

The code here was adapted from original work by [@perimosocordiae](https://github.com/perimosocordiae).

## Requirements

Currently the processing scripts only run in Python 2.7. You’ll need to negotiate compatible versions of h5py, openpyxl, and numpy.

The `mirror_pds.sh` driver script currently uses the [`lftp` utility](https://lftp.yar.ru/).

The `web_model.py` script requires the [Superman](https://github.com/all-umass/superman) library

**TODO:** Upgrade the code to run in Python 3.8, remove the need for `lftp`, and document the versions better.

**TODO:** Current server needs an upgrade; don’t forget to fix directory names for new permanent home.

## Active Contents

### Driver script `run-mhc-datasets.sh`

There are currently four local datasets receiving updates: MHC Mossbauer, MHC Raman, MHC ChemLIBS, and MHC SuperLIBS 5120. This script runs their individual processing scripts (listed below), `rsync`s the results to the appropriate directory on the DEVAS server, then triggers a data reload on that server. It’s currently run nightly by `/etc/crontab`.

We expect two more SuperLIBS datasets in the near future.

#### `_mhc_utils.py`

Common utilities for the processor scripts below.

#### `importer.py`

Base classes for the processor scripts below.

#### `process_mhc_files.py`

This script processes LIBS data; it’s used by the MHC ChemLIBS dataset.

#### `process_mossbauer_files.py`

This script processes Mössbauer data; it’s used by the MHC Mossbauer dataset.

#### `process_raman_files.py`

This script processes Raman data; it’s used by the MHC Raman dataset.

#### `process_superlibs_files.py`

This script processes LIBS data; it’s used by the MHC SuperLIBS 5120 dataset. In the future, it may need to be split into vector and trajectory versions.

## Inactive contents

### Driver script `cron_script.sh`

Invokes the two other driver scripts, `mirror_pds.sh` and `run-mhc-datasets.sh`. When the former is working, will replace the latter as the primary driver being run on the server.

#### `process_xrf_files.py`

Necessary for processing some static local datasets, but currently unused.

### Driver script `mirror_pds.sh`

Downloads MSL files from the Planetary Data Science repository at WUSTL, then runs processing scripts on them.

**TODO:** Find the missing some component files for `web_model.py` because the output of this processing is expected in DEVAS.

#### `kate_masks.py`

Used by `web_model.py`.

#### `process_msl_files.py`

The primary script to prepare data and metadata for DEVAS.

#### `web_model.py`

Processes the MSL data files to predict compositions and dust shots.
