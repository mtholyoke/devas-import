#!/usr/bin/env python3

import numpy as np
import openpyxl
import os
from collections import defaultdict
from glob import glob


# Scan the data directory for *_spect.csv files.
# Note: this requires the files be in 1 level of subdirectory.
def find_spectrum_files(input_dir, file_ext):
    fpattern = os.path.join(input_dir, '*', f'*{file_ext}')
    return [f for f in glob(fpattern)
            if '_TI_' not in f.upper() and '_DARK_' not in f.upper()]


def get_element_columns(sheet):
    elem_cols = []
    for col, _ in enumerate(sheet.columns, start=1):
        check = sheet.cell(row=1, column=col).value
        if not check or 'X' not in check:
            continue
        name = sheet.cell(row=2, column=col).value
        if not name:
            raise ValueError('Bad name for checked column %d' % col)
        elem_cols.append(('e_' + name, col))
    return elem_cols


# Truncates "_spect.csv" from the filename to get the ID.
def get_spectrum_id(filename):
    name, _ = os.path.splitext(os.path.basename(filename))
    if not name.endswith('_spect') or len(name) < 7:
        return None
    return name[:-6]


def parse_millennium_comps(filepath):
    book = openpyxl.load_workbook(filepath, data_only=True)
    sheet = book.active
    elem_cols = get_element_columns(sheet)
    samples = []
    rock_types = []
    randoms = []
    matrices = []
    dopants = []
    projects = []
    compositions = defaultdict(list)
    for i, _ in enumerate(sheet.rows):
        if i < 4:
            continue
        samples.append(sheet.cell(row=i, column=1).value)
        rock_types.append(sheet.cell(row=i, column=2).value)
        randoms.append(sheet.cell(row=i, column=3).value)
        matrices.append(sheet.cell(row=i, column=4).value)
        dopants.append(sheet.cell(row=i, column=5).value)
        projects.append(sheet.cell(row=i, column=6).value)
        for elem, col in elem_cols:
            if col < 7:
                continue
            val = sheet.cell(row=i, column=col).value
            if isinstance(val, float) or isinstance(val, int):
                compositions[elem].append(val)
            else:
                compositions[elem].append(np.nan)
    noncomps = [rock_types, randoms, matrices, dopants, projects]
    return samples, compositions, noncomps
