#!/usr/bin/env python3

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

print(f"metadata has {len(metadata.keys())} keys")
print(f"spectra has {len(spectra.keys())} keys")

dirname = f"{channels}_{dataset}/PREPROCESSED_NO_BLR/data"

for name, meta in metadata.items():
	filename = f"{dirname}/{name}_spect.csv"
	sequence = meta['Carousel#']
	date = datetime.strptime(sequence[:6], '%y%m%d').strftime('%d-%b-%Y')
	with open(filename, 'w') as out:
		out.write('Date: 03-Feb-2023\n')
		out.write(f"Carousel: {meta['Carousel#']}\n")
		out.write(f"Sample: {meta['Pellet Name']}\n")
		# out.write('Target: T01\n')
		# out.write('Location: 1\n')
		out.write(f"Atmosphere: {dataset}\n")
		out.write(f"LaserAttenuation: {float(meta['Laser Power'][:-1])}\n")
		out.write('DistToTarget: 300.0\n')
		out.write('wave, i1\n')
		for i, data in enumerate(spectra[name]):
			out.write(f"{spectra['wave'][i]},{data}\n")
