#!/users/grad/sajadi/backup/anaconda2/envs/wikisim/bin/python

import os
import sys


sys.path.insert(0,'.')
print "path:", sys.path
print "current:", os.getcwd()

from wikisim.calcsim import *

