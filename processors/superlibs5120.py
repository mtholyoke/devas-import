#!/usr/bin/env python3

import numpy as np
from . import utils
from ._base import _TrajectoryProcessor


class SuperLIBS5120Processor(_TrajectoryProcessor):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logger = self.get_child_logger()
        # required = []
        # for attr in required:
        #     if not hasattr(self, attr):
        #         raise AttributeError(f'Attribute "{attr}" is required')
        defaults = {
            'driver': 'family',
            'file_ext': '_spect.csv',
            'pkey_field': 'pkey',
        }
        for key, value in defaults.items():
            if not hasattr(self, key):
                setattr(self, key, value)

    def get_id(self, filename):
        return utils.get_spectrum_id(filename)

    def get_input_data(self):
        filepaths = []
        for dd in self.paths['data']:
            filepaths.extend(utils.find_spectrum_files(dd, self.file_ext))
        return [(self.get_id(path), path)
                for path in filepaths if self.get_id(path)]

    def parse_metadata(self):
        self.logger.debug('Parsing metadata')
        return utils.parse_millennium_comps(self.paths['metadata'][0])

    def prepare_meta(self, meta, wave, name=datafile[0]):
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
        meta_template = {
            'Carousel': int(meta['Carousel']),
            'Sample': meta['Sample'],
            'Target': int(meta['Target']),
            'Location': int(meta['Location']),
            'Atmosphere': meta['Atmosphere'],
            'LaserAttenuation': float(meta['LaserAttenuation']),
            'DistToTarget': float(meta['DistToTarget']),
            'Date': meta['Date'],
            'Projects': projects,
            'Name': name,
            'TASRockType': rock_type,
            'RandomNumber': int(random_no),
            'Matrix': matrix,
            'ApproxDopantConc': float(dopant),
        }
        for e, c in zip(elements, comps):
            meta_template[e] = c

        # Copied from superman-web/backend/web_datasets.py
        chan_ranges = (288., 288.5, 633., 635.5)
        den_lo, den_hi, num_lo, num_hi = np.searchsorted(wave, chan_ranges)

        trajs = []
        metas = []
        for shot_number, y in enumerate(spectra):
            trajs.append(np.column_stack((wave, y)))
            meta_instance =
            metas.append(meta_instance)


    def process_spectra(self, fname, masterdata):
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
        wave = spectra[0].copy()
        spectra[0] = spectra[1:].mean(axis=0)
        meta = self.prepare_meta(meta, wave, name=datafile[0])
        return trajs, metas
        # return spectra, meta




        # trajs = []
        # metas = []
        # for shot_number, y in enumerate(spectra):
        #     trajs.append(np.column_stack((wave, y)))
            meta = meta_tpl.copy()
            meta['Number'] = shot_number
            meta['pkey'] = '%s:%02d' % (name, shot_number)

            # Adapted from superman-web/backend/web_datasets.py to
            # compute the Si Ratio as a proxy for temperature:
            try:
                num_list = y[num_lo:num_hi]
                den_list = y[den_lo:den_hi]
                if not num_list.size or not den_list.size:
                    si_ratio = np.nan
                    if shot_number == 0:
                        print("WARNING: can't calculate Si Ratio in file:", fname)
                else:
                    si_ratio = max(0, num_list.max() / den_list.max())
                meta['Si Ratio'] = si_ratio
            except Exception as e:
                print('ERROR calculating Si Ratio in file:', fname, 'shot:', shot_number)
                print('  Numerator [', num_lo, ':', num_hi, ']:', y[num_lo:num_hi])
                print('  Denominator [', den_lo, ':', den_hi, ']:', y[den_lo:den_hi])
                print('  Exception:', str(e))
                raise

        #     metas.append(meta)
        # return trajs, metas
