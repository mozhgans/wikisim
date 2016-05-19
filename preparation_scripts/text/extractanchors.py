import json
import sys
import urllib

fileinput = sys.stdin

import StringIO
#fileinput = StringIO.StringIO(inputstr)
while True:
    line = fileinput.readline()
    if not line:
        break
    line = line.decode('utf-8').strip()
    js = json.loads(line)    
    if "annotation" not in js:
        continue
    for a in js["annotation"]:
        print u"{0}\t{1}".format(a["surface_form"],a["url"].replace(" ","_")).encode('utf-8')
                
    