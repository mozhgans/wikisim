#%%system

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