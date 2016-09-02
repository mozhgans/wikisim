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


def generate_candidates(S, M, max_t=10, enforce=True):
    candslist=[]
    for m in M:
        wid = title2id(m[1])
        if wid is None:
            raise Exception(m[1].encode('utf-8') + ' not found')
        
        clist = anchor2concept(S[m[0]])
        clist = sorted(clist, key=lambda x: -x[1])

        smooth=0    
        trg = [(i,(c,f)) for i,(c,f) in enumerate(clist) if c==wid]
        if not trg:
            trg=[(len(clist), (wid,0))]
            smooth=1

            
        clist = clist[:max_t]
        if smooth==1 or trg[0][0]>=max_t: 
            if clist:
                clist.pop()
            clist.append(trg[0][1])
        s = sum(c[1]+smooth for c in clist )        
        clist = [(c,float(f+smooth)/s) for c,f in clist ]
            
        candslist.append(clist)
    return  candslist 
def disambiguate(C, method, direction, op_method):
        
    if op_method == 'ilp':
        return disambiguate_ilp(C, method, direction)
    if op_method == 'ilp2':
        return disambiguate_ilp_2(C, method, direction)
    if  op_method == 'context1'  :
        return contextdisamb_1(C, direction)
    if  op_method == 'context2'  :
        return contextdisamb_2(C, direction)
    if  op_method == 'context3'  :
        return contextdisamb_3(C, direction)
    
    if  op_method == 'context4_1'  :
        return contextdisamb_4(C, direction, 1)
    if  op_method == 'context4_2'  :
        return contextdisamb_4(C, direction, 2)
    if  op_method == 'context4_3'  :
        return contextdisamb_4(C, direction, 3)
    
    if  op_method == 'context4_4'  :
        return contextdisamb_4(C, direction, 4)
    
    if  op_method == 'tagme'  :
        return tagme(C, method, direction)
    if  op_method == 'tagme2'  :
        return tagme(C, method, direction, True)
    
    return None



def disambiguate_driver(C, ws, method, direction, op_method):
    ids = []
    titles = []
    
    windows = [[start, min(start+ws, len(C))] for start in range(0,len(C),ws) ]
    last = len(windows)
    if last > 1 and windows[last-1][1]-windows[last-1][0]<2:
        windows[last-2][1] = len(C)
        windows.pop()
        
    for w in windows:
        chunk_c = C[w[0]:w[1]]
        chunk_ids, chunk_titles = disambiguate(chunk_c, method, direction, op_method)
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


# Integer Programming

from itertools import izip
from itertools import product
from pulp import *
import random

def getscore(x,y,method, direction):
    return getsim(x,y ,method, direction)
    #return random.random()

def disambiguate_ilp(C, method, direction):
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

# Context Vector

def contextdisamb_1(candslist, direction=DIR_OUT):
    cframelist=[]
    cveclist_bdrs = []
    for cands in candslist:
        cands_rep = [conceptrep(c[0], direction, get_titles=False) for c in cands]
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
        cands_rep = [conceptrep(c[0], direction, get_titles=False) for c in cands]
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
        cands_rep = [conceptrep(c[0], direction, get_titles=False) for c in cands]
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
        Dlist=[]        
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
            Dlist.append(D)

        max_concept, _ = max(enumerate(Dlist), key=lambda x: (x[1][0][1]-x[1][1][1]) if len(x[1])>1 else -1)
        max_candidate = Dlist[max_concept][0][0]
        
        b,e = cveclist_bdrs[max_concept]
        cveclist_bdrs[max_concept] = (b+max_concept,b+max_concept+1)
        aggr_cveclist[max_concept] =  cvec_arr[b:e][max_candidate]
        
        candslist[max_concept] = [candslist[max_concept][max_candidate]]
                                  
        #cframelist[max_index] =  [cframelist[max_index][Dlist[max_index][0][0]]]
        #break
            #print index,"\n"
    res = [c[0][0] for c in candslist]
    titles = ids2title(res)

    return res, titles        
    
    
######
def key_criteria(x):
    if len(x[1])==1 or x[1][1][1]==0:
        return float("inf")
    
    return (x[1][0][1]-x[1][1][1]) / x[1][1][1]

def find_key_concept(candslist, cveclist_bdrs, cvec_arr, ver):
    
    aggr_cveclist = np.zeros(shape=(len(candslist),cvec_arr.shape[1]))
    for i in range(len(cveclist_bdrs)):
        b,e = cveclist_bdrs[i]
        aggr_cveclist[i]=cvec_arr[b:e].sum(axis=0)
    
    from itertools import izip
    resolved = 0
    Dlist=[]        
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
        Dlist.append(D)

    if ver ==1: 
        max_concept, _ = max(enumerate(Dlist), key=lambda x: x[1][0][1] if len(x[1])>1 else -1)
    elif ver ==2: 
        max_concept, _ = max(enumerate(Dlist), key=lambda x: (x[1][0][1]-x[1][1][1]) if len(x[1])>1 else -1)
    elif ver ==3: 
        max_concept, _ = max(enumerate(Dlist), key=lambda x: (x[1][0][1]-x[1][1][1])/(x[1][0][1]+x[1][1][1]) if len(x[1])>1 else -1)
    elif ver ==4: 
        max_concept, _ = max(enumerate(Dlist), key=key_criteria)
    max_candidate = Dlist[max_concept][0][0]
    return max_concept, max_candidate


def contextdisamb_4(candslist, direction=DIR_OUT, ver=1):
    cframelist=[]
    cveclist_bdrs = []
    ambig_count=0
    for cands in candslist:
        if len(candslist)>1:
            ambig_count += 1
        cands_rep = [conceptrep(c[0], direction, get_titles=False) for c in cands]
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
    
        
    # find maximum ... 
        
    max_concept, max_candidate = find_key_concept(candslist, cveclist_bdrs, cvec_arr, ver)
    
    b,e = cveclist_bdrs[max_concept]
    
    convec =  cvec_arr[b:e][max_candidate]
        
    
    # Iterate 
    res=[]
    for i in range(len(candslist)):
        cands = candslist[i]
        b,e = cveclist_bdrs[i]
        cvec = cvec_arr[b:e]

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
        #print i, index, maxd    
        res.append(cands[index][0]) 
        b,e = cveclist_bdrs[i]
        cveclist_bdrs[i] = (b+index,b+index+1)
        
        #aggr_cveclist[i] =  cvec_arr[b:e][index]
        
        candslist[i] = candslist[i][index][0]
        
        

    titles = ids2title(res)

    return res, titles        

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


    