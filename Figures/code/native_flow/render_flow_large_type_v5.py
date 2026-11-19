"""Larger main text, smaller exclusions; identical physical type in A, B and AB.

Contract: preserve v4 content, arrow semantics, colors and external matching label.
Main 10 pt (was 7.5); exclusions 7 pt; fixed leading within each hierarchy.
Widen nodes instead of squeezing text or scaling the combined panel down.
Keep outlined Arial in TIFF/PDF/SVG for identical glyph placement everywhere.
"""
from pathlib import Path
import argparse
import json
import math
import sys
import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from PIL import Image
import render_flow_AB_typography_v3 as base
from render_flow_AB_refined import Panel

OUT=base.HERE/'flow_large_type_v5'
OUT.mkdir(exist_ok=True)
MAIN=10.0
EXCLUSION=7.0
EXCLUSION_LEADING=9.4
MATCHING=MAIN
MATCHING_LEADING=13.4
TAG='large_type_v5'
HEIGHT=176
AW,BW,GAP=134,77,5


class LargePanel(base.StrictPanel):
    def __init__(self,fig,letter,left,width,total_width):
        self.fig,self.letter,self.width,self.height=fig,letter,width,HEIGHT
        self.ax=fig.add_axes([left/total_width,0,width/total_width,1],
                            xlim=(0,width),ylim=(HEIGHT,0))
        self.ax.set_axis_off()
        self.nodes,self.routes,self.texts,self.typography=[],[],[],[]
        self.label('panel-letter',3,5,letter,bold=True)

    def label(self,name,cx,cy,text,bold=False,size=None,rect=None):
        excluded='exclusion' in name or name=='unusable'
        size=13 if name=='panel-letter' else EXCLUSION if excluded else MATCHING if name=='matching-annotation' else MAIN
        leading=EXCLUSION_LEADING if excluded else MATCHING_LEADING if name=='matching-annotation' else 13.4
        original=base.LEADING
        try:
            base.LEADING=leading
            super().label(name,cx,cy,text,bold=bold,size=size,rect=rect)
        finally:
            base.LEADING=original

    def box(self,name,x,y,w,h,text,fill=base.LIGHT,bold=False):
        self.ax.add_patch(FancyBboxPatch((x,y),w,h,
            boxstyle='round,pad=0,rounding_size=1.3',linewidth=.9,
            edgecolor=base.BLUE,facecolor=fill,zorder=3))
        self.nodes.append((name,x,y,w,h,text))
        self.label(name,x+w/2,y+h/2,text,bold=bold,rect=(x,y,w,h))

    def edge(self,points,arrow=True,meaning='sequence'):
        Panel.edge(self,points,arrow,meaning)

    def validate(self):
        min_pad=1e6
        for name,(x0,y0,x1,y1),rect in self.texts:
            assert 0<=x0<x1<=self.width and 0<=y0<y1<=self.height,(name,'canvas')
            if rect:
                x,y,w,h=rect
                pad=min(x0-x,x+w-x1,y0-y,y+h-y1)
                min_pad=min(min_pad,pad)
                assert pad>=1.3,(name,'text padding',pad)
        for i,(name,x,y,w,h,_) in enumerate(self.nodes):
            for other,xx,yy,ww,hh,_ in self.nodes[i+1:]:
                assert x+w<=xx or xx+ww<=x or y+h<=yy or yy+hh<=y,(name,other)
        obstacles=[(n,x,y,x+w,y+h) for n,x,y,w,h,_ in self.nodes]
        obstacles += [(n,*bounds) for n,bounds,_ in self.texts]
        for points,_ in self.routes:
            for (x1,y1),(x2,y2) in zip(points,points[1:]):
                assert x1==x2 or y1==y2
                for name,l,t,r,b in obstacles:
                    if x1==x2:
                        collision=l+.05<x1<r-.05 and max(min(y1,y2),t+.05)<min(max(y1,y2),b-.05)
                    else:
                        collision=t+.05<y1<b-.05 and max(min(x1,x2),l+.05)<min(max(x1,x2),r-.05)
                    assert not collision,(name,'connector collision',points)
        for entry in self.typography:
            name=entry['name']
            expected=13 if name=='panel-letter' else EXCLUSION if 'exclusion' in name or name=='unusable' else MATCHING if name=='matching-annotation' else MAIN
            assert entry['size_pt']==expected
            for x,y in zip(entry['baseline_y_mm'],entry['baseline_y_mm'][1:]):
                assert math.isclose((y-x)/base.PT_MM,entry['baseline_step_pt'],abs_tol=1e-10)
        return {'panel':self.letter,'main_pt':MAIN,'exclusion_pt':EXCLUSION,'matching_pt':MATCHING,
                'minimum_text_padding_mm':round(min_pad,3),'box_overlaps':0,
                'connector_collisions':0,'typography':self.typography}


def draw_a(p):
    p.box('initial',29,9,98,10,'103,687 participants with accelerometer records')
    p.box('quality',29,24,98,22,'Accelerometer Data Quality Control\nAdequate wear time\nValid device calibration\nMean acceleration \u2264 100 mg',fill='white')
    p.box('mdd-records',34,54,41,20,'2,592 participants\nwith ICD-10 F32/F33\nhospital-recorded MDD')
    p.box('non-incident',81,54,41,20,'101,095 participants\nwithout incident MDD\nduring follow-up')
    p.box('prevalent-exclusion',2,75,28,18,'Excluded: n = 1,788\nMDD diagnosed on or\nbefore wear completion',fill='white')
    p.box('incident',34,98,41,14,'804 incident MDD cases\nafter wear completion')
    p.box('case-qc-exclusion',2,113,28,18,'Excluded: n = 69\nFailed accelerometer\nquality control',fill='white')
    p.box('control-qc-exclusion',106,75,26,18,'Excluded: n = 7,294\nFailed accelerometer\nquality control',fill='white')
    p.box('final-mdd',34,135,41,14,'735 final incident\nMDD cases')
    p.box('final-control',81,135,41,14,'93,801 final\nnon-case participants')
    p.box('final-cohort',48,160,60,12,'94,536 participants',fill=base.HIGHLIGHT,bold=True)
    p.edge([(78,19),(78,24)])
    p.edge([(78,46),(78,50)],False)
    p.edge([(78,50),(54.5,50),(54.5,54)])
    p.edge([(78,50),(101.5,50),(101.5,54)])
    p.edge([(54.5,74),(54.5,98)])
    p.edge([(30,84),(54.5,84)],meaning='exclusion callout')
    p.edge([(54.5,112),(54.5,135)])
    p.edge([(30,122),(54.5,122)],meaning='exclusion callout')
    p.edge([(101.5,74),(101.5,135)])
    p.edge([(106,84),(101.5,84)],meaning='exclusion callout')
    p.edge([(54.5,149),(54.5,154),(78,154)],False)
    p.edge([(101.5,149),(101.5,154),(78,154)],False)
    p.edge([(78,154),(78,160)])


def draw_b(p):
    p.box('source-mdd',1,9,35,20,'735 participants\nwith incident MDD')
    p.box('source-control',41,9,35,20,'93,801 non-case\nparticipants')
    p.box('matched-total',6,73,65,16,'1,468 matched participants\n(735 MDD; 733 HC)')
    p.box('unusable',44,122,30,18,'Excluded:\nMissing data\nCorrupted data',fill='white')
    p.box('imaging',6,160,65,12,'189 participants with\nusable dMRI data',fill=base.HIGHLIGHT,bold=True)
    p.edge([(18.5,29),(18.5,38),(38.5,38)],False)
    p.edge([(58.5,29),(58.5,38),(38.5,38)],False)
    p.edge([(38.5,38),(38.5,73)])
    p.label('matching-annotation',59,54,'Matching by age,\nsex, and ethnicity')
    p.edge([(38.5,89),(38.5,160)])
    p.edge([(44,131),(38.5,131)],meaning='exclusion callout')


def export(fig,name,full):
    stem=OUT/name
    fig.savefig(str(stem)+'_preview.png',dpi=250,facecolor='white')
    fig.savefig(stem.with_suffix('.pdf'),facecolor='white')
    fig.savefig(stem.with_suffix('.svg'),facecolor='white')
    root=ET.parse(stem.with_suffix('.svg'))
    assert not list(root.iter('{http://www.w3.org/2000/svg}text'))
    assert not list(root.iter('{http://www.w3.org/2000/svg}image'))
    report={'name':name,'size_mm':[round(v*25.4,2) for v in fig.get_size_inches()]}
    if full:
        tif=str(stem)+'_1200dpi.tiff'
        fig.savefig(tif,dpi=1200,facecolor='white',pil_kwargs={'compression':'tiff_lzw'})
        with Image.open(tif) as im: rgb=im.convert('RGB')
        rgb.save(tif,compression='tiff_lzw',dpi=(1200,1200)); rgb.close()
        with Image.open(tif) as im:
            assert im.info['dpi']==(1200,1200) and im.mode=='RGB'
            report.update(pixels=im.size,dpi=[1200,1200])
    plt.close(fig)
    sys.path.insert(0,str(base.HERE/'pdf_qa_deps'))
    import pypdfium2 as pdfium
    pdf=pdfium.PdfDocument(str(stem.with_suffix('.pdf')))
    page=pdf[0]; page.render(scale=250/72).to_pil().save(str(stem)+'_PDF_check.png')
    page.close(); pdf.close()
    return report


def main(full):
    assert 103687==2592+101095 and 2592-1788==804 and 804-69==735
    assert 101095-7294==93801 and 735+93801==94536 and 735+733==1468
    reports=[]; typography=[]; panels={}
    for letter,width,draw in [('A',AW,draw_a),('B',BW,draw_b)]:
        fig=plt.figure(figsize=(width/25.4,HEIGHT/25.4),facecolor='white')
        p=LargePanel(fig,letter,0,width,width); draw(p)
        typography.append(p.validate()); panels[letter]=p
        reports.append(export(fig,f'Figure_1{letter}_{TAG}',full))
    fig=plt.figure(figsize=((AW+GAP+BW)/25.4,HEIGHT/25.4),facecolor='white')
    for letter,width,left,draw in [('A',AW,0,draw_a),('B',BW,AW+GAP,draw_b)]:
        p=LargePanel(fig,letter,left,width,AW+GAP+BW); draw(p); p.validate()
        assert p.typography==panels[letter].typography,'Standalone/combined type mismatch'
    terminal_a=next(t for t in panels['A'].typography if t['name']=='final-cohort')
    terminal_b=next(t for t in panels['B'].typography if t['name']=='imaging')
    for key in ('font','size_pt','weight','baseline_step_pt'):
        assert terminal_a[key]==terminal_b[key]
    reports.append(export(fig,f'Figure_1AB_{TAG}',full))
    (OUT/'quality_checks.json').write_text(json.dumps({'exports':reports,'panels':typography},indent=2),encoding='utf-8')
    print(json.dumps(reports,indent=2)); print(f'Main text: {MAIN:g} pt; exclusions: {EXCLUSION:g} pt. All typography and geometry checks passed.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--full',action='store_true')
    main(parser.parse_args().full)
