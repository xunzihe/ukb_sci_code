# Aggregate data dictionary

## Cox

All files below summarize models or groups, not individuals.

- `cox_per10_final.csv`: 11 narrow bands and the overall comparator; HR, ordinary 95% CI and raw P per 10 min/week. `p_fdr_within_11` covers only the 11 narrow bands.
- `cox_perSD_final.csv`: corresponding per-SD estimates.
- `baseline_characteristics_final.csv`: aggregate cohort characteristics. Ethnicity code 1001 is White British.
- `rcs_distribution_eligibility.csv`: exposure-distribution and knot-eligibility summaries.
- `rcs_nonlinearity_results.csv`: likelihood-ratio nonlinearity tests and correction across ten eligible bands. The 375–400 mg band is excluded from RCS because its P5 and P50 coincide, not because its RCS test was nonsignificant.
- `curves/rcs_curve_*.csv`: saved adjusted HR curves and ordinary 95% CI, referenced to P1 and displayed through P95. These are model predictions, not individual exposure measurements.
- `PH_all_terms_package.csv`, `PH_exposure_package.csv`, `PH_diagnostics_final.csv`: aggregate proportional-hazards diagnostics. Exposure-term correction covers the eleven narrow bands; covariate diagnostics must not be mistaken for adjusted exposure tests.
- `Townsend_full_precision.csv`: TDI-stratified sensitivity estimates.

## SC MLR

- `Model1_all_significant_annotated.csv`: all 86 significant band–edge records, not deduplicated. PA coefficients, conventional SE, t, raw P, joint FDR P and ordinary CI are retained alongside ROI labels and network annotations.
- `Model2_all_significant_annotated.csv`: all 34 significant interaction records, with the corresponding HC and MDD PA coefficients, ordinary CI, raw P and within-band/group FDR P. These are estimates from the interaction model, not separate unadjusted correlations.
- `Model1_network_matrix_unique.csv`, `Model2_network_matrix_unique.csv`: symmetric network counts after deduplicating anatomical edges across bands. Sum one triangle including the diagonal: 79 and 25. Do not sum both triangles.
- `PA_band_summary.csv`: record counts and unique-edge counts by band and model, including zero-result bands.
- `PA_distribution.csv`: imaging-sample exposure summaries, including nonzero counts; no individual durations.
- `SC_retained_edge_index.csv`: the exact mapping between retained model columns and original 1-based MATLAB upper-triangular edge indices and Brainnetome ROI labels. The original ordering is column-major, excluding the diagonal. Use this mapping when joining coefficients to anatomical edges.
- `Covariate_encoding.csv`: ten covariate concepts and coding, including smoking and alcohol. Income and alcohol use indicator columns; ten concepts do not mean ten design-matrix columns.

### Compact full-test files

`all_tests_by_band/All_tests_*.csv.gz` has 19,319 rows per band. There are 212,509 rows across eleven files. Columns are selected from the frozen full test outputs; row order, identifiers and P values are preserved.

| Field | Definition |
| --- | --- |
| `PA_variable` | Acceleration band, e.g. `225_250mg`; mg means milligravity |
| `original_edge`, `analysis_edge` | Original and retained feature indices, not participant IDs |
| `ROI_i`, `ROI_j` | Brainnetome labels 1–246 |
| `p_m1`, `q_m1` | Raw and joint-BH P for Model 1 PA |
| `p_int`, `q_int` | Raw and joint-BH P for Model 2 PA × group |
| `p_hc`, `q_hc_within_band` | HC PA-contrast P and BH P across 19,319 edges in that band |
| `p_mdd`, `q_mdd_within_band` | Corresponding MDD contrast P and within-band BH P |

Retaining all raw test P values is necessary to verify the BH families. Applying BH only to the significant-record tables would not reproduce the reported correction.

## Restricted model inputs

The Cox input contract is documented in `Cox/01_Code/DATA_DICTIONARY.md`. Its preparation script starts from existing processed cohort inputs and does not redo historical raw-data QC or imputation.

`MLR/01_Code/Input_schema.json` defines the two restricted inputs for SC refitting. The MAT file contains individual SC, PA and linkage fields; the covariate CSV contains participant records. Neither file is distributed. The public data do not permit participant-level reconstruction or model refitting on their own.
