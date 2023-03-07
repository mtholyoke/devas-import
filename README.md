# devas-import

Scripts for aggregating and preprocessing data for [Superman](https://github.com/all-umass/superman) service running at http://nemo.mtholyoke.edu and [Specx](https://github.com/mtholyoke/specx) service running at https://mossbauer.mtholyoke.edu.

The code here was adapted from original work by [@perimosocordiae](https://github.com/perimosocordiae).


## Requirements

For the development environment, you can either install the packages below or run a reasonably current version of [Lando](https://lando.dev/) (this was developed in Lando version 3.0.14 in 2021) for the development environment.

The code was developed in Python 3.7.8 with these packages:
- `h5py` 3.1.0
- `numpy` 1.20.1
- `openpyxl` 3.0.6
- `pyyaml` 5.4.1

The `mirror_pds.sh` driver script currently uses the [`lftp` utility](https://lftp.yar.ru/), which is available via `apt` for Debian and Ubuntu.

Before running `process_all.py` the first time, copy `config-sample.yml` to `config.yml` and edit the latter’s contents.


## Active contents

**NOTE:** The code in this branch is in active development.

### Driver script `config-sample.yml`

Shows sample and default values for config options. Copy to `config.yml` and edit that one.

### Driver script `process_all.py`

Runs the processors for all datasets in `config.yml`.

### Library package `processors/`

Defines processors to be run by `process_all.py`.


**TODO** Add contents defining new processor files from the Python 3 upgrades, then delete these old descriptions.

## Old active contents to be upgraded to run in Python 3

### Driver script `mirror_pds.sh`

Downloads MSL files from the Planetary Data Science repository at WUSTL, then runs processing scripts on them.

Some previous code (removed by commit `213d47e` in this repo) ran additional predictive models on this data, but the scripts were missing some component files by the time we got this code, and we have no way to regenerate them.

#### `process_msl_files.py`

The primary script to prepare data and metadata for DEVAS.

### Driver script `run-mhc-datasets.sh` _(becoming `process_all.py`)_

There are currently six local datasets receiving updates: MHC Mossbauer, MHC Raman, MHC ChemLIBS, and three flavors of MHC SuperLIBS: 5120, 10K, and 18K. This script runs their individual processing scripts (listed below), `rsync`s the results to the appropriate directory on the DEVAS server (and also the Mössbauer data to the Specx server), then triggers a data reload on DEVAS. It’s currently run nightly by `/etc/crontab`.

#### `_mhc_utils.py` _(becoming `processors/utils.py`)_

Common utilities for the processor scripts below.

#### `importer.py` _(becoming `processors/_base.py`)_

Base classes for the processor scripts below.

#### `process_mhc_files.py` _(becoming `processors/libs.py`)_

This script processes LIBS data; it’s set up for the MHC ChemLIBS dataset.

#### `process_mossbauer_files.py`

This script processes Mössbauer data; it’s set up for the MHC Mossbauer dataset.

#### `process_raman_files.py`

This script processes Raman data; it’s set up for the MHC Raman dataset.

#### `process_superlibs_files.py`

This script processes LIBS data; it’s set up for the MHC SuperLIBS 5120 dataset, which has varying numbers of channels and is handled (questionably) as trajectory data instead of vector.


## Old inactive contents to be upgraded or removed

### Driver script `cron_script.sh`

Invokes the two other driver scripts, `mirror_pds.sh` and `run-mhc-datasets.sh`. Could replace the latter as the primary driver being run on the server, but we haven’t done that yet.

#### `process_xrf_files.py`

Necessary for processing some static local datasets, but currently unused.
