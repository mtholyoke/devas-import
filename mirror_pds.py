#!/usr/bin/env python3
#run in container with lftp installed

import logging
import os
import yaml
import subprocess
from datetime import datetime
import subprocess as sp
from argparse import ArgumentParser
from process_all import logging_setup

def mirror_pds(msl_dataset, script_dir):
    remote_processed = "ftp://pds-geosciences.wustl.edu/msl/msl-m-chemcam-libs-4_5-rdr-v1/mslccm_1xxx"
    meta_file = msl_dataset['meta_file']

    if not script_dir:
        script_dir = "/app"

    msl_dir = script_dir + "/data"
    data_dir = msl_dir + "/" + msl_dataset['base_dir']
    output_prefix = data_dir + "/" + msl_dataset['output_prefix']
    originals = data_dir + "/" + msl_dataset['data_dir']

    date = datetime.now()
    nemo_root = "cj@nemo.mtholyoke.edu:/home/cj/datafiles"
    msl_log = data_dir + "/nightly-logs/MSL-" + date.strftime("%Y-%m-%d") + ".log"

    logging.info("Running MSL-PDS dataset")
    starttime = datetime.now()
    f = open(msl_log, "w")
    f.write("### " + str(date) + " - Starting MSL data downloads")
    f.close()

    #if overwrite is needed, turn xfer:clobber on (see lftp docs)
    command_1 = f'"get -O {data_dir} document/{meta_file}  -o {data_dir}/{meta_file}" {remote_processed}'
    command_2 = f'"mirror -c -I cl5_*ccs_*.csv --no-empty-dirs data {originals}" {remote_processed}'
    
    os.system("/usr/bin/lftp -e " + command_1)
    os.system("/usr/bin/lftp -e " + command_2)

    endtime = datetime.now()
    time_dif = endtime - starttime
    f = open(msl_log, 'a')
    f.write("###" + str(date) + " – Download finished after " 
            + str(time_dif.total_seconds()) + " seconds, starting processing.")
    f.close()

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
        #only run the mirror_pds part of this is MSL is present
        if dataset['name'] == 'MSL':
            mirror_pds(dataset, script_dir)

