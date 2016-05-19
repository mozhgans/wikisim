import sys
sys.path.append('../../cgi-bin/')
from collections import defaultdict
import imp
import json
import urllib
from wikipedia import *
fileinput = sys.stdin
errout = sys.stderr
import StringIO
#fileinput = StringIO.StringIO(inputstr)
pairdict = defaultdict(int)
while True:
    line = fileinput.readline()
    if not line:
        break
    line = line.strip()
    tp = line.split("\t")
    if len(tp) !=3:
        errout.write("Line Error: " + line)
        continue
    freq,anchor,title=tp
    wid=title2id(title)
    if wid is None:
        title=title[0].upper()+title[1:]
    wid=title2id(title)
    if wid is None:
        errout.write(anchor+"\t"+title+"\t"+str(freq)+"\n")
        continue
    pairdict[(anchor,wid)] += int(freq)
for (anchor,wid),freq in pairdict.iteritems():
    print anchor+"\t"+str(wid)+"\t"+str(freq)