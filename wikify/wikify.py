from __future__ import division
from mention_detection import *




def wikify_string(line, mentionmethod=CORE_NLP, max_t=20):
    S,M = detect_mentions(line, mentionmethod)      
    C = generate_candidates(S, M, max_t=max_t, enforce=False)
    E = wsd(S, M, C, method='learned')
    for m,e in zip(M,E[1]):
        m[1]=e
    return S,M

def wikify_a_line(line, mentionmethod=CORE_NLP):
    ''' Annotate a single line 
        Input:
            line: The given string
            mentionmethod: The mention detection method
        Output:
            Annotated Sentence inwhich mentiones are hyper-linked to the Wikipedia concepts
    '''
    S, M = wikify_string(line, mentionmethod=CORE_NLP) 
    for m in M: 
        S[m[0]]="<a href=https://en.wikipedia.org/wiki/%s>%s</a>"  % (S[m[0]],m[1])
    S_reconcat = " ".join(S)
    return S_reconcat
            
def wikify_api(text, mentionmethod=CORE_NLP):
    outlist=[]
    for line in text.splitlines():
        outlist.append(wikify_a_line(line, mentionmethod))
    return "\n".join(outlist).decode('utf-8')

def wikify_from_file_api(infilename, outfilename, mentionmethod=CORE_NLP):
    with open(infilename) as infile, open(outfilename, 'w') as outfile:
        for line in infilename.readlines():
            wikified = wikify_a_line(text, mentionmethod)
            outfile.write(wikified + "\n")

            