#!/usr/bin/env python3

import numpy as np
import os.path
from . import utils
from ._base import _VectorProcessor


class LIBSProcessor(_VectorProcessor):
    """
    Inherits from BaseProcessor
    Processes spectra data from LIBS (i.e, ChemLIBS and SuperLIBS)

    Implements these methods required by BaseProcessor:
    - get_id(filename): returns ID or None
    - parse_metadata(): returns parsed metadata structure
    - process_spectra(filename, metadata): return spectra, meta

    Implements these members required by BaseProcessor:
    - driver: family by default
    - file_ext: '_spect.csv' by default
    - pkey_field: 'Name' by default

    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logger = self.get_child_logger()
        self.wavelengths = None
        self.si_constants = None
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

    def calculate_si_ratio(self, spectra):
        den_lo, den_hi, num_lo, num_hi = self.si_constants
        si_ratio = np.asarray(spectra[:, num_lo:num_hi].max(axis=1)
                              / spectra[:, den_lo:den_hi].max(axis=1))
        np.maximum(si_ratio, 0, out=si_ratio)
        return si_ratio

    def get_id(self, filename):
        """
        Retrieves the id of a file using the general LIBS
        get_spectrum_id function from utils.py

        Parameters
        ----------
        filename 
            The path to a spectra file.

        Returns
        -------
        data
            A string representing the name of an individual spectra file
            without the spect.csv suffix.
        """
        return utils.get_spectrum_id(filename)

    def get_input_data(self):
        """
        Overwrites get_input_data in BaseProcessor.
        
        Returns
        -------
        data
            A dictionary of files in a directory.
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
        Output logger message, then runs utils.py's 
        parse_millenium_comps.

        Returns
        -------
            Data from the metadata file.
        """
        self.logger.debug('Parsing metadata')
        return utils.parse_millennium_comps(self.paths['metadata'][0])

    def prepare_meta(self, meta, shot_num, name):
        """
        Sets up each meta field and cleans values. 

        Parameters 
        ----------
        meta 
            The metadata contents of a spectra file.
        shot_num 
            A numpy array.
        name 
            The name of the file for which meta is being prepared.
        
        Returns
        -------
            A dictionary of meta fields to meta values.
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
            self.logger.warning(f'Failed to get comps for {name}: {e}')
            return None
        else:
            comps = [all_comps[elem][ind] for elem in elements]
            rock_type = all_noncomps[0][ind]
            random_no = int(all_noncomps[1][ind])
            matrix = all_noncomps[2][ind]
            dopant = np.nan 
            if all_noncomps[3][ind]:
                dopant = all_noncomps[3][ind]
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
                                    matrix, float(dopant), *comps)

        meta_fields = [
            'Number', 'Carousel', 'Sample', 'Target', 'Location', 'Atmosphere',
            'LaserAttenuation', 'DistToTarget', 'Date', 'Projects', 'Name',
            'TASRockType', 'RandomNumber', 'Matrix', 'ApproxDopantConc'
        ] + elements

        return dict(zip(meta_fields, metas))

    def process_spectra(self, datafile):
        """
        From a single datafile, retrieves their spectra and metadata,
        while asserting certain properties.

        Parameters
        ----------
        datafile
            A single tuple representing a file.

        Returns
        -------
        spectra
            A single file's spectra values.
        meta
            A struct containing a single file's metadata values, 
            including si_test value.
        """
        result = utils.load_spectra(datafile[1], self.channels)
        if not result:
            return
        if isinstance(result, str):
            self.logger.warning(result)
            return
        spectra, meta, is_prepro = result
        if is_prepro:
            if self.wavelengths is None:
                self.wavelengths = np.array(spectra[0], dtype=float)
                self.si_constants = np.searchsorted(
                    self.wavelengths,
                    (288., 288.5, 633., 635.5))
            spectra = spectra[1:]
        shot_num = [0]
        if not self.averaged:
            spectra = np.vstack((spectra.mean(0), spectra))
            shot_num = np.arange(spectra.shape[0])
        meta = self.prepare_meta(meta, shot_num, name=datafile[0])
        meta['si_test'] = self.calculate_si_ratio(spectra)
        return spectra, meta

    def write_data(self, filepath, all_spectra, all_meta):
        """
        Override of _VectorImporter’s write_data() to output wavelengths.

        Parameters
        ----------
        filepath : string
            Target filename to write to.
        all_spectra
            Data to write.
        all_meta
            Metadata about spectra.
        """
        super().write_data(filepath, all_spectra, all_meta)
        if not os.path.isfile(self.paths['channels']):
            np.save(self.paths['channels'], self.wavelengths,
                    allow_pickle=True)
