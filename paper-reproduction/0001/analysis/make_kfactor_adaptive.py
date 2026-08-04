"""
Adaptive-binned K-factor: instead of the fixed-width Tier-2 bins (which
leave the m_ttbar tail above ~900 GeV masked out for lack of effective MC
statistics -- see make_kfactor_plot.py), merge adjacent bins forward until
BOTH the LO+PS and NLO+PS effective counts (Kish neff) clear MIN_NEFF, then
close that merged bin and start the next one. This extends the K-factor
out to the full observable range (e.g. 1400 GeV for m_ttbar) using
variable-width bins instead of silently dropping the tail.

Key identity used (no need for per-event weights, only the already-binned
yield_pb/error_pb from {obs}_lops_vs_nlops.csv): for a Poisson-like
weighted count, neff = (yield/error)^2 exactly reproduces the Kish
effective sample size, and both yield and error^2 are additive across
merged bins (errors combine in quadrature since bins are disjoint event
sets). So merging is just: sum yields, sum error^2, then recompute neff
from the merged totals.

If the trailing merge group never reaches MIN_NEFF (not enough events left
at all), it is folded into the previous merged bin rather than dropped, so
no cross section is ever silently discarded.

Inputs:
  - output/data/lops_vs_nlops/{obs}_lops_vs_nlops.csv (per-fixed-bin data)

Outputs:
  - output/figures/lops_vs_nlops/{obs}_kfactor_adaptive.png / .pdf
  - output/data/lops_vs_nlops/{obs}_kfactor_adaptive.csv
"""

import csv
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from binning import BIN_EDGES

DATA_DIR = "output/data/lops_vs_nlops"
FIG_DIR = "output/figures/lops_vs_nlops"

MIN_NEFF = 20.0

OBS_META = {
    "pt_ttbar": r"$p_T^{t\bar{t}}$ [GeV]",
    "dphi_ttbar": r"$\Delta\phi_{t\bar{t}}$ [rad]",
    "pt_top_lead": r"$p_T^{t,\mathrm{lead}}$ [GeV]",
    "m_ttbar": r"$m_{t\bar{t}}$ [GeV]",
    "y_t": r"$y_t$",
}

K_INCL = 1.3249
DK_INCL = 0.0278


def load_rows(obs_name):
    path = os.path.join(DATA_DIR, f"{obs_name}_lops_vs_nlops.csv")
    with open(path) as f:
        return [{k: float(v) for k, v in row.items()} for row in csv.DictReader(f)]


def neff(yield_pb, error2_pb2):
    if error2_pb2 <= 0:
        return 0.0
    return (yield_pb ** 2) / error2_pb2


def adaptive_rebin(rows, min_neff=MIN_NEFF):
    merged = []
    cur = None
    for r in rows:
        if cur is None:
            cur = dict(bin_low=r["bin_low"], bin_high=r["bin_high"],
                       L=r["LOPS_yield_pb"], dL2=r["LOPS_error_pb"] ** 2,
                       N=r["NLOPS_yield_pb"], dN2=r["NLOPS_error_pb"] ** 2,
                       n_raw_L=r["LOPS_n_raw"], n_raw_N=r["NLOPS_n_raw"])
        else:
            cur["bin_high"] = r["bin_high"]
            cur["L"] += r["LOPS_yield_pb"]
            cur["dL2"] += r["LOPS_error_pb"] ** 2
            cur["N"] += r["NLOPS_yield_pb"]
            cur["dN2"] += r["NLOPS_error_pb"] ** 2
            cur["n_raw_L"] += r["LOPS_n_raw"]
            cur["n_raw_N"] += r["NLOPS_n_raw"]

        if (cur["L"] > 0 and cur["N"] > 0
                and neff(cur["L"], cur["dL2"]) >= min_neff
                and neff(cur["N"], cur["dN2"]) >= min_neff):
            merged.append(cur)
            cur = None

    if cur is not None:
        if merged:
            last = merged[-1]
            last["bin_high"] = cur["bin_high"]
            last["L"] += cur["L"]
            last["dL2"] += cur["dL2"]
            last["N"] += cur["N"]
            last["dN2"] += cur["dN2"]
            last["n_raw_L"] += cur["n_raw_L"]
            last["n_raw_N"] += cur["n_raw_N"]
        else:
            merged.append(cur)  # whole histogram short on stats -- keep, flagged via low neff

    out = []
    for m in merged:
        L, N = m["L"], m["N"]
        dL, dN = np.sqrt(m["dL2"]), np.sqrt(m["dN2"])
        K = N / L if L > 0 else np.nan
        dK = (K * np.sqrt((dN / N) ** 2 + (dL / L) ** 2)
              if L > 0 and N > 0 else np.nan)
        out.append(dict(bin_low=m["bin_low"], bin_high=m["bin_high"],
                         K=K, K_err=dK,
                         neff_L=neff(L, m["dL2"]), neff_N=neff(N, m["dN2"]),
                         n_raw_L=m["n_raw_L"], n_raw_N=m["n_raw_N"]))
    return out


def plot_observable(obs_name, merged):
    edges = [merged[0]["bin_low"]] + [m["bin_high"] for m in merged]
    centers = [(m["bin_low"] + m["bin_high"]) / 2 for m in merged]
    widths = [m["bin_high"] - m["bin_low"] for m in merged]
    K = np.array([m["K"] for m in merged])
    dK = np.array([m["K_err"] for m in merged])

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.errorbar(centers, K, yerr=dK, xerr=[w / 2 for w in widths], fmt="o",
                color="tab:red", ecolor="tab:red", markersize=5,
                elinewidth=1.2, capsize=0,
                label="K(x) = NLO+PS / LO+PS (adaptive bins)")
    ax.axhline(1.0, color="gray", linestyle=":", linewidth=1.0, label="K = 1")
    ax.axhline(K_INCL, color="black", linestyle="--", linewidth=1.0,
               label=f"inclusive K = {K_INCL:.3f} $\\pm$ {DK_INCL:.3f}")
    ax.axhspan(K_INCL - DK_INCL, K_INCL + DK_INCL, color="black", alpha=0.08)
    ax.set_xlabel(OBS_META[obs_name])
    ax.set_ylabel("K(x)")
    ax.set_title(f"Differential K-factor (adaptive, neff ≥ {MIN_NEFF:.0f}): "
                 f"{OBS_META[obs_name]}")
    ax.legend(frameon=False, fontsize=9)
    fig.tight_layout()

    out_pdf = os.path.join(FIG_DIR, f"{obs_name}_kfactor_adaptive.pdf")
    out_png = os.path.join(FIG_DIR, f"{obs_name}_kfactor_adaptive.png")
    fig.savefig(out_pdf)
    fig.savefig(out_png, dpi=150)
    plt.close(fig)
    print(f"[plot] wrote {out_pdf} and {out_png}  ({len(merged)} adaptive bins, "
          f"vs {len(BIN_EDGES[obs_name]) - 1} fixed bins)")


def write_csv(obs_name, merged):
    path = os.path.join(DATA_DIR, f"{obs_name}_kfactor_adaptive.csv")
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["bin_low", "bin_high", "K", "K_err", "neff_LOPS", "neff_NLOPS",
                    "n_raw_LOPS", "n_raw_NLOPS"])
        for m in merged:
            w.writerow([m["bin_low"], m["bin_high"], m["K"], m["K_err"],
                        m["neff_L"], m["neff_N"], m["n_raw_L"], m["n_raw_N"]])
    print(f"[csv] wrote {path}")


def main():
    for obs_name in BIN_EDGES:
        rows = load_rows(obs_name)
        merged = adaptive_rebin(rows)
        plot_observable(obs_name, merged)
        write_csv(obs_name, merged)


if __name__ == "__main__":
    main()
