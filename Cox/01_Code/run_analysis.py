"""Reproduce Cox/RCS inference using standard packages, not bespoke statistical kernels.

Core APIs: lifelines.CoxPHFitter; patsy.cr; statsmodels.multipletests;
lifelines.proportional_hazard_test; scipy.stats.chi2; statsmodels.t_test.
The input is a PRIVATE participant-level analysis table and must not be published.
"""
import os
for variable in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(variable, "1")
import argparse
import importlib.metadata
import json
import time
import warnings
from pathlib import Path
from types import SimpleNamespace
from concurrent.futures import ProcessPoolExecutor, as_completed
import numpy as np
import pandas as pd
from lifelines import CoxPHFitter
from lifelines.statistics import proportional_hazard_test
from patsy import dmatrix, build_design_matrices
from scipy.stats import chi2
from statsmodels.base.model import LikelihoodModelResults
from statsmodels.stats.multitest import multipletests
from prepare_analysis_data import COVARIATES, NARROW

FEATURES = NARROW + ["125_400mg"]


def fit(data, terms, strata=None):
    cols = [*terms, "followup_years", "observed"] + ([] if strata is None else [strata])
    return CoxPHFitter(penalizer=0.0).fit(data[cols], duration_col="followup_years",
                                         event_col="observed", strata=strata, batch_mode=True)


def adjust(table, p_col, output_col, feature_list):
    select = table.feature.isin(feature_list)
    table[output_col] = np.nan
    table.loc[select, output_col] = multipletests(table.loc[select, p_col], method="fdr_bh")[1]
    return table


def effect(model, term):
    row = model.summary.loc[term]
    return {"HR": row["exp(coef)"], "CI95_low": row["exp(coef) lower 95%"],
            "CI95_high": row["exp(coef) upper 95%"], "p_value": row["p"]}


def run_cox(data, out, tasks, features):
    results, ph_results, stratified, sd_results = [], [], [], []
    for feature in features:
        tick = time.monotonic()
        dm = data.copy()
        x = dm[feature]
        dm["exposure_10min"] = x / 10
        model = fit(dm, ["exposure_10min", *COVARIATES])
        result = {"feature": feature, "n": len(dm), "events": int(dm.observed.sum()),
                  "mean_min_week": x.mean(), "sd_min_week": x.std(ddof=1),
                  "zero_percent": x.eq(0).mean()*100, **effect(model, "exposure_10min")}
        results.append(result)
        if "cox" in tasks:
            dm["exposure_sd"] = (x - x.mean()) / x.std(ddof=1)
            sd_model = fit(dm, ["exposure_sd", *COVARIATES])
            sd_results.append({"feature": feature, "sd_min_week": x.std(ddof=1), **effect(sd_model, "exposure_sd")})
        if "townsend" in tasks:
            dm["townsend_quintile"] = pd.qcut(dm.Townsend_deprivation_index, q=5, labels=False)
            cov = [c for c in COVARIATES if c != "Townsend_deprivation_index"]
            model_s = fit(dm, ["exposure_10min", *cov], strata="townsend_quintile")
            stratified.append({"feature": feature, "primary_HR": result["HR"], **effect(model_s, "exposure_10min")})
        if "ph" in tasks:
            # Package-native residual computation; no custom fast residuals are passed.
            training = dm[["exposure_10min", *COVARIATES, "followup_years", "observed"]]
            ph = proportional_hazard_test(model, training, time_transform="rank").summary
            ph = ph.reset_index(names="term").rename(columns={"p": "ph_p"})
            ph.insert(0, "feature", feature)
            ph_results.extend(ph.to_dict("records"))
        print(f"Cox {feature}: {time.monotonic()-tick:.1f}s", flush=True)
    if "cox" in tasks:
        adjust(pd.DataFrame(results), "p_value", "p_fdr_within_11", NARROW).to_csv(out/"cox_per10_package.csv", index=False)
        adjust(pd.DataFrame(sd_results), "p_value", "p_fdr_within_11", NARROW).to_csv(out/"cox_perSD_package.csv", index=False)
    if stratified:
        pd.DataFrame(stratified).to_csv(out/"townsend_stratified_package.csv", index=False)
    if ph_results:
        table = pd.DataFrame(ph_results)
        table.to_csv(out/"ph_all_terms_package.csv", index=False)
        exposure = table.loc[table.term.eq("exposure_10min")].copy()
        # For a subset diagnostic run no FDR family is silently reduced.
        if set(features) == set(FEATURES):
            adjust(exposure, "ph_p", "ph_p_fdr_within_11", NARROW).to_csv(out/"ph_exposure_package.csv", index=False)


def run_rcs(data, out, features):
    diagnostics, results = [], []
    curves = out / "curves"
    curves.mkdir(exist_ok=True)
    for feature in features:
        tick = time.monotonic()
        x = data[feature].to_numpy(float)
        knots = np.percentile(x, [5, 50, 95])
        eligible = len(np.unique(knots)) == 3
        diagnostics.append({"feature": feature, "zero_percent": np.mean(x==0)*100,
                            "knot_5": knots[0], "knot_50": knots[1], "knot_95": knots[2], "rcs_eligible": eligible})
        if not eligible:
            print(f"RCS {feature}: excluded (non-distinct P5/P50/P95)", flush=True)
            continue
        design = dmatrix("cr(x, knots=(middle,), lower_bound=lo, upper_bound=hi, constraints='center') - 1",
                         {"x": x, "middle": knots[1], "lo": knots[0], "hi": knots[2]})
        assert design.shape[1] == 2 and np.linalg.matrix_rank(design) == 2
        dm = data.copy()
        terms = ["rcs_1", "rcs_2"]
        dm[terms] = np.asarray(design)
        dm["exposure_10min"] = x / 10
        linear = fit(dm, ["exposure_10min", *COVARIATES])
        spline = fit(dm, [*terms, *COVARIATES])
        lr = 2*(spline.log_likelihood_ - linear.log_likelihood_)
        assert lr > -1e-6
        p = chi2.sf(max(0., lr), df=1)
        reference, maximum = np.percentile(x, [1, 95])
        grid = np.linspace(reference, maximum, 350)
        basis_grid = build_design_matrices([design.design_info], {"x": grid, "middle": knots[1], "lo": knots[0], "hi": knots[2]})[0]
        basis_reference = build_design_matrices([design.design_info], {"x": [reference], "middle": knots[1], "lo": knots[0], "hi": knots[2]})[0]
        contrast = np.zeros((len(grid), len(spline.params_)))
        contrast[:, :2] = np.asarray(basis_grid) - np.asarray(basis_reference)[0]
        # Standard statsmodels contrast inference uses lifelines' estimated parameters/covariance.
        carrier = LikelihoodModelResults(SimpleNamespace(data=SimpleNamespace(cov_names=list(spline.params_.index))),
                                         spline.params_.to_numpy(), spline.variance_matrix_.to_numpy(), scale=1.)
        carrier.df_resid = len(data) - len(spline.params_)
        with np.errstate(divide="ignore", invalid="ignore"):
            inference = carrier.t_test(contrast, use_t=False)
        ci = inference.conf_int(alpha=0.05)
        curve = pd.DataFrame({"feature": feature, "minutes_per_week": grid, "reference_minutes": reference,
                              "HR": np.exp(inference.effect), "CI95_low": np.exp(ci[:,0]), "CI95_high": np.exp(ci[:,1])})
        curve.to_csv(curves/f"rcs_curve_{feature}.csv", index=False)
        results.append({"feature": feature, "n": len(data), "events": int(data.observed.sum()),
                        "knot_1_min_week": knots[0], "knot_2_min_week": knots[1], "knot_3_min_week": knots[2],
                        "linear_log_likelihood": linear.log_likelihood_, "rcs_log_likelihood": spline.log_likelihood_,
                        "lr_chi2_nonlinearity": max(0.,lr), "lr_df": 1, "p_nonlinearity": p})
        print(f"RCS {feature}: P={p:.8g}; {time.monotonic()-tick:.1f}s", flush=True)
    pd.DataFrame(diagnostics).to_csv(out/"rcs_eligibility_package.csv", index=False)
    rcs = pd.DataFrame(results)
    if set(features) == set(FEATURES):
        eligible_features = rcs.loc[rcs.feature.isin(NARROW), "feature"].tolist()
        assert len(eligible_features) == 10
        rcs = adjust(rcs, "p_nonlinearity", "p_nonlinearity_fdr", eligible_features)
    rcs.to_csv(out/"rcs_nonlinearity_package.csv", index=False)


def ph_worker(payload):
    input_path, out, feature = payload
    part_dir = Path(out) / "ph_parts" / feature
    part_dir.mkdir(parents=True, exist_ok=True)
    run_cox(pd.read_csv(input_path), part_dir, ["ph"], [feature])
    return pd.read_csv(part_dir / "ph_all_terms_package.csv")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--tasks", nargs="+", choices=["cox", "rcs", "ph", "townsend"], default=["cox", "rcs", "ph", "townsend"])
    parser.add_argument("--features", nargs="+", default=FEATURES, choices=FEATURES)
    parser.add_argument("--workers", type=int, default=1, help="Parallel workers for a PH-only run; never changes statistics.")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    data = pd.read_csv(args.data)
    assert len(data) == 94536 and data.observed.sum() == 735 and not data.isna().any().any()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        if set(args.tasks) == {"ph"} and args.workers > 1:
            parts = []
            with ProcessPoolExecutor(max_workers=args.workers) as pool:
                futures = [pool.submit(ph_worker, (args.data, args.out, f)) for f in args.features]
                for future in as_completed(futures):
                    parts.append(future.result())
                    pd.concat(parts, ignore_index=True).to_csv(args.out/"ph_completed_checkpoint.csv", index=False)
            ph = pd.concat(parts, ignore_index=True)
            ph.to_csv(args.out/"ph_all_terms_package.csv", index=False)
            exposure = ph.loc[ph.term.eq("exposure_10min")].copy()
            if set(args.features) == set(FEATURES):
                adjust(exposure, "ph_p", "ph_p_fdr_within_11", NARROW).to_csv(args.out/"ph_exposure_package.csv", index=False)
        elif set(args.tasks) & {"cox", "townsend", "ph"}:
            run_cox(data, args.out, args.tasks, args.features)
        if "rcs" in args.tasks:
            run_rcs(data, args.out, args.features)
    environment = {name:importlib.metadata.version(name) for name in ["numpy", "pandas", "scipy", "lifelines", "patsy", "statsmodels"]}
    (args.out/"run_manifest.json").write_text(json.dumps({"packages": environment, "tasks": args.tasks,
        "n": len(data), "events": int(data.observed.sum()), "warnings": [str(w.message) for w in caught]}, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
