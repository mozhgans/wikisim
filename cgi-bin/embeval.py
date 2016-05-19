"""Testing batch embedding for a given file. """

from scipy import stats
import os
import time;
from config import *


#%aimport calcsim
from calcsim import *



direction=DIR_IN;
initdirs(direction, 'rvspagerank')

dsfiles=('MC_28-edited.csv', 'MiniMayoSRS-edited.csv','MayoSRS-edited.csv')
start = time.time()
for dsname in dsfiles:
    printflush ("Processing",dsname)
    dsbase, dsext = os.path.splitext(dsname);
    infilename = os.path.join(dsdir, dsname)
    outfilename = os.path.join(resdir('rvspagerank', direction), dsbase+ '.emb'+ dsext)
    getembed_file(infilename, outfilename,direction, cutoff=10);
    
print str(timeformat(int(time.time()-start)));
#close()   