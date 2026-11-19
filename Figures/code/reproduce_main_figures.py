"""Reproduce the main figures without refitting statistical models."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import sys
import gc
import shutil
import numpy as np
import pandas as pd
import pymupdf as fitz
from PIL import Image
import compose_current_figures as current

ROOT = Path(__file__).resolve().parents[1]
PT_MM = 72 / 25.4

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def verify_brain_inputs():
    reports = {}
    for name, term, nrecords, nedge in [('Model1','PA',86,79),('Model2','Int',34,25)]:
        df = pd.read_csv(ROOT / f'data/mlr/{name}_all_significant_annotated.csv')
        assert len(df) == nrecords and df.edge_key.nunique() == nedge
        assert (df[f't_{term}'] > 0).all() and (df.p_FDR_global_11bands < .05).all()
        selected = df.assign(_abs=df[f't_{term}'].abs()).sort_values(
            ['_abs','PA_variable','edge'], ascending=[False,True,True]).drop_duplicates('edge_key')
        matrix = np.loadtxt(ROOT / f'brain/{name}/inputs/connectome.edge')
        expected = np.zeros((246,246))
        for row in selected.itertuples():
            i,j=row.ROI_i-1,row.ROI_j-1
            expected[i,j]=expected[j,i]=round(getattr(row,f't_{term}'),2)
        np.testing.assert_array_equal(matrix,expected)
        reports[name]=dict(records=nrecords,unique_edges=nedge,
                           statistic=f't_{term}',minimum_t=float(selected[f't_{term}'].min()),
                           maximum_t=float(selected[f't_{term}'].max()))
    return reports

def normalize_pdf(source, output):
    with fitz.open(source) as document, fitz.open() as target:
        assert len(document)==1
        old=document[0].rect
        width=166*PT_MM
        page=target.new_page(width=width,height=width*old.height/old.width)
        page.show_pdf_page(page.rect,document,0)
        target.save(output,garbage=4,deflate=True)

def export(pdf_path, output, dpi):
    with fitz.open(pdf_path) as document:
        assert len(document)==1
        page=document[0]
        pix=page.get_pixmap(dpi=dpi,colorspace=fitz.csRGB,alpha=False)
        image=Image.frombytes('RGB',(pix.width,pix.height),pix.samples)
        image.save(output,compression='tiff_lzw',dpi=(dpi,dpi))
        image.close()
        del pix
        info=dict(width_mm=page.rect.width/PT_MM,height_mm=page.rect.height/PT_MM,
                  dpi=dpi,mode='RGB',pages=1,sha256=sha(output))
        page.get_pixmap(dpi=150,alpha=False).save(pdf_path.with_name(pdf_path.stem+'_preview.png'))
    gc.collect()
    return info

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,default=ROOT/'outputs')
    parser.add_argument('--dpi',type=int,default=1200)
    parser.add_argument('--figure3-dpi',type=int,default=600,
                        help='Combined brain/matrix TIFF resolution; minimum 600 dpi. PDF paths stay vector.')
    parser.add_argument('--rebuild-brain',action='store_true')
    parser.add_argument('--brainnet-root',type=Path)
    parser.add_argument('--matlab',default='matlab')
    parser.add_argument('--figure3-layout', choices=['separate', 'combined'], default='combined',
                        help='One A-D page with A/B above C/D (default), or separate assembly components.')
    args=parser.parse_args()
    assert args.dpi>=1200
    assert args.figure3_dpi>=600
    output=args.output.resolve()
    output.mkdir(parents=True,exist_ok=True)
    work=output/'reproduction_details'
    work.mkdir(exist_ok=True)
    numeric=verify_brain_inputs()
    for name in ['flow']:
        subprocess.run([sys.executable,str(ROOT/'code/render_native.py'),name,
                        '--output',str(work/name)],check=True)
    sources={1:work/'flow/Figure_1AB_font9pt_v7.pdf'}
    info={}
    for index,source in sources.items():
        pdf=output/f'Figure_{index}.pdf'
        normalize_pdf(source,pdf)
        info[f'Figure_{index}']=export(pdf,output/f'Figure_{index}.tiff',args.dpi)
    panels={name:ROOT/f'brain/approved_panels/{name}_brain_connectome_3D.pdf' for name in ['Model1','Model2']}
    if args.rebuild_brain:
        if args.brainnet_root is None:
            raise ValueError('--brainnet-root is required when rebuilding BrainNet renders')
        brainwork=work/'brain'
        shutil.copytree(ROOT/'brain',brainwork,dirs_exist_ok=True)
        for name in ['Model1','Model2']:
            config=brainwork/name/'inputs/render_settings.json'
            settings=json.loads(config.read_text())
            settings['brainnet_root']=args.brainnet_root.resolve().as_posix()
            settings['surface_file']=(args.brainnet_root.resolve()/'Data/SurfTemplate/BrainMesh_ICBM152_smoothed.nv').as_posix()
            config.write_text(json.dumps(settings,indent=2),encoding='utf-8')
        command="run('"+(brainwork/'code/render_models.m').as_posix()+"')"
        subprocess.run([args.matlab,'-batch',command],check=True)
        for name in ['Model1','Model2']:
            subprocess.run([sys.executable,str(brainwork/'code/compose_models.py'),name],check=True)
            panels[name]=brainwork/name/'outputs'/f'{name}_brain_connectome_3D.pdf'
    composition=work/'current_layout'
    composition.mkdir(exist_ok=True)
    stats=pd.read_csv(ROOT/'data/cox/rcs_nonlinearity_results.csv').set_index('feature')
    cox=current.combined_cox(ROOT,composition,stats)
    for index,name in [(2,'Figure_2_combined')]:
        pdf=output/f'Figure_{index}.pdf'
        shutil.copy2(composition/(name+'.pdf'),pdf)
        info[f'Figure_{index}']=export(pdf,output/f'Figure_{index}.tiff',args.dpi)
    if args.figure3_layout == 'combined':
        matrices=current.matrices(ROOT,composition)
        current.brain_four_panels(ROOT,composition,panels)
        pdf=output/'Figure_3.pdf'
        shutil.copy2(composition/'Figure_3_connectomes_and_matrices.pdf',pdf)
        info['Figure_3']=export(pdf,output/'Figure_3.tiff',args.figure3_dpi)
    else:
        command=[sys.executable,str(ROOT/'code/export_figure3_parts.py'),
                 '--output',str(output),'--dpi',str(args.dpi),
                 '--brain-panels-dir',str(panels['Model1'].parent)]
        if args.rebuild_brain:
            command += ['--model2-panel',str(panels['Model2'])]
        subprocess.run(command,check=True)
        split=json.loads((output/'verification/split_export_validation.json').read_text())
        matrices=split['matrix_counts']
        info.update(split['exports'])
    report=dict(figures=info,brain_numeric_checks=numeric,models_refitted=False,
                brain_rendering='rerendered' if args.rebuild_brain else 'approved source panels',
                cox_layout=cox,network_matrices=matrices,
                figure3_layout=args.figure3_layout,
                note='Fig1: sample flow. Fig2: forest and seven RCS curves. Fig3: anatomical A/B and matrix C/D components. Three other narrow-band RCS curves form SDC5.')
    (output/'reproduction_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))

if __name__=='__main__':
    main()
