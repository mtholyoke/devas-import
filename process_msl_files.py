import numpy as np
import os
import re

from importer import _VecImporter


class MSLImporter(_VecImporter):
    driver = 'family'
    file_ext = '.csv'
    pkey_field = 'ids'
    n_chans = 6144

    def get_processed_ids(self, file_prefix):
        raw_ids = super(MSLImporter, self).get_processed_ids(file_prefix)
        return [ID[4:] for ID in raw_ids] # maybe make this more general

    def parse_masterfile(self, filename):
        # This still misses a handful of spectra,
        # could try using specific usecols={}
        return np.recfromcsv(filename, names=True,
                             invalid_raise=False, comments='"')

    def _get_id(self, fname):
        parts = fname.split('_')
        return parts[1].rstrip('ccs') if len(parts)==3 else None

    def _parse_csv(self, filename):
      data = np.genfromtxt(filename, delimiter=',')
      shots = data[:, 1:-2].T
      mean_spectrum = data[:, -1].T
      return np.row_stack((mean_spectrum, shots))

    def _process_spectra(self, filename, metadata):
      spectra = self._parse_csv(filename)
      if (spectra.ndim==1 and spectra.shape[0]!=self.n_chans) or \
         (spectra.ndim==2 and spectra.shape[1]!=self.n_chans):
          return
      meta = self._make_meta(filename, metadata, include_mean_spectrum=True)
      return spectra, meta

    def _make_meta(self, filename, metadata, include_mean_spectrum=False):
        meta_idx = self._match_metadata(filename, metadata)
        if meta_idx is None:
            return
        meta_row = metadata[meta_idx:meta_idx+1]
        if include_mean_spectrum:
            # mean spectrum is shot #0, actual shots go from 1 to n inclusive
            shot_num = np.arange(meta_row.nbr_of_shots+1)
        else:
            shot_num = np.arange(1, meta_row.nbr_of_shots+1)
        # TODO: make sure this catches all the cases
        autofocus = meta_row.autofocus == 'Yes'
        # distance column has some non-numeric values, so we have to convert manually
        dist = float(meta_row.distance_m[0])
        # Make the id
        edr_id = '%s_%d' % (meta_row.edr_type[0], meta_row.spacecraft_clock[0])
        # Extend out all the unary data to nshots length.
        # This uses a fun trick where we broadcast the 1-length arrays against the
        # shot_num array, which avoids actually copying the data.
        metas = np.broadcast_arrays(shot_num, edr_id, meta_row.target, autofocus,
                                    dist, meta_row.laser_energy,
                                    meta_row.sol, meta_row.temperature)
        meta_names = ('numbers', 'ids', 'names', 'foci', 'distances', 'powers',
                      'sols', 'raw_temps')
        return dict(zip(meta_names, metas))

    def _match_metadata(self, filename, metadata):
        name, _ = os.path.splitext(os.path.basename(filename))
        m = re.match(r'([a-z0-9]+)_(\d+)[a-z]{3}_\w+', name)
        if not m:
            print 'Invalid CCS name:', name
            return
        edr_type = m.group(1)
        clock = int(m.group(2))
        row_idx, = np.where(metadata.spacecraft_clock == clock)
        if len(row_idx) == 0:
            print 'Master list does not contain ID: %s_%d' % (edr_type, clock)
            return
        if len(row_idx) > 1:
            print 'Master list contains duplicate IDs: %s_%d' % (edr_type, clock)
            return
        return row_idx[0]


if __name__ == '__main__':
    MSLImporter().main()
