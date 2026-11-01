import argparse,json
from pathlib import Path
import numpy as np
import pandas as pd
from statsmodels.stats.multitest import multipletests
p=argparse.ArgumentParser();p.add_argument("--package",type=Path,required=True);a=p.parse_args()
files=sorted((a.package/"02_Results"/"all_tests_by_band").glob("*.csv.gz"));assert len(files)==11
frames=[pd.read_csv(f,float_precision="round_trip") for f in files]
report={}
for prefix,model,expected in [("m1","Model1",86),("int","Model2",34)]:
 raw=np.concatenate([d["p_"+prefix].to_numpy() for d in frames]);saved=np.concatenate([d["q_"+prefix].to_numpy() for d in frames])
 assert len(raw)==212509 and np.isfinite(raw).all()
 corrected=multipletests(raw,alpha=.05,method="fdr_bh")[1]
 assert np.allclose(saved,corrected,rtol=1e-10,atol=1e-12)
 assert np.array_equal(saved<.05,corrected<.05) and int((corrected<.05).sum())==expected
 report[model]={"tests":len(raw),"significant_records":expected,"max_absolute_BH_difference":float(np.max(abs(saved-corrected)))}
for d in frames:
 for group in ["hc","mdd"]:
  q=multipletests(d["p_"+group].to_numpy(),method="fdr_bh")[1]
  assert np.allclose(q,d["q_"+group+"_within_band"],rtol=1e-10,atol=1e-12)
print(json.dumps(report,indent=2))
