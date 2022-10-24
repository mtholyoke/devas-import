#UNDER CONSTRUCTION DO NOT RUN

cd ~/ChemLIBS/PREPROCESSED_NO_BLR/
NUM_PRENOBLR_FILES=$(ls | wc -l)
#find the current number of files in prenoblr

cd ~/ChemLIBS/hold/
NUM_HOLD_FILE=$(ls | wc -l)
#find the curent number of files in hold

DEVAS_IMPORT_PROCESS=~/Desktop/Projects/devas-import/process_all.py
SIZE_GROWTH=~/Desktop/Projects/devas-import/

cd ~/ChemLIBS
python3 $DEVAS_IMPORT_PROCESS
#begin the process

SIZE_PRENOBLR= du -sh ~/ChemLIBS/PREPROCESSED_NO_BLR/ 
#find the size of prenoblr
SIZE_TODEVAS = du -sh ~/ChemLIBS/to-DEVAS
#find the size of to-DEVAS after running

${SIZE_GROWTH}/sizeGrowth.txt < ${SIZE_PRENOBLR} : ${SIZE_TODEVAS}
#put the size of prenoblr and the size of to-DEVAS in a text file together

if [[$NUM_HOLD_FILE -gt $((2 * $NUM_PRENOBLR_FILES))]]
# if there are still at least twice as many files in hold as in prenoblr
#then move more files into prenoblr so that it doubles in size
then
    cd ~/ChemLIBS/hold/
    ~/holdFiles.txt < ls -a
    # head -n $((2 * $NUM_PRENOBLR_FILES)) ~/holdFiles.txt
    # trying to find some way of 'from hold, move 2*prenoblr size files into prenoblr'
    rm ~/holdFiles.txt
else
    #move all of hold's remaining files into prenoblr

#rm the to-DEVAS files and it should be ready to start again
#if this is to run automatically though, it will need some kind of check
#something like if hold is empty (i.e, all files are in prenoblr)
#then stop running




