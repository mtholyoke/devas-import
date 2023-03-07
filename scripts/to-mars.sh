#! /bin/bash
#for use in testing – moves data from local devas-import to mars-2021-08 

scp ../data/ChemLIBS/to-DEVAS/* mars-2021-08:/opt/devas-web/data/ChemLIBS_all15/
scp ../data/SuperLIBS_10k/to-DEVAS/* mars-2021-08:/opt/devas-web/data/Py3_SuperLIBS_10k/
scp ../data/SuperLIBS_18k/to-DEVAS/* mars-2021-08:/opt/devas-web/data/Py3_SuperLIBS_18k/

mv ../data/Mossbauer/to-DEVAS/mossbauer_meta.npz ../data/Mossbauer/to-DEVAS/prepro_no_blr_meta.npz
scp ../data/Mossbauer/to-DEVAS/* mars-2021-08:/opt/devas-web/data/Mossbauer/

mv ../data/Raman/to-DEVAS/raman_meta.npz ../data/Raman/to-DEVAS/prepro_no_blr_meta.npz
scp ../data/Raman/to-DEVAS/* mars-2021-08:/opt/devas-web/data/Raman/