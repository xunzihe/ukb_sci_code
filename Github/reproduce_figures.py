"""Call the existing study plotting functions on public aggregate results."""
import argparse
import importlib.util
from pathlib import Path
import shutil
import sys

import matplotlib
matplotlib.use('Agg')
import pandas as pd

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parent


def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    result=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,default=ROOT/'outputs/figures')
    args=parser.parse_args()
    dest=args.output.resolve()
    dest.mkdir(parents=True,exist_ok=True)
    sys.path.insert(0,str(ROOT/'Cox/01_Code'))
    forest=module('release_cox_forest',ROOT/'Cox/01_Code/make_forest.py')
    forest.main()
    shutil.copy2(ROOT/'Cox/02_Results/figures/Cox_forest_per10.pdf',dest/'Cox_forest_per10.pdf')
    curves=module('release_cox_curves',ROOT/'Cox/01_Code/make_figures.py')
    curves.OUT=dest
    curves.INTERNAL=dest/'reproduction_metadata'
    curves.INTERNAL.mkdir(exist_ok=True)
    curves.main()
    plots=module('release_mlr_plots',ROOT/'MLR/01_Code/figure_functions.py')
    matrices={m:pd.read_csv(ROOT/f'MLR/02_Results/{m}_network_matrix_unique.csv',index_col=0)
              for m in ['Model1','Model2']}
    plots.matrix_plot(matrices,dest/'SC_all_unique_network_matrices')
    print(f'Quantitative figures saved to {dest}')


if __name__=='__main__':
    main()
