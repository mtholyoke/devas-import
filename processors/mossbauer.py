import numpy as np
from . import utils
import itertools 
from ._base import _TrajectoryProcessor

class MossbauerImporter(_TrajectoryProcessor):
    """
    Inherits from BaseProcessor
    Processes spectra data from Mossbauer

    Implements these methods required by BaseProcessor:
    - get_id(filename) returns ID or None
    - parse_metadata() returns parsed metadata structure
    - process_spectra(filename, metadata) return spectra, meta

    Implements these members required by BaseProcessor:
    - driver: None by default
    - file_ext: '_.txt' by default
    - pkey_field: 'Sample #' by default
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.meta = {}
        self.logger = self.get_child_logger() 
        required = ['channels']
        for attr in required:
            if not hasattr(self, attr):
                raise AttributeError(f'Attribute "{attr}" is required')
        defaults = {
            'driver': None,
            'file_ext': '.txt',
            'pkey_field': 'Sample #',
            'skipped' : 0,
        }
        for key, value in defaults.items():
            if not hasattr(self, key):
                setattr(self, key, value) 
        self.superman_fields = set(['Sample #', 'T(K)', 'Sample Name', 'Post?',
                           'Dana Group', 'Group Folder', 'Owner/Source',
                           # Add 'Pubs' but make a search widget first
                           # Remove 'Group Folder' after Darby edits
                           ])

    def get_id(self, filename):
        """
        Finds the id from an individual file name.
        
        Parameters
        ----------
        filename 
            the name of an individual file, no path.

        Returns
        -------
            A string representing the name of an individual file
            without its file type at the end.
        """
        return filename.split('.')[0]

    def parse_metadata(self):
        """
        Reads the masterfile. 

        Returns
        -------
        self.meta
            a dict representing the metadata from the masterfile
        """
        self.logger.debug('Loading masterfile...')
        self.meta = utils.parse_masterfile(self.paths['metadata'][0], self.superman_fields, self.logger)
        self.logger.debug('Finished loading masterfile.')
        return self.meta

    def process_metadata(self, metadata, filename):
        """
        Processes the metadata for an individual file. 

        Parameters
        ---------- 
        filename 
            The name of a file in string format that still contains 
            an extension.
        metadata
            The dict formed by parse_metadata above. 

        Returns
        -------
        meta
            A dict representing an individual file's metadata.
        """
        pkeys = np.asarray(metadata[self.pkey_field], dtype=str)
        meta_idx, = np.where(pkeys == self.get_id(filename))
        if len(meta_idx) != 1:
            self.logger.warning(f'Cannot match spectrum and masterfile {filename}')
            return
        meta_idx = meta_idx[0]
        if metadata['Post?'][meta_idx] is None or \
            metadata['Post?'][meta_idx].upper()!='Y':
            self.skipped += 1
            return
        meta = {key: val[meta_idx] for key, val in metadata.items()}
        return meta
    
    def load_mossbauer_spectra(self, datafile):
        """
        Gets spectra from a single file.

        Parameters
        ----------
        datafile 
            The second entry from a tuple representing a file.

        Returns
        -------
        spectra
            An individual file's spectra. 

        """
        spectra = []
        with open(datafile) as f:
            for line in itertools.islice(f, 10, None):
                line = line.strip()
                try:
                    row = list(map(float, line.split()))
                    if len(row) != 2:
                      self.logger.warning(f'Wrong data format in file {datafile}')
                      return
                    spectra.append(np.asarray(row, dtype=float))
                except ValueError:
                    pass
        if len(spectra) != self.channels:
            self.logger.warning(f'Expected {self.channels} channels, got {len(spectra)} in {datafile}')
            return
        return spectra
    
    def process_spectra(self, datafile):
        """
        Processes a single file and returns both its spectra and metadata.

        Parameters
        ----------
        datafile 
            A single tuple representing a file.

        Returns
        -------
        spectra
            A single file's spectra.
        meta
            A dict of a single file's metadata.
        """
        result = self.load_mossbauer_spectra(datafile[1])
        if not result:
            return
        if isinstance(result, str):
            self.logger.warning(result)
            return 
        spectra = result
        meta = self.process_metadata(self.meta, filename=datafile[0])
        return spectra, meta


