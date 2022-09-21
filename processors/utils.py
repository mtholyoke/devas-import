#!/usr/bin/env python3

import csv
import numpy as np
import openpyxl
import os
from collections import defaultdict
from glob import glob


def can_be_float(string):
    try:
        float(string)
    except Exception:
        return False
    else:
        return True


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


META_FIELDS = ['Carousel', 'Sample', 'Target', 'Location', 'Atmosphere',
               'LaserAttenuation', 'DistToTarget', 'Date', 'Projects']


def load_spectra(filepath, channels=None):
    with open(filepath, 'r', encoding='latin1') as f:
        contents = list(csv.reader(f, quotechar='+'))
    meta = {}
    prepro = True
    # Spectra are assumed to start at first line of comma-separated data
    for i, line in enumerate(contents):
        if line and ':' in line[0]:
            field = line[0].split(':')[0]
            val = line[0].split(':')[1].strip()
            if field == 'Carousels':
                field = 'Carousel'
                val = val.split(' ')[0].strip()
            if field == 'Dates':
                field = 'Date'
                val = val.split(' ')[0].strip()
            if field == 'Locations':
                field = 'Location'
                val = val.split(' ')[0].strip()
            if field in META_FIELDS:
                meta[field] = val
        elif all(can_be_float(item) for item in line):
            if '.' not in line:
                # All integers means this is formatted.
                prepro = False
            break
    if meta['Sample'].lower() in ('ti', 'dark'):
        return
    try:
        data = np.array(contents[i:], dtype=float)
    except Exception as e:
        return f'Bad spectra in file {filepath}: {e}'
    if channels and data.shape[0] != channels:
        e = f'expected {channels} channels, got {data.shape[0]}'
        return f'Wrong channel count in file {filepath}: {e}'
    return data.T, meta, prepro


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
