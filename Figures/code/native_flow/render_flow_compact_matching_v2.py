"""Cohort-flow revision: explicitly distinguish candidate and matched controls.

Contract: A retains all original counts; B begins with 735 incident MDD cases
and 93,801 non-event participants, matching produces 733 controls, then 189
have usable dMRI. No invented matching ratio or diagnostic eligibility rule.
Reuse the existing editable vector renderer. No inter-panel connector.
Native combined canvas: 190 x 155 mm, 7.5 pt Arial; exclusion callouts 7 pt.
No illustrative glyph is needed for participant count bookkeeping.
"""
from pathlib import Path
import argparse
import json
import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
from PIL import Image
from render_flow_AB_refined import Panel, LIGHT, HIGHLIGHT

OUT = Path(__file__).resolve().parent / 'flow_compact_matching_v2'
OUT.mkdir(exist_ok=True)


def box(p, name, x, y, w, h, text, **kwargs):
    p.box(name, x, y, w, h, text, fs=kwargs.pop('fs', 7.5), **kwargs)


def draw_a(p):
    box(p, 'initial', 33, 9, 75, 9, '103,687 participants with accelerometer records')
    box(p, 'quality', 33, 22, 75, 18,
        'Accelerometer Data Quality Control\nAdequate wear time\nValid device calibration\nMean acceleration \u2264 100 mg', fill='white')
    box(p, 'mdd-records', 36, 47, 32, 16,
        '2,592 participants\nwith ICD-10 F32/F33\nhospital-recorded MDD')
    box(p, 'non-incident', 73, 47, 32, 16,
        '101,095 participants\nwithout incident MDD\nduring follow-up')
    box(p, 'prevalent-exclusion', 2, 64, 29, 18,
        'Excluded: n = 1,788\nMDD diagnosed on or\nbefore wear completion', fs=7, fill='white')
    box(p, 'incident', 36, 84, 32, 12,
        '804 incident MDD cases\nafter wear completion')
    box(p, 'case-qc-exclusion', 2, 98, 29, 18,
        'Excluded: n = 69\nFailed accelerometer\nquality control', fs=7, fill='white')
    box(p, 'control-qc-exclusion', 95, 64, 27, 18,
        'Excluded: n = 7,294\nFailed accelerometer\nquality control', fs=7, fill='white')
    box(p, 'final-mdd', 36, 119, 32, 12, '735 final incident\nMDD cases')
    box(p, 'final-control', 73, 119, 32, 12, '93,801 final\nnon-event participants')
    box(p, 'final-cohort', 47, 141, 47, 10, '94,536 participants', fill=HIGHLIGHT, bold=True)
    p.edge([(70.5,18),(70.5,22)])
    p.edge([(70.5,40),(70.5,43)], False)
    p.edge([(70.5,43),(52,43),(52,47)])
    p.edge([(70.5,43),(89,43),(89,47)])
    p.edge([(52,63),(52,84)])
    p.edge([(31,73),(52,73)], meaning='exclusion callout')
    p.edge([(52,96),(52,119)])
    p.edge([(31,107),(52,107)], meaning='exclusion callout')
    p.edge([(89,63),(89,119)])
    p.edge([(95,73),(89,73)], meaning='exclusion callout')
    p.edge([(52,131),(52,136),(70.5,136)], False)
    p.edge([(89,131),(89,136),(70.5,136)], False)
    p.edge([(70.5,136),(70.5,141)])


def draw_b(p):
    box(p, 'source-mdd', 1, 9, 27, 17, '735 participants\nwith incident MDD')
    box(p, 'source-control', 33, 9, 27, 17, '93,801 non-event\nparticipants')
    box(p, 'matching', 6, 44, 49, 16,
        'Matching by age,\nsex, and ethnicity', fill='white')
    box(p, 'matched-mdd', 1, 77, 27, 16, '735 participants\nwith incident MDD')
    box(p, 'matched-control', 33, 77, 27, 16, '733 matched\ncontrols (HC)')
    box(p, 'matched-total', 6, 110, 49, 14, '1,468 matched participants\n(735 MDD; 733 HC)')
    box(p, 'imaging', 6, 141, 49, 10, '189 participants with\nusable dMRI data', fill=HIGHLIGHT)
    p.edge([(14.5,26),(14.5,35),(30.5,35)], False)
    p.edge([(46.5,26),(46.5,35),(30.5,35)], False)
    p.edge([(30.5,35),(30.5,44)])
    p.edge([(30.5,60),(30.5,68)], False)
    p.edge([(30.5,68),(14.5,68),(14.5,77)])
    p.edge([(30.5,68),(46.5,68),(46.5,77)])
    p.edge([(14.5,93),(14.5,101),(30.5,101)], False)
    p.edge([(46.5,93),(46.5,101),(30.5,101)], False)
    p.edge([(30.5,101),(30.5,110)])
    p.edge([(30.5,124),(30.5,141)])


def export(fig, name, full):
    stem = OUT/name
    fig.savefig(str(stem)+'_preview.png', dpi=220, facecolor='white')
    fig.savefig(stem.with_suffix('.svg'), facecolor='white')
    fig.savefig(stem.with_suffix('.pdf'), facecolor='white')
    root = ET.parse(stem.with_suffix('.svg'))
    labels = ' '.join(''.join(e.itertext()) for e in root.iter('{http://www.w3.org/2000/svg}text'))
    assert all(t not in labels.lower() for t in ('dataset', 'participant screening', 'matching and imaging'))
    if '1B_' in name or '1AB_' in name:
        assert '93,801' in labels and '733 matched' in labels and 'incident MDD' in labels
    audit = {'file': name, 'size_mm': [round(v*25.4,2) for v in fig.get_size_inches()]}
    if full:
        target = str(stem)+'_1200dpi.tiff'
        fig.savefig(target, dpi=1200, facecolor='white', pil_kwargs={'compression':'tiff_lzw'})
        with Image.open(target) as im:
            rgb = im.convert('RGB')
        rgb.save(target, compression='tiff_lzw', dpi=(1200,1200))
        rgb.close()
        with Image.open(target) as im:
            assert im.mode == 'RGB' and im.info['dpi'] == (1200,1200)
            audit.update(pixels=im.size, dpi=[1200,1200])
    plt.close(fig)
    return audit


def main(full):
    assert 103687 == 2592+101095
    assert 2592-1788 == 804 and 804-69 == 735
    assert 101095-7294 == 93801 and 735+93801 == 94536
    assert 735+733 == 1468
    audits=[]
    for letter, width, draw in [('A',124,draw_a), ('B',61,draw_b)]:
        panel=Panel(letter,width,155)
        draw(panel)
        audits.append(panel.validate())
        audits.append(export(panel.fig,f'Figure_1{letter}_compact_matching_v2',full))
    fig=plt.figure(figsize=(190/25.4,155/25.4),facecolor='white')
    for letter,width,left,draw in [('A',124,0,draw_a),('B',61,129,draw_b)]:
        panel=Panel(letter,width,155)
        plt.close(panel.fig)
        panel.fig=fig
        panel.ax=fig.add_axes([left/190,0,width/190,1],xlim=(0,width),ylim=(155,0))
        panel.ax.set_axis_off()
        panel.ax.text(3,5,letter,ha='left',va='center',fontsize=13,fontweight='bold',color='#0c2b59')
        draw(panel)
        panel.validate()
    audits.append(export(fig,'Figure_1AB_compact_matching_v2',full))
    (OUT/'quality_checks.json').write_text(json.dumps(audits,indent=2),encoding='utf-8')
    print(json.dumps(audits,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--full',action='store_true')
    main(parser.parse_args().full)
