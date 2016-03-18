
#Calculating Relatedness
from wikipedia import *
from pagerank import *
from utils import *

from collections import defaultdict

def _unify_ids_scores(*id_sc_tuple):
    uids, id2in = e2i(*(ids for ids, _ in id_sc_tuple));
    
    uscs=tuple();            
    for ids,scs in id_sc_tuple:
        scs_u=sp.zeros(len(id2in))
        scs_u[[id2in[wid] for wid in ids]] = scs;            
        uscs += (scs_u,)                
    return uids, uscs       


def concept_embedding(wid, direction):
    """ Calculates concept embedding to be used in relatedness
    
    Args:
        wid: wikipedia id
        direction: 0 for in, 1 for out, 2 for all
        
    Returns:
        The neighbor ids, their scores and the whole neighorhood graph (for visualization purposes)
        
    """
    
    if direction == DIR_IN or direction==DIR_OUT:
        return _concept_embedding_io(wid, direction)
    if direction == DIR_BOTH:
        return _concept_embedding_both(wid, direction)
    
def _concept_embedding_io(wid, direction):
    #checkcache = _checkcache(wid, direction);
    #if checkcache:
        #logger.info('found in cache')
    
    #    return checkcache;
    (ids, links) = getneighbors(wid, direction);
        
    scores = pagerank_sparse(create_csr(links), reverse=True)
        
    #_cachescores(ids, scores, direction);
    #return (ids, scores);
    return defaultdict(int,zip(ids, scores))
            

def _concept_embedding_both(wid, direction):            
        in_em = _concept_embedding_io(wid, DIR_IN);
        out_em = _concept_embedding_io(wid, DIR_OUT )
        
        ids=list(set(in_em.keys()).union(out_em.keys()))
        in_sc=[in_em[wid] for wid in ids]
        out_sc=[out_em[wid] for wid in ids]               
        scores=([(x+y)/2 for x,y in zip(in_sc, out_sc)])

        return defaultdict(int,zip(ids, scores))

                             
def calcsim(id1,id2, direction):
    """ Calculates the similarity between two concepts
    Arg:
        id1, id2: the two concepts
        direction: 0 for in, 1 for out, 2 for all
        
    Returns:
        The similarity score
    """
    em1 = concept_embedding(id1, direction);
    em2 = concept_embedding(id2, direction);
    
    ids=list(set(em1.keys()).union(em2.keys()))
    sc1=[em1[wid] for wid in ids]
    sc2=[em2[wid] for wid in ids]               
    
    return 1-sp.spatial.distance.cosine(sp.array(sc1),sp.array(sc2));
    

    
def getsim_file(infilename, outfilename, direction):
    """ Batched (file) similarity.
    
    Args: 
        infilename: tsv file in the format of pair1    pair2   [goldstandard]
        outfilename: tsv file in the format of pair1    pair2   similarity
        direction: 0 for in, 1 for out, 2 for all
    Returns:
        vector of scores, and Spearmans's correlation if goldstandard is given
    """
    log('getsim_file started: %s -> %s', infilename, outfilename)
    outfile = open(outfilename, 'w');
    dsdata=readds(infilename);
    gs=[];
    scores=[];
    #scores=[1-spatial.distance.cosine(vectors[row[0]],vectors[row[1]]) if (row[0] in vectors) and  (row[1] in vectors) else 0 for row in dsdata]
    spcorr=None;
    for row in dsdata:        
        #print str(row[0]) + ','+str(row[1]);
        if (row[0]=='None') or (row[1]=='None'):
            continue;
        if len(row)>2: 
            gs.append(row[2]);
            
        wid1 = title2id(row[0])
        wid2 = title2id(row[1])
        if (wid1=='None') or (wid2=='None'):
            sim=0;
        else:
            sim=calcsim(wid1, wid2, direction);
        outfile.write("\t".join([str(row[0]), str(row[1]), str(sim)])+'\n')
        scores.append(sim)
    outfile.close();
    if gs:
        spcorr = sp.stats.spearmanr(scores, gs);
    log('finished')
    return scores, spcorr

def conceptrep(wid, direction, get_titles=True, cutoff=None):
    """ Finds a representation for a concept
    
        Concept Representation is a vector of concepts with their score
    Arg:
        wid: Wikipedia id
        direction: 0 for in, 1 for out, 2 for all
        titles: include titles in the embedding (not needed for mere calculations)
        cutoff: the first top cutoff dimensions (None for all)
        
    Returns:
        the vecotr of ids, their titles and theirs scores. It also returns the
        graph for visualization purposes. 
    """
    em=concept_embedding(wid, direction);    
    
    ids = em.keys();
    if cutoff is not None:
        ids = sorted(em.keys(), key=lambda k: em[k], reverse=True)
        ids=ids[:cutoff]
        em=defaultdict(int, {wid:em[wid] for wid in ids})
        
    if get_titles:
        em=defaultdict(int, {wid:(title, em[wid]) for wid,title in zip(ids,ids2title(ids))})
    return em
    

def getembed_file(infilename, outfilename, direction, get_titles=False, cutoff=None):
    """ Batched (file) concept representation.
    
    Args: 
        infilename: tsv file in the format of pair1    pair2   [goldstandard]
        outfilename: tsv file in the format of pair1    pair2   similarity
        direction: 0 for in, 1 for out, 2 for all
        titles: include titles in the embedding (not needed for mere calculations)
        cutoff: the first top cutoff dimensions (None for all)        

    """
    
    log('getembed_file started: %s -> %s', infilename, outfilename)
    outfile = open(outfilename, 'w');
    dsdata=readds(infilename);
    scores=[];
    for row in dsdata:        
        #print str(row[0]) + ','+str(row[1]);
        wid = title2id(row[0])
        if wid=='None':
            em='';
        else:
            em=conceptrep(wid, direction, get_titles, cutoff)
        outfile.write(row[0]+"\t"+json.dumps(em)+"\n")
    outfile.close();
    log('finished')
