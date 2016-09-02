"""Calculating Relatedness."""
# uncomment

from __future__ import division


#from collections import defaultdict
import json
import math
from scipy import stats

from wikipedia import * # uncomment
from pagerank import * # uncomment
from utils import * # uncomment

__author__ = "Armin Sajadi"
__copyright__ = "Copyright 215, The Wikisim Project"
__credits__ = ["Armin Sajadi", "Evangelo Milios", "Armin Sajadi"]
__license__ = "GPL"
__version__ = "1.0.1"
__maintainer__ = "Armin Sajadi"
__email__ = "sajadi@cs.dal.ca"
__status__ = "Development"

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
    log('[concept_embedding started]\twid = %s, direction = %s', wid, direction)

    if direction == DIR_IN or direction==DIR_OUT:
        em = _concept_embedding_io(wid, direction)
    if direction == DIR_BOTH:
        em = _concept_embedding_both(wid, direction)
    log('[concept_embedding]\tfinished')
    return em
    
def _concept_embedding_io(wid, direction):
    wid = resolveredir(wid)
    cached_em = checkcache(wid, direction);
    if cached_em is not None:
        return cached_em;

    (ids, links) = getneighbors(wid, direction);
    if ids:
        scores = pagerank_sparse_power(create_csr(links), reverse=True)
        em = pd.Series(scores, index=ids) 
    else:
        em = pd.Series([], index=[])  
    cachescores(wid, em, direction);
    return em
            

def _concept_embedding_both(wid, direction):            
        in_em = _concept_embedding_io(wid, DIR_IN);
        out_em = _concept_embedding_io(wid, DIR_OUT )
        if (in_em is None) or (out_em is None):
            return None;
        return in_em.add(out_em, fill_value=0)/2

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
    if em1.empty or em2.empty:
        return 0;
    
    em1, em2 = em1.align(em2, fill_value=0)
#     print em1
#     print em2
    return 1-sp.spatial.distance.cosine(em1.values,em2.values);

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
    log('[getsim started]\method = %s, direction = %s, id1=%s, id2=%s', method, direction, id1, id2)
    
    if method=='rvspagerank':
        sim = getsim_emb(id1,id2, direction)
    elif method=='wlm':
        sim = getsim_wlm(id1,id2)
    elif method=='cocit':
        sim = getsim_cocit(id1,id2)
    elif method=='coup':
        sim = getsim_coup(id1,id2)
    elif method=='ams':
        sim = getsim_ams(id1,id2)
    else:
        sim=None
    log('[getsim]\tfinished')
    return sim

    
def getsim_file(infilename, outfilename, method='rvspagerank', direction=None):
    """ Batched (file) similarity.
    
    Args: 
        infilename: tsv file in the format of pair1    pair2   [goldstandard]
        outfilename: tsv file in the format of pair1    pair2   similarity
        direction: 0 for in, 1 for out, 2 for all
    Returns:
        vector of scores, and Spearmans's correlation if goldstandard is given
    """
    log('[getsim_file started]\t%s -> %s', infilename, outfilename)
    outfile = open(outfilename, 'w');
    dsdata=readds(infilename);
    gs=[];
    scores=[];
    spcorr=None;
    for row in dsdata.itertuples():   
        log('processing %s, %s', row[1], row[2])
        if (row[1]=='null') or (row[2]=='null'):
            continue;
        if len(row)>3: 
            gs.append(row[3]);
            
        wid1 = title2id(row[1])
        wid2 = title2id(row[2])
        if (wid1 is None) or (wid2 is None):
            sim=0;
        else:
            sim=getsim(wid1, wid2, method, direction);
        outfile.write("\t".join([str(row[1]), str(row[2]), str(sim)])+'\n')
        scores.append(sim)
    outfile.close();
    if gs:
        spcorr = sp.stats.spearmanr(scores, gs);
    log('[getsim_file]\tfinished')
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
    
    log('[conceptrep started]\twid = %s, direction = %s', wid, direction)
    
    em=concept_embedding(wid, direction);    
    if em.empty:
        return em;
    
    
    #ids = em.keys();
    
    if cutoff is not None:
        em = em.sort_values(ascending=False)
        em = em[:cutoff]
    if get_titles:
        em = pd.Series(zip(ids2title(em.index), em.values.tolist()), index=em.index)
    log ('[conceptrep]\tfinished')
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
    
    log('[getembed_file started]\t%s -> %s', infilename, outfilename)
    outfile = open(outfilename, 'w');
    dsdata=readds(infilename, usecols=[0]);
    scores=[];
    for row in dsdata.itertuples():        
        wid = title2id(row[1])
        if wid is None:
            em=pd.Series();
        else:
            em=conceptrep(wid, direction, get_titles, cutoff)
        outfile.write(row[1]+"\t"+em.to_json()+"\n")
    outfile.close();
    log('[getembed_file]\tfinished')
