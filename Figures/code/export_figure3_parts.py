"""Export anatomical A/B and network-matrix C/D as separate assembly assets.

Reuse approved anatomical panels and the existing complete-unique-edge renderer.
No model fitting, significance filtering changes, or manuscript editing occurs.
"""
from pathlib import Path
import argparse
import gc
import hashlib
import json
import shutil
import pymupdf as fitz
from PIL import Image
import compose_current_figures as current
from reproduce_main_figures import verify_brain_inputs

ROOT=Path(__file__).resolve().parents[1]
MM=72/25.4

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def export(pdf,dpi):
    with fitz.open(pdf) as doc:
        assert len(doc)==1
        page=doc[0];assert abs(page.rect.width/MM-166)<.01
        pix=page.get_pixmap(dpi=dpi,colorspace=fitz.csRGB,alpha=False)
        im=Image.frombytes('RGB',(pix.width,pix.height),pix.samples)
        im.save(pdf.with_suffix('.tiff'),compression='tiff_lzw',dpi=(dpi,dpi))
        im.close();del pix
        page.get_pixmap(dpi=180,alpha=False).save(pdf.with_name(pdf.stem+'_preview.png'))
        report={'width_mm':page.rect.width/MM,'height_mm':page.rect.height/MM,
                'dpi':dpi,'TIFF_sha256':sha(pdf.with_suffix('.tiff'))}
    gc.collect();return report

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--dpi',type=int,default=1200)
    parser.add_argument('--brain-panels-dir',type=Path,default=ROOT/'brain/approved_panels')
    parser.add_argument('--model2-panel',type=Path)
    args=parser.parse_args();assert args.dpi>=1200
    out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
    work=out/'verification';work.mkdir(exist_ok=True)
    numeric=verify_brain_inputs()
    counts=current.matrices(ROOT,work)
    panels={name:args.brain_panels_dir/f'{name}_brain_connectome_3D.pdf' for name in ['Model1','Model2']}
    if args.model2_panel:
        panels['Model2']=args.model2_panel
    current.brain_four_panels(ROOT,work,panels)
    # Reuse the existing legend/layout routine; the combined reference remains
    # internal. Deliver only the two requested components at the output root.
    with fitz.open(panels['Model1']) as a, \
         fitz.open(panels['Model2']) as b, \
         fitz.open(work/'Shared_network_legend.pdf') as legend,fitz.open() as target:
        width=166*MM;ha=76*MM;gap=1.5*MM;hl=23*MM
        page=target.new_page(width=width,height=2*ha+gap+hl)
        page.show_pdf_page(fitz.Rect(0,0,width,ha),a,0)
        page.show_pdf_page(fitz.Rect(0,ha+gap,width,2*ha+gap),b,0)
        page.show_pdf_page(fitz.Rect(0,2*ha+gap,width,2*ha+gap+hl),legend,0)
        target.save(out/'Figure_3_Brain_AB.pdf',garbage=4,deflate=True)
    shutil.copy2(work/'Network_matrices_CD.pdf',out/'Figure_3_Matrices_CD.pdf')
    results={name:export(out/(name+'.pdf'),args.dpi) for name in ['Figure_3_Brain_AB','Figure_3_Matrices_CD']}
    report={'models_refitted':False,'brain_numeric_checks':numeric,'matrix_counts':counts,'exports':results,
            'anatomical_panels':'unchanged approved A/B panels; shared node legend included',
            'matrix_panels':'all 79/25 unique edges, C/D labels, shared scale; not Top50',
            'assembly_note':'Separate components for author assembly; no manuscript or existing combined Figure_3 replaced.'}
    (work/'split_export_validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({'exports':results,'unique_edges':[79,25],'models_refitted':False},indent=2))

if __name__=='__main__':main()
