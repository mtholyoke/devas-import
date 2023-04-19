# devas-import

Scripts for aggregating and preprocessing data for [Superman](https://github.com/all-umass/superman) service running at http://nemo.mtholyoke.edu and [Specx](https://github.com/mtholyoke/specx) service running at https://mossbauer.mtholyoke.edu.

The code here was adapted from original work by [@perimosocordiae](https://github.com/perimosocordiae).


## Requirements

For the development environment, you can either install the packages below or run a reasonably current version of [Lando](https://lando.dev/) (this was developed in Lando version 3.0.14 in 2021) for the development environment.

The code was developed in Python 3.9.6 with these packages:
- `h5py` 3.1.0
- `numpy` 1.23.3
- `openpyxl` 3.0.6
- `pyyaml` 5.4.1
These version are accurate as of March 27, 2023. 

The `mirror_pds.sh` driver script currently uses the [`lftp` utility](https://lftp.yar.ru/), which is available via `apt` for Debian and Ubuntu. Additionally, it used the the mail command, which is available with `apt install mailutils`.

Before running `process_all.py` the first time, copy `config-sample.yml` to `config.yml` and edit the latter’s contents.


## Active contents

NOTE: The files in this branch is in active development.

None currently. 


## Contents updated to Python 3.

### Driver script `mirror_pds.sh`

Downloads MSL files from the Planetary Data Science repository at WUSTL, then runs processing scripts on them.

Some previous code (removed by commit `213d47e` in this repo) ran additional predictive models on this data, but the scripts were missing some component files by the time we got this code, and we have no way to regenerate them.

Converting to a Python file as of 4/19/2023. Note that it currently runs using os.system: subprocess is the current standard, but issues were encountered when implementing it with lftp. 

### Driver script `cron_script.sh`

Invokes the two other driver scripts, `mirror_pds.sh` and `process_all.py`.

### Driver script `process_all.py` 

There are currently five local datasets receiving updates: MHC Mossbauer, MHC Raman, MHC ChemLIBS, and two versions of MHC SuperLIBS: 10k and 18k. The final three all run through the same processor, libs.py. This script runs this libs.py in addition to Mossbauer and Raman's individual scripts. 

#### `processors/utils.py`

Common utilities for the processor scripts below.

#### `processors/_base.py`

Provides base class for the individual processors. Additionally, provides two variants of this processor: VectorProcessor and TrajectoryProcessor.

#### `processors/libs.py`

This script processes all MHC LIBS data, namely ChemLIBS and both SuperLIBS. Its base is a VectorProcessor.

#### `processors/mossbauer.py`

This script processes MHC Mossbauer data. Its base is a TrajectoryProcessor.

#### `processors/msl.py`
This script processes MSL data. Its base is a VectorProcessor. 

#### `processors/raman.py`

This script processes MHC Raman data. Its base is a TrajectoryProcessor.


 

