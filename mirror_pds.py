#!/usr/bin/env python3

import logging
import os
import sys
import yaml
from datetime import datetime
from argparse import ArgumentParser

# TODO: this copied from process_all.py; move it back over and import
def logging_setup(log_cfg):
    defaults = {
        'datefmt': '%Y-%m-%d %H:%M:%S',
        'format': '%(asctime)s - %(levelname)s - %(message)s',
        'level': logging.INFO,
        'stream': sys.stdout,
    }
    if not log_cfg:
        log_cfg = {}
    for key, value in defaults.items():
        if key not in log_cfg:
            log_cfg[key] = value
    if 'filename' in log_cfg and log_cfg['filename']:
        del log_cfg['stream']
    if isinstance(log_cfg['level'], str):
        log_cfg['level'] = getattr(logging, log_cfg['level'], logging.INFO)
    logging.basicConfig(**log_cfg)

def mirror_pds(msl_dataset, script_dir):
    remote_processed = "ftp://pds-geosciences.wustl.edu/msl/msl-m-chemcam-libs-4_5-rdr-v1/mslccm_1xxx"

    # TODO: adapted from processors/_base.py; refactor?
    base_dir = os.path.join(msl_dataset['root_dir'], msl_dataset['base_dir'])
    meta_file = os.path.join(base_dir, msl_dataset['meta_file'])
    data_dir = os.path.join(base_dir, msl_dataset['data_dir'])

    date = datetime.now()

    logging.info("Running MSL-PDS dataset")
    starttime = datetime.now()
    print("### " + str(date) + " - Starting MSL data downloads")

    # If overwrite is needed, turn xfer:clobber on (see lftp docs).
    command_1 = f'"get document/msl_ccam_obs.csv -o {meta_file}" {remote_processed}'
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

    for dataset in config['datasets']:
        # Only run the mirror_pds part of this if MSL is present.
        if dataset['name'] == 'MSL':
            # TODO: this is also in process_all.py; move to utils?
            global_config = ['root_dir', 'chunk_size']
            for attr in global_config:
                dataset[attr] = config[attr]
            mirror_pds(dataset, script_dir)

