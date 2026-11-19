"""Independent cohort-flow panels; all geometry in millimetres.

Contract: A documents cohort screening; B documents matching and dMRI availability.
No inter-panel edge and no assertion of independent/non-overlapping cohorts.
Exclusion arrows are callouts INTO filtering junctions, as requested, not enrolment.
Existing matplotlib vector source is retained; no synthetic participant imagery.
Grid: A has two main lanes and side callouts in dedicated between-step rows.
Export: 9 pt Arial body, 8.5 pt callouts, uniform 1.25 line spacing; RGB 1200 dpi.
"""
from pathlib import Path
import argparse
import json
import xml.etree.ElementTree as ET
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from PIL import Image

OUT = Path(__file__).resolve().parent / 'flow_AB_refined'
OUT.mkdir(exist_ok=True)
BLUE, TEXT, LIGHT, HIGHLIGHT = '#3878d5', '#0c2b59', '#f8fbff', '#d9e7fa'
plt.rcParams.update({'font.family': 'Arial', 'pdf.fonttype': 42,
                     'svg.fonttype': 'none', 'text.usetex': False})


class Panel:
    def __init__(self, letter, width, height):
        self.letter, self.width, self.height = letter, width, height
        self.fig = plt.figure(figsize=(width/25.4, height/25.4), facecolor='white')
        self.ax = self.fig.add_axes([0, 0, 1, 1], xlim=(0, width), ylim=(height, 0))
        self.ax.set_axis_off()
        self.nodes, self.routes, self.texts = [], [], []
        self.ax.text(3, 5, letter, ha='left', va='center', fontsize=13,
                     fontweight='bold', color=TEXT)

    def box(self, name, x, y, w, h, text, fs=9, fill=LIGHT, bold=False):
        self.ax.add_patch(FancyBboxPatch((x, y), w, h,
            boxstyle='round,pad=0,rounding_size=1.3', linewidth=.9,
            edgecolor=BLUE, facecolor=fill, zorder=3))
        txt = self.ax.text(x+w/2, y+h/2, text, ha='center', va='center',
            fontsize=fs, fontweight='bold' if bold else 'normal', color=TEXT,
            linespacing=1.25, zorder=4)
        self.nodes.append((name, x, y, w, h, text))
        self.texts.append((name, (x, y, w, h), txt))

    def edge(self, points, arrow=True, meaning='sequence'):
        self.routes.append((points, meaning))
        if len(points) > 2:
            self.ax.plot(*zip(*points[:-1]), color=BLUE, lw=.85, zorder=2)
        a, b = points[-2:]
        if arrow:
            self.ax.add_patch(FancyArrowPatch(a, b, arrowstyle='-|>',
                mutation_scale=8, linewidth=.85, color=BLUE,
                shrinkA=0, shrinkB=0, zorder=2))
        else:
            self.ax.plot([a[0], b[0]], [a[1], b[1]], color=BLUE, lw=.85, zorder=2)

    def validate(self):
        self.fig.canvas.draw()
        renderer = self.fig.canvas.get_renderer()
        for name, (x, y, w, h), txt in self.texts:
            ext = txt.get_window_extent(renderer).transformed(self.ax.transData.inverted())
            left, right = sorted((ext.x0, ext.x1))
            top, bottom = sorted((ext.y0, ext.y1))
            assert left >= x+1.5 and right <= x+w-1.5, (name, 'horizontal padding', left, right)
            assert top >= y+1.5 and bottom <= y+h-1.5, (name, 'vertical padding')
            assert '  ' not in txt.get_text() and '\t' not in txt.get_text()
        for i, (name, x, y, w, h, _) in enumerate(self.nodes):
            for other, xx, yy, ww, hh, _ in self.nodes[i+1:]:
                assert x+w <= xx or xx+ww <= x or y+h <= yy or yy+hh <= y, (name, other)
            for points, meaning in self.routes:
                for (x1, y1), (x2, y2) in zip(points, points[1:]):
                    assert x1 == x2 or y1 == y2, 'Non-orthogonal route'
                    if x1 == x2:
                        collision = x+.1 < x1 < x+w-.1 and max(min(y1,y2), y+.1) < min(max(y1,y2), y+h-.1)
                    else:
                        collision = y+.1 < y1 < y+h-.1 and max(min(x1,x2), x+.1) < min(max(x1,x2), x+w-.1)
                    assert not collision, (name, 'connector intersects box', points)
        return {'panel': self.letter, 'nodes': len(self.nodes), 'routes': len(self.routes),
                'text_padding_mm': 1.5, 'line_spacing': 1.25,
                'box_overlaps': 0, 'connector_box_collisions': 0}

    def save(self, full=False):
        audit = self.validate()
        stem = OUT / f'Figure_1{self.letter}_refined'
        self.fig.savefig(str(stem)+'_preview.png', dpi=180, facecolor='white')
        self.fig.savefig(stem.with_suffix('.svg'), facecolor='white')
        self.fig.savefig(stem.with_suffix('.pdf'), facecolor='white')
        svg = ET.parse(stem.with_suffix('.svg'))
        labels = ' '.join(''.join(e.itertext()) for e in svg.iter('{http://www.w3.org/2000/svg}text'))
        assert all(s not in labels.lower() for s in ('dataset', 'participant screening', 'matching and imaging'))
        if full:
            path = str(stem)+'_1200dpi.tiff'
            self.fig.savefig(path, dpi=1200, facecolor='white', pil_kwargs={'compression': 'tiff_lzw'})
            with Image.open(path) as im:
                rgb = im.convert('RGB')
            rgb.save(path, compression='tiff_lzw', dpi=(1200, 1200))
            rgb.close()
            with Image.open(path) as im:
                assert im.info['dpi'] == (1200,1200) and im.mode == 'RGB'
                audit.update(pixels=im.size, dpi=tuple(float(v) for v in im.info['dpi']), mode=im.mode)
        plt.close(self.fig)
        return audit


def build_a():
    p = Panel('A', 183, 212)
    p.box('initial', 47, 11, 99, 13, '103,687 participants with accelerometer records')
    p.box('quality', 47, 32, 99, 25,
          'Accelerometer Data Quality Control\nAdequate wear time\nValid device calibration\nMean acceleration \u2264 100 mg', fill='white')
    p.box('mdd-records', 49, 67, 44, 23,
          '2,592 participants\nwith ICD-10 F32/F33\nhospital-recorded MDD')
    p.box('non-incident', 100, 67, 44, 23,
          '101,095 participants\nwithout incident MDD\nduring follow-up')
    p.box('prevalent-exclusion', 3, 94, 40, 22,
          'Excluded: n = 1,788\nMDD diagnosed on or\nbefore wear completion', fs=8.5, fill='white')
    p.box('incident', 49, 120, 44, 17,
          '804 incident MDD cases\nafter wear completion')
    p.box('case-qc-exclusion', 3, 140, 40, 22,
          'Excluded: n = 69\nFailed accelerometer\nquality control', fs=8.5, fill='white')
    p.box('control-qc-exclusion', 144, 94, 36, 22,
          'Excluded: n = 7,294\nFailed accelerometer\nquality control', fs=8.5, fill='white')
    p.box('final-mdd', 49, 167, 44, 17, '735 final incident\nMDD cases')
    p.box('final-control', 100, 167, 44, 17, '93,801 final\nnon-event participants')
    p.box('final-cohort', 67, 196, 59, 12, '94,536 participants', fill=HIGHLIGHT, bold=True)
    p.edge([(96.5,24),(96.5,32)])
    p.edge([(96.5,57),(96.5,62)], False)
    p.edge([(96.5,62),(71,62),(71,67)])
    p.edge([(96.5,62),(122,62),(122,67)])
    p.edge([(71,90),(71,120)])
    p.edge([(43,105),(71,105)], meaning='exclusion callout into filtering junction')
    p.edge([(71,137),(71,167)])
    p.edge([(43,151),(71,151)], meaning='exclusion callout into filtering junction')
    p.edge([(122,90),(122,167)])
    p.edge([(144,105),(122,105)], meaning='exclusion callout into filtering junction')
    p.edge([(71,184),(71,190),(96.5,190)], False)
    p.edge([(122,184),(122,190),(96.5,190)], False)
    p.edge([(96.5,190),(96.5,196)])
    return p


def build_b():
    p = Panel('B', 89, 123)
    p.box('matched-mdd', 5, 13, 33, 13, '735 MDD')
    p.box('matched-hc', 51, 13, 33, 13, '733 HC')
    p.box('matching', 16, 42, 57, 16, 'Matching by age,\nsex, and ethnicity', fill='white')
    p.box('matched-total', 12, 73, 65, 20,
          'Matched participants\nn = 1,468\n(MDD = 735; HC = 733)')
    p.box('imaging', 12, 108, 65, 12,
          '189 participants with\nusable dMRI data', fill=HIGHLIGHT)
    p.edge([(21.5,26),(21.5,34),(44.5,34)], False)
    p.edge([(67.5,26),(67.5,34),(44.5,34)], False)
    p.edge([(44.5,34),(44.5,42)])
    p.edge([(44.5,58),(44.5,73)])
    p.edge([(44.5,93),(44.5,108)])
    return p


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--full', action='store_true')
    args = parser.parse_args()
    assert 103687 == 2592+101095
    assert 2592-1788 == 804 and 804-69 == 735
    assert 101095-7294 == 93801 and 735+93801 == 94536
    assert 735+733 == 1468
    reports = [build_a().save(args.full), build_b().save(args.full)]
    (OUT/'quality_checks.json').write_text(json.dumps(reports, indent=2), encoding='utf-8')
    print(json.dumps(reports, indent=2))
