#!/users/grad/sajadi/backup/anaconda2/envs/wikisim/bin/python
#!/home/sajadi/anaconda2/bin/python

import json
import cgi, cgitb 

import sys

sys.path.insert(0,'..')
from wikify.wikify import *

log('cgi-wikify started');

# Import modules for CGI handling 

# Create instance of FieldStorage 
form = cgi.FieldStorage() 

# Get data from fields
mentionmethod=int(form.getvalue('mentionmethod'))
wikitext  = form.getvalue('wikitext')

print "Content-type:application/json\r\n\r\n"

wikifiedtext = wikify_api(wikitext, mentionmethod=mentionmethod)


print json.dumps({"outtext":wikifiedtext})

#close()

log('finished');
