import base64
import hashlib
import os
import os.path
import pandas
import time
import pkg_resources

# Median center rows,
# then divide rows by their stdDev
def center_scale_row(df):
  df = df.sub(df.median(axis=1), axis=0)
  df = df.div(df.std(axis=1), axis=0)
  return df
  
class Scorer:
  classnum = {'A':4, 'B':5, 'C':6}
  def __init__(self):
    #self.first_set  = pandas.read_pickle("first_set.pickle")
    data2 = pkg_resources.resource_stream(__name__, "/first_set.pickle")
    data1 = pkg_resources.resource_stream(__name__, "/second_set.pickle")
    self.first_set = pandas.read_pickle(data1, compression="gzip")
    self.second_set = pandas.read_pickle(data2, compression="gzip")
  
  def load_data(self, exprfile):
    self.expr = pandas.read_csv(exprfile, sep="\t", index_col=0)
    probes1_ok = all(self.first_set.index.isin(self.expr.index))
    probes2_ok = all(self.second_set.index.isin(self.expr.index))
    self.expr = center_scale_row(self.expr)
    
    if not all([probes1_ok, probes2_ok]):
      return (False, "One or more of the scoring genes are missing from the expression file")
    # This would be a sensible time to check for NAs
    return (True, "")
  
  def score(self):
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

