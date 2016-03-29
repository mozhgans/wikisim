# uncomment

# A General Class to interact with Wiki datasets
import MySQLdb
import sys;
import os
import scipy as sp
from collections import defaultdict
import cPickle as pickle

from utils import * # uncomment


DIR_IN=0;
DIR_OUT=1;
DIR_BOTH=2;
_db = MySQLdb.connect(host="127.0.0.1",port=3306,user='root',passwd="emilios",db="enwiki20140102")
_cursor = _db.cursor()
WIKI_SIZE = 10216236;

def close():
    _cursor.close();
    _cursor=_db=None;
    _db.close();
def reopen():
    global _db, _cursor;
    if _db is None:
        _db = MySQLdb.connect(host="127.0.0.1",port=3306,user='root',passwd="emilios",db="enwiki20140102")
        _cursor = _db.cursor()
        

def id2title(wid):
    """ Returns the title for a given id

    Args: 
        wid: Wikipedia id       
    Returns: 
        The title of the page
    """
    title=None;

    _cursor.execute("""SELECT * FROM `page` where page_id = %s""", (wid,))
    row= _cursor.fetchone();
    if row is not None:
        title=row[2];          
    return title;

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
    if rows:
        rows = tuple(r[0] for r in rows)
    return rows;


def title2id(title):
    """ Returns the id for a given title

    Args: 
        wid: Wikipedia id          
    Returns: 
        The title of the page
    """        
    wid=None;

    _cursor.execute("""SELECT * FROM `page` where page_title=%s and page_namespace=0""", (title,))
    row= _cursor.fetchone();
    if row is not None:
        wid = getredir_id(row[0]) if row[3] else row[0];
    return wid;

def getredir_id(wid):
    """ Returns the target of a redirected page 

    Args:
        wid: wikipedia id of the page
    Returns:
        The id of the target page
    """
    rid=None

    _cursor.execute("""select * from redirect where rd_from=%s;""", (wid,));
    row= _cursor.fetchone();
    if row is not None:
        rid=row[1]
    return rid 


def getredir_title(wid):
    """ Returns the target title of a redirected page 

    Args:
        wid: wikipedia id of the page
    Returns:
        The title of the target page
    """
    
    title=None;
    _cursor.execute(""" select page_title from redirect INNER JOIN page
                  on redirect.rd_to = page.page_id 
                  where redirect.rd_from =%s;""", (wid));
    row=_cursor.fetchone()
    if row is not  None:
        title=row[0];
    return title;

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
    if rows:
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
    if rows:
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
    log('getneighbors started, wid = %s, direction = %s', wid, direction)
    if id2title(wid) is None:
        return (), sp.array([])
    
    idsquery = """(select  {0} as lid) union {1}""".format(wid,_getlinkedpages_query(wid,direction));

    _cursor.execute(idsquery);
    sys.stdout.flush()


    rows = _cursor.fetchall();
    neighids = tuple(r[0] for r in rows);
    
    id2row = dict(zip(neighids, range(len(neighids))))
    sys.stdout.flush()

    neighbquery=  """select lid,pl_to as n_l_to from
                     ({0}) a  inner join
                     pagelinks on lid=pl_from""".format(idsquery);

    links=_cursor.execute(neighbquery);
    sys.stdout.flush()

    links = _cursor.fetchall();
    
    #links = tuple((id2row(u), id2row(v)) for u, v in links if (u in id2row) and (v in id2row));
    links = sp.array([[id2row[u], id2row[v]] for u, v in links if (u in id2row) and (v in id2row)]);
    sys.stdout.flush()
    log('getneighbors finished')
    return (neighids,links)

def clearcache():
    _cursor.execute("delete  from pagelinksorderedin");
    _cursor.execute("delete  from pagelinksorderedout");

def checkcache(wid, direction):
    log('checkcache started, wid = %s, direction = %s', wid, direction)
    
    em=None
    
    if direction == DIR_IN: 
        tablename = 'pagelinksorderedin';
        colname = 'in_neighb'
    elif direction == DIR_OUT: 
        tablename = 'pagelinksorderedout';
        colname = 'out_neighb';
    query =    """select {0} from {1} where cache_id={2}""".format(colname, tablename, wid)
    _cursor.execute(query);
    row = _cursor.fetchone();
    if row is not None:
        em=defaultdict(int, pickle.loads(row[0]))
    log('checkcache finished')
    return em


def cachescores(wid, em, direction):
    log('cachescores started, wid = %s, direction = %s', wid, direction)

    if direction == DIR_IN: 
        tablename = 'pagelinksorderedin';
        colname = 'in_neighb'

    elif direction == DIR_OUT: 
        tablename = 'pagelinksorderedout';
        colname = 'out_neighb';
        
    idscstr=pickle.dumps(em, pickle.HIGHEST_PROTOCOL);
    _cursor.execute("""insert into %s values (%s,'%s');""" %(tablename, wid, _db.escape_string(idscstr)));
    
    
    log('cachescores finished')