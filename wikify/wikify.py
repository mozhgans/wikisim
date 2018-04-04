

from __future__ import division

from collections import Counter
import cPickle as pickle
import sys
from coherence import *
#sys.path.insert(0,'..')

#from wikisim.calcsim import *
#from wsd.wsd import *
# My methods
#from senseembed_train_test.ipynb

disam_model_file_name = os.path.join(home,'backup/datasets/ner/ltr.pkl')
disam_model = pickle.load(open(disam_model_file_name, 'rb'))    

def get_context(anchor, eid):
    
    params={'wt':'json', 'rows':'50000'}
    anchor = solr_escape(anchor)
    
    q='anchor:"%s" AND entityid:%s' % (anchor, eid)
    params['q']=q
    
#     session = requests.Session()
#     http_retries = Retry(total=20,
#                     backoff_factor=.1)
#     http = requests.adapters.HTTPAdapter(max_retries=http_retries)
#     session.mount('http://localhost:8983/solr', http)
    
    r = session.get(qstr, params=params).json()
    if 'response' not in r: 
        print "[terminating]\t%s",(str(r),)
        sys.stdout.flush()
        os._exit(0)
        
    if not r:
        return []
    return r['response']['docs']

#from wsd
def word2vec_context_candidate_scores (S, M, candslist, ws):
    '''returns entity scores using the similarity with their context
       Inputs: 
           S: Sentence
           M: Mentions
           candslist: candidate list [[(c11, p11),...(c1k, p1k)],...[(cn1, pn1),...(c1m, p1m)]]
            ws: word size
       Returns:
           Scores [[s11,...s1k],...[sn1,...s1m]] where sij is cij similarity to the key-entity
    '''
    
    candslist_scores=[]
    for i in range(len(candslist)):
        cands = candslist[i]
        pos = M[i][0]
        #print "At: ", M[i]
        context = S[max(pos-ws,0):pos]+S[pos+1:pos+ws+1]
        #print context
        #print candslist[i], pos,context
        context_vec = sp.zeros(getword2vec_model().vector_size)
        for c in context:
            #print "getting vector for: " , c
            context_vec += getword2vector(c).as_matrix()
        #print context_vec
        cand_scores=[]

        for c in cands:
            try:
                cand_vector = getentity2vector(encode_entity(c[0],'word2vec', get_id=False))
                d = 1-sp.spatial.distance.cosine(context_vec, cand_vector);
            except:
                d=0                
            if np.isnan(d):
                d=0
            
            cand_scores.append(d)    
        candslist_scores.append(cand_scores) 

    return candslist_scores

#from wsd
def word2vec_context_disambiguate(S, M, candslist, ws ):
    '''Disambiguate a sentence using word-context similarity
       Inputs: 
           S: Sentence
           M: Mentions
           candslist: candidate list [[(c11, p11),...(c1k, p1k)],...[(cn1, pn1),...(c1m, p1m)]]
           
       Returns: 
           a list of entity ids and a list of titles
    '''
    
        
    candslist_scores = word2vec_context_candidate_scores (S, M, candslist, ws)
                      
    # Iterate 
    true_entities = []
    for cands, cands_scores in zip(candslist, candslist_scores):
        max_index, max_value = max(enumerate(cands_scores), key= lambda x:x[1])
        true_entities.append(cands[max_index][0])

    titles = ids2title(true_entities)
    return true_entities, titles 


def solr_escape(s):
    #ToDo: probably && and || nead to be escaped as a whole, and also AND, OR, NOT are not included
    to_sub=re.escape(r'+-&&||!(){}[]^"~*?:\/')
    return re.sub('[%s]'%(to_sub,), r'\\\g<0>', s)

#from wikisim
def get_solr_count(s):
    """ Gets the number of documents the string occurs 
        NOTE: Multi words should be quoted
    Arg:
        s: the string (can contain AND, OR, ..)
    Returns:
        The number of documents
    """
    q='+text:(%s)'%(s,)
    qstr = 'http://localhost:8983/solr/enwiki20160305/select'
    params={'indent':'on', 'wt':'json', 'q':q, 'rows':0}
    r = requests.get(qstr, params=params)
    D = r.json()['response']
    return D['numFound']



# Editing Ryan's code
def context_to_profile_sim(mention, context, candidates):
    """
    Description:
        Uses Solr to find the relevancy scores of the candidates based on the context.
    Args:
        mentionStr: The mention as it appears in the text
        context: The words that surround the target word.
        candidates: A list of candidates that each have the entity id and its frequency/popularity.
    Return:
        The score for each candidate in the same order as the candidates.
    """
    
    
    # put text in right format
    if not context:
        return [0]*len(candidates)
    context = solr_escape(context)
    mention = solr_escape(mention)
    
    filter_ids = " ".join(['id:' +  str(tid) for tid,_ in candidates])
        

    # select all the docs from Solr with the best scores, highest first.
    qst = 'http://localhost:8983/solr/enwiki20160305/select'
    q='text:('+context+')^1 title:(' + mention+')^1.35'
    
    params={'fl':'id score', 'fq':filter_ids, 'indent':'on',
            'q':q, 'wt':'json'}
    
    #print params
    
    r = requests.get(qst, params = params).json()['response']['docs']
    id_score_map=defaultdict(float, {long(ri['id']):ri['score'] for ri in r})
    id_score=[id_score_map[c] for c,_ in candidates]
    return id_score

# Important TODO
# This queriy is very much skewed toward popularity, better to replace space with AND
#!!!! I don't like this implementation, instead of retrieving and counting, better to let the 
# solr does the counting, 
def context_to_context_sim(mention, context, candidates, rows=10):
    """
    Description:
        Uses Solr to find the relevancy scores of the candidates based on the context.
    Args:
        mentionStr: The mention as it appears in the text
        context: The words that surround the target word.
        candidates: A list of candidates that each have the entity id and its frequency/popularity.
    Return:
        The score for each candidate in the same order as the candidates.
    """
    if not context:
        return [0]*len(candidates)
    
    # put text in right format
    context = solr_escape(context)
    mention = solr_escape(mention)
    
    filter_ids = " ".join(['entityid:' +  str(tid) for tid,_ in candidates])
    
    
    # select all the docs from Solr with the best scores, highest first.
    qstr = 'http://localhost:8983/solr/enwiki20160305_context/select'
    q="_context_:(%s) entity:(%s)" % (context,mention)
    
    params={'fl':'entityid', 'fq':filter_ids, 'indent':'on',
            'q':q,'wt':'json', 'rows':rows}
    #print params
    r = requests.get(qstr, params = params)
    cnt = Counter()
    
    for doc in r.json()['response']['docs']:
        cnt[long(doc['entityid'])] += 1
    
    id_score=[cnt[c] for c,_ in candidates]
    return id_score

def get_mention_count(s):
    """
    Description:
        Returns the amount of times that the given string appears as a mention in wikipedia.
    Args:
        s: the string (can contain AND, OR, ..)
    Return:
        The amount of times the given string appears as a mention in wikipedia
    """
    
    return sum(c for _,c in anchor2concept(s))  

def mention_prob(text):
    """
    Description:
        Returns the probability that the text is a mention in Wikipedia.
    Args:
        text: 
    Return:
        The probability that the text is a mention in Wikipedia.
    """
    
    total_mentions = get_mention_count(text)
    total_appearances = get_solr_count(text.replace(".", ""))
    if total_appearances == 0:
        return 0 # a mention never used probably is not a good link
    return float(total_mentions)/total_appearances


def context_candidate_scores (S, M, candslist, ws, method='c2c', rows=10):
    '''returns entity scores using  context seatch
       Inputs: 
           S: Sentence
           M: Mentions
           candslist: candidate list [[(c11, p11),...(c1k, p1k)],...[(cn1, pn1),...(c1m, p1m)]]
            ws: word size
            method: Either 'c2p': for context to profile, or 'c2c' for context to context
       Returns:
           Scores [[s11,...s1k],...[sn1,...s1m]] where sij is cij similarity to the key-entity
    '''
    
    candslist_scores=[]
    for i in range(len(candslist)):
        cands = candslist[i]
        pos = M[i][0]
        mention=S[pos]
        context = S[max(pos-ws,0):pos]+S[pos+1:pos+ws+1]
        context=" ".join(context)
        #print "mention: ",mention
        #print "context: ",context
        
        if method == 'c2p':
            cand_scores=context_to_profile_sim(mention, context, cands)
        if method == 'c2c':
            cand_scores=context_to_context_sim(mention, context, cands, rows=rows)
            
        candslist_scores.append(cand_scores) 

    return candslist_scores

def popularity_score(candslist):
    scores=[[s for _, s in cands] for cands in candslist]
    return scores

def normalize(scores_list):
    normalized_scoreslist=[]
    for scores in scores_list:
        smooth=0
        if 0 in scores:
            smooth=1
        sum_s = sum(s+smooth for s in scores )        
        n_scores = [float(s+smooth)/sum_s for s in scores]
        normalized_scoreslist.append(n_scores)
    return normalized_scoreslist
        
def normalize_minmax(scores_list):
    normalized_scoreslist=[]
    for scores in scores_list:
        scores_min = min(scores)        
        scores_max = max(scores)        
        if scores_min == scores_max:
            n_scores = [0]*len(scores)
        else:
            n_scores = [(float(s)-scores_min)/(scores_max-scores_min) for s in scores]
        normalized_scoreslist.append(n_scores)
    return normalized_scoreslist

def find_max(candslist,candslist_scores):
    '''Disambiguate a sentence using a list of candidate-score tuples
       Inputs: 
           candslist: candidate list [[(c11, s11),...(c1k, s1k)],...[(cn1, sn1),...(c1m, s1m)]]
       Returns: 
           a list of entity ids and a list of titles
    '''
            
    true_entities = []
    for cands, cands_scores in zip(candslist, candslist_scores):
        max_index, max_value = max(enumerate(cands_scores), key= lambda x:x[1])
        true_entities.append(cands[max_index][0])

    titles = ids2title(true_entities)
    return true_entities, titles        


def get_scores(S, M, C, ws, method, rows=10):
    """ Disambiguate C list using a disambiguation method 
        Inputs:
            C: Candidate list [[(c11, p11),...(c1k, p1k)],...[(cn1, pn1),...(c1m, p1m)]]
            method: similarity method
            direction: embedding type
            op_method: disambiguation method 
                        most important ones: ilp (integer linear programming), 
                                             key: Key Entity based method
        
    """
    scores=None
    if method == 'popularity'  :
        scores = popularity_score(C)
    if method == 'keydisamb'  :
        scores = coherence_scores_driver(C, ws, method='rvspagerank', direction=DIR_BOTH, op_method="keydisamb")
    if method == 'entitycontext'  :
        scores = coherence_scores_driver(C, ws, method='rvspagerank', direction=DIR_BOTH, op_method="entitycontext")
    if method == 'context2context'  :
        scores = context_candidate_scores (S, M, C, ws, method='c2c', rows=rows)
    if method == 'context2profile'  :
        scores = context_candidate_scores (S, M, C, ws, method='c2p')    
    if method == 'learned'  :
        scores = learned_scores (S, M, C, ws)    
        
    scores = normalize_minmax(scores)    
    return scores

def formated_scores(scores):
    scores = [['{0:.2f}'.format(s) for s in cand_scores] for cand_scores in scores]
    return scores

def get_all_scores(S, M, C, ws, rows=10):
    all_scores= [get_scores(S, M, C, ws, method, rows) for method in \
           ['popularity','keydisamb','entitycontext','context2context','context2profile']]
    return [zip(*s) for s in zip(*all_scores)]


def formated_all_scores(scores):
    scores = [[tuple('{0:.2f}'.format(s) for s in sub_scores) for sub_scores in cand_scores] for cand_scores in scores]
    return scores

def keyentity_disambiguate(candslist, direction=DIR_OUT, method='rvspagerank', ver=4):
    '''Disambiguate a sentence using key-entity method
       Inputs: 
           candslist: candidate list [[(c11, p11),...(c1k, p1k)],...[(cn1, pn1),...(c1m, p1m)]]
           direction: embedding direction
           method: similarity method
           ver: 1 for the method explained in the paper
       Returns: 
           a list of entity ids and a list of titles
    '''
    
        
    candslist_scores = keyentity_candidate_scores (candslist, direction, method, ver)
    # Iterate 
    true_entities = []
    for cands, cands_scores in zip(candslist, candslist_scores):
        max_index, max_value = max(enumerate(cands_scores), key= lambda x:x[1])
        true_entities.append(cands[max_index][0])

    titles = ids2title(true_entities)
    return true_entities, titles  

def learned_scores (S, M, candslist, ws):
    '''returns entity scores using the similarity with their context
       Inputs: 
           S: Sentence
           M: Mentions
           candslist: candidate list [[(c11, p11),...(c1k, p1k)],...[(cn1, pn1),...(c1m, p1m)]]
            ws: word size
       Returns:
           Scores [[s11,...s1k],...[sn1,...s1m]] where sij is cij similarity to the key-entity
    '''
    all_scores=get_all_scores(S,M,candslist, ws, 10)
    return [disam_model.predict(cand_scores) for cand_scores in all_scores] 

def wikify(S, M, C, ws, method, rows=10):
    candslist_scores = get_scores(S, M, C, ws, method, rows)
    return find_max(C,candslist_scores)