# uncomment
from __future__ import division

#Calculating Relatedness
from wikipedia import * # uncomment
from pagerank import * # uncomment
from utils import * # uncomment

from collections import defaultdict
from scipy import stats
import json
import math

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
    log('concept_embedding started, wid = %s, direction = %s', wid, direction)

    if direction == DIR_IN or direction==DIR_OUT:
        em = _concept_embedding_io(wid, direction)
    if direction == DIR_BOTH:
        em = _concept_embedding_both(wid, direction)
    log('concept_embedding finished')
    return em
    
def _concept_embedding_io(wid, direction):
    cached_em = checkcache(wid, direction);
    if cached_em is not None:
        log('found in cache, wid = %s, direction = %s', wid, direction)
        return cached_em;

    (ids, links) = getneighbors(wid, direction);
    if not ids:
        return None;
    scores = pagerank_sparse(create_csr(links), reverse=True)
     
    em=defaultdict(int,zip(ids, scores));    
    cachescores(wid, em, direction);
    return em
            

def _concept_embedding_both(wid, direction):            
        in_em = _concept_embedding_io(wid, DIR_IN);
        out_em = _concept_embedding_io(wid, DIR_OUT )
        if (in_em is None) or (out_em is None):
            return None;
        
        ids=list(set(in_em.keys()).union(out_em.keys()))
        in_sc=[in_em[wid] for wid in ids]
        out_sc=[out_em[wid] for wid in ids]               
        scores=([(x+y)/2 for x,y in zip(in_sc, out_sc)])

        return defaultdict(int,zip(ids, scores))

def getsim_wlm(id1, id2):
    """ Calculates wlm (ngd) similarity between two concepts 
    Arg:
        id1, id2: the two concepts 
    Returns:
        The similarity score        
    """
    in1 = set(getlinkedpages(id1, DIR_IN))
    in2 = set(getlinkedpages(id2, DIR_IN))
    f1 = len(in1)
    f2 = len(in2)
    f12=len(in1.intersection(in2))
    dist = (sp.log(max(f1,f2))-sp.log(f12))/(sp.log(WIKI_SIZE)-sp.log(min(f1,f2)));
    if (f1==0) or (f2==0) or (f12==0):
        return 0;
    sim = 1-dist if dist <=1 else 0
    return sim

def getsim_cocit(id1, id2):
    """ Calculates co-citation similarity between two concepts 
    Arg:
        id1, id2: the two concepts 
    Returns:
        The similarity score        
    """
    in1 = set(getlinkedpages(id1, DIR_IN))
    in2 = set(getlinkedpages(id2, DIR_IN))
    f1 = len(in1)
    f2 = len(in2)
    if (f1==0) or (f2==0):
        return 0;
    
    f12=len(in1.intersection(in2))
    sim = (f12)/(f1+f2-f12);
    return sim


def getsim_coup(id1, id2):
    """ Calculates coupler similarity between two concepts 
    Arg:
        id1, id2: the two concepts 
    Returns:
        The similarity score        
    """
    in1 = set(getlinkedpages(id1, DIR_OUT))
    in2 = set(getlinkedpages(id2, DIR_OUT))
    f1 = len(in1)
    f2 = len(in2)
    if (f1==0) or (f2==0):
        return 0;
    
    f12=len(in1.intersection(in2))
    sim = (f12)/(f1+f2-f12);
    return sim

def getsim_ams(id1, id2):
    """ Calculates amlser similarity between two concepts 
    Arg:
        id1, id2: the two concepts 
    Returns:
        The similarity score        
    """
    in1 = set(getlinkedpages(id1, DIR_IN))
    out1 = set(getlinkedpages(id1, DIR_OUT))
    link1 = in1.union(out1)
    
    in2 = set(getlinkedpages(id2, DIR_IN))
    out2 = set(getlinkedpages(id2, DIR_OUT))
    link2 = in2.union(out2)
    
    f1 = len(link1)
    f2 = len(link2)
    if (f1==0) or (f2==0):
        return 0;
    
    f12=len(link1.intersection(link2))
    sim = (f12)/(f1+f2-f12);
    return sim




    
    
def getsim_emb(id1,id2, direction):
    """ Calculates the similarity between two concepts
    Arg:
        id1, id2: the two concepts
        direction: 0 for in, 1 for out, 2 for all
        
    Returns:
        The similarity score
    """
    em1 = concept_embedding(id1, direction);
    em2 = concept_embedding(id2, direction);
    if (em1 is None) or (em2 is None):
        return None;
    
    ids=list(set(em1.keys()).union(em2.keys()))
    sc1=[em1[wid] for wid in ids]
    sc2=[em2[wid] for wid in ids]               
    
    return 1-sp.spatial.distance.cosine(sp.array(sc1),sp.array(sc2));

def getsim(id1,id2, method, direction=None):
    """ Calculates well-known similarity metrics between two concepts 
    Arg:
        id1, id2: the two concepts 
        method:
            wlm: Wikipedia-Miner method
            cocit: cocitation
            coup: coupling
            ams: amsler
            rvspagerank: ebedding based similarity (in our case, 
                 reversed-page rank method)
    Returns:
        The similarity score        
    """
    if method=='rvspagerank':
        return getsim_emb(id1,id2, direction)
    if method=='wlm':
        return getsim_wlm(id1,id2)
    if method=='cocit':
        return getsim_cocit(id1,id2)
    if method=='coup':
        return getsim_coup(id1,id2)
    if method=='ams':
        return getsim_ams(id1,id2)

    
def getsim_file(infilename, outfilename, method='rvspagerank', direction=None):
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
        log('processing %s, %s', row[0], row[1])
        if (row[0]=='None') or (row[1]=='None'):
            continue;
        if len(row)>2: 
            gs.append(row[2]);
            
        wid1 = title2id(row[0])
        wid2 = title2id(row[1])
        if (wid1=='None') or (wid2=='None'):
            sim=0;
        else:
            sim=getsim(wid1, wid2, method, direction);
        outfile.write("\t".join([str(row[0]), str(row[1]), str(sim)])+'\n')
        scores.append(sim)
    outfile.close();
    if gs:
        spcorr = sp.stats.spearmanr(scores, gs);
    log('getsim_file finished')
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
    
    log('conceptrep started, wid = %s, direction = %s', wid, direction)
    
    em=concept_embedding(wid, direction);    
    if em is None:
        return None;
    ids = em.keys();
    if cutoff is not None:
        ids = sorted(em.keys(), key=lambda k: em[k], reverse=True)
        ids=ids[:cutoff]
        em=defaultdict(int, {wid:em[wid] for wid in ids})
        
    if get_titles:
        em=defaultdict(int, {wid:(title, em[wid]) for wid,title in zip(ids,ids2title(ids))})
    log ('conceptrep finished')
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
        wid = title2id(row[0])
        if wid=='None':
            em='';
        else:
            em=conceptrep(wid, direction, get_titles, cutoff)
        outfile.write(row[0]+"\t"+json.dumps(em)+"\n")
    outfile.close();
    log('getembed_file finished')
