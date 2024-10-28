#!/usr/bin/env python3

import logging
import os
import yaml
from argparse import ArgumentParser
from datetime import datetime
from process_all import GLOBAL_CONFIG, logging_setup


def mirror_pds(msl_dataset, script_dir):
    remote_processed = "ftp://pds-geosciences.wustl.edu/msl/msl-m-chemcam-libs-4_5-rdr-v1/mslccm_1xxx"

    # TODO: adapted from processors/_base.py; refactor?
    base_dir = os.path.join(msl_dataset['root_dir'], msl_dataset['base_dir'])
    meta_file = msl_dataset['meta_file']
    meta_path = os.path.join(base_dir, meta_file)
    data_dir = os.path.join(base_dir, msl_dataset['data_dir'])

    date = datetime.now()

    logging.info("Running MSL-PDS dataset")
    starttime = datetime.now()
    print("### " + str(date) + " - Starting MSL data downloads")

    # If overwrite is needed, turn xfer:clobber on (see lftp docs).
    command_1 = f'"get document/{meta_file} -o {meta_path}" {remote_processed}'
    command_2 = f'"mirror -c -I cl5_*ccs_*.csv --no-empty-dirs data {data_dir}" {remote_processed}'

    print("###" + str(datetime.now()) + " - /usr/bin/lftp -e " + command_1)
    os.system("/usr/bin/lftp -e " + command_1)
    print("###" + str(datetime.now()) + " - /usr/bin/lftp -e " + command_1)
    os.system("/usr/bin/lftp -e " + command_2)

    endtime = datetime.now()
    time_dif = endtime - starttime
    print("###" + str(endtime) + " – Download finished after " + str(time_dif.total_seconds()) + " seconds.")

    return


if __name__ == '__main__':
    script_dir = os.path.dirname(__file__)
    ap = ArgumentParser()
    ap.add_argument('--config', type=open,
                    default=os.path.join(script_dir, 'config.yml'),
                    help='YAML file with configuration options.')
    args = ap.parse_args()
    config = yaml.safe_load(args.config)
    config.setdefault('chunk_size', 500)

    logging_setup(config['logging'])

    datasets = list(filter(lambda d: 'type' in d and d['type'] == 'MSL',
                           config['datasets']))
    for dataset in datasets:
        for attr in GLOBAL_CONFIG:
            dataset[attr] = config[attr]
        mirror_pds(dataset, script_dir)
