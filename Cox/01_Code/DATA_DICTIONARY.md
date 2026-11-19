# Input contract — private data are not distributed

`prepare_analysis_data.py` expects the following already processed files beneath `--data-root`:

| File | Required fields |
|---|---|
| `Part_Data/supplyment/ICD-10/all_id_with_event.csv` | `eid`, `event`, `Date` (hospital-recorded depression date) |
| `Part_Data/Covariate/new_extracted.csv` | `eid`, age, sex, BMI, Townsend, education, ethnicity, employment, income, smoking, alcohol fields named in the script |
| `Part_Data/PA/all_subjects/new_wear_time.csv` | `eid`, `End_time_0_0` |
| `Part_Result/L_shape_analysis/data/PA_time_all_adjacent.csv` | `eid`, `125_150mg` through `375_400mg`; min/week |
| `Part_Result/L_shape_analysis/data/PA_time_4bins.csv` | `eid`, `125_400mg`; min/week |

`--death-dates` supplies a separate processed table with `eid` and `death_date`. Participants without a death record have no linked death date. Duplicate identifiers cause an error rather than silently multiplying rows.

The endpoint is the earliest eligible first depression diagnosis, death, or 2017-12-31. Diagnoses on/before wear completion are excluded. Duration is in years (365.25 days), although the choice of the time unit does not alter the HR.

The final model table contains `followup_years`, `observed`, 12 activity-duration columns and 17 covariate design columns. It contains no `eid`, but remains PRIVATE participant-level data. The expected final counts are checked explicitly.

Covariate design preserves the original processed-data coding: `Sex_c=Sex`; `Edu_c=(Education==1)`; `Ethn_c=(Ethnicity==1001)`; `Emp_b=(Employment_status!=1)`; `Smk_b=(smoking_status!=0)`; income indicators for codes 2–5 (code 1 reference); alcohol indicators for codes 1–5 (the processed never-drinking category is the reference). Age, BMI and Townsend are continuous. These comparisons are coding declarations, not a new imputation step; missing/invalid values must already have been handled in the input preprocessing. The source model inputs had no remaining missing values.

The binary ethnicity coding is stated explicitly to avoid ambiguity: the script tests code 1001 versus all other processed codes. Its verbal label in a manuscript must match the meaning of that code in the author's preprocessing; do not infer a broader category from the code alone.
