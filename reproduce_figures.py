"""Current Fig1-Fig3 main-figure entry point; statistical models are not refit."""
from pathlib import Path
import argparse
import subprocess
import sys

ROOT=Path(__file__).resolve().parent

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,default=ROOT/'outputs/main_figures')
    parser.add_argument('--dpi',type=int,default=1200)
    parser.add_argument('--figure3-dpi',type=int,default=600,
                        help='Combined brain/matrix TIFF resolution; minimum 600 dpi.')
    parser.add_argument('--figure3-layout',choices=['combined','separate'],default='combined',
                        help='One compact A-D page (default), or separate assembly components.')
    parser.add_argument('--rebuild-brain',action='store_true')
    parser.add_argument('--brainnet-root',type=Path)
    parser.add_argument('--matlab',default='matlab')
    args=parser.parse_args()
    cmd=[sys.executable,str(ROOT/'Figures/code/reproduce_main_figures.py'),
         '--output',str(args.output.resolve()),'--dpi',str(args.dpi),
         '--figure3-dpi',str(args.figure3_dpi),'--figure3-layout',args.figure3_layout]
    if args.rebuild_brain:
        cmd.extend(['--rebuild-brain','--matlab',args.matlab])
        if args.brainnet_root:
            cmd.extend(['--brainnet-root',str(args.brainnet_root.resolve())])
    subprocess.run(cmd,check=True)

if __name__=='__main__':main()
