#!/usr/bin/env python3

import os
from glob import glob

# Scan the data directory for *_spect.csv files.
# Note: this requires the files be in 1 level of subdirectory.
def find_spectrum_files(input_dir, file_ext):
    fpattern = os.path.join(input_dir, '*', f'*{file_ext}')
    return [f for f in glob(fpattern)
            if '_TI_' not in f.upper() and '_DARK_' not in f.upper()]

# Truncates "_spect.csv" from the filename to get the ID.
def get_spectrum_id(filename):
    name, _ = os.path.splitext(os.path.basename(filename))
    if not name.endswith('_spect') or len(name) < 7:
        return None
    return name[:-6]
