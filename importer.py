from __future__ import print_function
from argparse import ArgumentParser
from time import time
import h5py
import numpy as np
import os


class _BaseImporter(object):
    '''Abstract base class. Requires implementations of these methods:
     - parse_masterfile(path) return meta
     - _get_id(fname) return ids or None
     - _process_spectra(filename, metadata) return spectra, meta

     Requires implementations of these members:
     - file_ext, e.g., '.txt'
     - pkey_field
     - driver, either 'family' for distributed or None for single file
    '''
    def main(self):
        ap = ArgumentParser()
        ap.add_argument('-i', '--input-dir', type=str, nargs='+',
                        help='Path to directories containing input data.')
        ap.add_argument('-o', '--output-prefix', type=str, required=True,
                        help='Path to directory containing output data.')
        ap.add_argument('-m', '--master', required=True,
                        help='Path to the master metadata file.')
        ap.add_argument('-m2', '--master2', required=False,
                        help='Path to an auxiliary master metadata file.')
        args = ap.parse_args()
        processed_ids = set(self.get_processed_ids(args.output_prefix))
        print('Found', len(processed_ids), 'existing IDs')
        dir_ids, dir_files = self.get_directory_data(*args.input_dir)
        print('Found', len(dir_ids), 'IDs in the input dir')
        new_files = []
        new_IDs = set()
        for ID, fname in zip(dir_ids, dir_files):
            if ID not in processed_ids and ID not in new_IDs:
                new_files.append(fname)
                new_IDs.add(ID)
        if not new_files:
            print('No new files, nothing to do.')
            return
        if args.master2:
            metadata = self.parse_masterfile(args.master, args.master2)
        else:
            metadata = self.parse_masterfile(args.master)
        self.process_data(new_files, metadata, args.output_prefix)


    def get_directory_data(self, *input_dirs):
        ids, files = [], []
        for input_dir in input_dirs:
            for root, _, filenames in os.walk(input_dir):
                for filename in filenames:
                    if filename.lower().endswith(self.file_ext.lower()):
                        files.append(os.path.join(root, filename))
                        ids.append(self._get_id(filename))
        return ids, files

    def get_processed_ids(self, file_prefix):
        fname = file_prefix + '_meta.npz'
        if not os.path.isfile(fname):
            return []
        meta = np.load(fname)
        return meta[self.pkey_field]

    def _write_metadata(self, fname, meta):
        if os.path.exists(fname):
            existing = np.load(fname, allow_pickle=True)
            for k, v in list(meta.items()):
                meta[k] = np.concatenate((existing[k], v))
        np.savez(fname, **meta)

    def process_data(self, files, metadata, output_prefix, chunk_size=500):
        print('Processing', len(files),
              'files in chunks of %d...' % chunk_size)
        total_chunks = int(np.ceil(float(len(files)) / chunk_size))
        toc = time()
        for i, chunk_idx in enumerate(xrange(0, len(files), chunk_size),
                                      start=1):
            print('chunk', i, 'of', total_chunks)
            flist = files[chunk_idx:chunk_idx+chunk_size]
            self._chunk_main(flist, metadata, output_prefix)
            tic = time()
            print('  took', tic - toc, 'seconds')
            toc = tic
        return

    def _chunk_main(self, filelist, metadata, output_prefix):
        all_spectra, all_meta = [], []
        for f in filelist:
            ret = self._process_spectra(f, metadata)
            if ret is None or ret[0] is None or ret[1] is None:
                # Something failed in the processing function
                continue
            spectra, meta = ret
            if issubclass(type(self), _VecImporter):
                pkeys = meta[self.pkey_field]
                n_meta = len(pkeys) if isinstance(pkeys,(list, np.ndarray)) else 1
                n_spectra = 1 if spectra.ndim == 1 else spectra.shape[0]
                if n_spectra != n_meta:
                    print('Mismatching # of shots:', os.path.basename(f))
                    continue
            if issubclass(type(self), _TrajImporter) and isinstance(spectra, list):
                all_spectra.extend(spectra)
                all_meta.extend(meta)
            else:
                all_spectra.append(spectra)
                all_meta.append(meta)
        if not all_spectra:
            return
        if isinstance(all_meta[0][self.pkey_field], (list, np.ndarray)):
            all_meta = dict((k, np.concatenate([m[k] for m in all_meta]))
                            for k in all_meta[0].keys())
        else:
            all_meta = dict((k, np.array([m[k] for m in all_meta]))
                            for k in all_meta[0].keys())
        output_suffix = '.hdf5' if self.driver is None else '.%03d.hdf5'
        if issubclass(type(self), _VecImporter):
            self._write_data(output_prefix + output_suffix,
                             np.vstack(all_spectra),
                             self.n_chans)
        elif issubclass(type(self), _TrajImporter):
            self._write_data(output_prefix + output_suffix,
                             all_spectra,
                             all_meta[self.pkey_field])
        else:
            print('Unknown class, cannot write file.')
            return
        self._write_metadata(output_prefix + '_meta.npz', all_meta)


class _VecImporter(_BaseImporter):
    '''Abstract base class. Requires implementations of these members:
     - n_chans e.g., 6144
    '''
    def _write_data(self, fpattern, spectra, n_chans):
        fh = h5py.File(fpattern, driver=self.driver, libver='latest')
        if '/spectra' in fh:
            dset = fh['/spectra']
            n = dset.shape[0]
            dset.resize(n + spectra.shape[0], axis=0)
            dset[n:] = spectra
        else:
            fh.create_dataset('spectra', data=spectra, maxshape=(None, n_chans))
        fh.close()


class _TrajImporter(_BaseImporter):
    def _write_data(self, fpattern, spectra, ids):
        fh = h5py.File(fpattern, driver=self.driver, libver='latest')
        for ID, spectrum in zip(ids, spectra):
            path = '/spectra/%s' % ID
            if path in fh:
                if np.array_equal(fh[path][:], spectrum):
                    print('WARNING: Overwriting previous entry in', path)
                del fh[path]
            fh.create_dataset(path, data=spectrum)
        fh.close()
