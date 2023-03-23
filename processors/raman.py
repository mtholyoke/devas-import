import numpy as np
from . import utils
import itertools 
from ._base import _TrajectoryProcessor
from os.path import basename



class RamanImporter(_TrajectoryProcessor):
    """
    Inherits from base.py
    Processes spectra data from Mossbauer

    Implements these methods required by _base.py:
    - get_id(filename) returns ID or None
    - parse_metadata() returns parsed metadata structure
    - process_spectra(filename, metadata) return spectra, meta

    Implements these members required by _base.py:
    - driver: None by default
    - file_ext: '.txt' by default
    - pkey_field: 'spectrum_number' by default

    meta: a dictionary to hold metadata
    logger: for logging errors
    """
    def __init__(self, **kwargs):
        self.meta = {}
        super().__init__(**kwargs)
        self.logger = self.get_child_logger() 
        required = ['channels']
        for attr in required:
            if not hasattr(self, attr):
                raise AttributeError(f'Attribute "{attr}" is required')
        #defaults goes here with the raman specific vars and req. vars
        defaults = {
            'driver': None,
            'file_ext': '.txt',
            'pkey_field': 'spectrum_number',
            'output_prefix': 'raman',
        }
        for key, value in defaults.items():
            if not hasattr(self, key):
                setattr(self, key, value)

    def get_id(self, datafile):
        """
        Returns a integer representing the name of an individual txt file
        without the .txt suffix.
        Parameters datafile: the path to a txt file
        """
        id_list = basename(datafile).rstrip(self.file_ext).split('_')
        id = id_list[0]
        for i in range (1, len(id_list)-1):
            id = id + "_" + id_list[i]
        return id
        #return basename(datafile).rstrip(self.file_ext).split('_')[0]
    
    def is_underscored(self, datafile):
        """
        Returns the final number if the given datafile has something like _0 or
        _1 at the end of it (which marks it as having a 
        duplicate id). Returns "" otherwise.
        Parameter datafile: the path to a txt file.
        """
        id_list = basename(datafile).rstrip(self.file_ext).split('_')
        if len(id_list[len(id_list)-1]) == 1:
            return id_list[len(id_list)-1]
        return ""
    
    def is_raman(self):
        """
        Overrides base.py to say it is raman
        """
        return True 

    def parse_metadata(self):
        """
        Returns data from metadata file. 
        """
        self.logger.debug('Loading masterfile...')
        self.meta = utils.parse_masterfile(self.paths['metadata'][0], self.pkey_field, self.logger)
        self.logger.debug('Finished loading masterfile.')
        return self.meta 

    def process_spectra(self, datafile):
        """
        Returns a single processed file from a batch of files, represented by
        its spectra and metadata.
        Parameter datafile: a single tuple representing a file
        """
        pkeys = np.array(self.meta[self.pkey_field])

        #is_duplicate will contain either an empty string or a number now
        #ISSUE: there are files with _0 that ARE NOT duplicates
        is_underscored = self.is_underscored(datafile[1])

        #datafile is a tuple, so get the second value which is the path
        meta_idx, = np.where(pkeys == self.get_id(datafile[1]))
        if len(meta_idx) < 1:
            #self.logger.warning(f'Cannot match spectra and masterfile {datafile[1]}')
            return
        meta = {key: val[meta_idx[0]] for key, val in self.meta.items()}

        #change the spectrum_number to the underscored version if necessary 
        if is_underscored:
            meta[self.pkey_field] = meta[self.pkey_field] + "_" + is_underscored

        #switched to datafile[1] for path
        spectra = np.genfromtxt(datafile[1], delimiter=',')
        if spectra.ndim != 2 or spectra.shape[1] != 2:
            self.logger.warning('Spectra must be a trajectory')
            return

        # Make sure wavelengths are increasing
        if spectra[0,0] > spectra[1,0]:
            spectra = spectra[::-1]
        return spectra, meta

