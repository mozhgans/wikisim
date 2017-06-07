""" Evaluating the method on Semantic Relatedness Datasets."""


import sys
import os
import time;
import json 
import requests
from itertools import chain
from itertools import product
from itertools import combinations

import numpy as np
        


sys.path.insert(0,'..')
from wikisim.config import *

from wikisim.calcsim import *
#reopen()


def generate_candidates(S, M, max_t=10, enforce=False):
    """ Given a sentence list (S) and  a mentions list (M), returns a list of candiates
        Inputs:
            S: segmented sentence [w1, ..., wn]
            M: mensions [m1, ... , mj]
            max_t: maximum candiate per mention
            enforce: Makes sure the "correct" entity is among the candidates
        Outputs:
         Candidate list [[(c11, p11),...(c1k, p1k)],...[(cn1, pn1),...(c1m, p1m)]]
             where cij is the jth candidate for ith mention and pij is the relative frequency of cij
    
    """
    candslist=[]
    for m in M:
        wid = title2id(m[1])
        if wid is None:
            raise Exception(m[1].encode('utf-8') + ' not found')
        
        clist = anchor2concept(S[m[0]])
        clist = sorted(clist, key=lambda x: -x[1])

        smooth=0    
        trg = [(i,(c,f)) for i,(c,f) in enumerate(clist) if c==wid]
        if enforce and (not trg):
            trg=[(len(clist), (wid,0))]
            smooth=1

            
        clist = clist[:max_t]
        if enforce and (smooth==1 or trg[0][0]>=max_t): 
            if clist:
                clist.pop()
            clist.append(trg[0][1])
        s = sum(c[1]+smooth for c in clist )        
        clist = [(c,float(f+smooth)/s) for c,f in clist ]
            
        candslist.append(clist)
    return  candslist 

def disambiguate(S,M, C, method, direction, op_method):
    """ Disambiguate C list using a disambiguation method 
        Inputs:
            C: Candidate list [[(c11, p11),...(c1k, p1k)],...[(cn1, pn1),...(c1m, p1m)]]
            method: similarity method
            direction: embedding type
            op_method: disambiguation method 
                        most important ones: ilp (integer linear programming), 
                                             key: Key Entity based method
        
    """
    if op_method == 'popularity':
        return disambiguate_popular(C)
    if op_method == 'ilp':
        return disambiguate_ilp(C, method, direction)
    if op_method == 'ilp2':
        return disambiguate_ilp_2(C, method, direction)
    if op_method == 'keyq':
        return key_quad(C, method, direction)
    if op_method == 'pkeyq':
        return Pkey_quad(C, method, direction)
    if  op_method == 'context1'  :
        return contextdisamb_1(C, direction)
    if  op_method == 'context2'  :
        return contextdisamb_2(C, direction)
    if  op_method == 'context3'  :
        return contextdisamb_3(C, direction)
    if  op_method == 'entitycontext'  :
        return entity_context_disambiguate(C, direction, method)

        
    if  op_method == 'context4_1'  :
        return keyentity_disambiguate(C, direction, method, 1)
    if  op_method == 'context4_2'  :
        return keyentity_disambiguate(C, direction, method, 2)
    if  op_method == 'context4_3'  :
        return keyentity_disambiguate(C, direction, method, 3)    
    if  op_method == 'keydisamb'  :
        return keyentity_disambiguate(C, direction, method, 4)
    
    if  op_method == 'tagme'  :
        return tagme(C, method, direction)
    if  op_method == 'tagme2'  :
        return tagme(C, method, direction, True)
    
    if  op_method == 'word2vec_word_context'  :
        return word_context_disambiguate(S, M, C, 5)
    
    return None



def disambiguate_driver(S,M, C, ws, method='rvspagerank', direction=DIR_BOTH, op_method="keydisamb"):
    """ Initiate the disambiguation by chunking the sentence 
        Disambiguate C list using a disambiguation method 
        Inputs:
            C: Candidate list [[(c11, p11),...(c1k, p1k)],...[(cn1, pn1),...(c1m, p1m)]]
            ws: Windows size for chunking
            method: similarity method
            direction: embedding type
            op_method: disambiguation method 
                        most important ones: ilp (integer linear programming), 
                                             keyq: Key Entity based method
        
    """
    if ws == 0: 
        return  disambiguate(S,M, C, method, direction, op_method)
    
    ids = []
    titles = []
    
    windows = [[start, min(start+ws, len(C))] for start in range(0,len(C),ws) ]
    last = len(windows)
    if last > 1 and windows[last-1][1]-windows[last-1][0]<2:
        windows[last-2][1] = len(C)
        windows.pop()
        
    for w in windows:
        chunk_c = C[w[0]:w[1]]
        chunk_ids, chunk_titles = disambiguate(S, M, chunk_c, method, direction, op_method)
        ids += chunk_ids
        titles += chunk_titles
    return ids, titles     

def get_tp(gold_titles, ids):
    tp=0
    for m,id2 in zip(gold_titles, ids):
        if title2id(m[1]) == id2:
            tp += 1
    return [tp, len(ids)]

def get_prec(tp_list):
    overall_tp = 0
    simple_count=0
    overall_count=0
    macro_prec = 0;
    for tp, count in tp_list:
        if tp is None:
            continue
        simple_count +=1    
        overall_tp += tp
        overall_count += count
        macro_prec += float(tp)/count
        
    macro_prec = macro_prec/simple_count
    micro_prec = float(overall_tp)/overall_count
    
    return micro_prec, macro_prec

def disambiguate_popular(C):
    ids = [c[0][0] for c in C ]
    titles= ids2title(ids)
    return ids, titles
# Integer Programming

from itertools import izip
from itertools import product
from pulp import *
import random

def getscore(x,y,method, direction):
    """Get similarity score for a method and a direction """
    x = encode_entity(x, method, get_id=False)
    y = encode_entity(y, method, get_id=False)
    return getsim(x,y ,method, direction)
    #return random.random()

def disambiguate_ilp(C, method, direction):
    """ Disambiguate using ILP 
        Inputs: 
            C: Candidate List [[(c11, p11),...(c1k, p1k)],...[(cn1, pn1),...(c1m, p1m)]]
            method: Similarity method
            direction: embedding direction"""
    #C = [('a','b','c'), ('e', 'f', 'g'), ('h', 'i')]

    R1 = [zip([i]*len(c), range(len(c))) for i,c in enumerate(C)]

    #R1 = {r:str(r) for r in itertools.chain(*RI1)}
    #R1 = [[str(rij) for rij in ri] for ri in RI1]

    #RI1_flat = list(itertools.chain(*RI1))


    R2=[]
    for e in combination(R1,2):
        R2 += [r for r in itertools.product(e[0], e[1]) ]        


    #R2 = {r:str(r) for r in RI2}


    
    S = {((u0,u1),(v0,v1)):getscore(C[u0][u1][0],C[v0][v1][0], method, direction) for ((u0,u1),(v0,v1)) in R2}


    prob = LpProblem("wsd", LpMaximize)

    R=list(itertools.chain(*R1)) + R2
    R_vars = LpVariable.dicts("R",R,
                                lowBound = 0,
                                upBound = 1,
                                cat = pulp.LpInteger)
    prob += lpSum([S[r]*R_vars[r] for r in R2])


    i=0
    for ri in R1:
        prob += lpSum([R_vars[rij] for rij in ri])==1, ("R1 %s constraint")%i
        i += 1


    for r in R2:
        prob += lpSum([R_vars[r[0]],R_vars[r[1]],-2*R_vars[r]]) >=0, ("R_%s_%s constraint"%(r[0], r[1]))

    prob.solve() 
    #print("Status:", LpStatus[prob.status])
    #print("Score:", value(prob.objective))
    ids    = [C[r[0]][r[1]][0] for r in list(itertools.chain(*R1)) if R_vars[r].value() == 1.0]
    titles = ids2title(ids)
    return ids, titles
        
def disambiguate_ilp_2(C, method, direction):
    
    #C = [('a','b','c'), ('e', 'f', 'g'), ('h', 'i')]

    #R1 = [zip(["R"z]*len(c),zip([i]*len(c), range(len(c)))) for i,c in enumerate(C)]
    R1 = [zip(['R']*len(c),[i]*len(c), range(len(c))) for i,c in enumerate(C)]
    Q = [zip(['Q']*len(c),[i]*len(c), range(len(c))) for i,c in enumerate(C)]

    #R1 = {r:str(r) for r in itertools.chain(*RI1)}
    #R1 = [[str(rij) for rij in ri] for ri in RI1]

    #RI1_flat = list(itertools.chain(*RI1))


    R2=[]
    for e in combination(R1,2):
            R2 += [('R',(i,k),(j,l)) for (_,i,k),(_,j,l) in itertools.product(e[0], e[1]) ]        


    #R2 = {r:str(r) for r in RI2}



    S = {('R',(i,k),(j,l)):getscore(C[i][k][0],C[j][l][0], method, direction) for _,(i,k),(j,l) in R2}


    prob = LpProblem("wsd", LpMaximize)

    R=list(itertools.chain(*R1)) + R2
    Q=list(itertools.chain(*Q))
    R_vars = LpVariable.dicts("R",R,
                                lowBound = 0,
                                upBound = 1,
                                cat = pulp.LpInteger)

    Q_vars = LpVariable.dicts("Q",Q,
                                lowBound = 0,
                                upBound = 1,
                                cat = pulp.LpInteger)

    prob += lpSum([S[r]*R_vars[r] for r in R2])


    i=0
    for ri in R1:
        prob += lpSum([R_vars[rij] for rij in ri])==1, ("R1 %s constraint")%i
        i += 1

    prob += lpSum(Q_vars.values())==1, ("Q constraint")


    for _,(i,k),(j,l) in R2:
        prob += lpSum([R_vars[('R',i,k)],R_vars[('R',j,l)],-2*R_vars[('R',(i,k),(j,l))]]) >=0, ("R_%s_%s constraint"%((i,k),(j,l)))
        prob += lpSum([Q_vars[('Q',i,k)],Q_vars[('Q',j,l)], -1*R_vars[('R',(i,k),(j,l))]]) >=0, ("Q_%s_%s constraint"%((i,k),(j,l)))

    prob.solve() 
#     print("Status:", LpStatus[prob.status])
#     print("Score:", value(prob.objective))

#     for (_,i,k), q in Q_vars.items():
#         if q.value()==1:
#             print("central concept: ", id2title(C[i][k][0]))
    ids    = [C[i][k][0] for _,i,k in list(itertools.chain(*R1)) if R_vars[('R',i,k)].value() == 1.0]
    
    
    titles = ids2title(ids)
    return ids, titles

# key
def evalkey(c, a, candslist, simmatrix):
    resolved=[]
    score=0;
    for i in  range(len(candslist)):
        if a==i:
            resolved.append(c[0])
            continue
        cands = candslist[i]
        vb = [(cj[0], simmatrix[c[0]][cj[0]])  for cj in cands]
        max_concept, max_sc = max(vb, key=lambda x: x[1])
        score += max_sc
        resolved.append(max_concept)
    return resolved,score

def key_quad(candslist, method, direction):
    res_all=[]
    simmatrix = get_sim_matrix(candslist, method, direction)

    for i in range(len(candslist)):
        for j in range(len(candslist[i])):
            res_ij =  evalkey(candslist[i][j], i, candslist, simmatrix)
            res_all.append(res_ij)
    res, score = max(res_all, key=lambda x: x[1])
    #print("Score:", score)
    titles = ids2title(res)
    return res, titles

# Parallel Keyquad
from functools import partial
from multiprocessing import Pool as ThreadPool 
def Pevalkey((c, a), candslist, simmatrix):
    resolved=[]
    score=0;
    for i in  range(len(candslist)):
        if a==i:
            resolved.append(c[0])
            continue
        cands = candslist[i]
        vb = [(cj[0], simmatrix[c[0]][cj[0]])  for cj in cands]
        max_concept, max_sc = max(vb, key=lambda x: x[1])
        score += max_sc
        resolved.append(max_concept)
    return resolved,score
def Pkey_quad(candslist, method, direction):
    res_all=[]
    simmatrix = get_sim_matrix(candslist, method, direction)
    pool = ThreadPool(25) 
    
    partial_evalkey = partial(Pevalkey, candslist=candslist, simmatrix=simmatrix)
    I=[[j]*len(candslist[j]) for j in range(len(candslist))]
    
    res_all= pool.map(partial_evalkey, zip(itertools.chain(*candslist), itertools.chain(*I)))
    pool.close() 
    pool.join() 
    
    res, score = max(res_all, key=lambda x: x[1])
    titles = ids2title(res)
    return res, titles


# Context Vector

        

def contextdisamb_1(candslist, direction=DIR_OUT):
    cframelist=[]
    cveclist_bdrs = []
    for cands in candslist:
        cands_rep = [conceptrep(c[0], direction=direction, get_titles=False) for c in cands]
        cveclist_bdrs += [(len(cframelist), len(cframelist)+len(cands_rep))]
        cframelist += cands_rep

    # for cands in candslist:
    #     cveclisttitles.append([conceptrep(c, direction, get_titles=False) for c in cands])

    cvec_fr = pd.concat(cframelist, join='outer', axis=1)
    cvec_fr.fillna(0, inplace=True)
    cvec_arr = cvec_fr.as_matrix().T

    i=0
    for cframe in cframelist:
        if cframe.empty:
            cvec_arr = np.insert(cvec_arr,i,0, axis=0)
        i+=1    
    
    convec = cvec_arr.sum(axis=0)
    from itertools import izip
    res=[]
    for i in range(len(candslist)):
        cands = candslist[i]
        b,e = cveclist_bdrs[i]
        cvec = cvec_arr[b:e]
        
        maxd=-1
        mi=0
        for v in cvec:
            d = 1-sp.spatial.distance.cosine(convec, v);
            if d>maxd:
                maxd=d
                index=mi
            mi +=1
        res.append(cands[index][0]) 
        #print index,"\n"
    titles = ids2title(res)
    return res, titles

                                   
def contextdisamb_2(candslist, direction=DIR_OUT):
    cframelist=[]
    cveclist_bdrs = []
    for cands in candslist:
        cands_rep = [conceptrep(c[0], direction=direction, get_titles=False) for c in cands]
        cveclist_bdrs += [(len(cframelist), len(cframelist)+len(cands_rep))]
        cframelist += cands_rep

    #print "ambig_count:", ambig_count
    cvec_fr = pd.concat(cframelist, join='outer', axis=1)
    cvec_fr.fillna(0, inplace=True)
    cvec_arr = cvec_fr.as_matrix().T
    i=0
    for cframe in cframelist:
        if cframe.empty:
            cvec_arr = np.insert(cvec_arr,i,0, axis=0)
        i+=1    
    
    aggr_cveclist = np.zeros(shape=(len(candslist),cvec_arr.shape[1]))
    for i in range(len(cveclist_bdrs)):
        b,e = cveclist_bdrs[i]
        aggr_cveclist[i]=cvec_arr[b:e].sum(axis=0)
    
    res=[]
    for i in range(len(candslist)):
        cands = candslist[i]
        b,e = cveclist_bdrs[i]
        cvec = cvec_arr[b:e]
        convec=aggr_cveclist[:i].sum(axis=0) + aggr_cveclist[i+1:].sum(axis=0)

        maxd=-1
        index = -1
        mi=0

        for v in cvec:
            d = 1-sp.spatial.distance.cosine(convec, v);
            if d>maxd:
                maxd=d
                index=mi
            mi +=1
        if index==-1:
            index=0
        res.append(cands[index][0]) 
        b,e = cveclist_bdrs[i]
        cveclist_bdrs[i] = (b+index,b+index+1)
        
        aggr_cveclist[i] =  cvec_arr[b:e][index]
        
        candslist[i] = candslist[i][index][0]
        
        

    titles = ids2title(res)

    return res, titles

def contextdisamb_3(candslist, direction=DIR_OUT):
    cframelist=[]
    cveclist_bdrs = []
    ambig_count=0
    for cands in candslist:
        if len(candslist)>1:
            ambig_count += 1
        cands_rep = [conceptrep(c[0], direction=direction, get_titles=False) for c in cands]
        cveclist_bdrs += [(len(cframelist), len(cframelist)+len(cands_rep))]
        cframelist += cands_rep

    #print "ambig_count:", ambig_count
        
    cvec_fr = pd.concat(cframelist, join='outer', axis=1)
    cvec_fr.fillna(0, inplace=True)
    cvec_arr = cvec_fr.as_matrix().T
    i=0
    for cframe in cframelist:
        if cframe.empty:
            cvec_arr = np.insert(cvec_arr,i,0, axis=0)
        i+=1    
    
    aggr_cveclist = np.zeros(shape=(len(candslist),cvec_arr.shape[1]))
    for i in range(len(cveclist_bdrs)):
        b,e = cveclist_bdrs[i]
        aggr_cveclist[i]=cvec_arr[b:e].sum(axis=0)
    from itertools import izip
    resolved = 0
    for resolved in range(ambig_count):
        cands_score_list=[]        
        for i in range(len(candslist)):
            cands = candslist[i]
            b,e = cveclist_bdrs[i]
            cvec = cvec_arr[b:e]
            convec=aggr_cveclist[:i].sum(axis=0) + aggr_cveclist[i+1:].sum(axis=0)
            D=[]    
            for v in cvec:
                d = 1-sp.spatial.distance.cosine(convec, v);
                if np.isnan(d):
                    d=0
                D.append(d)
            D=sorted(enumerate(D), key=lambda x: -x[1])
            cands_score_list.append(D)

        max_concept, _ = max(enumerate(cands_score_list), key=lambda x: (x[1][0][1]-x[1][1][1]) if len(x[1])>1 else -1)
        max_candidate = cands_score_list[max_concept][0][0]
        
        b,e = cveclist_bdrs[max_concept]
        cveclist_bdrs[max_concept] = (b+max_concept,b+max_concept+1)
        aggr_cveclist[max_concept] =  cvec_arr[b:e][max_candidate]
        
        candslist[max_concept] = [candslist[max_concept][max_candidate]]
                                  
        #cframelist[max_index] =  [cframelist[max_index][cands_score_list[max_index][0][0]]]
        #break
            #print index,"\n"
    res = [c[0][0] for c in candslist]
    titles = ids2title(res)

    return res, titles        
    
    
#########################
# KeyBased Method
#########################

def coherence_scores_driver(C, ws, method='rvspagerank', direction=DIR_BOTH, op_method="keydisamb"):
    """ Assigns a score to every candidate 
        Inputs:
            C: Candidate list [[(c11, p11),...(c1k, p1k)],...[(cn1, pn1),...(c1m, p1m)]]
            ws: Windows size for chunking
            method: similarity method
            direction: embedding type
            op_method: disambiguation method, either keyentity or entitycontext
            
        
    """
    
    windows = [[start, min(start+ws, len(C))] for start in range(0,len(C),ws) ]
    last = len(windows)
    if last > 1 and windows[last-1][1]-windows[last-1][0]<2:
        windows[last-2][1] = len(C)
        windows.pop()
    scores=[]    
    for w in windows:
        chunk_c = C[w[0]:w[1]]
        if op_method == 'keydisamb':
            scores += keyentity_candidate_scores(chunk_c, direction, method,4)
            
        if op_method == 'entitycontext':
            _, _, candslist_scores = entity_to_context_scores(chunk_c, direction, method);
            scores += candslist_scores
    return scores

def get_candidate_representations(candslist, direction, method):
    '''returns an array of vector representations. 
       Inputs: 
           candslist: candidate list [[(c11, p11),...(c1k, p1k)],...[(cn1, pn1),...(c1m, p1m)]]
           direction: embedding direction
           method: similarity method
      Outputs
           cvec_arr: Candidate embeddings, a two dimensional array, each column 
                   is the representation of a candidate
           cveclist_bdrs: a list of pairs (beginning, end), to indicate where 
                   the embeddings for a concepts indicates start and end. In other words
                   The embedding of candidates [ci1...cik] in candslist is
                   cvec_arr[cveclist_bdrs[i][0]:cveclist_bdrs[i][1]] 
    '''
    
    cframelist=[]
    cveclist_bdrs = []
    ambig_count=0
    for cands in candslist:
        if len(candslist)>1:
            ambig_count += 1
        cands_rep = [conceptrep(encode_entity(c[0], method, get_id=False), method=method, direction=direction, get_titles=False) for c in cands]
        cveclist_bdrs += [(len(cframelist), len(cframelist)+len(cands_rep))]
        cframelist += cands_rep

    #print "ambig_count:", ambig_count
        
    cvec_fr = pd.concat(cframelist, join='outer', axis=1)
    cvec_fr.fillna(0, inplace=True)
    cvec_arr = cvec_fr.as_matrix().T
    i=0
    for cframe in cframelist:
        if cframe.empty:
            cvec_arr = np.insert(cvec_arr,i,0, axis=0)
        i+=1    
    return cvec_arr, cveclist_bdrs

def entity_to_context_scores(candslist, direction, method):
    ''' finds the similarity between each entity and its context representation
        Inputs:
            candslist: the list of candidates [[(c11, p11),...(c1k, p1k)],...[(cn1, pn1),...(c1m, p1m)]]
            cvec_arr: the array of all embeddings for the candidates
            cveclist_bdrs: The embedding vector for each candidate: [[c11,...c1k],...[cn1,...c1m]]
        Returns:
           cvec_arr: Candidate embeddings, a two dimensional array, each column 
           cveclist_bdrs: a list of pairs (beginning, end), to indicate where the 
                   reperesentation of the candidates for cij reside        
           cands_score_list: scroes in the form of [[s11,...s1k],...[sn1,...s1m]]
                    where sij  is the similarity of c[i,j] to to ci-th context
                    
            '''
    cvec_arr, cveclist_bdrs =  get_candidate_representations(candslist, direction, method)    
    
    aggr_cveclist = np.zeros(shape=(len(candslist),cvec_arr.shape[1]))
    for i in range(len(cveclist_bdrs)):
        b,e = cveclist_bdrs[i]
        aggr_cveclist[i]=cvec_arr[b:e].sum(axis=0)
    
    from itertools import izip
    resolved = 0
    cands_score_list=[]        
    for i in range(len(candslist)):
        cands = candslist[i]
        b,e = cveclist_bdrs[i]
        cvec = cvec_arr[b:e]
        convec=aggr_cveclist[:i].sum(axis=0) + aggr_cveclist[i+1:].sum(axis=0)
        S=[]    
        for v in cvec:
            try:
                s = 1-sp.spatial.distance.cosine(convec, v);
            except:
                s=0                
            if np.isnan(s):
                s=0
            S.append(s)
        cands_score_list.append(S)

    return cvec_arr, cveclist_bdrs, cands_score_list

def entity_context_disambiguate(candslist, direction=DIR_OUT, method='rvspagerank'):
    '''Disambiguate a sentence using entity-context method
       Inputs: 
           candslist: candidate list [[(c11, p11),...(c1k, p1k)],...[(cn1, pn1),...(c1m, p1m)]]
           direction: embedding direction
           method: similarity method
       Returns: 
           a list of entity ids and a list of titles
    '''
    
        
    _, _, candslist_scores = entity_to_context_scores(candslist, direction, method);
    # Iterate 
    true_entities = []
    for cands, cands_scores in zip(candslist, candslist_scores):
        max_index, max_value = max(enumerate(cands_scores), key= lambda x:x[1])
        true_entities.append(cands[max_index][0])

    titles = ids2title(true_entities)
    return true_entities, titles        

def key_criteria(cands_score):
    ''' helper function for find_key_concept: returns a score indicating how good a key is x
        Input:
            scroes for candidates [ci1, ..., cik] in the form of (i, [(ri1, si1), ..., (rik, sik)] ) 
            where (rij,sij) indicates that sij is the similarity of c[i][rij] to to cith context
            
    '''
    if len(cands_score[1])==0:
        return -float("inf")    
    if len(cands_score[1])==1 or cands_score[1][1][1]==0:
        return float("inf")
    
    return (cands_score[1][0][1]-cands_score[1][1][1]) / cands_score[1][1][1]

def find_key_concept(candslist, direction, method, ver=4):
    ''' finds the key entity in the candidate list
        Inputs:
            candslist: the list of candidates [[(c11, p11),...(c1k, p1k)],...[(cn1, pn1),...(c1m, p1m)]]
            cvec_arr: the array of all embeddings for the candidates
            cveclist_bdrs: The embedding vector for each candidate: [[c11,...c1k],...[cn1,...c1m]]
        Returns:
            cvec_arr: Candidate embeddings, a two dimensional array, each column 
            cveclist_bdrs: a list of pairs (beginning, end), to indicate where the 
            key_concept: the concept forwhich one of the candidates is the key entity
            key_entity: candidate index for key_cancept that is detected to be key_entity
            key_entity_vector: The embedding of key entity
            '''
    cvec_arr, cveclist_bdrs, cands_score_list = entity_to_context_scores(candslist, direction, method);
    S=[sorted(enumerate(S), key=lambda x: -x[1]) for S in cands_score_list]
        
    if ver ==1: 
        key_concept, _ = max(enumerate(S), key=lambda x: x[1][0][1] if len(x[1])>1 else -1)
    elif ver ==2: 
        key_concept, _ = max(enumerate(S), key=lambda x: (x[1][0][1]-x[1][1][1]) if len(x[1])>1 else -1)
    elif ver ==3: 
        key_concept, _ = max(enumerate(S), key=lambda x: (x[1][0][1]-x[1][1][1])/(x[1][0][1]+x[1][1][1]) if len(x[1])>1 else -1)
    elif ver ==4: 
        key_concept, _ = max(enumerate(S), key=key_criteria)
    key_entity = S[key_concept][0][0]
    
    b,e = cveclist_bdrs[key_concept]
    
    key_entity_vector =  cvec_arr[b:e][key_entity]    
    return cvec_arr, cveclist_bdrs, key_concept, key_entity, key_entity_vector


def keyentity_candidate_scores(candslist, direction, method, ver):
    '''returns entity scores using key-entity scoring 
       Inputs: 
           candslist: candidate list [[(c11, p11),...(c1k, p1k)],...[(cn1, pn1),...(c1m, p1m)]]
           direction: embedding direction
           method: similarity method
           ver: 1 for the method explained in the paper
           
       Returns:
           Scores [[s11,...s1k],...[sn1,...s1m]] where sij is cij similarity to the key-entity
    '''
    
        
    cvec_arr, cveclist_bdrs, key_concept, key_entity, key_entity_vector = find_key_concept(candslist, direction, method, ver)
    
    # Iterate 
    candslist_scores=[]
    for i in range(len(candslist)):
        cands = candslist[i]
        b,e = cveclist_bdrs[i]
        cvec = cvec_arr[b:e]
        cand_scores=[]

        for v in cvec:
            try:
                d = 1-sp.spatial.distance.cosine(key_entity_vector, v);
            except:
                d=0                
            if np.isnan(d):
                d=0
            
            cand_scores.append(d)    
        candslist_scores.append(cand_scores) 
    return candslist_scores

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

## Plain context with word2vec

def word_context_candidate_scores (S, M, candslist, ws):
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


        
        
def word_context_disambiguate(S, M, candslist, ws ):
    '''Disambiguate a sentence using word-context similarity
       Inputs: 
           S: Sentence
           M: Mentions
           candslist: candidate list [[(c11, p11),...(c1k, p1k)],...[(cn1, pn1),...(c1m, p1m)]]
           
       Returns: 
           a list of entity ids and a list of titles
    '''
    
        
    candslist_scores = word_context_candidate_scores (S, M, candslist, ws)
                      
    # Iterate 
    true_entities = []
    for cands, cands_scores in zip(candslist, candslist_scores):
        max_index, max_value = max(enumerate(cands_scores), key= lambda x:x[1])
        true_entities.append(cands[max_index][0])

    titles = ids2title(true_entities)
    return true_entities, titles     
######
def get_sim_matrix(candslist,method, direction):
    concepts=  list(chain(*candslist))
    concepts=  list(set(c[0] for c in concepts))
    sims = pd.DataFrame(index=concepts, columns=concepts)
    for cands1,cands2 in combinations(candslist,2):
        for c1,c2 in product(cands1,cands2):
            sims[c1[0]][c2[0]]= sims[c2[0]][c1[0]] = getsim(c1[0],c2[0] , method, direction)
    return sims        

def tagme_vote(c, a, candslist, simmatrix, pop):
    v = 0
    for b in  range(len(candslist)):
        if a==b:
            continue
        cands = candslist[b]
        if pop:
            vb = [ci[1]*simmatrix[c[0]][ci[0]] for ci in cands]
        else:
            vb = [simmatrix[c[0]][ci[0]]  for ci in cands]
        vb = sum(vb) / len(vb)
        v += vb    
    return v

def tagme(candslist, method, direction, pop=False):
    res=[]
    simmatrix = get_sim_matrix(candslist, method, direction)
    for i in range(len(candslist)):
        cands = candslist[i]
        
        maxd=-1
        mi=0
        #print len(cands)
        for c in cands:
            d = tagme_vote(c, i, candslist , simmatrix, pop);
            if d>maxd:
                maxd=d
                index=mi
            mi +=1
        res.append(cands[index][0]) 
        #print index,"\n"
    titles = ids2title(res)
    return res, titles


    