#!/usr/bin/env python3

import numpy as np
from . import utils
from ._base import _VectorProcessor


class LIBSProcessor(_VectorProcessor):
    """
    Inherits from _base.py
    Processes spectra data from LIBS (i.e, ChemLIBS and SuperLIBS)

    Implements these methods required by _base.py:
    - get_id(filename) returns ID or None
    - parse_metadata() returns parsed metadata structure
    - process_spectra(filename, metadata) return spectra, meta

    Implements these members required by _base.py:
    - driver: family by default
    - file_ext: '_spect.csv' by default
    - pkey_field: 'Name' by default

    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logger = self.get_child_logger()
        required = ['channels']
        for attr in required:
            if not hasattr(self, attr):
                raise AttributeError(f'Attribute "{attr}" is required')
        defaults = {
            'driver': 'family',
            'file_ext': '_spect.csv',
            'pkey_field': 'Name',
        }
        for key, value in defaults.items():
            if not hasattr(self, key):
                setattr(self, key, value)

    def get_id(self, filename):
        """
        Returns a string representing the name of an individual spectra file
        without the spect.csv suffix.
        Parameters filename: the path to a spectra file
        """
        return utils.get_spectrum_id(filename)

    def get_input_data(self):
        """
        Returns a dictionary of files in a directory.
        """
        data = {}
        for dd in self.paths['data']:
            files = utils.find_spectrum_files(dd, self.file_ext)
            for file in files:
                if not self.get_id(file):
                    continue
                path = utils.get_directory(file)
                if path not in data:
                    data[path] = []
                data[path].append((self.get_id(file), file))
        return data

    def parse_metadata(self):
        """
        Returns data from Millennium_comps file. 
        """
        self.logger.debug('Parsing metadata')
        return utils.parse_millennium_comps(self.paths['metadata'][0])

    def prepare_meta(self, meta, shot_num, name):
        """
        Returns a dictionary of strings corresponding to metadata fields

        Parameter meta: the metadata contents of a spectra file
        Parameter shot_num: an numpy array
        Parameter name: the name of a spectra file
        """
        all_samps, all_comps, all_noncomps = self.metadata
        elements = sorted(all_comps.keys())
        sample = meta['Sample'].lower()
        all_samps = [samp.lower() if samp else None for samp in all_samps]
        rock_type = ''
        random_no = -1
        matrix = ''
        dopant = np.nan
        projects = ''
        try:
            ind = all_samps.index(sample)
        except Exception as e:
            self.logger.warn(f'Failed to get comps for {name}: {e}')
            return None
        else:
            comps = [all_comps[elem][ind] for elem in elements]
            rock_type = all_noncomps[0][ind]
            random_no = int(all_noncomps[1][ind])
            matrix = all_noncomps[2][ind]
            dopant = None
            if all_noncomps[3][ind]:
                dopant = float(all_noncomps[3][ind])
            if all_noncomps[4][ind]:
                projects = all_noncomps[4][ind].upper()
                projects = projects.translate({ord(c): None for c in ' ;'})

        numeric_meta = {
            'Carousel': {'cast': int, 'default': 0},
            'Target': {'cast': int, 'default': 0},
            'Location': {'cast': int, 'default': 0},
            'LaserAttenuation': {'cast': float, 'default': 0},
            'DistToTarget': {'cast': float, 'default': 0},
        } 
        for key, spec in numeric_meta.items():
            if key in meta:
                meta[key] = utils.clean_data(meta[key], **spec)
            else:
                meta[key] = spec['default']

        metas = np.broadcast_arrays(shot_num, meta['Carousel'],
                                    meta['Sample'], meta['Target'],
                                    meta['Location'], meta['Atmosphere'],
                                    meta['LaserAttenuation'],
                                    meta['DistToTarget'], meta['Date'],
                                    projects, name, rock_type, random_no,
                                    matrix, dopant, *comps)

        meta_fields = [
            'Number', 'Carousel', 'Sample', 'Target', 'Location', 'Atmosphere',
            'LaserAttenuation', 'DistToTarget', 'Date', 'Projects', 'Name',
            'TASRockType', 'RandomNumber', 'Matrix', 'ApproxDopantConc'
        ] + elements

        return dict(zip(meta_fields, metas))

    def process_spectra(self, datafile):
        """
        Returns a processed single file from a batch of file, 
        including data and metadata

        Parameter datafile: a single tuple representing a file
        """
        result = utils.load_spectra(datafile[1], self.channels)
        if not result:
            return
        if isinstance(result, str):
            self.logger.warn(result)
            return
        spectra, meta, is_prepro = result
        # TODO: This is required for SuperLIBS but not for ChemLIBS:
        # assert is_prepro, 'Unexpected SuperLIBS raw data'
        if is_prepro:
            spectra = spectra[1:]
        shot_num = [0]
        if not self.averaged:
            spectra = np.vstack((spectra.mean(0), spectra))
            shot_num = np.arange(spectra.shape[0])
        meta = self.prepare_meta(meta, shot_num, name=datafile[0]) 
        return spectra, meta
