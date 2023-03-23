#!/usr/bin/env python3

import h5py
import logging
import numpy as np
import re
import os
from time import time, strftime

"""
Description

Parameters
----------
p1:
p2:

Returns
---------
"""


class _BaseProcessor(object):
    """
    Abstract base class for processing spectrum data.

    Requires implementations of these methods:
    - `get_id(filename)`: returns ID or None.
    - `parse_metadata()`: returns parsed metadata structure.
    - `process_spectra(filename, metadata)`: return spectra, meta.
    - `write_data(output_pattern, all_spectra, all_meta)`

    Requires implementations of these members:
    - `driver`: either 'family' for distributed or None for one file.
    - `file_ext`: what spectra files all end with, like '_spect.csv'.
    - `pkey_field`: which metadata uniquely identifies spectra.
    """

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
            'averaged': False,
            'logger': logging.getLogger(),
            'log_dir': 'nightly-logs',
            'output_dir': 'to-DEVAS',
            'output_prefix': 'prepro_no_blr',
            'channels_file': 'prepro_channels.npy'
        }
        for key, value in defaults.items():
            if not hasattr(self, key):
                setattr(self, key, value)
        self.construct_paths()

    def main(self):
        """
        Drive the processing of spectra from input data.
        """
        self.logger.info(f'Starting processing for {self.name}')
        # Check output for spectra we have already processed
        processed_ids = set(self.get_processed_ids())
        self.logger.info(f'Found {len(processed_ids)} IDs in existing output')
        # Scan input data for all possible spectra to process
        input_data = self.get_input_data()
        if not input_data:
            self.logger.info('No data in input, nothing to do')
            return
        id_count = len([file for val in input_data.values() for file in val])
        dirs = 'directory' if len(self.paths['data']) == 1 else 'directories'
        self.logger.info(f'Found {id_count} IDs in the data {dirs}')
        # Remove previously processed spectra
        unprocessed = self.filter_input_data(input_data, processed_ids)
        if not unprocessed:
            self.logger.info('No new IDs, nothing to do')
            return
        # Process the spectra
        self.metadata = self.parse_metadata()
        self.process_all(unprocessed)
        self.logger.info(f'Finished processing for {self.name}')

    def construct_paths(self):
        """
        Identify input and output directories based on config.
        """
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
        channels = os.path.join(output, self.channels_file)
        self.paths = {
          'base': base,
          'metadata': meta,
          'data': data,
          'log': logpath,
          'output': output,
          'channels': channels,
        }

    def filter_input_data(self, input_data, processed_ids):
        """
        Remove previously seen files from `input_data`.

        Parameters
        ----------
        input_data : dict
            Non-empty result from `get_input_data()`.
        processed_ids : list
            Result from `get_processed_ids()`.

        Returns
        -------
        dict
            A copy of `input_data` with files removed.
        """
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

    def get_child_logger(self):
        """
        Create a child logger with the root logger’s formatter.

        Returns
        -------
        logger
            A logger for use throughout base.py and its children,
            used primarily to output warnings and errors. 
        """
        handler = logging.FileHandler(self.paths['log'])
        handler.setFormatter(self.logger.handlers[0].formatter)
        logger = self.logger.getChild(self.safe_name)
        logger.addHandler(handler)
        return logger

    # This is overridden in LIBSProcessor:
    def get_input_data(self):
        """
        Iterates through the input directoriy to check for files
        to be processed and retrieves ids from those files if present.
        If the dataset is not raman, id is equal to the file's name 
        with the file type removed. If the dataset IS raman, then
        id is equal to the file's name with the file type removed,
        then checking for possible underscores. 

        Returns
        -------
        data
            a dictionary where keys are directories to be checked for 
            data files, and values are lists of tuples that follow the
            format (ID, filename)
        """
        data = {}
        for input_dir in self.paths['data']:
            base = os.path.basename(input_dir)
            data[base] = []
            for root, _, filenames in os.walk(input_dir):
                for filename in filenames:
                    if filename.lower().endswith(self.file_ext.lower()):
                        fid = self.get_id(filename)
                        if fid is not None:
                            if not self.is_raman():
                                full_filename = os.path.join(root, filename)
                                data[base].append((fid, full_filename))
                            if self.is_raman():
                                full_filename = os.path.join(root, filename)
                                #as code in process spectra in raman
                                is_underscored = self.is_underscored(full_filename)
                                if is_underscored:
                                    fid = fid + "_" + is_underscored
                                data[base].append((fid, full_filename))

        return data

    def get_processed_ids(self):
        """
        Return a list of the spectra present in previous output.
        """
        filename = self.output_prefix + '_meta.npz'
        filepath = os.path.join(self.paths['output'], filename)
        self.logger.debug(f'Checking for previous output file {filepath}')
        if not os.path.isfile(filepath):
            return []
        #so raman data is not pickled
        meta = np.load(filepath, allow_pickle = not self.is_raman())
        ids = meta[self.pkey_field]
        return [x.decode() if isinstance(x, bytes) else x for x in ids]

    # This is overridden in _TrajectoryProcessor:
    def is_trajectory(self):
        """
        Return a boolean whether the spectrum data is trajectory format.
        """
        return False

    def is_raman(self):
        """
        Return a boolean if running Raman. Overriden in raman.py.
        """
        return False

    def make_batches(self, unprocessed):
        """
        Return a struct of batches of files to be processed.

        The structure is similar to the output of `get_input_data()`,
        but the contents of the list are lists of tuples instead of
        just tuples. Maximum size of a list is `self.batch_size`.

        Parameters
        ----------
        unprocessed
            Struct of files to be processed.
        """
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
        """
        Drive the processing of files in reasonably-sized batches.

        Print messages that show how long each batch has taken to
        complete along with when the batch starts.

        Parameters
        ----------
        unprocessed
            Struct of files to be processed.
        """
        to_process = self.make_batches(unprocessed)
        toc = time()
        for label, batch in to_process.items():
            file = 'file' if len(batch) == 1 else 'files'
            self.logger.info(f'Starting {len(batch)} {file} in {label}')
            self.process_batch(batch)
            tic = time()
            self.logger.debug(f'Batch completed in {tic - toc:0.1f} seconds')
            toc = tic

    def process_batch(self, batch):
        """
        Take each file in a batch and create/append to the output.

        Parameters
        ----------
        batch : list
            Tuples representing files to be processed.
        """
        all_spectra, all_meta = [], []
        for datafile in batch:
            spectra, meta = self.process_file(datafile)
            if spectra is None or meta is None:
                continue
            else:
                all_spectra.append(spectra)
                all_meta.append(meta)
        if not all_spectra:
            self.logger.debug('No spectra found in batch')
            return
        all_meta = self.restructure_meta(all_meta)
        output_suffix = '.hdf5' if self.driver is None else '.%03d.hdf5'
        output_pattern = self.output_prefix + output_suffix
        output_filepath = os.path.join(self.paths['output'], output_pattern)
        self.write_data(output_filepath, all_spectra, all_meta)
        self.write_metadata(all_meta)

    # This is extended by _VectorProcessor:
    def process_file(self, datafile):
        """
        Return a processed single file from a batch.

        Gives warning if the file, its spectra, or metadata does
        not exist.

        Parameters
        ----------
        datafile
            A single tuple representing a file.
        """
        processed = self.process_spectra(datafile)
        if processed is None or processed[0] is None or processed[1] is None:
            return None, None
        return processed

    def restructure_meta(self, all_meta):
        """
        Return a dict to be the metadata portion of the output.

        Parameters
        ----------
        all_meta
            Metadata as extracted from the spectra files.
        """
        if isinstance(all_meta[0][self.pkey_field], (list, np.ndarray)):
            return dict((k, np.concatenate([m[k] for m in all_meta]))
                        for k in all_meta[0].keys())
        return dict((k, np.array([m[k] for m in all_meta]))
                    for k in all_meta[0].keys())

    def write_metadata(self, all_meta):
        """
        Output the metadata.

        Parameters
        ----------
        all_meta : dict
            As received from `restructure_meta()`.
        """
        filename = self.output_prefix + '_meta.npz'
        filepath = os.path.join(self.paths['output'], filename)
        if os.path.exists(filepath):
            existing = np.load(filepath, allow_pickle=True)
            for k, v in list(all_meta.items()):
                #all_meta[k] = just one
                #existing[k] = if multiple runs, then multiple times
                #below does not work, but v here is the id
                #if k == self.pkey_field and v in existing[k]:
                   #continue
                all_meta[k] = np.concatenate((existing[k], v))
        np.savez(filepath, **all_meta)


class _VectorProcessor(_BaseProcessor):
    """
    Abstract base class.

    Requires implementations of these members:
    - `channels`: the number of bands expected in the spectra
    """

    def process_file(self, datafile):
        """
        Override _BaseProcessor to enforce data shape.
        """
        spectra, meta = super().process_file(datafile)
        if spectra is None or meta is None:
            return None, None
        pkeys = meta[self.pkey_field]
        n_meta = len(pkeys) if isinstance(pkeys, (list, np.ndarray)) else 1
        n_spectra = 1 if spectra.ndim == 1 else spectra.shape[0]
        if n_spectra != n_meta:
            self.logger.warning(f'Unexpected number of shots in {datafile[1]}')
            return None, None
        return spectra, meta

    def write_data(self, filepath, all_spectra, all_meta):
        """
        Write output data files.

        Parameters
        ----------
        filepath : string
            Target filename to write to.
        all_spectra
            Data to write.
        all_meta
            Metadata about spectra. Unused in Vector output but we
            need it in the API for Trajectory output.
        """
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
    """
    Abstract base class.
    """

    def is_trajectory(self):
        """
        Override _BaseProcessor.
        """
        return True

    def write_data(self, filepath, all_spectra, all_meta):
        """
        Write output data files.

        Parameters
        ----------
        filepath : string
            Target filename to write to.
        all_spectra
            Data to write.
        all_meta
            Metadata about spectra.
        """
        ids = all_meta[self.pkey_field]
        fh = h5py.File(filepath, 'a', driver=self.driver, libver='latest')
        for id, spectrum in zip(ids, all_spectra):
            path = f'/spectra/{id}'
            if path in fh:
                self.logger.warning(f'Overwriting previous entry in {path}')
                del fh[path]
            fh.create_dataset(path, data=spectrum)
        fh.close()
