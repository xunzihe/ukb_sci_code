"""Vector export of the existing blue/yellow Cox forest style; no model fitting."""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from prepare_analysis_data import NARROW


def main():
    root = Path(__file__).resolve().parents[1]
    out = root/"02_Results/figures"
    out.mkdir(exist_ok=True)
    data = pd.read_csv(root/"02_Results/cox_per10_final.csv").set_index("feature").loc[list(reversed(NARROW))+["125_400mg"]]
    plt.rcParams.update({"font.family":"Arial", "font.size":7.5, "pdf.fonttype":42})
    fig, ax = plt.subplots(figsize=(166/25.4, 170/25.4), facecolor="white")
    fig.subplots_adjust(left=0.24, right=0.985, top=0.98, bottom=0.12)
    palette = dict(zip(NARROW, plt.cm.Blues(np.linspace(0.48,0.90,len(NARROW)))))
    palette["125_400mg"] = "#E9B526"
    for i, (feature,row) in enumerate(data.iterrows()):
        ax.hlines(i,row.CI95_low_per_10min,row.CI95_high_per_10min,color=palette[feature],linewidth=1.5)
        ax.scatter(row.HR_per_10min,i,s=28,color=palette[feature],edgecolor="white",linewidth=0.6,zorder=3)
        ax.text(1.015,i,f"HR={row.HR_per_10min:.3f}   {(1-row.HR_per_10min)*100:.1f}%",ha="left",va="center",fontsize=6.2)
    labels = ["MPA 125–400 mg" if f=="125_400mg" else f.replace("_","–").replace("mg"," mg") for f in data.index]
    ax.set_yticks(np.arange(len(data)),labels)
    ax.invert_yaxis()
    ax.axvline(1,color="#666666",linewidth=0.8,linestyle=(0,(3,3)))
    ax.set_xlim(0.64,1.14)
    ax.set_xticks([.7,.8,.9,1.,1.1])
    ax.grid(axis="x",color="#E4E8EC",linewidth=.6)
    ax.set_axisbelow(True)
    ax.spines[["left","top","right"]].set_visible(False)
    ax.tick_params(axis="y",length=0,pad=5)
    ax.set_xlabel("Hazard ratio per 10 min/week (95% CI)",labelpad=8)
    ax.set_ylabel("Acceleration intensity interval",labelpad=10)
    fig.savefig(out/"Cox_forest_per10.pdf",facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    main()
