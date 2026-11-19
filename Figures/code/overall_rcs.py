"""Export the retained overall-MPA supplemental RCS curve; no model fitting.

Seven narrow-band curves appear in main Figure 2; three others form SDC5.
This module exports the overall 125-400 mg curve as SDC2.
"""
from pathlib import Path
import hashlib
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INTERNAL = ROOT / "outputs" / "verification" / "SDC2"
OUT = ROOT / "outputs" / "supplementary_figures"
SOURCE = ROOT / "data" / "cox"


def p_text(value):
    if not np.isfinite(value) or value <= 0 or value > 1:
        raise ValueError("A plotted P value must be finite and in (0, 1].")
    if value < 0.001:
        mantissa, exponent = f"{value:.2e}".split("e")
        return rf"=${mantissa}\times10^{{{int(exponent)}}}$"
    return f"={value:.4f}"


def panel(ax, curve, result, letter=""):
    ax.fill_between(curve.minutes_per_week, curve.CI95_low, curve.CI95_high,
                    color="#A8CEE8", alpha=0.48, linewidth=0)
    ax.plot(curve.minutes_per_week, curve.HR, color="#1769AA", linewidth=1.6)
    ax.axhline(1, color="#555555", linewidth=0.65, linestyle=(0, (3, 2)))
    ax.set_title(result.intensity_interval, fontsize=7.2, fontweight="bold", pad=3)
    if letter:
        ax.text(-0.16, 1.08, letter, transform=ax.transAxes, fontsize=8, fontweight="bold", va="top")
    annotation = "P-nonlinearity" + p_text(result.p_nonlinearity)
    if np.isfinite(result.p_nonlinearity_fdr):
        annotation += "\nFDR P" + p_text(result.p_nonlinearity_fdr)
    # Layout-only change: keep the annotation below the reference line with an opaque background.
    ax.text(0.98, 0.88, annotation, transform=ax.transAxes, ha="right", va="top", fontsize=6,
            bbox=dict(facecolor="white", edgecolor="none", pad=1.5), zorder=10)
    low = max(0.20, float(np.nanpercentile(curve.CI95_low, 2)) - 0.03)
    high = min(1.80, max(1.05, float(np.nanpercentile(curve.CI95_high, 98)) + 0.03))
    ax.set_ylim(low, high)
    ax.grid(axis="y", color="#E7E7E7", linewidth=0.45)
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(labelsize=6, length=2)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    INTERNAL.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.family": "Arial", "pdf.fonttype": 42, "ps.fonttype": 42,
                         "mathtext.fontset": "dejavusans", "mathtext.default": "regular"})
    results = pd.read_csv(SOURCE / "rcs_nonlinearity_results.csv").set_index("feature")
    curve_paths = [SOURCE / "curves" / "rcs_curve_125_400mg.csv"]
    fig, ax = plt.subplots(figsize=(3.23, 2.75), facecolor="white")
    fig.subplots_adjust(left=0.19, right=0.97, top=0.88, bottom=0.20)
    panel(ax, pd.read_csv(curve_paths[-1]), results.loc["125_400mg"])
    ax.set_xlabel("Weekly activity duration (min/week)", fontsize=7)
    ax.set_ylabel("Hazard ratio", fontsize=7)
    fig.savefig(OUT / "Supplemental_Digital_Content_2_RCS_overall_MPA.pdf", bbox_inches=None, facecolor="white")
    plt.close(fig)
    (INTERNAL / "figure_curve_sources.json").write_text(json.dumps({
        "note": "Saved final curves and statistics unchanged; numeric P-value labels, annotation layout and typography only.",
        "source_files": [{"path": str(p.relative_to(ROOT)), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in curve_paths],
    }, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
