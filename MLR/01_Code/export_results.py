"""Export library-fitted MLR results using the established atlas-labeling workflow."""
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
import reused_annotation as annotation


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--package", type=Path, required=True)
    p.add_argument("--model-results", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args(); args.output.mkdir(parents=True, exist_ok=True)
    r = np.load(args.model_results)
    reference = pd.read_csv(args.package / "02_Results/SC_retained_edge_index.csv")
    assert np.array_equal(r["original_edges"], reference.original_edge)
    annotation.INPUT = args.package / "01_Code/atlas_reference"
    mapping, hierarchy = annotation.validate_mapping()
    bands = [f"{v}_{v+25}mg" for v in range(125,400,25)]
    for model, prefix, target in [("Model1","m1","PA"),("Model2","int","Int")]:
        rows = []
        for b, band in enumerate(bands):
            for e in np.flatnonzero(r["q_"+prefix][b] < .05):
                item = reference.iloc[e]
                row = {"Model": model, "PA_variable": band, "edge": int(item.original_edge),
                       "analysis_edge": int(item.analysis_edge), "ROI_i": int(item.ROI_i), "ROI_j": int(item.ROI_j),
                       "p_raw": r["p_"+prefix][b,e], "p_FDR_global_11bands": r["q_"+prefix][b,e],
                       "CI95_low": r["lo_"+prefix][b,e], "CI95_high": r["hi_"+prefix][b,e],
                       "beta_"+target: r["beta_"+prefix][b,e], "se_"+target: r["se_"+prefix][b,e],
                       "t_"+target: r["t_"+prefix][b,e], "direction": "Positive" if r["beta_"+prefix][b,e] > 0 else "Negative"}
                if model == "Model2":
                    row["beta_Group"] = r["beta_group"][b,e]
                    row["p_Group_raw"] = r["p_group"][b,e]
                    for group, label in [("hc","HC"),("mdd","MDD")]:
                        row.update({f"beta_PA_{label}":r[f"beta_{group}"][b,e], f"se_PA_{label}":r[f"se_{group}"][b,e],
                                    f"CI95_low_{label}":r[f"lo_{group}"][b,e], f"CI95_high_{label}":r[f"hi_{group}"][b,e],
                                    f"p_{label}_raw":r[f"p_{group}"][b,e], f"p_{label}_FDR_within_band":r[f"q_{group}_within_band"][b,e]})
                rows.append(row)
        raw = args.output / (model+"_raw.csv")
        pd.DataFrame(rows).to_csv(raw,index=False,float_format="%.17g")
        d = annotation.annotate(raw, model, mapping, hierarchy).sort_values("abs_t",ascending=False)
        d.to_csv(args.output/(model+"_all_significant_annotated.csv"),index=False,float_format="%.17g")
        for unique in [False,True]:
            annotation.network_matrix(d,unique).to_csv(args.output/(model+"_network_matrix_"+("unique" if unique else "records")+".csv"))
        expected = pd.read_csv(args.package/"02_Results"/(model+"_all_significant_annotated.csv"))
        merged = d.merge(expected,on=["PA_variable","edge"],suffixes=("_new","_reference"),validate="one_to_one")
        assert len(merged)==len(d)==len(expected)
        for col in ["ROI_i","ROI_j","Region_official_i","Region_official_j","network_pair"]:
            assert (merged[col+"_new"]==merged[col+"_reference"]).all()
        for col in ["beta_"+target,"t_"+target,"p_raw","p_FDR_global_11bands"]:
            assert np.allclose(merged[col+"_new"],merged[col+"_reference"],rtol=1e-10,atol=1e-12)
        if model == "Model2":
            group_rows=[]
            for row in d.itertuples():
                for label in ["HC","MDD"]:
                    group_rows.append({"PA_variable":row.PA_variable,"edge":row.edge,"Node_i":row.Region_official_i,
                                       "Node_j":row.Region_official_j,"Group":label,"beta":getattr(row,f"beta_PA_{label}"),
                                       "CI95_low":getattr(row,f"CI95_low_{label}"),"CI95_high":getattr(row,f"CI95_high_{label}"),
                                       "p_raw":getattr(row,f"p_{label}_raw"),"p_FDR_within_band_group":getattr(row,f"p_{label}_FDR_within_band"),
                                       "interaction_p_FDR_global":row.p_FDR_global_11bands})
            pd.DataFrame(group_rows).to_csv(args.output/"Group_specific_estimates.csv",index=False,float_format="%.17g")
        print(model,len(d),d.edge_key.nunique(),"annotations and statistics verified")


if __name__ == "__main__": main()
