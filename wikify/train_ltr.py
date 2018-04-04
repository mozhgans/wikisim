
import pyltr
import pandas as pd
import os
from wikify import *

outdir = os.path.join(baseresdir, 'wikify')
tr_file_name = os.path.join(home,'backup/datasets/ner/trainrepository.30000.5000.tsv')
data=pd.read_table(tr_file_name, header=None)
#data=data.head(100)

grouped=data.groupby(1)
total_len=len(grouped)
group = grouped.filter(lambda x:x.iloc[0,1] >= 0 and x.iloc[0,1] < 0.6*total_len)
TrX = group.iloc[:,2:7].as_matrix()
TrY = group.iloc[:,7].as_matrix()
Trqid = group.iloc[:,1].as_matrix()

group=grouped.filter(lambda x:x.iloc[0,1] >= 0.6*total_len and x.iloc[0,1] < 0.8*total_len)
VaX = group.iloc[:,2:7].as_matrix()
VaY = group.iloc[:,7].as_matrix()
Vaqid = group.iloc[:,1].as_matrix()


group=grouped.filter(lambda x:x.iloc[0,1] >= 0.8*total_len and x.iloc[0,1] < 1.0*total_len)
TsX = group.iloc[:,2:7].as_matrix()
TsY = group.iloc[:,7].as_matrix()
Tsqid = group.iloc[:,1].as_matrix()

monitor = pyltr.models.monitors.ValidationMonitor(
     VaX, VaY, Vaqid, metric=pyltr.metrics.NDCG(k=10), stop_after=250)
model = pyltr.models.LambdaMART(n_estimators=300, learning_rate=0.1, verbose = 0)
#lmart.fit(TX, TY, Tqid, monitor=monitor)
model.fit(TrX, TrY, Trqid, monitor=monitor)

metric = pyltr.metrics.NDCG(k=10)
Ts_pred = model.predict(TsX)
print 'Random ranking:', metric.calc_mean_random(Tsqid, TsY)
print 'Our model:', metric.calc_mean(Tsqid, TsY, Ts_pred)

import cPickle as pickle
model_file_name = os.path.join(home,'backup/datasets/ner/ltr.pkl')

pickle.dump(model, open(model_file_name, 'wb'))

print 'Model saved'