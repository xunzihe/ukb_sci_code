import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np
import pandas as pd
NETWORKS = ['SC', 'VIS', 'SMN', 'DAN', 'VAN', 'LIM', 'FPN', 'DMN']
STRUCTURES = ['Thalamus', 'Basal ganglia', 'Hippocampus', 'Amygdala']

def save_figure(fig, stem):
    for suffix in ('pdf', 'svg', 'png'):
        fig.savefig(stem.with_suffix('.' + suffix), dpi=600, facecolor='white', bbox_inches='tight')
    plt.close(fig)

def matrix_plot(matrices, stem):
    (fig, axes) = plt.subplots(1, 2, figsize=(166 / 25.4, 84 / 25.4), layout='constrained')
    vmax = max(1, max((int(m.to_numpy().max()) for m in matrices.values())))
    cmap = plt.get_cmap('Blues').copy()
    cmap.set_bad('white')
    for (label, ax, (model, m)) in zip('AB', axes, matrices.items()):
        v = m.to_numpy()
        mask = np.triu(np.ones(v.shape, dtype=bool), 1)
        image = ax.imshow(np.ma.array(v, mask=mask), cmap=cmap, vmin=0, vmax=vmax)
        ticklabels = ['Subc.' if n == 'SC' else n for n in NETWORKS]
        ax.set_xticks(range(8), ticklabels, fontsize=6.5)
        ax.set_yticks(range(8), ticklabels, fontsize=6.5)
        ax.set_title('PA-SC associations' if model == 'Model1' else 'MDD-HC association differences', fontsize=8)
        ax.text(-0.14, 1.07, label, transform=ax.transAxes, fontsize=10, weight='bold')
        for i in range(8):
            for j in range(i + 1):
                ax.add_patch(Rectangle((j - 0.5, i - 0.5), 1, 1, fill=False, edgecolor='black', linewidth=0.45))
                ax.text(j, i, str(int(v[i, j])), ha='center', va='center', fontsize=6.7, color='white' if v[i, j] > 0.55 * vmax else '#222222')
        for spine in ax.spines.values():
            spine.set_visible(False)
    c = fig.colorbar(image, ax=axes, fraction=0.025, pad=0.025)
    c.set_label('Unique significant connections', fontsize=7)
    c.ax.tick_params(labelsize=6.5)
    save_figure(fig, stem)

def band_plot(data, stem):
    (fig, axes) = plt.subplots(2, 1, figsize=(166 / 25.4, 112 / 25.4), sharex=True, layout='constrained')
    for (panel, ax, model) in zip('AB', axes, ('Model1', 'Model2')):
        d = data[model]
        positive = [int(((d.PA_variable == b) & (d.effect_target > 0)).sum()) for b in BANDS]
        negative = [int(((d.PA_variable == b) & (d.effect_target < 0)).sum()) for b in BANDS]
        ax.bar(range(11), positive, color='#E6A532', width=0.73, label='Positive')
        if any(negative):
            ax.bar(range(11), negative, bottom=positive, color='#3E7CB1', width=0.73, label='Negative')
        for (i, n) in enumerate(np.array(positive) + negative):
            ax.text(i, n + 0.25, str(n), ha='center', fontsize=7)
        ax.set_ylim(0, max(positive) * 1.18 + 1)
        ax.set_ylabel('Significant association records' if model == 'Model1' else 'Significant interaction records', fontsize=7)
        ax.set_title('PA-SC associations' if model == 'Model1' else 'MDD-HC association differences', fontsize=8)
        ax.text(-0.09, 1.03, panel, transform=ax.transAxes, fontsize=10, weight='bold')
        ax.spines[['top', 'right']].set_visible(False)
        ax.tick_params(labelsize=7)
    axes[0].legend(frameon=False, fontsize=7, loc='upper right')
    axes[-1].set_xticks(range(11), [b.replace('mg', '').replace('_', '-') for b in BANDS], rotation=40, ha='right', fontsize=7)
    axes[-1].set_xlabel('Acceleration intensity band (mg)', fontsize=8)
    save_figure(fig, stem)

BANDS = [f'{v}_{v+25}mg' for v in range(125,400,25)]
