""" Evaluating the method on Semantic Relatedness Datasets."""

import os
import time;
#D = sparse(k,k,1./c(k),n,n);

# %autoreload 1

# %aimport wikipedia
# %aimport visualize
# from visualize import *
# from wikipedia import *
from config import *
from calcsim import *


direction=DIR_OUT;
method = 'rvspagerank'
initdirs(direction, 'rvspagerank')
resfilename =  os.path.join(baseresdir, 'reslog.txt')

dsfiles=('MC_28-edited.csv', 'RG-edited.csv', 'MiniMayoSRS-edited.csv', 'MayoSRS-edited.csv',
        'UMNSRS_relatedness-edited.csv', 'UMNSRS_similarity-edited.csv')
start = time.time()
for dsname in dsfiles:
    printflush ("Processing",dsname)
    dsbase, dsext = os.path.splitext(dsname);
    infilename = os.path.join(dsdir, dsname)
    outfilename = os.path.join(resdir(method, direction), dsbase+ '.out'+ dsext)
    _ , corr = getsim_file(infilename, outfilename, method, direction);
    logres(resfilename, 'rvspagerank\t%s\t%s\t%s\t%s', dsname, graphtype(direction), corr.correlation
                        , corr.pvalue)
    print corr
    
print str(timeformat(int(time.time()-start)));
#close()   