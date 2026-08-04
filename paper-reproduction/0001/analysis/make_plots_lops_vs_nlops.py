"""
NEW comparison (separate from the original LO/NLO/NLO+PS 3-way study):
LO+PS vs NLO+PS, to isolate the pure parton-shower/resummation effect
(shower attached directly to LO vs. shower matched via MC@NLO to NLO)
from the NLO rate correction.

Produces, for each of the 5 Tier-2 observables: one overlay plot (LO+PS
vs NLO+PS) with STATISTICAL (MC) error bars only -- no scale/theory
uncertainty band, per the user's explicit, already-agreed scope decision
(see task instructions: this comparison is about shower-induced shape
differences, which statistical error bars answer directly).

Normalization mode: ABSOLUTE YIELD (pb per bin, not shape-normalized) --
same convention as the original Tier 2 plots (analysis/make_plots.py),
so this new comparison is visually/methodologically consistent with the
earlier ones.

Inputs:
  - output/data/lops_vs_nlops/lops_results.json (this task; Run 4, LO+PS)
  - output/data/nlops_results.json (already existed; Run 3, NLO+PS --
    reused as-is, not regenerated)

Outputs (kept in a dedicated subdirectory/suffix so the ORIGINAL
LO/NLO/NLO+PS CSVs and plots under output/data/*.csv and
output/figures/*.png are never touched/overwritten):
  - output/figures/lops_vs_nlops/{obs}_lops_vs_nlops.png / .pdf
  - output/data/lops_vs_nlops/{obs}_lops_vs_nlops.csv

The overlay now also carries a bottom ratio panel: the plain, per-bin
K-factor K(x) = NLO+PS_yield / LO+PS_yield with propagated statistical
errors (no neff masking/rebinning -- see make_kfactor_plot.py /
make_kfactor_adaptive.py for masked/adaptive variants), plus a K=1
reference line and the inclusive rate K-factor as a dashed reference.
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

OUT_DATA_DIR = "output/data/lops_vs_nlops"
OUT_FIG_DIR = "output/figures/lops_vs_nlops"
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
    "LO+PS": dict(color="tab:blue", label="LO+PS (Pythia8, direct attach)"),
    "NLO+PS": dict(color="tab:green", label="NLO+PS (MC@NLO+Pythia8)"),
}


def load_all():
    with open("output/data/lops_vs_nlops/lops_results.json") as f:
        lops = json.load(f)
    with open("output/data/nlops_results.json") as f:
        nlops = json.load(f)
    return {"LO+PS": lops, "NLO+PS": nlops}


def inclusive_kfactor(results):
    L, dL = results["LO+PS"]["sigma_pb_self_summed"], results["LO+PS"]["sigma_err_pb_self_summed"]
    N, dN = results["NLO+PS"]["sigma_pb_self_summed"], results["NLO+PS"]["sigma_err_pb_self_summed"]
    K = N / L
    dK = K * np.sqrt((dN / N) ** 2 + (dL / L) ** 2)
    return K, dK


def plot_observable(obs_name, results, K_incl, dK_incl):
    meta = OBS_META[obs_name]
    edges = np.array(results["LO+PS"]["histograms"][obs_name]["bin_edges"])
    edges_check = np.array(results["NLO+PS"]["histograms"][obs_name]["bin_edges"])
    assert np.allclose(edges, edges_check), (
        f"Bin edges mismatch between LO+PS and NLO+PS for {obs_name} -- "
        "would not be an apples-to-apples comparison."
    )
    centers = 0.5 * (edges[:-1] + edges[1:])
    widths = np.diff(edges)

    fig, (ax, ax2) = plt.subplots(
        2, 1, figsize=(7, 7), sharex=True,
        gridspec_kw={"height_ratios": [2, 1], "hspace": 0.06},
    )

    yields_by_run = {}
    errors_by_run = {}
    for run in ("LO+PS", "NLO+PS"):
        h = results[run]["histograms"][obs_name]
        yields = np.array(h["yield_pb"])
        errors = np.array(h["error_pb"])
        yields_by_run[run] = yields
        errors_by_run[run] = errors
        style = RUN_STYLE[run]
        ax.step(edges, np.append(yields, yields[-1]), where="post",
                color=style["color"], label=style["label"], linewidth=1.6)
        ax.errorbar(centers, yields, yerr=errors, fmt="none",
                    ecolor=style["color"], elinewidth=1.0, capsize=2, alpha=0.8)

    ax.set_ylabel(f"d$\\sigma$ / bin  [pb / {widths[0]:.3g} unit bin]")
    ax.set_title(meta["title"] + r":  $pp \to t\bar{t}$ @ 13 TeV, LO+PS vs NLO+PS "
                 "(statistical errors only)")
    ax.legend(frameon=False)
    ax.set_yscale("log")

    # Plain per-bin K-factor: K(x) = NLO+PS / LO+PS, no neff masking/rebinning
    # (see make_kfactor_plot.py / make_kfactor_adaptive.py for masked/adaptive
    # variants) -- every bin is shown as-is, with propagated stat errors.
    L, dL = yields_by_run["LO+PS"], errors_by_run["LO+PS"]
    N, dN = yields_by_run["NLO+PS"], errors_by_run["NLO+PS"]
    valid = L > 0
    K = np.full_like(L, np.nan)
    dK = np.full_like(L, np.nan)
    with np.errstate(divide="ignore", invalid="ignore"):
        K[valid] = N[valid] / L[valid]
        dK[valid] = K[valid] * np.sqrt((dN[valid] / N[valid]) ** 2 + (dL[valid] / L[valid]) ** 2)

    ax2.errorbar(centers[valid], K[valid], yerr=dK[valid], fmt="o",
                 color="tab:red", ecolor="tab:red", markersize=4,
                 elinewidth=1.0, capsize=2, label="K(x) = NLO+PS / LO+PS")
    ax2.axhline(1.0, color="gray", linestyle=":", linewidth=1.0, label="K = 1")
    ax2.axhline(K_incl, color="black", linestyle="--", linewidth=1.0,
                label=f"inclusive K = {K_incl:.3f} $\\pm$ {dK_incl:.3f}")
    ax2.axhspan(K_incl - dK_incl, K_incl + dK_incl, color="black", alpha=0.08)
    ax2.set_xlabel(meta["xlabel"])
    ax2.set_ylabel("K(x)")
    ax2.legend(frameon=False, fontsize=8, loc="best")

    fig.tight_layout()

    out_path_pdf = os.path.join(OUT_FIG_DIR, f"{obs_name}_lops_vs_nlops.pdf")
    out_path_png = os.path.join(OUT_FIG_DIR, f"{obs_name}_lops_vs_nlops.png")
    fig.savefig(out_path_pdf)
    fig.savefig(out_path_png, dpi=150)
    plt.close(fig)
    print(f"[plot] wrote {out_path_pdf} and {out_path_png}")


def write_csv(obs_name, results):
    edges = np.array(results["LO+PS"]["histograms"][obs_name]["bin_edges"])
    centers = 0.5 * (edges[:-1] + edges[1:])
    n_bins = len(centers)

    csv_path = os.path.join(OUT_DATA_DIR, f"{obs_name}_lops_vs_nlops.csv")
    with open(csv_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "bin_low", "bin_high", "bin_center",
            "LOPS_yield_pb", "LOPS_error_pb", "LOPS_neff", "LOPS_n_raw",
            "NLOPS_yield_pb", "NLOPS_error_pb", "NLOPS_neff", "NLOPS_n_raw",
        ])
        for i in range(n_bins):
            row = [edges[i], edges[i + 1], centers[i]]
            for run in ("LO+PS", "NLO+PS"):
                h = results[run]["histograms"][obs_name]
                row += [h["yield_pb"][i], h["error_pb"][i], h["neff"][i], h["n_raw"][i]]
            w.writerow(row)
    print(f"[csv] wrote {csv_path}")


def main():
    results = load_all()
    K_incl, dK_incl = inclusive_kfactor(results)
    print(f"[kfactor] inclusive K = {K_incl:.4f} +/- {dK_incl:.4f}")
    for obs_name in BIN_EDGES:
        plot_observable(obs_name, results, K_incl, dK_incl)
        write_csv(obs_name, results)


if __name__ == "__main__":
    main()
