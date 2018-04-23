"""Evaluating the wsd module. It assumes the sentences are already segmented
"""
from wikify import *
import sys
from optparse import OptionParser
#sys.path.insert(0,'..')
#from wikisim.calcsim import *
import time
from random import shuffle
np.seterr(all='raise')

# parser = OptionParser()
# parser.add_option("-t", "--max_t", action="store", type="int", dest="max_t", default=5)
# parser.add_option("-c", "--max_count", action="store", type="int", dest="max_count", default=-1)
# parser.add_option("-w", "--win_size", action="store", type="int", dest="win_size", default=5)
# parser.add_option("-v", action="store_true", dest="verbose", default=False)

#(options, args) = parser.parse_args()



# max_t = options.max_t
# max_count = options.max_count
# verbose = options.verbose
# ws = options.win_size


max_t = 20
max_count = -1
verbose = True

fresh_restart=True


dsnames = [os.path.join(home,'backup/datasets/ner/kore.json'),
           os.path.join(home,'backup/datasets/ner/wiki-mentions.5000.json'),
          ]

mentionmethods = (CORE_NLP, LEARNED_MENTION)

outdir = os.path.join(baseresdir, 'wikify')
# if not os.path.exists(outdir): #Causes synchronization problem
#     os.makedirs(outdir)

tmpdir = os.path.join(outdir, 'tmp')
# if not os.path.exists(tmpdir): #Causes synchronization problem
#     os.makedirs(tmpdir)
    
resname =  os.path.join(outdir, 'reslog.csv')
#clearlog(resname)

detailedresname=  os.path.join(outdir, 'detailedreslog.txt')
#clearlog(detailedresname)



for mentionmethod in mentionmethods:
    for dsname in dsnames:
        start = time.time()
        
        print "dsname: %s, method: %s, max_t: %s, ws: %s ..."  % (dsname,
                method, max_t, ws)
        sys.stdout.flush()
        
        tmpfilename = os.path.join(tmpdir, 
                                   '-'.join([method, str(max_t), str(ws), os.path.basename(dsname)]))
        overall_tp=[]
        overall_fp=[]
        overall_tn=[]
        start_count=-1
        if os.path.isfile(tmpfilename) and not fresh_restart:
            with open(tmpfilename,'r') as tmpf:
                for line in tmpf:
                    js = json.loads(line.strip())
                    start_count = js['no']
                    if js['tp'] is not None:
                        overall_tp.append(js['tp'])
                        overall_fp.append(js['fp'])
                        overall_tn.append(js['tn'])
        
        if start_count !=-1:
            print "Continuing from\t", start_count
            
        count=0
        with open(dsname,'r') as ds, open(tmpfilename,'a') as tmpf:
            for line in ds:
                js = json.loads(line.decode('utf-8').strip());
                S = js["text"]
                M = js["mentions"]
                count +=1
                if count <= start_count:
                    continue
                if verbose:
                    print "%s:\tS=%s\n\tM=%s" % (count, json.dumps(S, ensure_ascii=False).encode('utf-8'),json.dumps(M, ensure_ascii=False).encode('utf-8'))
                    sys.stdout.flush()
                    
                S2,M2 = wikify_a_line(line, mentionmethod=mentionmethod)
                mention_measures = get_sentence_measures(S2, M2, S, M, wsd_measure=False)
                mention_overall.append(mention_measures)
                
                wikify_measures = get_sentence_measures(S2, M2, S, M, wsd_measure=True)
                wikify_overall.append(wikify_measures)
                
                if (max_count !=-1) and (count >= max_count):
                    break
                    

        elapsed = str(timeformat(int(time.time()-start)));
        print "done"
        detailedres ={"dsname":dsname, "method": method, 
                      "max_t": max_t, "tp":overall, "elapsed": elapsed, "ws": ws}
        
        
        logres(detailedresname, '%s',  json.dumps(detailedres))
        
        mention_overall_measures = get_overall_measures(mention_overall)    
        output = ('mention_evaluation',method, max_t , dsname) + mention_overall_measures + (elapsed,)
        
        logres(resname, '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n', output)
        
        wikify_overall_measures = get_overall_measures(wikify_overall)  
        output = ('wikify_evaluation',method, max_t , dsname) + wikify_overall_measures + (elapsed,)
            

print "done"