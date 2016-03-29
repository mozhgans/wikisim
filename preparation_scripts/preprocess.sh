#Automatic constructing databases, 

#input: $1 mysql user, $2: mysql password

# Download wikipedia dumps to ~/Downloads/wikidumps, make sure it exists
bash download.sh

# Decompress the dumps
bash decompress.sh

# Parsing the dumps
bash parsdumps.sh

# Setting up mysql variables
bash setupmysql.sh $1 $2

# Start importing
bash startimport.sh $1 $2

