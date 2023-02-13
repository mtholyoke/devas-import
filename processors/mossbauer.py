import numpy as np
from . import utils
import itertools 
from ._base import _TrajectoryProcessor

class MossbauerImporter(_TrajectoryProcessor):
    """
    Inherits from base.py
    Processes spectra data from Mossbauer

    Implements these methods required by _base.py:
    - get_id(filename) returns ID or None
    - parse_metadata() returns parsed metadata structure
    - process_spectra(filename, metadata) return spectra, meta

    Implements these members required by _base.py:
    - driver: None by default
    - file_ext: '_.txt' by default
    - pkey_field: 'Sample #' by default
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        #making self.meta here to avoid referencing meta before assignment
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
        Returns a string representing the name of an individual txt file
        without the .txt suffix.
        Parameters filename: the path to a txt file
        """
        return filename.split('.')[0]

    def parse_metadata(self):
        """
        Returns data from metadata file. 
        
        The function that this calls in utils is lifted directly from
        its equivalent function in process_mossbauer_files.py
        """
        self.logger.debug('Loading masterfile...')
        self.meta = utils.parse_masterfile(self.paths['metadata'][0], self.superman_fields)
        self.logger.debug('Finished loading masterfile.')
        return self.meta

    def process_metadata(self, metadata, filename):
        """
        Returns the metadata of a file

        Parameters: 
        filename, the name of a file in string format that still contains 
        an extension
        metadata: an empty to which the metadata is added
        """
        pkeys = np.asarray(metadata[self.pkey_field], dtype=str) #for unicode
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
        Version of load_spectra for mossbauer files
        Parameter datafile: the second entry from a tuple representing a file
        Returns the spectra of a file.
        """
        spectra = []
        with open(datafile) as f:
            for line in itertools.islice(f, 10, None):
                line = line.strip()
                try:
                    #make a list so that len will function as expected
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
        Returns a single processed file from a batch of files, represented by
        its spectra and metadata.
        Parameter datafile: a single tuple representing a file
        """
        result = self.load_mossbauer_spectra(datafile[1])
        if not result:
            return
        if isinstance(result, str):
            self.logger.warning(result)
            return 
        #spectra starts as empty list in pmf 
        spectra = result
        #this part lifted from process_spectra is pmf after meta is finished
        #being made. self.n_chans replaced with self.channels, fname replaced
        #with datafile, spectrum replaced with spectra
        #PROBLEM: sometimes process_metadata doesn't return anything?
        meta = self.process_metadata(self.meta, filename=datafile[0])
        return spectra, meta


