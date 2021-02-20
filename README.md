# devas-import

Scripts for aggregating and preprocessing data for [Superman](https://github.com/all-umass/superman) service running at http://nemo.mtholyoke.edu and [Specx](https://github.com/mtholyoke/specx) service running at https://mossbauer.mtholyoke.edu.

The code here was adapted from original work by [@perimosocordiae](https://github.com/perimosocordiae).

## Requirements

Currently the processing scripts only run in Python 2.7. You’ll need to negotiate mutually compatible versions of h5py, openpyxl, and numpy.

> The current server was built in Debian 8. I believe we used `apt` to install `python-h5py` and `python-numpy`, but `pip` to install `openpyxl`. The server was then upgraded to Debian 9, and reports these versions: `python-h5py 2.7.0-1`, `python-numpy 1:1.12.1-3`, `openpyxl 2.6.4`.

The `mirror_pds.sh` driver script currently uses the [`lftp` utility](https://lftp.yar.ru/), which is available via `apt` for Debian and Ubuntu.

**TODO:** Upgrade the code to run in Python 3.x and document dependencies better.

## Active Contents

### Driver script `mirror_pds.sh`

Downloads MSL files from the Planetary Data Science repository at WUSTL, then runs processing scripts on them.

Some previous code (removed by commit `213d47e` in this repo) ran additional predictive models on this data, but the scripts were missing some component files by the time we got this code, and we have no way to regenerate them.

#### `process_msl_files.py`

The primary script to prepare data and metadata for DEVAS.

### Driver script `run-mhc-datasets.sh`

There are currently six local datasets receiving updates: MHC Mossbauer, MHC Raman, MHC ChemLIBS, and three flavors of MHC SuperLIBS: 5120, 10K, and 18K. This script runs their individual processing scripts (listed below), `rsync`s the results to the appropriate directory on the DEVAS server (and also the Mössbauer data to the Specx server), then triggers a data reload on DEVAS. It’s currently run nightly by `/etc/crontab`.

#### `_mhc_utils.py`

Common utilities for the processor scripts below.

#### `importer.py`

Base classes for the processor scripts below.

#### `process_mhc_files.py`

This script processes LIBS data; it’s set up for the MHC ChemLIBS dataset.

#### `process_mossbauer_files.py`

This script processes Mössbauer data; it’s set up for the MHC Mossbauer dataset.

#### `process_raman_files.py`

This script processes Raman data; it’s set up for the MHC Raman dataset.

#### `process_superlibs_files.py`

This script processes LIBS data; it’s set up for the MHC SuperLIBS 5120 dataset, which has varying numbers of channels and is handled (questionably) as trajectory data instead of vector.

**TODO:** This script is somewhat unreliable at building on previous processing, and needs to get that sorted before it goes into heavy use.

#### `process_superlibs_10k_files.py`

This script processes LIBS data; it’s set up for the MHC SuperLIBS 10K dataset.

#### `process_superlibs_18k_files.py`

This script processes LIBS data; it’s set up for the MHC SuperLIBS 18k dataset.


## Inactive contents

### Driver script `cron_script.sh`

Invokes the two other driver scripts, `mirror_pds.sh` and `run-mhc-datasets.sh`. Could replace the latter as the primary driver being run on the server, but we haven’t done that yet.

#### `process_xrf_files.py`

Necessary for processing some static local datasets, but currently unused.
