"""Compare package-native reruns against frozen aggregate results; no private values printed."""
import argparse
from pathlib import Path
import numpy as np
import pandas as pd


def main(reference, candidate, ph_folder, output):
    checks = []
    def check(label, old, new, tolerance):
        difference = float(np.nanmax(np.abs(np.asarray(old, float)-np.asarray(new, float))))
        checks.append({"check":label, "max_absolute_difference":difference, "tolerance":tolerance, "passed":difference<=tolerance})
    for scale in ["10min", "SD"]:
        old_file = "cox_per10_final.csv" if scale=="10min" else "cox_perSD_final.csv"
        new_file = "cox_per10_package.csv" if scale=="10min" else "cox_perSD_package.csv"
        old = pd.read_csv(reference/old_file).set_index("feature")
        new = pd.read_csv(candidate/new_file).set_index("feature").loc[old.index]
        for source, target in [(f"HR_per_{scale}", "HR"), (f"CI95_low_per_{scale}", "CI95_low"), (f"CI95_high_per_{scale}", "CI95_high"), ("p_value", "p_value"), ("p_fdr_within_11", "p_fdr_within_11")]:
            tolerance = 5e-6 if target.startswith("CI95") else 1e-8
            check(f"Cox {scale} {target}", old[source], new[target], tolerance)
            if target.startswith("CI95"):
                check(f"Cox {scale} {target} manuscript 3-decimal rounding", np.round(old[source],3), np.round(new[target],3), 1e-12)
    old = pd.read_csv(reference/"rcs_nonlinearity_results.csv").set_index("feature")
    new = pd.read_csv(candidate/"rcs_nonlinearity_package.csv").set_index("feature").loc[old.index]
    for column in ["linear_log_likelihood", "rcs_log_likelihood", "p_nonlinearity", "p_nonlinearity_fdr"]:
        check("RCS "+column, old[column], new[column], 1e-6)
    for path in (reference/"curves").glob("*.csv"):
        old_curve = pd.read_csv(path)
        new_curve = pd.read_csv(candidate/"curves"/path.name)
        for column in ["minutes_per_week", "HR", "CI95_low", "CI95_high"]:
            check(path.stem+" "+column, old_curve[column], new_curve[column], 5e-5)
    if ph_folder is not None:
        old = pd.read_csv(reference/"PH_diagnostics_final.csv").set_index("Acceleration intensity interval")
        new = pd.read_csv(ph_folder/"ph_exposure_package.csv").set_index("feature")
        new.index = new.index.str.replace("_", "-", regex=False).str.replace("mg", " mg", regex=False)
        new = new.loc[old.index]
        check("PH exposure raw P (reference rounded to 4 decimals)",old["Raw exposure PH P"],new.ph_p,5.1e-5)
        check("PH exposure FDR P (reference rounded to 4 decimals)",old["FDR-adjusted exposure PH P within 11 narrow intervals"],new.ph_p_fdr_within_11,5.1e-5)
    table = pd.DataFrame(checks)
    output.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(output, index=False)
    print(table.to_string(index=False))
    assert table.passed.all(), "A validation tolerance was exceeded; do not call the package validated."


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--ph", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    main(args.reference, args.candidate, args.ph, args.out)
