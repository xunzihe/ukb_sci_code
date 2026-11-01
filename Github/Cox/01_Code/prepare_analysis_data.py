"""Prepare the existing processed UKB inputs; NEVER distribute the output CSV.

This does not redo the historical UKB quality-control or imputation steps.
It uses the same processed inputs as the final analysis, selecting only needed columns.
"""
import argparse
from pathlib import Path
import pandas as pd

NARROW = [f"{a}_{a+25}mg" for a in range(125, 400, 25)]
COVARIATES = ["Age_at_recruitment", "Sex_c", "Body_mass_index", "Townsend_deprivation_index",
              "Edu_c", "Ethn_c", "Emp_b", "Smk_b", "tax_2", "tax_3", "tax_4", "tax_5",
              "alc_1", "alc_2", "alc_3", "alc_4", "alc_5"]


def prepare(root, death_path):
    cov_names = ["Age_at_recruitment", "Sex", "Body_mass_index", "Townsend_deprivation_index",
                 "Education", "Ethnicity", "Employment_status", "smoking_status",
                 "Average_total_household_income_before_tax", "Alcohol_intake_frequency"]
    def read(relative, cols):
        return pd.read_csv(root / relative, usecols=["eid", *cols], dtype={"eid": str})
    labels = read("Part_Data/supplyment/ICD-10/all_id_with_event.csv", ["event", "Date"])
    cov = read("Part_Data/Covariate/new_extracted.csv", cov_names)
    wear = read("Part_Data/PA/all_subjects/new_wear_time.csv", ["End_time_0_0"])
    deaths = pd.read_csv(death_path, usecols=["eid", "death_date"], dtype={"eid": str})
    df = labels.merge(cov, on="eid", validate="one_to_one").merge(wear, on="eid", validate="one_to_one")
    df = df.merge(deaths, on="eid", how="left", validate="one_to_one")
    for old, new in [("End_time_0_0", "entry"), ("Date", "onset"), ("death_date", "death_date")]:
        df[new] = pd.to_datetime(df[old], errors="coerce")
    cutoff = pd.Timestamp("2017-12-31")
    diagnosed = df.event.eq(1) & df.onset.notna()
    df = df.loc[~(diagnosed & df.onset.le(df.entry)) & df.entry.notna()].copy()
    died = df.death_date.gt(df.entry) & df.death_date.le(cutoff)
    incident = df.event.eq(1) & df.onset.gt(df.entry) & df.onset.le(cutoff) & (~died | df.onset.le(df.death_date))
    censor = pd.Series(cutoff, index=df.index).where(~died, df.death_date)
    endpoint = df.onset.where(incident, censor)
    df["followup_years"] = (endpoint - df.entry).dt.total_seconds() / (365.25 * 24 * 60 * 60)
    df["observed"] = incident.astype(int)
    df = df.loc[df.followup_years.gt(0)].copy()
    df["Sex_c"] = pd.to_numeric(df.Sex, errors="coerce")
    df["Edu_c"] = df.Education.eq(1).astype(int)
    df["Ethn_c"] = df.Ethnicity.eq(1001).astype(int)
    df["Emp_b"] = df.Employment_status.ne(1).astype(int)
    df["Smk_b"] = df.smoking_status.ne(0).astype(int)
    for level in range(2, 6):
        df[f"tax_{level}"] = df.Average_total_household_income_before_tax.eq(level).astype(int)
    for level in range(1, 6):
        df[f"alc_{level}"] = df.Alcohol_intake_frequency.eq(level).astype(int)
    adjacent = read("Part_Result/L_shape_analysis/data/PA_time_all_adjacent.csv", NARROW)
    overall = read("Part_Result/L_shape_analysis/data/PA_time_4bins.csv", ["125_400mg"])
    df = df.merge(adjacent, on="eid", validate="one_to_one").merge(overall, on="eid", validate="one_to_one")
    cols = ["followup_years", "observed", *COVARIATES, *NARROW, "125_400mg"]
    assert len(df) == 94536 and df.observed.sum() == 735
    assert not df[cols].isna().any().any(), "The final processed model inputs must contain no missing values."
    return df[cols]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--death-dates", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    data = prepare(args.data_root, args.death_dates)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(args.out, index=False)
    print(f"PRIVATE analysis input prepared: n={len(data)}, events={data.observed.sum()}", flush=True)
