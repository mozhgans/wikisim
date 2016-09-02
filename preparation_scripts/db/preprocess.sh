#Automatic constructing databases, 

# Usage:
# bash preprocess.sh <mysql user> <mysql password>

# Download wikipedia dumps to ~/Downloads/wikidumps, make sure it exists
bash download.sh

# Decompress the dumps
bash decompress.sh

# Parsing the dumps
bash parsdumps.sh

# Setting up mysql variables
bash setupmysql.sh $1 $2

# Start importing
mysql -u $1 -p$2 -e 'CREATE SCHEMA `enwikilast` DEFAULT CHARACTER SET binary;'
./importall  ~/Downloads/wikidumps last $1 $2

