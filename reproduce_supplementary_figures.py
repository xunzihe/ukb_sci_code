"""Reproduce the overall-MPA RCS (SDC2) and three narrow-band RCS curves (SDC5)."""
from pathlib import Path
import argparse
import subprocess
import sys

ROOT=Path(__file__).resolve().parent

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,default=ROOT/'outputs/supplementary_figures')
    args=parser.parse_args()
    subprocess.run([sys.executable,str(ROOT/'Figures/code/reproduce_supplementary_figures.py'),
                    '--output',str(args.output.resolve())],check=True)

if __name__=='__main__':main()
