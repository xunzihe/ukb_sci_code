# Fine-grained physical activity, depression and structural connectivity

Analysis code and aggregate statistics for 11 consecutive 25-mg acceleration bands within 125–400 mg. Cox analyses also include the overall 125–400 mg duration comparator.

## Contents

- `Cox/01_Code/`: processed-input preparation, Cox/RCS models, baseline summaries and diagnostics.
- `Cox/02_Results/`: cohort summaries, regression estimates, diagnostics and saved RCS curves.
- `MLR/01_Code/`: SC regression, result annotation and verification scripts; atlas reference tables have separate terms.
- `MLR/02_Results/`: significant association records, network matrices and compact full-test P-value tables.
- `docs/`: data definitions, access restrictions and reproduction instructions.
- `verify_release.py`: verify file checksums, multiple-testing results and network counts without participant-level data.
- `reproduce_figures.py`: regenerate quantitative figures from the included aggregate statistics.
- `Figures/`: current Fig1–Fig3 drawing sources, aggregate plotting inputs and approved BrainNet panels, synchronized with the final submission figures.
- `reproduce_supplementary_figures.py`: reproduce the overall 125–400 mg RCS curve as SDC2 and three narrow-band RCS curves without significant nonlinearity as SDC5. Seven other narrow-band curves appear in main Fig2.

No participant-level UK Biobank records, individual SC matrices, MRI volumes or linkage identifiers are distributed. The data directory contains statistical summaries, not the original research dataset. Refitting models requires approved access to the processed participant-level inputs.

## Environment and public verification

Python 3.10.20 was used. Install the pinned analysis packages in an isolated environment:

```sh
python -m pip install -r requirements.txt
python verify_release.py
python reproduce_figures.py --output outputs/figures
```

The main-figure entry point produces the cohort flowchart (Fig1), a combined Cox forest/seven-RCS figure (Fig2), and the complete Model1/Model2 anatomical connectomes plus their full unique-edge network matrices (Fig3A–D). Install figure dependencies with `python -m pip install -r Figures/requirements-figures.txt`. See `Figures/README.md` for licensed Arial fonts, full BrainNet rerendering and the distinction between approved-panel assembly and new anatomical rendering. Separate superseded main Fig4/Fig5 outputs are no longer generated.

The current drawing sources use non-case terminology in Fig1; HR = 0.60 red reference guides, inward ticks and superscript scientific P-value notation in Fig2; and the compact 166 × 204 mm combined Fig3 with no matrix-axis tick marks. Fig1/Fig2 TIFFs are 1200 dpi and the combined Fig3 TIFF is 600 dpi by default. Add `--figure3-dpi 1200` only if a higher-resolution combined export is needed. These are presentation updates; statistical models and saved numerical results are unchanged. The approved PDF panels under `Figures/brain/approved_panels/` are public rendering inputs and are explicitly retained by `.gitignore`.

The existing statistical scripts use lifelines, Patsy, SciPy and statsmodels. They do not replace the packages' Cox, OLS, contrast or BH implementations. The model-fitting and annotation scripts are copied from the frozen analysis workflow without changes to their statistical code.

Use the two root-level `reproduce_*.py` commands for the current figures. Historical standalone forest, duplicate RCS and unused diagnostic plotting scripts are excluded from this release. The shared network legend is generated from the network colour table, rather than loaded from an additional prebuilt PDF.

Keep the complete `Cox`, `MLR`, `Figures` and `docs` directories and the root-level entry points, requirements, manifest and ignore file together. The compressed full-test tables are retained to independently verify joint BH-FDR; significant-only tables cannot replace them. The plotting input copies under `Figures/data` are intentional so that the drawing package remains self-contained.

## Analysis scope

| Analysis | Sample | Multiple-testing family | Significant records |
| --- | --- | --- | --- |
| Cox, duration per 10 min/week | 94,536; 735 events | 11 narrow bands; overall comparator unadjusted | See Cox results |
| RCS nonlinearity | Same cohort | 10 eligible narrow bands; overall comparator unadjusted | Seven narrow bands |
| SC Model 1, PA main association | 189; 73 MDD, 116 HC | 11 × 19,319 = 212,509 tests | 86; 79 unique connections |
| SC Model 2, PA × group | Same imaging sample | Separate family of 212,509 tests | 34; 25 unique connections |

Both imaging models adjust for ten covariate concepts, including smoking and alcohol. PA duration and SC weights are standardized across the imaging sample. Model 1 does not include group; Model 2 adds group (HC=0, MDD=1) and PA × group. Supplementary group-specific P values are BH-adjusted separately within each band and group across 19,319 edges. Confidence intervals are ordinary 95% intervals, not simultaneous intervals.

A record is a band–edge combination. A unique connection is counted once across bands. The network matrices contain all significant unique connections, without Top50 selection. Positive interactions indicate a higher PA–SC coefficient in MDD, not a proven treatment effect.

## Access, attribution and reuse

See [data access and terms](docs/DATA_ACCESS_AND_TERMS.md), [data dictionary](docs/DATA_DICTIONARY.md), and [reproduction instructions](docs/REPRODUCTION.md).

UK Biobank access is controlled. Atlas resources retain the Brainnetome Center's terms and are not relicensed as project code. A project-code license has not been assigned in this local release; public hosting must not be interpreted as a blanket reuse license. No publication DOI or repository URL is invented here.
