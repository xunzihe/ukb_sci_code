# Reproduction instructions

Run commands from the repository root. Choose a separate, access-controlled location for private inputs and model reruns.

## Without participant-level data

```sh
python -m pip install -r requirements.txt
python verify_release.py
python reproduce_figures.py --output outputs/figures
```

Verification checks file hashes, recomputes Cox/RCS/PH and imaging BH corrections, validates the retained edge mapping, and checks significant-record and network counts. It does not refit the regression models.

Figure reproduction uses the existing plotting functions and the saved aggregate curves/matrices. It generates the Cox forest plot, the two RCS figures and the all-unique-edge SC network matrices. A cohort flowchart and copies of manuscript/Word/Excel attachments are intentionally not duplicated in this computational repository. Font availability can affect typography without changing numerical content.

## With authorized processed Cox inputs

```sh
python Cox/01_Code/prepare_analysis_data.py --data-root /private/PA_MDD --death-dates /private/death_dates_for_cox.csv --out /private/cox_model_input.csv
python Cox/01_Code/run_analysis.py --data /private/cox_model_input.csv --out /private/cox_rerun --tasks cox rcs townsend
python Cox/01_Code/run_analysis.py --data /private/cox_model_input.csv --out /private/ph_rerun --tasks ph --workers 1
python Cox/01_Code/summarize_baseline.py --data /private/cox_model_input.csv --out /private/cox_rerun/baseline.csv
python Cox/01_Code/validate_results.py --reference Cox/02_Results --candidate /private/cox_rerun --ph /private/ph_rerun --out /private/cox_comparison.csv
```

PH computation uses the unchanged lifelines implementation and can be slow. Increase workers only if memory permits. The input remains participant-level even if its identifier column has been dropped. Do not upload it or the private input directory.

## With authorized processed SC inputs

The source directory must contain the two exact inputs described in `MLR/01_Code/Input_schema.json`. Participant order is linked explicitly; no new imputation is performed.

```sh
python MLR/01_Code/run_mlr.py --source-root /private/sc_inputs --output-root /private/sc_rerun --workers 1
python MLR/01_Code/export_results.py --package MLR --model-results /private/sc_rerun/99_Internal_Records_Not_For_Upload/standard_results/standard_full_results.npz --output /private/sc_rerun/annotated
```

The export script checks the retained-edge mapping, official atlas tables and agreement with the frozen annotated results. Regression uses conventional OLS covariance and two-sided tests. Both PA and SC use sample-SD standardization (`ddof=1`) across all 189 participants. A result from another cohort, input version or coding should not be described as reproducing this release merely because the program finishes.

## File provenance

`release_manifest.json` lists SHA-256 hashes for the public files, source-relative locations and any column selection. The model-fitting and annotation scripts are unchanged copies of the frozen study files. Full-test exports omit unused coefficient columns but preserve every test's raw and adjusted P values. The ethnicity description in the public coding table is made explicit as White British; this is a label clarification, not a numerical change.

No code license, UK Biobank application number, publication DOI or public repository URL is inferred from local folder names.
