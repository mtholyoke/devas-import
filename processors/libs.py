#!/usr/bin/env python3

# import numpy as np

from ._base import _VectorProcessor
from ._utils import mhc_spectrum_id
# from _mhc_utils import (
#     find_mhc_spectrum_files, mhc_spectrum_id, parse_mhc_masterfile,
#     process_mhc_spectra)


class LibsProcessor(_VectorProcessor):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        required = [ 'channels', 'comps_file' ]
        for attr in required:
            if not hasattr(self, attr):
                raise AttributeError(f'Attribute "{attr}" is required')
        defaults = {
            'driver': 'family',
            'file_ext': '.csv',
            'pkey_field': 'Name',
        }
        for key, value in defaults.items():
            if not hasattr(self, key):
                setattr(self, key, value)

    def _get_id(self, fpath):
        return mhc_spectrum_id(fpath)



#     def get_directory_data(self, *input_dirs):
#         fpaths = []
#         for input_dir in input_dirs:
#             fpaths.extend(find_mhc_spectrum_files(input_dir))
#         print('Located', len(fpaths), 'MHC LIBS spectrum files.')
#         ids = [self._get_id(path) for path in fpaths]
#         return ids, fpaths
#
#     def parse_masterfile(self, filename):
#         return parse_mhc_masterfile(filename)
#
#     def _process_spectra(self, fname, masterdata):
#         result = process_mhc_spectra(fname, n_chans=self.n_chans)
#         if not result:
#             return
#         spectra, meta, is_prepro = result
#         if is_prepro:
#             spectra = spectra[1:]
#         spectra = np.vstack((spectra.mean(0), spectra))
#         shot_num = np.arange(spectra.shape[0])
#         all_samps, all_comps, all_noncomps = masterdata
#         elements = sorted(all_comps.keys())
#         sample = meta['Sample'].lower()
#         all_samps = [samp.lower() if samp else None for samp in all_samps]
#         rock_type = ''
#         random_no = -1
#         matrix = ''
#         dopant = np.nan
#         projects = ''
#         try:
#             ind = all_samps.index(sample)
#         except Exception as e:
#             print('Failed to get compositions for', fname, ': ', e)
#             return
#         else:
#             comps = [all_comps[elem][ind] for elem in elements]
#             rock_type = all_noncomps[0][ind]
#             random_no = all_noncomps[1][ind]
#             matrix = all_noncomps[2][ind]
#             if all_noncomps[3][ind]:
#                 dopant = all_noncomps[3][ind]
#             if all_noncomps[4][ind]:
#                 projects = all_noncomps[4][ind].upper().translate({ord(c): None for c in ' ;'})
#         name = self._get_id(fname)
#         metas = np.broadcast_arrays(shot_num, int(meta['Carousel']),
#                                     meta['Sample'], int(meta['Target']),
#                                     int(meta['Location']), meta['Atmosphere'],
#                                     float(meta['LaserAttenuation']),
#                                     float(meta['DistToTarget']), meta['Date'],
#                                     projects, name, rock_type, int(random_no),
#                                     matrix, float(dopant), *comps)
#         meta_fields = [
#             'Number', 'Carousel', 'Sample', 'Target', 'Location', 'Atmosphere',
#             'LaserAttenuation', 'DistToTarget', 'Date', 'Projects', 'Name',
#             'TASRockType', 'RandomNumber', 'Matrix', 'ApproxDopantConc'
#         ] + elements
#         return spectra, dict(zip(meta_fields, metas))
#
#
# if __name__ == '__main__':
#     MHCImporter().main()
