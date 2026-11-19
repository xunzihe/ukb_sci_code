# Reproduction instructions

Run commands from the repository root. Choose a separate, access-controlled location for private inputs and model reruns.

## Without participant-level data

```sh
python -m pip install -r requirements.txt
python verify_release.py
python reproduce_figures.py --output outputs/figures
```

Verification checks file hashes, recomputes Cox/RCS/PH and imaging BH corrections, validates the retained edge mapping, and checks significant-record and network counts. It does not refit the regression models.

Main-figure reproduction uses saved aggregate results in `Figures/`. It generates the cohort flowchart with non-case terminology (Fig1), combined Cox forest and seven significant-nonlinearity RCS curves (Fig2A–H), and all 79/25 unique anatomical SC connections with corresponding complete network matrices (Fig3A–D). Matrix lower-triangle totals are 79 and 25; no Top50 selection is used. Fig2 retains the HR = 0.60 red guides, solid markers, unboxed red weekly-duration labels, inward ticks and superscript scientific P values. The current combined Fig3 is 166 × 204 mm; its matrix axes have labels but no tick marks. Default TIFF resolutions are 1200 dpi for Fig1/Fig2 and 600 dpi for Fig3. Optional `--figure3-dpi` and `--figure3-layout` arguments are forwarded to the drawing package.

Install figure dependencies using `python -m pip install -r Figures/requirements-figures.txt`. The default runner assembles Fig3A/B from the exact approved Model1/Model2 PDF panels and redraws C/D from all significant unique edges. Full anatomical rerendering is available with `--rebuild-brain --brainnet-root /path/to/BrainNetViewer_20191031 --matlab /path/to/matlab`. Fig1 requires locally licensed Arial regular/bold font files as described in `Figures/README.md`. No participant-level inputs are required for plotting. Manuscript/Word/Excel attachments are not included.

The two supplementary RCS figures have a separate entry point:

```sh
python reproduce_supplementary_figures.py --output outputs/supplementary_figures
```

Outputs are `Supplemental_Digital_Content_2_RCS_overall_MPA.pdf` and `Supplemental_Digital_Content_5_RCS_nonsignificant_bands.pdf`. The latter contains 300–325, 325–350 and 350–375 mg curves; these are no longer main-figure panels. Seven other narrow-band curves appear in main Fig2. SDC1–4 retain their existing numbers; SDC5 is added as Figure S2. Word and Excel attachments are not distributed in this code repository.

Both root-level drawing commands delegate to `Figures/code/`, so main and supplementary rendering use the same current plotting functions. Approved anatomical PDFs are retained by a specific `.gitignore` exception; do not omit them from a Git checkout or upload.

Statistical-fitting scripts, aggregate results and supplementary models are unchanged. The current matrix renderer is in `Figures/code/compose_current_figures.py`. Historical standalone plotting scripts are not included; use the root-level main-figure and supplementary-figure entry points. The two approved anatomical PDFs and the small validation records used by optional BrainNet rerendering must be retained.

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
