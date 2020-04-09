from __future__ import print_function
import numpy as np
from collections import defaultdict
from openpyxl import load_workbook
from os.path import basename
from time import time

from importer import _TrajImporter
from process_mhc_files import MHCImporter

class XRFImporter(_TrajImporter):
    driver = None
    file_ext = '.csv'
    pkey_field = 'spectrum_number'

    def parse_masterfile(self, master_file, comp_file):
        print('Loading masterfile...')
        start = time()
        book = load_workbook(master_file, data_only=True)
        sheet = book.active
        headers = [field.value for field in sheet.rows[0]]
        meta = defaultdict(list)
        id_ind = headers==self.pkey_field
        for i, row in enumerate(sheet.rows):
            if i < 1 or row[id_ind].value is None:
                continue
            for header, cell in zip(headers, row):
                if not header:
                    continue
                meta[header].append(cell.value)
        print('  done. %.2fs' % (time() - start))
        self.samps,self.comps,_ = MHCImporter().parse_masterfile(comp_file)
        return meta

    def _process_spectra(self, fname, metadata):
        pkeys = np.array(metadata[self.pkey_field], dtype=str)
        meta_idx, = np.where(pkeys == str(self._get_id(fname)))
        if len(meta_idx) != 1:
            print('  Cannot match spectrum and masterfile', fname)
            return
        meta = {key: val[meta_idx[0]] for key, val in metadata.items()}
        try:
            channel_ev_row = np.genfromtxt(fname, skip_header=17, max_rows=1,
                                           delimiter=',', dtype=str, comments=False)
            if channel_ev_row[0] != 'eV per channel':
                raise ValueError('Missing eV per channel')
            channel_ev = float(channel_ev_row[1])
            converters = {0:lambda x: float(x) / 1000,
                          1:lambda x: float(str(x).strip('"'))}
            traj = np.genfromtxt(fname, skip_header=21, delimiter=',', converters=converters)
            if traj.ndim != 2 or traj.shape[1] != 2:
                raise ValueError('Spectrum must be a trajectory')
            if np.isnan(traj).any():
                raise ValueError('Trajectory contains NaNs')
            traj[:,0] *= channel_ev
            cmask = np.array(str(meta['pellet_name']).strip()) == self.samps
            if not sum(cmask):
                raise ValueError('Missing compositions')
            for elem, comp in self.comps.iteritems():
                meta[elem] = np.array(comp)[cmask][0]
        except Exception as e:
            print(' ', e, fname)
            return
        # Make sure wavelengths are increasing
        if traj[0,0] > traj[1,0]:
            traj = traj[::-1]
        return traj, meta

    def _get_id(self, path):
        try:
            return int(basename(path).rstrip(self.file_ext))
        except:
            return


if __name__ == '__main__':
    XRFImporter().main()
