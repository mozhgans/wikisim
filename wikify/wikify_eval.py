import sys
from optparse import OptionParser

#sys.path.insert(0,'..')
#from wikisim.calcsim import *
from wikify import *
import time
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
ws = 5


fresh_restart=True

#word2vec_path = os.path.join(home, 'backup/wikipedia/WikipediaClean5Negative300Skip10.Ehsan/WikipediaClean5Negative300Skip10')
#word2vec_path = os.path.join(home, '/users/grad/sajadi/backup/wikipedia/20160305/embed/word2vec.enwiki-20160305-replace_surface.1.0.500.10.5.15.5.5/word2vec.enwiki-20160305-replace_surface.1.0.500.10.5.15.5.5')


dsnames = [os.path.join(home,'backup/datasets/ner/kore.json'),
           os.path.join(home,'backup/datasets/ner/wiki-mentions.5000.json'),
           os.path.join(home,'backup/datasets/ner/aida.json'), 
           os.path.join(home,'backup/datasets/ner/msnbc.json'),
           os.path.join(home,'backup/datasets/ner/aquaint.json') 
          ]

dsnames = [os.path.join(home,'backup/datasets/ner/wiki-mentions.30000.5000.json')]

          
# dsnames = [os.path.join(home,'backup/datasets/ner/kore.json'),
#            os.path.join(home,'backup/datasets/ner/msnbc.json'),
#           ]


methods = ('popularity', 'keydisamb', 'entitycontext', 'context2context', 'context2profile','learned')



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



for method in methods:
    if 'word2vec' in method:
        gensim_loadmodel(word2vec_path)
        print "loaded"
        sys.stdout.flush()
    for dsname in dsnames:
        start = time.time()
        
        print "dsname: %s, method: %s, max_t: %s, ws: %s ..."  % (dsname,
                method, max_t, ws)
        sys.stdout.flush()
        
        tmpfilename = os.path.join(tmpdir, 
                                   '-'.join([method, str(max_t), str(ws), os.path.basename(dsname)]))
        overall=[]
        start_count=-1
        if os.path.isfile(tmpfilename) and not fresh_restart:
            with open(tmpfilename,'r') as tmpf:
                for line in tmpf:
                    js = json.loads(line.strip())
                    start_count = js['no']
                    if js['tp'] is not None:
                        overall.append(js['tp'])
        
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
                    
                C = generate_candidates(S, M, max_t=max_t, enforce=False)
                
                try:
                    #ids, titles = disambiguate_driver(S,M, C, ws=0, method=method, direction=direction, op_method=op_method)
                    ids, titles = wikify(S,M,C, ws, method=method)
                    tp = get_tp(M, ids) 
                except Exception as ex:
                    tp = (None, None)
                    print "[Error]:\t", type(ex), ex
                    raise
                    continue
                
                overall.append(tp)
                tmpf.write(json.dumps({"no":count, "tp":tp})+"\n")
                if (max_count !=-1) and (count >= max_count):
                    break
                    

        elapsed = str(timeformat(int(time.time()-start)));
        print "done"
        detailedres ={"dsname":dsname, "method": method, 
                      "max_t": max_t, "tp":overall, "elapsed": elapsed, "ws": ws}
        
        
        logres(detailedresname, '%s',  json.dumps(detailedres))
        
        micro_prec, macro_prec = get_prec(overall)        
        logres(resname, '%s\t%s\t%s\t%s\t%s\t%s\t%s', method, max_t , ws, 
               dsname, micro_prec, macro_prec, elapsed)

print "done"