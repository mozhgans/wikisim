
#Downloading the datasets, it might take a while, and make sure the destination exists 
wget https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-page.sql.gz            \
	-P ~/Downloads/wikidumps
wget https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-pagelinks.sql.gz      \
	 -P ~/Downloads/wikidumps
wget https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-redirect.sql.gz       \
	 -P ~/Downloads/wikidumps
wget https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-category.sql.gz       \
	-P ~/Downloads/wikidumps
wget https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-categorylinks.sql.gz \
	-P ~/Downloads/wikidumps

gunzip -c ~/Downloads/wikidumps/enwiki-latest-page.sql.gz		\
		> ~/Downloads/wikidumps/enwiki-latest-page.sql 		
gunzip -c ~/Downloads/wikidumps/enwiki-latest-pagelinks.sql.gz 	\
		> ~/Downloads/wikidumps/enwiki-latest-pagelinks.sql	
gunzip -c ~/Downloads/wikidumps/enwiki-latest-redirect.sql.gz		\
		> ~/Downloads/wikidumps/enwiki-latest-redirect.sql	
gunzip -c ~/Downloads/wikidumps/enwiki-latest-category.sql.gz		\
		> ~/Downloads/wikidumps/enwiki-latest-category.sql	
gunzip -c ~/Downloads/wikidumps/enwiki-latest-categorylinks.sql.gz	\
		> ~/Downloads/wikidumps/enwiki-latest-categorylinks.sql	

java ProcessSQLDumps ~/Downloads/wikidumps

#mysql -u <u> -p<p> -e 'set global key_buffer_size=4*1024*1024*1024;'
#mysql -u <u> -p<p> -e 'set global bulk_insert_buffer_size=1024*1024*1024;'
#mysql -u <u> -p<p> -e 'set global query_cache_size = 4*1024*1024*1024;'
#mysql -u <u> -p<p> -e 'set global query_cache_limit = 4*1024*1024*1024;'
#mysql -u <u> -p<p> -e 'set global tmp_table_size = 4*1024*1024*1024;'

#mysql -u <u> -p<p> -e 'CREATE SCHEMA `enwikilast` DEFAULT CHARACTER SET binary;'
#./importall  ~/Downloads/wikidumps last <MYSQLROOTPASSWORD> 


