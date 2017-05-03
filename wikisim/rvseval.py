""" Evaluating the method on Semantic Relatedness Datasets."""

#%load_ext autoreload
#%autoreload

import os
import time;
import pandas as pd


#%aimport wikipedia
#%aimport calcsim
from config import *
from calcsim import *
import gensim

import functools

#print DISABLE_CACHE
#clearcache()
direction=None;
method = 'word2vec'
    
    
initdirs(direction, 'word2vec')
resfilename =  os.path.join(baseresdir, 'reslog.txt')

dsfiles=('MiniMayoSRS-edited.csv', 'MayoSRS-edited.csv')
dsfiles=('MC_28-edited.csv', 'RG-edited.csv', 'wsim353-edited.csv', 'Kore-edited.csv', 'MiniMayoSRS-edited.csv', 
         'MayoSRS-edited.csv', 'UMNSRS_relatedness-edited.csv', 'UMNSRS_similarity-edited.csv')
for dsname in dsfiles:
    start = time.time()
    
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