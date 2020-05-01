from __future__ import print_function
import numpy as np

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

        all_samps, all_comps, all_projects = masterdata
        elements = sorted(all_comps.keys())
        sample = meta['Sample'].lower()
        all_samps = [samp.lower() if samp else None for samp in all_samps]
        projects = ''
        try:
            ind = all_samps.index(sample)
        except Exception as e:
            print('Failed to get compositions for', fname, ': ', e)
            comps = [np.nan for elem in elements]
        else:
            comps = [all_comps[elem][ind] for elem in elements]
            if all_projects[ind]:
              projects = all_projects[ind].upper().translate({ord(c): None for c in ' ;'})

        name = mhc_spectrum_id(fname)
        meta_tpl = dict(
            Carousel=int(meta['Carousel']), Sample=meta['Sample'],
            Target=int(meta['Target']), Location=int(meta['Location']),
            Atmosphere=meta['Atmosphere'],
            LaserAttenuation=float(meta['LaserAttenuation']),
            DistToTarget=float(meta['DistToTarget']),
            Date=meta['Date'], Projects=projects, Name=name)
        for e, c in zip(elements, comps):
            meta_tpl[e] = c

        trajs = []
        metas = []
        for shot_number, y in enumerate(spectra):
            trajs.append(np.column_stack((wave, y)))
            meta = meta_tpl.copy()
            meta['Number'] = shot_number
            meta['pkey'] = '%s:%02d' % (name, shot_number)
            metas.append(meta)
        return trajs, metas

if __name__ == '__main__':
    SuperLIBSImporter().main()
