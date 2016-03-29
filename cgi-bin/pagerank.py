# uncomment

# Two implementations of PageRank
import scipy as sp
import scipy.sparse as sprs
import scipy.spatial
import scipy.sparse.linalg 
#from scipy.sparse.linalg import spsolve
#import networkx as nx
#import numpy as np;
#example 1


from utils import * # uncomment

def create_csr(Z):
    """ Creates a csr presentation from 2darray presentation and 
        calculates the pagerank
    Args:
        G: input graph in the form of a 2d array, such as [[2,0], [1,2], [2,1]]
    Returns:
        Pagerank Scores for the nodes
    
    each row of the array is an edge of the graph [[a,b], [c,d]], a and b are the node numbers. 

    """   
    rows = Z[:,0];
    cols = Z[:,1];
    n = max(max(rows), max(cols))+1;
    G=sprs.csr_matrix((sp.ones(rows.shape),(rows,cols)), shape=(n,n));
    return G

def pagerank_sparse(G, p=0.85, personalize=None, reverse=False):
    """ Calculates pagerank given a csr graph
    
    Args:
        G: a csr graph.
        p: damping factor
        personlize: if not None, should be an array with the size of the nodes
                    containing probability distributions. It will be normalized automatically
        reverse: If true, returns the reversed-pagerank 
        
    Returns:
        Pagerank Scores for the nodes
     
    """
    log('pagerank_sparse started')

    if not reverse:
        G=G.T;

    n,n=G.shape
    c=sp.asarray(G.sum(axis=0)).reshape(-1)
    r=sp.asarray(G.sum(axis=1)).reshape(-1)

    k=c.nonzero()[0]

    D=sprs.csr_matrix((1/c[k],(k,k)),shape=(n,n))

    if personalize is None:
        e=sp.ones((n,1))
    else:
        e = personalize/sum(personalize);
        
    I=sprs.eye(n)
    X1 = sprs.linalg.spsolve((I - p*G.dot(D)), e);

    X1=X1/sum(X1)
    log('pagerank_sparse finished')
    return X1
def pagerank_sparse_power(G, p=0.85, max_iter = 100, personalize=None, reverse=False):
    """ Calculates pagerank given a csr graph
    
    Args:
        G: a csr graph.
        p: damping factor
        max_iter: maximum number of iterations
        personlize: if not None, should be an array with the size of the nodes
                    containing probability distributions. It will be normalized automatically
        reverse: If true, returns the reversed-pagerank 
        
    Returns:
        Pagerank Scores for the nodes
     
    """
    log('pagerank_sparse_power started')
    
    if not reverse: 
        G=G.T;

    n,n=G.shape
    c=sp.asarray(G.sum(axis=0)).reshape(-1)
    r=sp.asarray(G.sum(axis=1)).reshape(-1)

    k=c.nonzero()[0]

    D=sprs.csr_matrix((1/c[k],(k,k)),shape=(n,n))

    if personalize is None:
        e=sp.ones((n,1))
    else:
        e = personalize/sum(personalize);
        
    z = (((1-p)*(c!=0) + (c==0))/n)[sp.newaxis,:]
    G = p*G.dot(D)
    x = e/n
    oldx = sp.zeros((n,1));
    
    iteration = 0
    start = time.time()    
    while sp.linalg.norm(x-oldx) > 0.01:
        oldx = x
        x = G.dot(x) + e.dot(z.dot(x))
        iteration += 1
        if iteration >= max_iter:
            break;
    x = x/sum(x)
    
    log('pagerank_sparse_power finished')
    return x.reshape(-1) 
