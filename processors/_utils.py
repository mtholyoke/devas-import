#!/usr/bin/env python3

import os


def mhc_spectrum_id(fpath):
    # TODO: Return None if ID can’t be determined.
    name, _ = os.path.splitext(os.path.basename(fpath))
    # Drop the '_spect' suffix.
    name, suffix = name.rsplit('_', 1)
    assert suffix == 'spect', 'Invalid spectrum path: ' + fpath
    return name
