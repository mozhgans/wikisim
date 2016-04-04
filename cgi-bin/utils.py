"""Utility functions"""
# uncomment

import itertools
import scipy as sp
import os

import datetime

__author__ = "Armin Sajadi"
__copyright__ = "Copyright 215, The Wikisim Project"
__credits__ = ["Armin Sajadi", "Evangelo Milios", "Armin Sajadi"]
__license__ = "GPL"
__version__ = "1.0.1"
__maintainer__ = "Armin Sajadi"
__email__ = "sajadi@cs.dal.ca"
__status__ = "Development"

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
    