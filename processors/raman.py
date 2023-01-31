import numpy as np
from . import utils
import itertools 
from ._base import _TrajectoryProcessor

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
        #rfind() should get the last instance of character
        #this way both formats of datafile should work 
        if '/' in datafile: datafile = datafile[datafile.rfind('/')+1:]
        return int(str(datafile.rstrip(self.file_ext)).split('_')[0])
        

    def parse_metadata(self):
        """
        Returns data from metadata file. 
        """
        self.logger.debug('Parsing metadata')
        self.meta = utils.parse_masterfile(self.paths['metadata'][0], self.pkey_field)
        return self.meta 

    def process_spectra(self, datafile):
        """
        Returns a single processed file from a batch of files, represented by
        its spectra and metadata.
        Parameter datafile: a single tuple representing a file
        """
        pkeys = np.array(self.meta[self.pkey_field])
        #datafile is a tuple, so get the second value which is the path
        meta_idx, = np.where(pkeys == self.get_id(datafile[1]))

        if len(meta_idx) != 1:
            print('  Cannot match spectra and masterfile', datafile[1])
            return
        meta = {key: val[meta_idx[0]] for key, val in self.meta.items()}
        
        #switched to datafile[1] for path
        spectra = np.genfromtxt(datafile[1], delimiter=',')
        print("process_spectra test #0")
        print(spectra)
        if spectra.ndim != 2 or spectra.shape[1] != 2:
            raise ValueError('Spectra must be a trajectory')

        # Make sure wavelengths are increasing
        if spectra[0,0] > spectra[1,0]:
            spectra = spectra[::-1]
        return spectra, meta
    
