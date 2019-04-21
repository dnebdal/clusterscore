import pandas
import numpy

high_span  = 0.2
high_shift = 2
low_span   = 0.2
low_shift  = 0
N_each     = 30

surv_sd_frac = 0.2
A_median_surv = 12
B_median_surv = 24
C_median_surv = 36
A_event_frac  = 0.8
B_event_frac  = 0.5
C_event_frac  = 0.2

outfile      = "static/expression_example.txt"
outfile_surv = "static/survival_example.txt"

first_set  = pandas.read_pickle("scorer/first_set.pickle", compression="gzip")
second_set = pandas.read_pickle("scorer/second_set.pickle", compression="gzip")
# There is a small overlap between set1 and set2. Set2 is smaller, so it gets to keep them.
first_set = first_set[~first_set.index.isin(second_set.index)]

N1 = first_set.shape[0]
N2 = second_set.shape[0]
allgenes = list(first_set.index)
allgenes.extend(second_set.index)

def make_vals(setnr, high):
  x = {1:first_set, 2:second_set}[setnr]
  if not high:
    x = x * -1
  x += abs(min(x))
  x = 10*(x/max(x))
  x += numpy.random.standard_normal(x.shape[0])
  return(x)

def make_sample(group):
    if group=='b':
        # high first_set, ignores second_set
        res1 = make_vals(1, True)
        res2 = make_vals(2, False)
        return(numpy.append(res1,res2))
    if group=='a':
        # low first_set, low second_set
        res1 = make_vals(1, False)
        res2 = make_vals(2, False)
        return(numpy.append(res1,res2))
    if group=='c':
        # low first_set, high second_set
        res1 = make_vals(1, False)
        res2 = make_vals(2, True)
        return(numpy.append(res1,res2))
    return None

def make_surv(names, median, sd, event_frac):
    N = len(names)
    followup = median + sd*numpy.random.standard_normal(N)
    event = numpy.random.choice(a=[0,1], size=N, p=[1-event_frac, event_frac], replace=True)
    return pandas.DataFrame({'sampleid':names, 'followup':followup, 'event':event})

# Gene expression
res = pandas.DataFrame(index=allgenes)
for group in ('a', 'b', 'c'):
    for i in range(N_each):
      sampleid = "sample%02d_%s" % (i+1,group)
      col = dict( ((sampleid, make_sample(group)), ))
      res = res.assign(**col)

res.to_csv(outfile, sep="\t", index_label = "genes", float_format="%.3f")

# Survival data
a = make_surv(
    names = ["sample%02d_%s" % (i+1,'a') for i in range(N_each)],
    median = A_median_surv, 
    sd = A_median_surv * surv_sd_frac,
    event_frac = A_event_frac)
b = make_surv(
    names = ["sample%02d_%s" % (i+1,'b') for i in range(N_each)],
    median = B_median_surv, 
    sd = B_median_surv * surv_sd_frac,
    event_frac = B_event_frac)
c = make_surv(
    names = ["sample%02d_%s" % (i+1,'c') for i in range(N_each)],
    median = C_median_surv, 
    sd = C_median_surv * surv_sd_frac,
    event_frac = C_event_frac)

surv = a.append(b).append(c)
surv.to_csv(outfile_surv, sep="\t", index=False, float_format="%.3f")
