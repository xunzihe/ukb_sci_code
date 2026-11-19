# Main and supplementary figure reproduction

Figure 1 consistently labels the 93,801 participants as non-case participants. Figure 2 displays small P values with a multiplication sign and superscript power of ten instead of e notation; numerical values and rounding precision are unchanged.

Figure 2A uses inward-pointing x-axis ticks, with numeric labels retained below the axis at their original positions. Figure 1 retains the original approved layout.

Figure 2B-H use inward-pointing x- and y-axis ticks, with numeric labels retained below and to the left at their original positions. Figure 3C/D omit all matrix-axis tick marks; labels, cell borders, counts and colour scales are unchanged. The original outward tick style is retained for the supplementary RCS figures.

This directory reproduces the current companion submission figures and the two supplemental figure PDFs. Statistical models are not refitted.

|Figure|Content|
|---|---|
|1|Cohort selection and imaging-sample flowchart; non-case terminology harmonized, layout unchanged|
|2|A: Cox HRs/95% CIs per 10 min/week for 11 narrow bands and overall MPA. B–H: seven RCS curves with significant nonlinearity|
|3|A/B: complete Model1/Model2 anatomical connectomes. C/D: corresponding lower-triangle network-count matrices|

Fig3 contains all 79 unique Model1 edges from 86 significant band–edge association records and all 25 unique Model2 edges from 34 significant band–edge interaction records. Each model uses joint BH-FDR across 11 × 19,319 = 212,509 tests. The matrices count unique edges once across bands, not association records; there is no Top50 selection. Their lower-triangle totals, including diagonals, are 79 and 25. Both matrices share a color scale. Subcortical regions form a separate anatomical category, not an eighth Yeo network.

The approved anatomical panels retain all 246 atlas nodes, equal edge radius, and t-statistic color encoding. The maximum absolute t statistic represents an edge significant in multiple bands. Color limits differ between Model1 and Model2. The node-network legend is shared. Positive interactions mean a higher PA–SC coefficient in MDD, not demonstrated treatment benefit.

Sample counts are omitted from the upper-right corners of the forest/RCS plots and retained in captions. Numerical estimates, CIs, curve values, tests and FDR corrections are unchanged. Fig. 2B-H show HR = 0.60 red horizontal dashed guides; red vertical guides, solid red intersection markers, and unboxed red labels give all crossing durations (min/week) within the displayed range. Duration labels retain the 6-point type size. These are interpolated point-estimate readouts relative to each band-specific reference, not treatment targets. No duration is extrapolated for a curve that does not reach HR = 0.60. The three SDC5 panels are unchanged.

## Reproduce

```sh
python -m pip install -r requirements-figures.txt
python code/reproduce_main_figures.py --output outputs
```

Default outputs are `Figure_1`, `Figure_2`, and `Figure_3`, as PDF and RGB LZW TIFF, plus previews and verification records. Figures 1 and 2 use 1200 dpi; the combined brain/matrix Figure 3 uses 600 dpi. Each has a width of 166 mm. Figure 3 is one compact 166 x 204 mm A-D page: anatomical panels A/B are above the C/D matrices. Colourbars move into the lateral-view whitespace, the shared node legend has two rows, and empty margins are cropped. All components are translated at unit scale: brain sizes, fonts, stroke widths, colours and statistics are unchanged. The PDF retains vector matrix cells and text, and the approved brain raster resolution. Add `--figure3-dpi 1200` for a larger TIFF, or `--figure3-layout separate` for the original assembly components.

`code/compose_current_figures.py` draws the combined Cox/RCS layout, full unique-edge matrices and shared node legend. `code/native_flow` retains the interdependent original flowchart modules. Superseded separate forest/RCS and two-panel-only assembly modules have been removed from this active package.

Default anatomical composition uses `brain/approved_panels/Model1_brain_connectome_3D.pdf` and the Model2 counterpart.

These are the only prebuilt PDFs required in this release. The shared network legend is regenerated from `brain/Model1/inputs/Network_color_key.csv`; no additional approved legend PDF is read. Main plotting reads the significant-record tables under `data/mlr`, so duplicate full-record CSVs are not needed in the model-specific brain input directories.

Full MATLAB/BrainNet rerendering remains optional:

```sh
python code/reproduce_main_figures.py --output outputs_rerendered --rebuild-brain --brainnet-root /path/to/BrainNetViewer_20191031 --matlab /path/to/matlab
```

BrainNet Viewer and MATLAB are external dependencies. Fig1 requires locally licensed Arial regular/bold fonts; see `code/native_flow/render_flow_AB_typography_v3.py` for font paths. Font files are not redistributed. Atlas coordinates are not participant locations; plotting edge weights are display t statistics, not individual SC weights.

The overall-MPA RCS remains SDC2. Three narrow-band RCS curves without significant evidence of nonlinearity form Figure S2/SDC5, not a main figure. Both PDFs can be generated using this package alone:

```sh
python code/reproduce_supplementary_figures.py --output outputs/supplementary_figures
```

`code/overall_rcs.py` retains the existing overall-MPA RCS renderer; only its input/output paths were adapted. SDC5 uses `other_rcs` in `code/compose_current_figures.py`. Both read saved curves and test results. Word/Excel attachments are separate from this code package. No participant-level UK Biobank data are included.

Source hashes and layout changes are documented in `code_provenance.json`, checks in `reproduction_validation.json`, and package hashes in `SHA256SUMS.json`.

## Separate Fig3 components for author assembly

```sh
python code/export_figure3_parts.py --output outputs/figure3_parts
```

This optional command exports `Figure_3_Brain_AB` and `Figure_3_Matrices_CD` as PDF/1200-dpi TIFF, plus PNG previews. A/B retain the node-network legend; C/D retain the common count scale and all 79/25 unique edges. Submit the combined `Figure_3` rather than uploading the component files as additional figures. These scripts do not edit the manuscript.
