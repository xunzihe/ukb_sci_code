"""Re-use the verified inputs/coding; estimate statistics with public library APIs.

No participant-level data are written. Run with the existing pa_mdd environment.
"""
import os
for _name in ("OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS"):
    os.environ[_name] = "1"

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import time

import numpy as np
import pandas as pd
from scipy.io import loadmat
from scipy.stats import zscore
from statsmodels.regression.linear_model import OLS
from statsmodels.stats.multitest import multipletests

BANDS = [f"{v}_{v + 25}mg" for v in range(125, 400, 25)]
COVARIATE_NAMES = ["Age_at_recruitment", "Sex_c", "Body_mass_index",
                   "Townsend_deprivation_index", "Edu_c", "Ethn_c", "Emp_b",
                   "Smk_b", "tax_2", "tax_3", "tax_4", "tax_5",
                   "alc_1", "alc_2", "alc_3", "alc_4", "alc_5"]
_INPUT = None


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_inputs(source):
    source = Path(source)
    m = loadmat(source / "SC_adjacent_PLS_data_filt.mat", squeeze_me=True)
    ids = pd.Series(m["subject_ids"].ravel()).astype(str).str.strip()
    labels = [str(v.item() if isinstance(v, np.ndarray) and v.size == 1 else v).strip()
              for v in np.ravel(m["Y_labels"])]
    pa = np.asarray(m["Y_all"][:, [labels.index(b) for b in BANDS]], dtype=float)
    raw_sc = np.asarray(m["X"], dtype=float)
    group = np.asarray(m["group_labels"], dtype=float).ravel()
    columns = ["eid", "Age_at_recruitment", "Sex", "Body_mass_index",
               "Townsend_deprivation_index", "Education", "Ethnicity",
               "Employment_status", "Average_total_household_income_before_tax",
               "Alcohol_intake_frequency", "smoking_status"]
    table = pd.read_csv(source / "new_extracted.csv", usecols=columns, dtype={"eid": str})
    assert table.eid.is_unique, "Duplicate covariate participant keys"
    table = table.set_index("eid").loc[ids].reset_index()
    for col in columns[1:]:
        table[col] = pd.to_numeric(table[col], errors="raise")
    assert np.isfinite(table[columns[1:]].to_numpy()).all(), "Missing raw covariates"
    assert set(table.smoking_status.unique()).issubset({0, 1, 2})
    assert set(table.Alcohol_intake_frequency.unique()).issubset(set(range(1, 7)))
    assert set(table.Average_total_household_income_before_tax.unique()).issubset(set(range(1, 6)))
    cov = np.column_stack([
        table.Age_at_recruitment, table.Sex, table.Body_mass_index,
        table.Townsend_deprivation_index, (table.Education == 1).astype(int),
        (table.Ethnicity == 1001).astype(int), (table.Employment_status != 1).astype(int),
        (table.smoking_status != 0).astype(int),
        *[(table.Average_total_household_income_before_tax == v).astype(int) for v in range(2, 6)],
        *[(table.Alcohol_intake_frequency == v).astype(int) for v in range(1, 6)]
    ]).astype(float)
    original_edges = np.flatnonzero(np.asarray(m["edge_mask"], dtype=bool).ravel()) + 1
    assert raw_sc.shape == (189, 19319) and pa.shape == (189, 11)
    assert len(original_edges) == raw_sc.shape[1] and cov.shape == (189, 17)
    assert np.isfinite(raw_sc).all() and np.isfinite(pa).all() and (pa >= 0).all()
    assert (group == 0).sum() == 116 and (group == 1).sum() == 73
    assert int((raw_sc != 0).sum(axis=0).min()) >= 10
    sc = zscore(raw_sc, axis=0, ddof=1)
    paz = zscore(pa, axis=0, ddof=1)
    assert np.isfinite(sc).all() and np.isfinite(paz).all()
    return sc, paz, group, cov, original_edges, table, pa


def initialise(source):
    global _INPUT
    _INPUT = read_inputs(source)


def fit_band(band_index):
    sc, pa, group, cov, _, _, _ = _INPUT
    n, edges = sc.shape
    x1 = np.column_stack([np.ones(n), pa[:, band_index], cov])
    x2 = np.column_stack([np.ones(n), pa[:, band_index], group,
                          pa[:, band_index] * group, cov])
    assert np.linalg.matrix_rank(x1) == 19 and np.linalg.matrix_rank(x2) == 21
    keys = ["beta_m1", "se_m1", "t_m1", "p_m1", "lo_m1", "hi_m1",
            "beta_int", "se_int", "t_int", "p_int", "lo_int", "hi_int",
            "beta_hc", "se_hc", "t_hc", "p_hc", "lo_hc", "hi_hc",
            "beta_mdd", "se_mdd", "t_mdd", "p_mdd", "lo_mdd", "hi_mdd",
            "beta_group", "se_group", "t_group", "p_group", "lo_group", "hi_group"]
    out = {k: np.empty(edges) for k in keys}
    hc_contrast = np.zeros(21); hc_contrast[1] = 1
    mdd_contrast = np.zeros(21); mdd_contrast[[1, 3]] = 1
    started = time.perf_counter()
    for edge in range(edges):
        r1 = OLS(sc[:, edge], x1, missing="raise").fit()
        r2 = OLS(sc[:, edge], x2, missing="raise").fit()
        ci1 = r1.conf_int(alpha=0.05)[1]
        ci2 = r2.conf_int(alpha=0.05)
        for prefix, result, col, ci in [("m1", r1, 1, ci1), ("int", r2, 3, ci2[3]),
                                         ("group", r2, 2, ci2[2])]:
            for measure, value in [("beta", result.params[col]), ("se", result.bse[col]),
                                   ("t", result.tvalues[col]), ("p", result.pvalues[col]),
                                   ("lo", ci[0]), ("hi", ci[1])]:
                out[f"{measure}_{prefix}"][edge] = value
        for prefix, contrast in [("hc", hc_contrast), ("mdd", mdd_contrast)]:
            test = r2.t_test(contrast)
            ci = test.conf_int(alpha=0.05).ravel()
            for measure, value in [("beta", test.effect.item()), ("se", test.sd.item()),
                                   ("t", test.tvalue.item()), ("p", test.pvalue.item()),
                                   ("lo", ci[0]), ("hi", ci[1])]:
                out[f"{measure}_{prefix}"][edge] = value
    return band_index, out, time.perf_counter() - started


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    raw_out = args.output_root / "99_Internal_Records_Not_For_Upload" / "standard_results"
    raw_out.mkdir(parents=True, exist_ok=True)
    if (raw_out / "standard_full_results.npz").exists():
        raise FileExistsError("Existing standard results: choose a new output root to preserve provenance")
    inputs = read_inputs(args.source_root)
    result = {}
    with ProcessPoolExecutor(max_workers=args.workers, initializer=initialise,
                             initargs=(str(args.source_root),)) as pool:
        futures = [pool.submit(fit_band, b) for b in range(11)]
        for future in as_completed(futures):
            b, values, seconds = future.result()
            if not result:
                result = {k: np.empty((11, 19319)) for k in values}
            for k, values_for_band in values.items():
                result[k][b] = values_for_band
            np.savez_compressed(raw_out / f"band_{BANDS[b]}.npz", **values)
            print(f"Completed {BANDS[b]}: {seconds:.1f}s", flush=True)
    for prefix in ("m1", "int"):
        p = result[f"p_{prefix}"]
        assert np.isfinite(p).all() and ((p >= 0) & (p <= 1)).all()
        result[f"q_{prefix}"] = multipletests(p.ravel(), alpha=0.05, method="fdr_bh")[1].reshape(p.shape)
    # Supplementary group-specific interpretation: preserve the previous scope,
    # one 19,319-edge family per band per group, not the main interaction family.
    for prefix in ("hc", "mdd"):
        result[f"q_{prefix}_within_band"] = np.row_stack([
            multipletests(p, alpha=0.05, method="fdr_bh")[1]
            for p in result[f"p_{prefix}"]
        ])
    result["original_edges"] = inputs[4]
    np.savez_compressed(raw_out / "standard_full_results.npz", **result)
    summary = []
    for model, prefix in [("Model1", "m1"), ("Model2", "int")]:
        for b, band in enumerate(BANDS):
            use = result[f"q_{prefix}"][b] < 0.05
            summary.append({"Model": model, "PA_band": band, "Records": int(use.sum()),
                            "Positive": int((result[f"beta_{prefix}"][b, use] > 0).sum()),
                            "Negative": int((result[f"beta_{prefix}"][b, use] < 0).sum())})
    pd.DataFrame(summary).to_csv(raw_out / "band_summary.csv", index=False)
    audit = {
        "completed_utc": datetime.now(timezone.utc).isoformat(),
        "estimator": "statsmodels.regression.linear_model.OLS.fit (default nonrobust covariance)",
        "contrast": "OLSResults.t_test",
        "standardization": "scipy.stats.zscore(axis=0, ddof=1)",
        "primary_correction": "multipletests(method='fdr_bh'), 212509 raw P values per model",
        "group_specific_correction": "multipletests(method='fdr_bh'), 19319 edges per band per group",
        "participants": 189, "HC": 116, "MDD": 73, "edges": 19319,
        "covariate_concepts": 10, "covariate_columns": COVARIATE_NAMES,
        "model1_design_shape": [189, 19], "model2_design_shape": [189, 21],
        "model1_df_resid": 170, "model2_df_resid": 168,
        "software": {n: importlib.metadata.version(n) for n in ["numpy", "scipy", "pandas", "statsmodels"]},
        "python": platform.python_version(),
        "input_sha256": {p.name: digest(p) for p in args.source_root.iterdir() if p.is_file()},
        "source_root_internal_only": str(args.source_root.resolve()),
        "script_sha256": digest(__file__),
        "missing_raw_covariates": 0,
    }
    (raw_out / "run_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    for prefix, expected in [("m1", 86), ("int", 34)]:
        observed = int((result[f"q_{prefix}"] < 0.05).sum())
        print(f"{prefix}: {observed} significant records (previous reference {expected})", flush=True)
    print("FINISHED", flush=True)


if __name__ == "__main__":
    main()
