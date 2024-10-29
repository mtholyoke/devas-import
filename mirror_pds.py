#!/usr/bin/env python3

import logging
import os
import yaml
from argparse import ArgumentParser
from datetime import datetime
from process_all import GLOBAL_CONFIG, logging_setup
from urllib.parse import unsplit


# TODO: this should be moved into processors/_base.py.
def download(dataset):
    if "download" not in dataset:
        return
    d = dataset["download"]
    remote = unsplit((d["scheme"], d["netloc"], d["path"], "", ""))

    base_dir = os.path.join(dataset["root_dir"], dataset["base_dir"])
    meta_file = dataset["meta_file"]
    meta_path = os.path.join(base_dir, meta_file)
    data_dir = os.path.join(base_dir, dataset["data_dir"])

    logging.info(f'Running {dataset["name"]} dataset; starting download')
    start_time = datetime.now()
    backup_stamp = start_time.isoformat(timespec="seconds")
    os.system(f'mv {meta_path} {meta_path}.{os.getpid()}.{backup_stamp}')

    # If overwrite is needed, turn xfer:clobber on (see lftp docs).
    lftp_commands = [
        f'"get1 document/{meta_file} -o {meta_path}"'
        f'"mirror -c -I cl5_*ccs_*.csv --no-empty-dirs data {data_dir}"'
    ]
    for lftp_command in lftp_commands:
        executable = f'/usr/bin/lftp -e {lftp_commmand} {remote}'
        logging.debug(executable)
        os.system(executable)

    time_diff = (datetime.now() - start_time).total_seconds()
    logging.info(f'Download finished after {time_diff} sec')

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
        download(dataset)
