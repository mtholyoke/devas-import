#!/usr/bin/env python3

import numpy as np
from . import utils
from ._base import _VectorProcessor


class LIBSProcessor(_VectorProcessor):
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
        return utils.get_spectrum_id(filename)

    def get_input_data(self):
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
        self.logger.debug('Parsing metadata')
        return utils.parse_millennium_comps(self.paths['metadata'][0])

    def prepare_meta(self, meta, shot_num, name):
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
            self.logger.warn(f'Failed to get comps for {filename}: {e}')
            return None
        else:
            comps = [all_comps[elem][ind] for elem in elements]
            rock_type = all_noncomps[0][ind]
            random_no = all_noncomps[1][ind]
            matrix = all_noncomps[2][ind]
            if all_noncomps[3][ind]:
                dopant = all_noncomps[3][ind]
            if all_noncomps[4][ind]:
                projects = all_noncomps[4][ind].upper()
                projects = projects.translate({ord(c): None for c in ' ;'})
        metas = np.broadcast_arrays(shot_num, int(meta['Carousel']),
                                    meta['Sample'], int(meta['Target']),
                                    int(meta['Location']), meta['Atmosphere'],
                                    float(meta['LaserAttenuation']),
                                    float(meta['DistToTarget']), meta['Date'],
                                    projects, name, rock_type, int(random_no),
                                    matrix, float(dopant), *comps)
        meta_fields = [
            'Number', 'Carousel', 'Sample', 'Target', 'Location', 'Atmosphere',
            'LaserAttenuation', 'DistToTarget', 'Date', 'Projects', 'Name',
            'TASRockType', 'RandomNumber', 'Matrix', 'ApproxDopantConc'
        ] + elements
        return dict(zip(meta_fields, metas))

    def process_spectra(self, datafile):
        result = utils.load_spectra(datafile[1], self.channels)
        if not result:
            return
        if isinstance(result, str):
            self.logger.warn(result)
            return
        spectra, meta, is_prepro = result
        # TODO: Sort out the way this needs to work. This test and the
        # reassignment of spectra was copied from process_mhc_files;
        # the SuperLIBS processors have a failure condition instead:
        # assert is_prepro, 'Unexpected SuperLIBS raw data'
        if is_prepro:
            self.logger.warn(f'Found prepro in {datafile[1]}')
            spectra = spectra[1:]
        spectra = np.vstack((spectra.mean(0), spectra))
        shot_num = np.arange(spectra.shape[0])
        meta = self.prepare_meta(meta, shot_num, name=datafile[0])
        return spectra, meta
