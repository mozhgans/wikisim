""" Train a LambdaMart (LTR) Method
"""

def split_solr_text(text,tags):
    start=0
    termindex=0
    t=[]
    mentions=[]
    # pass 1, adjust partial mentions. 
    # approach one, expand (the other could be shrink)
    
    for tag in tags:
        seg = text[start:tag[1]]
        t += seg.strip().split()
        mentions.append([len(t),'UNKNOWN'])
        t+=[" ".join(text[tag[1]:tag[3]].split())]
        start = tag[3]
        
    t += text[start:].strip().split()
    return t, mentions

def annotate_with_solrtagger(text):
    
    addr = 'http://localhost:8983/solr/enwikianchors20160305/tag'
    params={'overlaps':'LONGEST_DOMINANT_RIGHT', 'tagsLimit':'5000', 'fl':'id','wt':'json','indent':'on'}
    text=solr_escape(text)
    r = requests.post(addr, params=params, data=text)    

    S,M = splittext(text,r.json()['tags'])
    return S,M

CORE_NLP=0
LEARNED_MENTION=1
def wikify_a_line(line, mentionmethod=CORE_NLP):
    S,M = annotate_with_solrtagger(line)
    C = generate_candidates(S, M, max_t=10, enforce=False)
    E = wsd(S, M, C, ws=5, method='learned', rows=10)
    return E

def wikify_api(text, mentionmethod=CORE_NLP):
    outlist=[]
    for line in text.splitlines():
        outlist.append(wikify_a_line(line, mentionmethod))
    return "\n".join(outlist)

def wikify_from_file_api(infilename, outfilename, mentionmethod=CORE_NLP):
    with open(infilename) as infile, open(outfilename, 'w') as outfile:
        for line in infilename.readlines():
            wikified = wikify_a_line(text, mentionmethod)
            outfile.write(wikified + "\n")
        