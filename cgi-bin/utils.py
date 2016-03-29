# uncomment
import itertools
import scipy as sp
import os

import datetime

def readds(url):    
    data = sp.genfromtxt(url, dtype=None)
    return data

def logres(outfile, instr, *params):
    outstr = instr % params;
    with open(outfile, 'a') as f:
        f.write("[%s]\t%s\n" % (str(datetime.datetime.now()) , outstr));          
        
def log(instr, *params):
    logres(logfile, instr, *params)

outdir = '../out'    
logfile=os.path.join(outdir, 'log.txt');
if not os.path.exists(logfile):
    log('log created') 
    os.chmod(logfile, 0777)    
    
    
def timeformat(sec):
    return datetime.timedelta(seconds=sec)
    