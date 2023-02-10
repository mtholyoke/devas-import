#!/usr/bin/env python3

"""
This script takes a previously aggregated dataset and splits it into
individual files for processing, because that was easier than modifying
the processor to deal with the aggregate files.

It could be improved, but we only needed to run it four times.
"""

import csv
from datetime import datetime

channels = '10K'
dataset = 'EARTH'
metadata = {}
spectra = {}

with open(f"{channels}_metadata_{dataset}.csv") as meta_file:
	reader = csv.DictReader(meta_file)
	for row in reader:
		metadata[row['pkey']] = row

with open(f"{channels}_spectra_{dataset}.csv") as spectra_file:
	reader = csv.reader(spectra_file)
	spectra = {col[0]:col[1:] for col in [list(row) for row in zip(*reader)]}

assert len(metadata.keys()) + 1 == len(spectra.keys()), "Mismatched spectra"

dirname = f"{channels}_{dataset}/PREPROCESSED_NO_BLR/data"

for name, meta in metadata.items():
	filename = f"{dirname}/{name}_spect.csv"
	sequence = meta['Carousel#']
	date = datetime.strptime(sequence[:6], '%y%m%d').strftime('%d-%b-%Y')
	with open(filename, 'w') as out:
		out.write(f"Date: {date}\n")
		out.write(f"Carousel: {meta['Carousel#']}\n")
		out.write(f"Sample: {meta['Pellet Name']}\n")
		out.write(f"Atmosphere: {dataset}\n")
		out.write(f"LaserAttenuation: {meta['Laser Power'][:-1]}\n")
		out.write('DistToTarget: 300\n')
		out.write('wave, mean\n')
		for i, data in enumerate(spectra[name]):
			out.write(f"{spectra['wave'][i]},{data}\n")
