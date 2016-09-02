"""Calculating Relatedness."""
# uncomment

from __future__ import division
import scipy.spatial


#from collections import defaultdict
from scipy import stats
import json
import math

from wikismall import * # uncomment

__author__ = "Armin Sajadi"
__copyright__ = "Copyright 215, The Wikisim Project"
__credits__ = ["Armin Sajadi", "Evangelo Milios", "Armin Sajadi"]
__license__ = "GPL"
__version__ = "1.0.1"
__maintainer__ = "Armin Sajadi"
__email__ = "sajadi@cs.dal.ca"
__status__ = "Development"


def concept_embedding(wid, direction):
    """ Calculates concept embedding to be used in relatedness
    
    Args:
        wid: wikipedia id
        direction: 0 for in, 1 for out, 2 for all
        
    Returns:
        The neighbor ids, their scores and the whole neighorhood graph (for visualization purposes)
        
    """
    if direction == DIR_IN or direction==DIR_OUT:
        em = _concept_embedding_io(wid, direction)
    if direction == DIR_BOTH:
        em = _concept_embedding_both(wid, direction)
    return em
    
def _concept_embedding_io(wid, direction):
    wid = resolveredir(wid)
    return checkcache(wid, direction);
            

def _concept_embedding_both(wid, direction):            
        in_em = _concept_embedding_io(wid, DIR_IN);
        out_em = _concept_embedding_io(wid, DIR_OUT )
        if (in_em is None) or (out_em is None):
            return None;
        return in_em.add(out_em, fill_value=0)/2


def getsim(id1,id2, direction):
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
    if em.empty:
        return em;
    
    
    #ids = em.keys();
    
    if cutoff is not None:
        em = em.sort_values(ascending=False)
        em = em[:cutoff]
    if get_titles:
        em = pd.Series(zip(ids2title(em.index), em.values.tolist()), index=em.index)
    return em
    
