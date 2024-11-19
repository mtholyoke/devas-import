# devas-import

Scripts for aggregating and preprocessing data for [DEVAS Web](https://github.com/mtholyoke/devas-web) (formerly [superman-web](https://github.com/all-umass/superman-web)) service running at http://nemo.mtholyoke.edu and [Specx](https://github.com/mtholyoke/specx) service running at https://mossbauer.mtholyoke.edu.

The code here was adapted from original work by [@perimosocordiae](https://github.com/perimosocordiae).



## Requirements

The current production environment is an Ubuntu 22.04 server running Python 3.10.12 with the modules listed in `requirements.txt`. See the [DEVAS web](https://github.com/mtholyoke/devas-web) repo for notes on installing the [Superman](https://github.com/all-umass/superman) library.

The `mirror_pds.py` driver script currently uses the [`lftp` utility](https://lftp.yar.ru/), which is available via `apt` for Debian and Ubuntu.

Before running either script the first time, copy `config-sample.yml` to `config.yml` and edit the latter’s contents.

In practice, it’s useful to have a small driver script to be called by `cron` that runs the script(s) and copies the output to the DEVAS Web server.



## `mirror_pds.py`

Downloads MSL files from the Planetary Data Science repository at WUSTL, then runs processing scripts on them.

Some previous code (removed by commit `213d47e` in this repo) ran additional predictive models on this data, but the scripts were missing some component files by the time we got this code, and we have no way to regenerate them.

Converted from shell script to Python on 4/19/2023.

**TODO:** This currently runs `lftp` using `os.system()`; `subprocess.Popen()` would be preferable, but we encountered implementation issues.



## `process_all.py`

This script checks for updates to several datasets collected from instruments at MHC as well as the MSL files from `mirror_pds.py`, and runs the appropriate processing script (below) based on the type of data specified in the config file.


### Support files

#### `processors/utils.py`

Common utilities for the processor scripts below.

#### `processors/_base.py`

Provides base class for the individual processors. Additionally, provides two variants of this processor: VectorProcessor and TrajectoryProcessor.

#### `processors/libs.py`

This script processes all MHC LIBS data, namely ChemLIBS and both SuperLIBS.

#### `processors/mossbauer.py`

This script processes MHC Mossbauer data.

#### `processors/msl.py`

This script processes the MSL data downloaded by `mirror_pds.py`.

**TODO:** Consolidate with LIBS?

#### `processors/raman.py`

This script processes MHC Raman data. Its base is a TrajectoryProcessor.
