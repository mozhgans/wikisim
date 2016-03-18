
# A General Class to interact with Wiki datasets
import MySQLdb
import sys;
import os
import scipy as sp
import json
from json import encoder

from utils import *

encoder.FLOAT_REPR = lambda o: format(o, '.2f')

DIR_IN=0;
DIR_OUT=1;
DIR_BOTH=2;
_db = MySQLdb.connect(host="127.0.0.1",port=3306,user='root',passwd="emilios",db="enwiki20140102")
_cursor = _db.cursor()

def close():
    _cursor.close();
    _db.close();

def id2title(wid):
    """ Returns the title for a given id

    Args: 
        wid: Wikipedia id       
    Returns: 
        The title of the page
    """

    _cursor.execute("""SELECT * FROM `page` where page_id = %s""", (wid,))
    r= _cursor.fetchone();
#         title=None;
#         if r is not None:
#             title = getredir_title(id) if r[3] else r[2];           
    return r[2];

def ids2title(wids):
    """ Returns the titles for given list of wikipedia ids 

    Args: 
        wids: A list of Wikipedia ids          
    Returns: 
        The list of titles
    """

    wid_list = [str(wid) for wid in wids] ;
    order = ','.join(['page_id'] + wid_list) ;
    wid_str = ",".join(wid_list)
    query = "SELECT page_title FROM `page` where page_id in ({0}) order by field ({1})" \
    .format(wid_str, order);
    _cursor.execute(query);
    rows = _cursor.fetchall();
    rows = tuple(r[0] for r in rows)
    return rows;


def title2id(title):
    """ Returns the id for a given title

    Args: 
        wid: Wikipedia id          
    Returns: 
        The title of the page
    """        
    _cursor.execute("""SELECT * FROM `page` where page_title=%s and page_namespace=0""", (title,))
    r= _cursor.fetchone();
    wid=None;
    if r is not None:
        wid = getredir_id(r[0]) if r[3] else r[0];
    return wid;

def getredir_id(wid):
    """ Returns the target of a redirected page 

    Args:
        wid: wikipedia id of the page
    Returns:
        The id of the target page
    """
    _cursor.execute("""select * from redirect where rd_from=%s;""", (wid,));
    wid=None
    r= _cursor.fetchone();
    if r is not None:
        wid=r[1]
    return wid 


def getredir_title(wid):
    """ Returns the target title of a redirected page 

    Args:
        wid: wikipedia id of the page
    Returns:
        The title of the target page
    """
    _cursor.execute(""" select page_title from redirect INNER JOIN page
                  on redirect.rd_to = page.page_id 
                  where redirect.rd_from =%s;""", (wid));
    return _cursor.fetchone()[0];

def synonymring_titles(wid):
    """ Returns the synonim ring of a page

    Example: synonymring_titles('USA')={('U.S.A', 'US', 'United_States_of_America', ...)}

    Args:
        wid: the wikipedia id
    Returns:
        all the titles in its synonym ring
    """

    tid = getredir_id(wid);
    if tid is not None:
        wid = tid;
    _cursor.execute("""(select page_title from page where page_id=%s) union 
                 (select page_title from redirect INNER JOIN page
                    on redirect.rd_from = page.page_id 
                    where redirect.rd_to =%s);""", (wid,wid));
    rows=_cursor.fetchall();
    rows = tuple(r[0] for r in rows)
    return rows;

def _getlinkedpages_query(id, direction):
    query="(SELECT {0} as lid FROM pagelinks where ({1} = {2}))"
    if direction == DIR_IN:
        query=query.format("pl_from","pl_to",id);
    elif direction == DIR_OUT:
        query=query.format("pl_to","pl_from",id);
    return query;

def getlinkedpages(wid,direction):
    """ Returns the linkage for a node

    Args:
        id: the wikipedia id
        direction: 0 for in, 1 for out, 2 for all
    Returns:
        The list of the ids of the linked pages
    """
    _cursor.execute(_getlinkedpages_query(wid, direction));
    rows =_cursor.fetchall()
    rows = tuple(r[0] for r in rows)
    return rows

def e2i(wids):
    elist=[];
    edict=dict();
    last=0;    
    for wid in itertools.chain(*iters):
        if wid not in edict:
            edict[wid]=last;
            elist.append(wid);
            last +=1; 
    return elist, edict;

def getneighbors(wid, direction):
    """ Returns the neighborhood for a node

    Args:
        id: the wikipedia id
        direction: 0 for in, 1 for out, 2 for all
    Returns:
        The vector of ids, and the 2d array sparse representation of the graph, in the form of
        array([[row1,col1],[row2, col2]]). This form is flexible for general use or be converted to scipy.sparse 
        formats
    """
    log('getneighbors started')
    idsquery = """(select  {0} as lid) union {1}""".format(wid,_getlinkedpages_query(wid,direction));

    _cursor.execute(idsquery);
    sys.stdout.flush()

    neighids = tuple(r[0] for r in _cursor.fetchall());
    
    id2row = dict(zip(neighids, range(len(neighids))))
    sys.stdout.flush()

    neighbquery=  """select lid,pl_to as n_l_to from
                     ({0}) a  inner join
                     pagelinks on lid=pl_from""".format(idsquery);

    links=_cursor.execute(neighbquery);
    sys.stdout.flush()

    links = _cursor.fetchall();

    #print links
    #links = tuple((id2row(u), id2row(v)) for u, v in links if (u in id2row) and (v in id2row));
    links = sp.array([[id2row[u], id2row[v]] for u, v in links if (u in id2row) and (v in id2row)]);
    #print "5:" + str(timeformat(int(time.time()-start)));
    sys.stdout.flush()
    log('finished')
    return (neighids,links)

def clearcache():
    _cursor.execute("delete  from pagelinksorderedin");
    _cursor.execute("delete  from pagelinksorderedout");

def _checkcache(wid, direction):
    log('_checkcache started')
    if direction == DIR_IN: 
        tablename = 'pagelinksorderedin';
        colname = 'in_neighb'
    elif direction == DIR_OUT: 
        tablename = 'pagelinksorderedout';
        colname = 'out_neighb';
    query =    """select {0} from {1} where cache_id={2}""".format(colname, tablename, wid)
    _cursor.execute(query);
    log('finished')
    row = _cursor.fetchall();
    if row is None:
        return None
    row=row[0]
    row = str.split(row,',')
    ids_str=row[0]
    ids = idstr.split('\t')
    ids = [int(wdi) for wid in ids];

    scs_str=row[1]        
    scs = scs_str.split('\t')
    scs = [float(sc) for sc in scs];

    return ids, scs


def _cachescores(ids, scs, direction):
    log('_cachescores started')

    id_str=[str(wid) for wid in ids]
    scs_str=["{:.4f}".format(s) for i in scs]
    idscstr="\t".join(id_str) + ','+"\t".join(scs_str);
    if direction == DIR_IN: 
        tablename = pagelinksorderedin;
        colname = 'in_neighb'

    elif direction == DIR_OUT: 
        tablename = pagelinksorderedout;
        colname = 'out_neighb';
    _cursor.execute(""" insert into %s values (%s,%s);""", (tablename, id, idscstr));
    log('finished')