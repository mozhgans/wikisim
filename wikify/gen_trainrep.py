
from wikify import *
sys.stdout.flush()
max_t=5
ws=5
outdir = os.path.join(baseresdir, 'wikify')
outfile = os.path.join(home,'backup/datasets/ner/trainrepository.30000.5000.tsv')

dsname = os.path.join(home,'backup/datasets/ner/wiki-mentions.30000.json')

max_count=5000
count = 0          
with open(dsname,'r') as ds, open(outfile,'w') as outf:
    qid=0
    for line in ds:                           
        js = json.loads(line.decode('utf-8').strip());
        S = js["text"]
        M = js["mentions"]
        count +=1        
        print "%s:\tS=%s\n\tM=%s" % (count, json.dumps(S, ensure_ascii=False).encode('utf-8'),json.dumps(M, ensure_ascii=False).encode('utf-8'))        
        C = generate_candidates(S, M, max_t=max_t, enforce=False)
        #print C
        all_scores=get_all_scores(S,M,C, ws, 10)
        for i in  range(len(C)):
            m=M[i]
            cands = C[i]
            cand_scores = all_scores[i]
            wid = title2id(m[1]) 
            for (eid,_),scores in zip (cands, cand_scores):
                is_true_eid = (wid == eid)
                string_scores=[str(s) for s in scores]
                outf.write("\t".join([str(eid), str(qid)]+string_scores+[str(int(is_true_eid))])+"\n")
            qid += 1
        if count >= max_count:
            break
print "Done"             
        

        