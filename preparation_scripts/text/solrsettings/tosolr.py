import json
import sys
import os

fileinput = sys.stdin

import StringIO
#fileinput = StringIO.StringIO(inputstr)

n=1000
count=0;
f=None
os.mkdir("chunks")
seperator=''
firstline=None
while True:
    line = fileinput.readline()
    if not line:
        break
        
    line = line.decode('utf-8').strip()
    if not line:
        continue
        
    if count%n==0:
        if f is not None:
            f.write('\n]\n')
            f.close()
        f=open('chunks/chunk'+str(int(count/n)).zfill(10)+'.json','w')    
        f.write('[\n')
        firstline=True
        seperator=""
    count +=1
    
    page=json.loads(line)
    page["annotation"]=json.dumps(page["annotation"], ensure_ascii=False)
    page["opening_annotation"]=json.dumps(page["opening_annotation"], ensure_ascii=False)
    f.write(seperator+json.dumps(page, ensure_ascii=False).encode('utf-8'))
    if firstline:
        firstline=False
        seperator=",\n"
    
    
if f is not None:
    f.write('\n]\n')
    f.close()
    

    
    