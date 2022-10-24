from __future__ import print_function
import numpy as np
import os

from importer import _TrajImporter
from _mhc_utils import (
    find_mhc_spectrum_files, mhc_spectrum_id, parse_mhc_masterfile,
    process_mhc_spectra)


class SuperLIBSImporter(_TrajImporter):
    driver = 'family'
    file_ext = '.csv'
    pkey_field = 'pkey'

    def get_directory_data(self, *input_dirs):
        fpaths = []
        for input_dir in input_dirs:
            fpaths.extend(find_mhc_spectrum_files(input_dir))
        print('Located', len(fpaths), 'MHC SuperLIBS spectrum files.')
        ids = [mhc_spectrum_id(path) for path in fpaths]
        return ids, fpaths

    def _get_id(self, fpath):
        return mhc_spectrum_id(fpath)

    def get_processed_ids(self, file_prefix):
        fname = file_prefix + '_meta.npz'
        if not os.path.isfile(fname):
            return []
        meta = np.load(fname)
        keys = meta[self.pkey_field]
        save = list(set([key.split(':')[0] for key in keys]))
        return save

    def parse_masterfile(self, filename):
        return parse_mhc_masterfile(filename)

    def _process_spectra(self, fname, masterdata):
        result = process_mhc_spectra(fname)
        if not result:
            return
        spectra, meta, is_prepro = result
        assert is_prepro, 'Unexpected SuperLIBS raw data'
        wave = spectra[0].copy()
        spectra[0] = spectra[1:].mean(axis=0)

        all_samps, all_comps, all_noncomps = masterdata
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
            print('Failed to get compositions for', fname, ': ', e)
            return
        else:
            comps = [all_comps[elem][ind] for elem in elements]
            rock_type = all_noncomps[0][ind]
            random_no = all_noncomps[1][ind]
            matrix = all_noncomps[2][ind]
            if all_noncomps[3][ind]:
                dopant = all_noncomps[3][ind]
            if all_noncomps[4][ind]:
                projects = all_noncomps[4][ind].upper().translate({ord(c): None for c in ' ;'})

        name = mhc_spectrum_id(fname)
        meta_tpl = dict(
            Carousel=int(meta['Carousel']), Sample=meta['Sample'],
            Target=int(meta['Target']), Location=int(meta['Location']),
            Atmosphere=meta['Atmosphere'],
            LaserAttenuation=float(meta['LaserAttenuation']),
            DistToTarget=float(meta['DistToTarget']),
            Date=meta['Date'], Projects=projects, Name=name,
            TASRockType=rock_type, RandomNumber=int(random_no),
            Matrix=matrix, ApproxDopantConc=float(dopant))
        for e, c in zip(elements, comps):
            meta_tpl[e] = c

        # Copied from superman-web/backend/web_datasets.py
        chan_ranges = (288., 288.5, 633., 635.5)
        den_lo, den_hi, num_lo, num_hi = np.searchsorted(wave, chan_ranges)

        trajs = []
        metas = []
        for shot_number, y in enumerate(spectra):
            trajs.append(np.column_stack((wave, y)))
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

            metas.append(meta)
        return trajs, metas

if __name__ == '__main__':
    SuperLIBSImporter().main()
