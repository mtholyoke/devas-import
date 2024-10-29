import numpy as np
import os
import re
from ._base import _VectorProcessor


class MSLProcessor(_VectorProcessor):
    """
    Inherits from VectorProcessor from BaseProcessor
    Processes spectra data from MSL (i.e, NASA data)

    Implements these methods required by BaseProcessor:
    - get_id(filename) returns ID or None
    - parse_metadata() returns parsed metadata structure
    - process_spectra(filename, metadata) return spectra, meta

    Implements these members required by BaseProcessor:
    - driver: None by default
    - file_ext: '.txt' by default
    - pkey_field: 'spectrum_number' by default

    logger: for logging errors
    metadata: to ensure that metadata can be used through processor
    but still respects process_spectra single argument.
    """
    def __init__(self, **kwargs):
        self.metadata = {}
        super().__init__(**kwargs)
        self.logger = self.get_child_logger()
        required = ['channels']
        for attr in required:
            if not hasattr(self, attr):
                raise AttributeError(f'Attribute "{attr}" is required')
        defaults = {
            'driver': 'family',
            'file_ext': '.csv',
            'pkey_field': 'ids',
        }
        for key, value in defaults.items():
            if not hasattr(self, key):
                setattr(self, key, value)

    def get_id(self, filename):
        """
        Gets the id of a file.

        Parameters
        ----------
        filename
            The name of a file.

        Returns
        -------
            A string representation of that file name without ending.
        """
        parts = filename.split('_')
        return parts[1].rstrip('ccs') if len(parts) == 3 else None

    def get_processed_ids(self):
        """
        Gets the processed ids of MSL. Overrides base get_processed_ids.

        Returns
        -------
            IDs that have already been run.
        """
        raw_ids = super().get_processed_ids()
        return [id[7:] for id in raw_ids]

    def make_meta(self, datafile, include_mean_spectrum=False):
        """
        Generates the metadata for MSL files.

        Parameters
        ----------
        datafile
            A tuple representing a file.
        include_mean_spectrum
            A boolean that controls whether or not 0 is include in shot_num.

        Returns
        -------
            A dict of meta categories to their values.
        """
        meta_idx = self.match_metadata(datafile[1])
        if meta_idx is None:
            self.logger.warning(f'Cannot match spectra and masterfile {datafile[1]}')
            return
        meta_row = self.metadata[meta_idx:meta_idx+1]
        if include_mean_spectrum:
            shot_num = np.arange(meta_row.nbr_of_shots+1)
        else:
            shot_num = np.arange(1, meta_row.nbr_of_shots+1)
        autofocus = meta_row.autofocus == 'Yes'
        dist = float(meta_row.distance_m[0])
        edr_id = '%s_%d' % (meta_row.edr_type[0], meta_row.spacecraft_clock[0])
        metas = np.broadcast_arrays(shot_num, edr_id, meta_row.target, autofocus,
                                    dist, meta_row.laser_energy,
                                    meta_row.sol, meta_row.temperature)
        meta_names = ('numbers', 'ids', 'names', 'foci', 'distances', 'powers',
                      'sols', 'raw_temps')
        return dict(zip(meta_names, metas))

    def match_metadata(self, filename):
        """
        Checks to see if an ID exists (already) in metadata.

        Parameters
        ----------
        filename
            The full path of a file.

        Returns
        -------
        row_idx[0]
            The row – and only row, after tests – where the ID is located in masterfile.
        """
        name, _ = os.path.splitext(os.path.basename(filename))
        m = re.match(r'([a-z0-9]+)_(\d+)[a-z]{3}_\w+', name)
        if not m:
            self.logger.warning(f"Invalid CCS name: {name}")
            return
        edr_type = m.group(1)
        clock = int(m.group(2))
        row_idx, = np.where(self.metadata.spacecraft_clock == clock)
        if len(row_idx) == 0:
            self.logger.warning(f"Masterfile does not contain ID: {edr_type, clock}")
            return
        if len(row_idx) > 1:
            self.logger.warning(f"Masterfile contains duplicate IDs: {edr_type, clock}")
            return
        return row_idx[0]

    def parse_csv(self, filename):
        """
        Processes a single spectra file.

        Parameters
        ----------
        filename
            The full path of a file.

        Returns
        -------
            The spectra of a file.
        """
        data = np.genfromtxt(filename, delimiter=',')
        shots = data[:, 1:-2].T
        mean_spectrum = data[:, -1].T
        return np.row_stack((mean_spectrum, shots))

    def parse_metadata(self):
        """
        Required from base.py. Assigns metadata to self.metadata.

        Returns
        -------
        metadata
            The metadata from MSL masterfile.
        """
        self.metadata = self.parse_masterfile(self.paths['metadata'][0])
        return self.metadata

    def parse_masterfile(self, metapath):
        """
        Initializes metadata from masterfile.

        Parameters
        ----------
        metapath
            The path to the MSL masterfile.

        Returns
        -------
            The metadata from that file.
        """
        return np.recfromcsv(metapath, names=True,
                             invalid_raise=False, comments='"')

    def process_spectra(self, datafile):
        """
        Parameters
        ----------
        datafile
            A single tuple representing a file.

        Returns
        -------
        spectra
            A single file's spectra values.
        meta
            A struct containing a single file's metadata values,
            including si_test value.
        """
        spectra = self.parse_csv(datafile[1])
        if (spectra.ndim == 1 and spectra.shape[0] != self.channels) or \
           (spectra.ndim == 2 and spectra.shape[1] != self.channels):
            self.logger.warning("Problem encountered with spectra.ndim or spectra.shape.")
            return
        meta = self.make_meta(datafile, True)
        return spectra, meta
