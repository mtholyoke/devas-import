#!/usr/bin/env python3

import h5py
import logging
import numpy as np
import re
import os
from time import time, strftime


class _BaseProcessor(object):
    '''
    Abstract base class. Requires implementations of these methods:
    - get_id(filename) returns ID or None
    - parse_metadata() returns parsed metadata structure
    - process_spectra(filename, metadata) return spectra, meta
    - write_data(output_pattern, all_spectra, all_meta)

    Requires implementations of these members:
    - driver, either 'family' for distributed or None for single file
    - file_ext, e.g., '.txt'
    - pkey_field
    '''
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.safe_name = re.sub(r'\W', '_', self.name)
        required = ['meta_file']
        for attr in required:
            if not hasattr(self, attr):
                raise AttributeError(f'Attribute "{attr}" is required')
        defaults = {
            'batch_size': 500,
            'logger': logging.getLogger(),
            'log_dir': 'nightly-logs',
            'output_dir': 'to-DEVAS',
            'output_prefix': 'prepro_no_blr',
        }
        for key, value in defaults.items():
            if not hasattr(self, key):
                setattr(self, key, value)
        self.construct_paths()

    def main(self):
        self.logger.info(f'Starting processing for {self.name}')
        processed_ids = set(self.get_processed_ids())
        self.logger.info(f'Found {len(processed_ids)} IDs in existing output')
        input_data = self.get_input_data()
        id_count = len([x for batch in input_data.values() for x in batch])
        dirs = 'directory' if len(self.paths['data']) == 1 else 'directories'
        self.logger.info(f'Found {id_count} IDs in the data {dirs}')
        unprocessed = self.filter_input_data(input_data, processed_ids)
        if not unprocessed:
            self.logger.info('No new IDs, nothing to do')
            return
        self.metadata = self.parse_metadata()
        self.process_all(unprocessed)
        self.logger.info(f'Finished processing for {self.name}')

    def construct_paths(self):
        root = getattr(self, 'root_dir', '')
        base = os.path.join(root, getattr(self, 'base_dir', ''))
        meta = getattr(self, 'meta_file')
        if isinstance(meta, str):
            meta = [meta]
        meta = [os.path.join(base, f) for f in meta]
        data = getattr(self, 'data_dir', '')
        if isinstance(data, str):
            data = [data]
        data = [os.path.join(base, d) for d in data]
        logdir = os.path.join(base, getattr(self, 'log_dir', ''))
        if not os.path.exists(logdir):
            os.makedirs(logdir, mode=0o755)
        logfile = self.safe_name + '-' + strftime('%Y-%m-%d')
        if hasattr(self, 'log_suffix') and self.log_suffix:
            logfile += '-' + self.log_suffix
        logpath = os.path.join(logdir, logfile + '.log')
        output = os.path.join(base, getattr(self, 'output_dir', ''))
        if not os.path.exists(output):
            os.makedirs(output, mode=0o755)
        self.paths = {
          'base': base,
          'metadata': meta,
          'data': data,
          'log': logpath,
          'output': output,
        }

    # Removes any files we’ve already processed or queued for processing.
    def filter_input_data(self, input_data, processed_ids):
        unprocessed = {}
        for dirname in input_data:
            for file in input_data[dirname]:
                if file[0] in processed_ids:
                    continue
                if dirname in unprocessed:
                    if file in unprocessed[dirname]:
                        continue
                else:
                    unprocessed[dirname] = []
                unprocessed[dirname].append(file)
        return unprocessed

    # Creates a child log with the root logger’s formatter.
    def get_child_logger(self):
        handler = logging.FileHandler(self.paths['log'])
        handler.setFormatter(self.logger.handlers[0].formatter)
        logger = self.logger.getChild(self.safe_name)
        logger.addHandler(handler)
        return logger

    # Scans the input data directory and returns tuples (ID, filepath).
    def get_input_data(self):
        data = []
        for input_dir in self.paths['data']:
            for root, _, filenames in os.walk(input_dir):
                for filename in filenames:
                    if filename.lower().endswith(self.file_ext.lower()):
                        file_id = self.get_id(filename)
                        if file_id is not None:
                            data.append((file_id, os.path.join(root, filename)))
        return {'.': data}

    def get_processed_ids(self):
        filename = self.output_prefix + '_meta.npz'
        filepath = os.path.join(self.paths['output'], filename)
        self.logger.debug(f'Checking for previous output file {filepath}')
        if not os.path.isfile(filepath):
            return []
        meta = np.load(filepath)
        return meta[self.pkey_field]

    def is_trajectory(self):
        return False

    def make_batches(self, unprocessed):
        data = {}
        for dirname, files in unprocessed.items():
            if len(files) > self.batch_size:
                batches = [files[i:i + self.batch_size]
                           for i in range(0, len(files), self.batch_size)]
            else:
                batches = [files]
            data[dirname] = batches

        # Label the batches for processing:
        to_process = {}
        count = len([b for d in data for b in data[d]])
        i = 1
        for dirname, batches in data.items():
            for batch in batches:
                label = f'batch {i} of {count}'
                i += 1
                if dirname != '.':
                    label = f'directory {dirname} ({label})'
                to_process[label] = batch
        return to_process

    def process_all(self, unprocessed):
        to_process = self.make_batches(unprocessed)
        toc = time()
        for label, batch in to_process.items():
            file = 'file' if len(batch) == 1 else 'files'
            self.logger.info(f'Starting {len(batch)} {file} in {label}')
            self.process_batch(batch)
            tic = time()
            self.logger.debug(f'Batch completed in {tic - toc:0.1f} seconds')
            toc = tic
        return

    def process_batch(self, batch):
        all_spectra, all_meta = [], []
        for datafile in batch:
            spectra, meta = self.process_file(datafile)
            if spectra is None or meta is None:
                continue
            if self.is_trajectory() and isinstance(spectra, list):
                all_spectra.extend(spectra)
                all_meta.extend(meta)
            else:
                all_spectra.append(spectra)
                all_meta.append(meta)
        if not all_spectra:
            self.logger.error('No spectra found in batch')
            return
        all_meta = self.restructure_meta(all_meta)
        output_suffix = '.hdf5' if self.driver is None else '.%03d.hdf5'
        output_pattern = self.output_prefix + output_suffix
        ouput_filepath = os.path.join(self.paths['output'], output_pattern)
        self.write_data(ouput_filepath, all_spectra, all_meta)
        self.write_metadata(all_meta)

    # This is extended by _VectorProcessor.
    def process_file(self, datafile):
        processed = self.process_spectra(datafile)
        if processed is None or processed[0] is None or processed[1] is None:
            self.logger.warn(f'Problem processing {datafile[1]}')
            return None, None
        return processed

    def restructure_meta(self, all_meta):
        if isinstance(all_meta[0][self.pkey_field], (list, np.ndarray)):
            return dict((k, np.concatenate([m[k] for m in all_meta]))
                        for k in all_meta[0].keys())
        return dict((k, np.array([m[k] for m in all_meta]))
                    for k in all_meta[0].keys())

    def write_metadata(self, all_meta):
        filename = self.output_prefix + '_meta.npz'
        filepath = os.path.join(self.paths['output'], filename)
        if os.path.exists(filepath):
            existing = np.load(filepath, allow_pickle=True)
            for k, v in list(all_meta.items()):
                all_meta[k] = np.concatenate((existing[k], v))
        np.savez(filepath, **all_meta)


class _VectorProcessor(_BaseProcessor):
    '''
    Abstract base class. Requires implementations of these members:
    - n_chans e.g., 6144
    '''
    def process_file(self, datafile):
        spectra, meta = super().process_file(datafile)
        if spectra is None or meta is None:
            return None, None
        pkeys = meta[self.pkey_field]
        n_meta = len(pkeys) if isinstance(pkeys, (list, np.ndarray)) else 1
        n_spectra = 1 if spectra.ndim == 1 else spectra.shape[0]
        if n_spectra != n_meta:
            self.logger.warn(f'Unexpected number of shots in {filepath[1]}')
            return None, None
        return spectra, meta

    def write_data(self, filepath, all_spectra, all_meta):
        spectra = np.vstack(all_spectra)
        fh = h5py.File(filepath, 'a', driver=self.driver, libver='latest')
        if '/spectra' in fh:
            dset = fh['/spectra']
            n = dset.shape[0]
            dset.resize(n + spectra.shape[0], axis=0)
            dset[n:] = spectra
        else:
            fh.create_dataset('spectra', chunks=True, data=spectra,
                              maxshape=(None, self.channels))
        fh.close()


class _TrajectoryProcessor(_BaseProcessor):
    def is_trajectory(self):
        return True

    def write_data(self, filepath, all_spectra, all_meta):
        ids = all_meta[self.pkey_field]
        fh = h5py.File(filepath, 'a', driver=self.driver, libver='latest')
        for id, spectrum in zip(ids, all_spectra):
            path = f'/spectra/{id}'
            if path in fh:
                self.logger.warn(f'Overwriting previous entry in {path}')
                del fh[path]
            fh.create_dataset(path, data=spectrum)
        fh.close()
