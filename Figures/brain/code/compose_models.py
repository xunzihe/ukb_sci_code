"""Compose true BrainNet Viewer renders; trim whitespace only, no data editing."""
from pathlib import Path
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, Normalize
from matplotlib.colorbar import ColorbarBase
from matplotlib.patches import Patch, PathPatch
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties, findfont
from matplotlib.transforms import Affine2D
import numpy as np
import pandas as pd
from PIL import Image


import sys
PROJECT = Path(__file__).resolve().parents[1]
MODEL = sys.argv[1]
assert MODEL in ['Model1', 'Model2']
ROOT = PROJECT / MODEL
OUT = ROOT / "outputs"
SETTINGS = json.loads((ROOT / "inputs/render_settings.json").read_text())
COLORS = pd.read_csv(ROOT / "inputs/Network_color_key.csv")
ORDER = ["DMN", "VIS", "VAN", "SMN", "LIM", "FPN", "DAN", "SC"]
plt.rcParams.update({"font.family": "DejaVu Sans", "font.sans-serif": ["DejaVu Sans"],
                     "font.size": 7, "mathtext.fontset": "dejavusans",
                     "pdf.fonttype": 42, "svg.fonttype": "path"})


def crop_whitespace(path):
    image = Image.open(path).convert("RGB")
    data = np.asarray(image)
    mask = (data.min(axis=2) < 243)
    yy, xx = np.where(mask)
    if len(xx) == 0:
        raise ValueError(f"Empty render: {path}")
    margin = 40
    box = (max(0, xx.min() - margin), max(0, yy.min() - margin),
           min(image.width, xx.max() + margin + 1), min(image.height, yy.max() + margin + 1))
    return image.crop(box)


def color_handles():
    handles = []
    for network in ORDER:
        row = COLORS[COLORS.Network == network].iloc[0]
        handles.append(Patch(facecolor=[row.R, row.G, row.B], edgecolor="none",
                             label=f"{row.Name} ({network})" if network != "SC" else row.Name))
    return handles


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    images = [crop_whitespace(OUT / "raw_views" / f"{MODEL}_{view}.png")
              for view in ["left", "right", "superior"]]
    fig = plt.figure(figsize=(166 / 25.4, 76 / 25.4), facecolor="white")
    panel_letter = 'A' if MODEL == 'Model1' else 'B'
    fig.text(.018, .965, panel_letter, ha='left', va='top', fontsize=11, fontweight='bold')
    for i, (image, label) in enumerate(zip(images, ["Left view", "Right view", "Superior view"])):
        ax = fig.add_axes([.012 + i * .330, .23, .316, .70])
        ax.imshow(image)
        ax.set_axis_off()
        fig.text(.170 + i * .330, .95, label, ha="center", va="center", fontsize=8)
    # Network colour/name legend is exported separately, not repeated here.
    cmap = ListedColormap(SETTINGS["edge_colormap_rgb"], name="positive_t")
    cax = fig.add_axes([.31, .105, .38, .035])
    cb = ColorbarBase(cax, cmap=cmap, norm=Normalize(SETTINGS["t_min"], SETTINGS["t_max"]), orientation="horizontal")
    ticks = np.linspace(SETTINGS['t_min'], SETTINGS['t_max'], 4)
    cb.set_ticks(ticks)
    cb.set_ticklabels([f'{x:.2f}' for x in ticks])
    for label in cb.ax.get_xticklabels():
        label.set_horizontalalignment('center')
        label.set_fontfamily('DejaVu Sans')
    cb.ax.tick_params(labelsize=7, length=2, pad=2)
    cb.outline.set_linewidth(.5)
    colorbar_title = ('Physical activity t-statistic' if MODEL == 'Model1' else
                      'Physical activity × group interaction t-statistic')
    # Render the complete title as one glyph path using a fixed font file.
    # This preserves kerning and prevents viewer-side font substitution.
    font_file = findfont(FontProperties(family='DejaVu Sans'), fallback_to_default=False)
    title_path = TextPath((0, 0), colorbar_title, size=7.5,
                          prop=FontProperties(fname=font_file), usetex=False)
    title_box = title_path.get_extents()
    title_width = title_box.width / (72 * fig.get_figwidth())
    assert title_width < .9, 'Full title exceeds the canvas'
    title_transform = (Affine2D().translate(-title_box.x0 - title_box.width / 2, -title_box.y0)
                       .scale(1 / (72 * fig.get_figwidth()), 1 / (72 * fig.get_figheight()))
                       .translate(.5, .165) + fig.transFigure)
    fig.add_artist(PathPatch(title_path, transform=title_transform, facecolor='black',
                             edgecolor='none', clip_on=False))
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    tick_x = cax.transData.transform(np.column_stack([ticks, np.zeros(4)]))[:, 0]
    gaps = np.diff(tick_x)
    np.testing.assert_allclose(gaps, np.repeat(gaps[0], 3), atol=1e-9)
    boxes = [label.get_window_extent(renderer) for label in cb.ax.get_xticklabels()]
    centers = np.array([(box.x0 + box.x1) / 2 for box in boxes])
    np.testing.assert_allclose(centers, tick_x, atol=.01)
    assert all(boxes[i].x1 < boxes[i+1].x0 for i in range(3))
    assert len({label.get_fontsize() for label in cb.ax.get_xticklabels()}) == 1
    (ROOT / 'tick_layout_check.json').write_text(json.dumps({
        'tick_values_full_precision': ticks.tolist(),
        'tick_labels_rounded_2_decimals': [f'{x:.2f}' for x in ticks],
        'equal_tick_center_spacing': True, 'linear_mapping_unchanged': True,
        'label_centers_on_ticks': True, 'labels_do_not_overlap': True,
        'font': 'DejaVu Sans', 'fontsize_pt': 7, 'colorbar_title': colorbar_title,
        'panel_letter': panel_letter,
        'title_font_file': font_file, 'title_rendered_as_single_glyph_path': True,
        'title_width_fraction_of_canvas': title_width,
        'svg_fonts_outlined': True, 'pdf_fonts_embedded': True,
        'intervals_normalized': (gaps / (tick_x[-1] - tick_x[0])).tolist()
    }, indent=2), encoding='utf-8')
    for extension in ["png", "pdf", "svg"]:
        fig.savefig(OUT / f"{MODEL}_brain_connectome_3D.{extension}", dpi=600,
                    facecolor="white", bbox_inches=None)
    fig.savefig(OUT / f"{MODEL}_brain_connectome_3D_preview.png", dpi=220, facecolor="white")
    plt.close(fig)

    legend_fig, ax = plt.subplots(figsize=(5.2, 1.6))
    ax.axis("off")
    ax.legend(handles=color_handles(), loc="center", ncol=2, frameon=False,
              fontsize=8, handlelength=1.2, labelspacing=.8, columnspacing=2)
    legend_fig.tight_layout(pad=.2)
    for extension in ["png", "pdf", "svg"]:
        legend_fig.savefig(OUT / f"Shared_node_network_legend.{extension}", dpi=400, bbox_inches="tight", pad_inches=.08)
        if MODEL == 'Model1':
            legend_dir = PROJECT / 'Shared_legend'
            legend_dir.mkdir(exist_ok=True)
            legend_fig.savefig(legend_dir / f"Shared_node_network_legend.{extension}", dpi=400, bbox_inches="tight", pad_inches=.08)
    plt.close(legend_fig)
    manifest = json.loads((ROOT / "validation_manifest.json").read_text(encoding="utf-8"))
    assert all(manifest["checks"].values())
    render_checks = json.loads((ROOT / "render_checks.json").read_text())
    assert all(v["loaded_nodes"] == 246 and v["loaded_unique_edges"] == SETTINGS['unique_edges'] and
               v["actual_rendered_edges"] == SETTINGS['unique_edges'] and
               v["mesh_objects"] == 246 + SETTINGS['unique_edges'] and v['lit_3D_nodes'] == 246
               for v in render_checks.values())
    for p in sorted(OUT.glob("*")):
        if p.is_file():
            print(p.name, p.stat().st_size)
    print(MODEL, "validated:", SETTINGS['unique_edges'], "unique connections, all 246 nodes, official mapping, three anatomical views.")


if __name__ == "__main__":
    main()
