#!/usr/bin/env python2.7

from __future__ import print_function
from argparse import ArgumentParser
import numpy as np

from _mhc_utils import (process_mhc_spectra)

class ChannelExporter():
    def main(self):
        ap = ArgumentParser()
        ap.add_argument('-i', '--input-file', type=str, required=True,
                        help='File containing data to extract channels from.')
        ap.add_argument('-o', '--output-file', type=str, required=True,
                        help='Filename to export channels into.')
        args = ap.parse_args()
        self.process_data(args.input_file, args.output_file)

    def process_data(self, input_file, output_file):
        result = process_mhc_spectra(input_file)
        if not result:
            print('Cannot process input file')
            return
        spectra, meta, is_prepro = result
        assert is_prepro, 'Unexpected SuperLIBS raw data in {0}'.format(fname)
        channels = np.array(spectra[0], dtype=float)
        np.save(output_file, channels, allow_pickle=True)
        return

if __name__ == '__main__':
    ChannelExporter().main()
