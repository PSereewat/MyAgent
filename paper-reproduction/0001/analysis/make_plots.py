"""
Tier 2: produce LO vs NLO vs NLO+PS comparison plots for the 5
differential observables, plus a CSV of the underlying binned numbers
for each observable (bin edges/centers + LO/NLO/NLO+PS yield+error per
bin), saved alongside the plots.

Normalization mode: ABSOLUTE YIELD (pb per bin; not shape-normalized) --
same convention as Tier 1, so the K-factor-like normalization difference
between LO/NLO/NLO+PS is visible directly in the overlay, per the task's
request to "compare LO vs NLO vs NLO+PS on the same plot" (an explicit
units-bearing comparison of absolute predictions, not a shape-only
comparison).
"""

import csv
import json
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from binning import BIN_EDGES

OUT_DATA_DIR = "output/data"
OUT_FIG_DIR = "output/figures"
os.makedirs(OUT_FIG_DIR, exist_ok=True)
os.makedirs(OUT_DATA_DIR, exist_ok=True)

OBS_META = {
    "pt_ttbar": dict(xlabel=r"$p_T^{t\bar{t}}$ [GeV]", title=r"$p_T^{t\bar{t}}$"),
    "dphi_ttbar": dict(xlabel=r"$\Delta\phi_{t\bar{t}}$ [rad]", title=r"$\Delta\phi_{t\bar{t}}$"),
    "pt_top_lead": dict(xlabel=r"$p_T^{t,\mathrm{lead}}$ [GeV]", title=r"Leading top $p_T$"),
    "m_ttbar": dict(xlabel=r"$m_{t\bar{t}}$ [GeV]", title=r"$m_{t\bar{t}}$"),
    "y_t": dict(xlabel=r"$y_t$", title=r"Top rapidity $y_t$"),
}

RUN_STYLE = {
    "LO": dict(color="tab:blue", label="LO"),
    "NLO": dict(color="tab:orange", label="NLO fixed-order"),
    "NLO+PS": dict(color="tab:green", label="NLO+PS (MC@NLO+Pythia8)"),
}


def load_all():
    with open(os.path.join(OUT_DATA_DIR, "lo_results.json")) as f:
        lo = json.load(f)
    with open(os.path.join(OUT_DATA_DIR, "nlo_results.json")) as f:
        nlo = json.load(f)
    with open(os.path.join(OUT_DATA_DIR, "nlops_results.json")) as f:
        nlops = json.load(f)
    return {"LO": lo, "NLO": nlo, "NLO+PS": nlops}


def plot_observable(obs_name, results):
    meta = OBS_META[obs_name]
    edges = np.array(results["LO"]["histograms"][obs_name]["bin_edges"])
    centers = 0.5 * (edges[:-1] + edges[1:])
    widths = np.diff(edges)

    fig, ax = plt.subplots(figsize=(7, 5))
    for run in ("LO", "NLO", "NLO+PS"):
        h = results[run]["histograms"][obs_name]
        yields = np.array(h["yield_pb"])
        errors = np.array(h["error_pb"])
        style = RUN_STYLE[run]
        ax.step(edges, np.append(yields, yields[-1]), where="post",
                color=style["color"], label=style["label"], linewidth=1.6)
        ax.errorbar(centers, yields, yerr=errors, fmt="none",
                    ecolor=style["color"], elinewidth=1.0, capsize=2, alpha=0.8)

    ax.set_xlabel(meta["xlabel"])
    ax.set_ylabel(f"d$\\sigma$ / bin  [pb / {widths[0]:.3g} unit bin]")
    ax.set_title(meta["title"] + r":  $pp \to t\bar{t}$ @ 13 TeV, LO vs NLO vs NLO+PS")
    ax.legend(frameon=False)
    ax.set_yscale("log")
    fig.tight_layout()

    out_path_pdf = os.path.join(OUT_FIG_DIR, f"{obs_name}.pdf")
    out_path_png = os.path.join(OUT_FIG_DIR, f"{obs_name}.png")
    fig.savefig(out_path_pdf)
    fig.savefig(out_path_png, dpi=150)
    plt.close(fig)
    print(f"[plot] wrote {out_path_pdf} and {out_path_png}")


def write_csv(obs_name, results):
    edges = np.array(results["LO"]["histograms"][obs_name]["bin_edges"])
    centers = 0.5 * (edges[:-1] + edges[1:])
    n_bins = len(centers)

    csv_path = os.path.join(OUT_DATA_DIR, f"{obs_name}.csv")
    with open(csv_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "bin_low", "bin_high", "bin_center",
            "LO_yield_pb", "LO_error_pb", "LO_neff", "LO_n_raw",
            "NLO_yield_pb", "NLO_error_pb", "NLO_neff", "NLO_n_raw",
            "NLOPS_yield_pb", "NLOPS_error_pb", "NLOPS_neff", "NLOPS_n_raw",
        ])
        for i in range(n_bins):
            row = [edges[i], edges[i + 1], centers[i]]
            for run in ("LO", "NLO", "NLO+PS"):
                h = results[run]["histograms"][obs_name]
                row += [h["yield_pb"][i], h["error_pb"][i], h["neff"][i], h["n_raw"][i]]
            w.writerow(row)
    print(f"[csv] wrote {csv_path}")


def main():
    results = load_all()
    for obs_name in BIN_EDGES:
        plot_observable(obs_name, results)
        write_csv(obs_name, results)


if __name__ == "__main__":
    main()
