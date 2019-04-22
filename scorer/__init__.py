import base64
import hashlib
import os
import os.path
import pandas
import time
import pkg_resources
import lifelines


# Median center rows,
# then divide rows by their stdDev
def center_scale_row(df):
  df = df.sub(df.mean(axis=1), axis=0)
  df = df.div(df.std(axis=1), axis=0)
  return df
  
class Scorer:
  classnum = {'A':4, 'B':5, 'C':6}
  def __init__(self):
    #self.first_set  = pandas.read_pickle("first_set.pickle")
    data1 = pkg_resources.resource_stream(__name__, "/first_set.pickle")
    data2 = pkg_resources.resource_stream(__name__, "/second_set.pickle")
    self.first_set = pandas.read_pickle(data1, compression="gzip")
    self.second_set = pandas.read_pickle(data2, compression="gzip")
  
  def load_data(self, exprfile, center=False):
    self.expr = pandas.read_csv(exprfile, sep="\t", index_col=0)
    probes1_ok = all(self.first_set.index.isin(self.expr.index))
    probes2_ok = all(self.second_set.index.isin(self.expr.index))
    if center:
      self.expr = center_scale_row(self.expr)
    
    if not all([probes1_ok, probes2_ok]):
      return (False, "One or more of the scoring genes are missing from the expression file")
    # This would be a sensible time to check for NAs
    return (True, "")
  
  def load_surv(self, survfile, clusterfile):
    try:
      self.surv = pandas.read_csv(survfile, sep="\t", index_col=0).iloc[:, 0:2]
      self.surv.columns = ['followup', 'event']
      self.results = pandas.read_csv(clusterfile, sep="\t", index_col=0)
      return (True, "")
    except e:
      return (False, str(e))
  
  def score(self, keep_junk=False):
    expr1   = self.expr.loc[self.first_set.index]
    scores1 = expr1.mul(self.first_set, axis=0).sum(axis=0)
    is_ac    = scores1 < 1.20653865666178

    expr2   = self.expr.loc[self.second_set.index,  is_ac]
    scores2 = expr2.mul(self.second_set, axis=0).sum(axis=0)
    is_a    = scores2 < 0.993071948779753
    
    results = pandas.DataFrame({'is_ac':is_ac, 'is_a':False, 'Class':'C'})
    results.is_a = results.index.isin( is_a[is_a].index )
    results.loc[results.is_a, "Class"]   = 'A'
    results.loc[~results.is_ac, "Class"] = 'B'

    # Translate classnames to class numbers
    results = results.assign(Classnum = [self.classnum[x] for x in results.Class] )
    if not keep_junk:
      results = results.loc[:, ["Class", "Classnum"]]
    self.results = results
  
  def get_results(self):
    return self.results
  
  def save(self, outdir):
    md5 = hashlib.new("md5")
    md5.update("".join(self.expr.columns).encode("utf-8"))
    md5 = base64.b32encode( md5.digest() ).decode("ascii")[0:5]
    filename = time.strftime("%Y-%m-%d-%H-%M-") + md5 + ".csv"
    outfile = os.path.join(outdir, filename)
    self.results.to_csv(outfile, sep="\t", index_label="Sample")
    return outfile

  def score_surv(self, plotfile, textfile):
    import matplotlib.pyplot as plt
    both = self.results.merge(self.surv, left_index=True, right_index=True)
    
    # Plot
    ax = plt.subplot(111)
    kmf = lifelines.KaplanMeierFitter()
    for group, grouped in both.groupby("Class"):
      kmf.fit(grouped["followup"], grouped["event"], label=group)
      kmf.plot(ax=ax)
    plt.savefig(plotfile)
    
    # Text
    both = both.iloc[:, [0,2,3] ]
    mlt = lifelines.statistics.multivariate_logrank_test(both.followup, both.Class, both.event)
    plt = lifelines.statistics.pairwise_logrank_test(both.followup, both.Class, both.event)
    
    multi_res     = mlt._to_string().split("\n")
    pairwise_res  = plt._to_string().split("\n")
    multi_res[0] = "Multivariate logrank test:"
    pairwise_res[0] = "Pairwise logrank test:"
    res = "\n".join(multi_res) + "\n\n###\n\n"+"\n".join(pairwise_res)
    with open(textfile, "w") as f:
      f.write(res)
