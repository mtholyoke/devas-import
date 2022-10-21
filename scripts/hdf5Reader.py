from colorsys import hsv_to_rgb
import h5py
import os
import numpy as np
import io
path = "/Users/mille35a/ChemLIBS/backup-toDEVAS/"


#bytesHdf5 = io.open(path+'prepro_no_blr.000.hdf5', "rb", buffering = 0)
#print(bytesHdf5.read())
#bytesForFile = bytearray()
#bytesHdf5.readinto(bytesForFile)
#bytesHdf5.close()


data_file = os.path.join(path, 'prepro_no_blr.%03d.hdf5') #this seems to open 000 specifically
print(data_file)
hdf5 = h5py.File(data_file, driver='family', mode='r')
keys = hdf5.keys()
print(keys) #there is a single key called spectra
print(type(hdf5['spectra'])) #spectra is a 'h5py._hl.dataset.Dataset'

print(hdf5['spectra'].shape)
print(hdf5['spectra'].size)
print(hdf5['spectra'].ndim)
print(hdf5['spectra'].dtype)
print(hdf5['spectra'].nbytes)

 
#shape of onefile: (7, 6144)
#size of onefile: 43008
#ndim of onefile: 2
#dtype of onefile: float64
#nbytes of onefile: 344064

#shape of one plus one file: (14, 6144)
#size of one plus one file: 86016
#ndim of one plus one file: 2
#type of one plus one file: float64
#nbytes of one plus one file: 688128

#shape of two file: (14, 6144)
#size of two file: 86016
#ndim of two file: 2
#type of two file: float64
#nbytes of two file: 688128

hdf5.close()




