"""Reproduce SDC2 and SDC5 using the retained RCS plotting functions."""
from pathlib import Path
import argparse
import json
import shutil
import pandas as pd
import pymupdf as fitz
import overall_rcs
import compose_current_figures as current

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=ROOT/'outputs/supplementary_figures')
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    work = out/'verification'
    work.mkdir(exist_ok=True)
    overall_rcs.OUT = out
    overall_rcs.INTERNAL = work/'SDC2'
    overall_rcs.main()
    stats = pd.read_csv(ROOT/'data/cox/rcs_nonlinearity_results.csv').set_index('feature')
    details = work/'SDC5'
    details.mkdir(parents=True, exist_ok=True)
    audit = current.other_rcs(ROOT, details, stats)
    shutil.copy2(details/'Supplementary_Figure_S2_RCS.pdf',
                 out/'Supplemental_Digital_Content_5_RCS_nonsignificant_bands.pdf')
    for pdf in out.glob('Supplemental_Digital_Content_*.pdf'):
        with fitz.open(pdf) as doc:
            assert len(doc) == 1
            doc[0].get_pixmap(dpi=150, alpha=False).save(work/(pdf.stem+'_preview.png'))
    (work/'source_checks.json').write_text(json.dumps(audit, indent=2), encoding='utf-8')
    print('SDC2 and SDC5 reproduced from saved curves; no models refitted.')

if __name__ == '__main__':
    main()
