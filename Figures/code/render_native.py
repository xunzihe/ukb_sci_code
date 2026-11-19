"""Run the existing approved plotting modules with explicit input/output paths."""
from pathlib import Path
import argparse
import sys
import importlib.util
import os
os.environ.setdefault('MPLBACKEND', 'Agg')
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('figure', choices=['flow'])
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    if args.figure == 'flow':
        sys.path.insert(0, str(HERE / 'native_flow'))
        import render_flow_font9pt_v7 as driver
        base = driver.base
        base.EXCLUSION = base.MATCHING = 9.0
        base.EXCLUSION_LEADING = base.MATCHING_LEADING = 12.2
        base.AW = 142
        base.TAG = 'font9pt_v7'
        base.OUT = output
        base.LargePanel = driver.NinePointPanel
        # Preserve all original drawing/geometry checks. Use the shared export
        # dependency instead of the old machine-specific PDF QA directory.
        def export(fig, name, full):
            fig.savefig(output / (name + '.pdf'), facecolor='white')
            fig.savefig(output / (name + '.svg'), facecolor='white')
            result = dict(name=name, size_mm=[round(v * 25.4, 2) for v in fig.get_size_inches()])
            plt.close(fig)
            return result
        base.export = export
        base.main(False)

if __name__ == '__main__':
    main()
