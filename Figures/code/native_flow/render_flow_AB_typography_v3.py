"""Publication revision: fixed font metrics, simplified B, explicit availability.

Contract: preserve A counts and palette; B: 735 incident cases + 93,801 non-event
participants -> matching annotation -> 1,468 matched -> usable dMRI -> 189.
Exclusion callout reasons are user-provided: missing data / corrupted data.
Alfaro-Almagro et al. (2018), PMC5770339, Data organization, supports terminology
only. It does not establish this study's reasons or category-specific counts.
No new exclusion count, matching ratio, QC threshold, or cause is inferred.

Typography contract: explicit Arial files; every body line is 7.5 pt with a
10.2 pt baseline interval. Use one normal ASCII space, no justification,
per-line stretching, mathtext, or fallback fonts. Render font outlines so TIFF,
PDF and SVG all use identical glyph placements and cannot reflow in WPS.
Preserve the existing code-native vector workflow and source scripts.
"""
from pathlib import Path
import argparse
import json
import math
import re
import sys
import xml.etree.ElementTree as ET
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.textpath import TextPath
from matplotlib.transforms import Affine2D
from matplotlib.patches import FancyBboxPatch, PathPatch
from matplotlib.ft2font import FT2Font
from PIL import Image
from render_flow_AB_refined import Panel, BLUE, TEXT, LIGHT, HIGHLIGHT
from render_flow_compact_matching_v2 import draw_a

HERE=Path(__file__).resolve().parent
OUT=HERE/'flow_AB_typography_v3'
OUT.mkdir(exist_ok=True)
STEM=OUT/'Figure_1AB_typography_v3'
FONT_SIZE=7.5
LEADING=10.2
PT_MM=25.4/72
REGULAR=Path('C:/Windows/Fonts/arial.ttf')
BOLD=Path('C:/Windows/Fonts/arialbd.ttf')
plt.rcParams.update({'text.usetex':False, 'path.simplify':False,
                     'svg.fonttype':'path', 'axes.unicode_minus':False})


class StrictPanel(Panel):
    def __init__(self,fig,letter,left,width):
        self.fig,self.letter,self.width,self.height=fig,letter,width,155
        self.ax=fig.add_axes([left/190,0,width/190,1],xlim=(0,width),ylim=(155,0))
        self.ax.set_axis_off()
        self.nodes,self.routes,self.texts=[],[],[]
        self.typography=[]
        self.label('panel-letter',3,5,letter,bold=True,size=13)

    def label(self,name,cx,cy,text,bold=False,size=FONT_SIZE,rect=None):
        assert not re.search(r'[^\S\n ]',text), ('Non-standard whitespace',name)
        assert '  ' not in text and all(s==s.strip() for s in text.split('\n'))
        fontfile=BOLD if bold else REGULAR
        prop=FontProperties(fname=str(fontfile),size=size)
        face=FT2Font(str(fontfile))
        for ch in text.replace('\n',''):
            assert ch==' ' or face.get_char_index(ord(ch)), ('Missing glyph',ch)
        paths=[TextPath((0,-i*LEADING),line,prop=prop,size=size,usetex=False)
               for i,line in enumerate(text.split('\n'))]
        # Centre the whole block vertically, but use identical baseline steps.
        ymin=min(p.get_extents().y0 for p in paths)
        ymax=max(p.get_extents().y1 for p in paths)
        baseline_origin=cy+(ymin+ymax)*PT_MM/2
        for i,path in enumerate(paths):
            bounds=path.get_extents()
            tx=cx-(bounds.x0+bounds.x1)*PT_MM/2
            transform=Affine2D().scale(PT_MM,-PT_MM).translate(tx,baseline_origin)
            artist=PathPatch(path,transform=transform+self.ax.transData,
                             facecolor=TEXT,edgecolor='none',linewidth=0,zorder=5)
            artist.set_gid(f'{self.letter}-{name}-line-{i}')
            self.ax.add_patch(artist)
            extent=transform.transform_bbox(bounds)
            x0,x1=sorted((extent.x0,extent.x1)); y0,y1=sorted((extent.y0,extent.y1))
            self.texts.append((name,(x0,y0,x1,y1),rect))
        self.typography.append({'name':name,'text':text,'font':str(fontfile),
             'size_pt':size,'weight':'bold' if bold else 'regular',
             'baseline_step_pt':LEADING,'baseline_y_mm':[
                 baseline_origin+i*LEADING*PT_MM for i in range(len(paths))]})

    def box(self,name,x,y,w,h,text,fs=FONT_SIZE,fill=LIGHT,bold=False):
        # Widen one callout to keep the now-uniform type size, not shrink its font.
        if name=='prevalent-exclusion': x,w=1,30
        if name=='control-qc-exclusion': x,w=93,29
        self.ax.add_patch(FancyBboxPatch((x,y),w,h,
            boxstyle='round,pad=0,rounding_size=1.3',linewidth=.9,
            edgecolor=BLUE,facecolor=fill,zorder=3))
        self.nodes.append((name,x,y,w,h,text))
        self.label(name,x+w/2,y+h/2,text,bold=bold,rect=(x,y,w,h))

    def edge(self,points,arrow=True,meaning='sequence'):
        if points==[(95,73),(89,73)]: points=[(93,73),(89,73)]
        super().edge(points,arrow,meaning)

    def validate(self):
        min_padding=1e6
        for name,(x0,y0,x1,y1),rect in self.texts:
            assert 0<=x0<x1<=self.width and 0<=y0<y1<=self.height, (name,'canvas')
            if rect:
                x,y,w,h=rect
                pad=min(x0-x,x+w-x1,y0-y,y+h-y1)
                min_padding=min(min_padding,pad)
                assert pad>=1.2,(name,'padding',pad)
        for i,(name,x,y,w,h,_) in enumerate(self.nodes):
            for other,xx,yy,ww,hh,_ in self.nodes[i+1:]:
                assert x+w<=xx or xx+ww<=x or y+h<=yy or yy+hh<=y,(name,other)
        for points,meaning in self.routes:
            for (x1,y1),(x2,y2) in zip(points,points[1:]):
                assert x1==x2 or y1==y2
                # Protect all text, including the two frameless edge annotations.
                obstacles=[(n,x,y,x+w,y+h) for n,x,y,w,h,_ in self.nodes]
                obstacles += [(n,x0,y0,x3,y3) for n,(x0,y0,x3,y3),_ in self.texts]
                for name,l,t,r,b in obstacles:
                    if x1==x2:
                        collision=l+.05<x1<r-.05 and max(min(y1,y2),t+.05)<min(max(y1,y2),b-.05)
                    else:
                        collision=t+.05<y1<b-.05 and max(min(x1,x2),l+.05)<min(max(x1,x2),r-.05)
                    assert not collision,(name,'route collision',points)
        for entry in self.typography:
            if entry['name']=='panel-letter': continue
            assert entry['size_pt']==FONT_SIZE
            baselines=entry['baseline_y_mm']
            for x,y in zip(baselines,baselines[1:]):
                assert math.isclose((y-x)/PT_MM,LEADING,abs_tol=1e-10)
        return {'panel':self.letter,'body_font_pt':FONT_SIZE,
                'baseline_step_pt':LEADING,'minimum_text_padding_mm':round(min_padding,3),
                'box_overlaps':0,'connector_text_or_box_collisions':0,
                'typography':self.typography}


def draw_b(p):
    p.box('source-mdd',1,9,27,17,'735 participants\nwith incident MDD')
    p.box('source-control',33,9,27,17,'93,801 non-event\nparticipants')
    p.box('matched-total',6,64,49,14,'1,468 matched participants\n(735 MDD; 733 HC)')
    p.box('unusable',35,109,25,20,'Excluded:\nMissing data\nCorrupted data',fill='white')
    p.box('imaging',6,141,49,10,'189 participants with\nusable dMRI data',fill=HIGHLIGHT,bold=True)
    p.edge([(14.5,26),(14.5,35),(30.5,35)],False)
    p.edge([(46.5,26),(46.5,35),(30.5,35)],False)
    p.edge([(30.5,35),(30.5,43)],False)
    # Line is intentionally interrupted by its annotation: no surrounding box.
    p.label('matching-annotation',30.5,48,'Matching by age,\nsex, and ethnicity')
    p.edge([(30.5,53),(30.5,64)])
    p.edge([(30.5,78),(30.5,89)],False)
    p.label('availability-annotation',30.5,94,'Availability of\nusable dMRI data')
    p.edge([(30.5,99),(30.5,141)])
    p.edge([(35,119),(30.5,119)],meaning='exclusion callout into availability filter')


def main(full=False):
    assert 103687==2592+101095
    assert 2592-1788==804 and 804-69==735
    assert 101095-7294==93801 and 735+93801==94536 and 735+733==1468
    fig=plt.figure(figsize=(190/25.4,155/25.4),facecolor='white')
    a=StrictPanel(fig,'A',0,124); draw_a(a)
    b=StrictPanel(fig,'B',129,61); draw_b(b)
    reports=[a.validate(),b.validate()]
    afinal=next(t for t in a.typography if t['name']=='final-cohort')
    bfinal=next(t for t in b.typography if t['name']=='imaging')
    for k in ('font','size_pt','weight','baseline_step_pt'):
        assert afinal[k]==bfinal[k],('Terminal style mismatch',k)
    assert len(b.nodes)==5
    assert not any(n[0] in ('matching','matched-mdd','matched-control') for n in b.nodes)
    fig.savefig(str(STEM)+'_preview.png',dpi=300,facecolor='white')
    fig.savefig(STEM.with_suffix('.svg'),facecolor='white')
    fig.savefig(STEM.with_suffix('.pdf'),facecolor='white')
    root=ET.parse(STEM.with_suffix('.svg'))
    assert not list(root.iter('{http://www.w3.org/2000/svg}text')), 'SVG contains reflowable text'
    assert not list(root.iter('{http://www.w3.org/2000/svg}image')), 'SVG contains raster image'
    audit={'panels':reports,'canvas_mm':[190,155],
       'font_mode':'explicit Arial outlines; no substitution or text reflow',
       'terminal_styles_identical':True,
       'reason_source':'https://pmc.ncbi.nlm.nih.gov/articles/PMC5770339/',
       'reason_counts':'not provided; not inferred'}
    if full:
        tif=str(STEM)+'_1200dpi.tiff'
        fig.savefig(tif,dpi=1200,facecolor='white',pil_kwargs={'compression':'tiff_lzw'})
        with Image.open(tif) as im: rgb=im.convert('RGB')
        rgb.save(tif,compression='tiff_lzw',dpi=(1200,1200)); rgb.close()
        with Image.open(tif) as im:
            assert im.mode=='RGB' and im.info['dpi']==(1200,1200)
            audit['tiff']={'pixels':im.size,'dpi':[1200,1200],'mode':im.mode}
    plt.close(fig)
    sys.path.insert(0,str(HERE/'pdf_qa_deps'))
    try:
        import pypdfium2 as pdfium
        pdf=pdfium.PdfDocument(str(STEM.with_suffix('.pdf')))
        page=pdf[0]
        preview=page.render(scale=300/72).to_pil()
        preview.save(str(STEM)+'_PDF_check.png')
        audit['pdf_rendered_for_visual_check']=True
        page.close(); pdf.close()
    except ImportError:
        audit['pdf_rendered_for_visual_check']=False
    (OUT/'typography_quality_checks.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in audit.items() if k!='panels'},indent=2))
    print('All font, whitespace, baseline, padding, count and collision checks passed.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--full',action='store_true')
    main(parser.parse_args().full)
