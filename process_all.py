#!/usr/bin/env python3

import logging
import os
import sys
import yaml
from argparse import ArgumentParser
from processors import LIBSProcessor
from processors import MossbauerImporter 
from processors import RamanImporter
from processors import MSLImporter



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

    processor = {
        'LIBS': LIBSProcessor,
        'Mossbauer' : MossbauerImporter,
        'Raman' : RamanImporter,
        'MSL' : MSLImporter,
    }

    for dataset in config['datasets']:
        if 'name' not in dataset:
            logging.error('Dataset missing name; skipping')
            continue
        if 'type' not in dataset:
            logging.error(f'Dataset {dataset.name} missing type; skipping')
            continue
        global_config = ['root_dir', 'chunk_size']
        for attr in global_config:
            dataset[attr] = config[attr]
        processor[dataset['type']](**dataset).main()
        
        
