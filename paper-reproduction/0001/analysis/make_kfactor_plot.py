"""
Differential K-factor: K(x) = d-sigma(NLO+PS) / d-sigma(LO+PS), bin by bin,
for each of the 5 Tier-2 observables. This isolates how the shape (not just
the rate) differs between showering-a-LO-sample and showering-a-matched-NLO
(MC@NLO) sample -- i.e. how much of the NLO/LO difference survives after
both are showered, and where in phase space it is concentrated.

K is NOT flat: a flat K would mean the shower washes out all shape
differences and only the rate changes. Deviations of K(x) from a flat line
show shower/matching-driven shape effects on top of the rate correction.

Statistical error propagation (bins are independent MC samples, so no
correlation term):
    K = N / L
    sigma_K / K = sqrt( (sigma_N/N)^2 + (sigma_L/L)^2 )

Bins where the LO+PS denominator has too few effective entries are masked
(K is meaningless / wildly noisy there) rather than plotted.

Inputs (already produced by make_plots_lops_vs_nlops.py -- not regenerated
here):
  - output/data/lops_vs_nlops/{obs}_lops_vs_nlops.csv

Outputs:
  - output/figures/lops_vs_nlops/{obs}_kfactor.png / .pdf
    (top panel: absolute yields, log scale; bottom panel: K(x) with
    stat error bars, K=1 reference line, and the inclusive rate K-factor
    as a dashed reference line)
  - output/data/lops_vs_nlops/{obs}_kfactor.csv
  - prints an inclusive (integrated) K-factor summary to stdout
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

DATA_DIR = "output/data/lops_vs_nlops"
FIG_DIR = "output/figures/lops_vs_nlops"
os.makedirs(FIG_DIR, exist_ok=True)

MIN_NEFF = 20.0  # below this, mask the bin -- ratio is too noisy to trust

OBS_META = {
    "pt_ttbar": dict(xlabel=r"$p_T^{t\bar{t}}$ [GeV]", title=r"$p_T^{t\bar{t}}$"),
    "dphi_ttbar": dict(xlabel=r"$\Delta\phi_{t\bar{t}}$ [rad]", title=r"$\Delta\phi_{t\bar{t}}$"),
    "pt_top_lead": dict(xlabel=r"$p_T^{t,\mathrm{lead}}$ [GeV]", title=r"Leading top $p_T$"),
    "m_ttbar": dict(xlabel=r"$m_{t\bar{t}}$ [GeV]", title=r"$m_{t\bar{t}}$"),
    "y_t": dict(xlabel=r"$y_t$", title=r"Top rapidity $y_t$"),
}


def inclusive_kfactor():
    with open(os.path.join(DATA_DIR, "lops_results.json")) as f:
        lops = json.load(f)
    with open("output/data/nlops_results.json") as f:
        nlops = json.load(f)

    L, dL = lops["sigma_pb_self_summed"], lops["sigma_err_pb_self_summed"]
    N, dN = nlops["sigma_pb_self_summed"], nlops["sigma_err_pb_self_summed"]
    K = N / L
    dK = K * np.sqrt((dN / N) ** 2 + (dL / L) ** 2)
    return L, dL, N, dN, K, dK


def load_csv(obs_name):
    path = os.path.join(DATA_DIR, f"{obs_name}_lops_vs_nlops.csv")
    rows = []
    with open(path) as f:
        for row in csv.DictReader(f):
            rows.append({k: float(v) for k, v in row.items()})
    return rows


def compute_kfactor(rows):
    edges = np.array([r["bin_low"] for r in rows] + [rows[-1]["bin_high"]])
    centers = np.array([r["bin_center"] for r in rows])
    L = np.array([r["LOPS_yield_pb"] for r in rows])
    dL = np.array([r["LOPS_error_pb"] for r in rows])
    N = np.array([r["NLOPS_yield_pb"] for r in rows])
    dN = np.array([r["NLOPS_error_pb"] for r in rows])
    neffL = np.array([r["LOPS_neff"] for r in rows])
    neffN = np.array([r["NLOPS_neff"] for r in rows])

    valid = (L > 0) & (N > 0) & (neffL >= MIN_NEFF) & (neffN >= MIN_NEFF)

    K = np.full_like(L, np.nan)
    dK = np.full_like(L, np.nan)
    with np.errstate(divide="ignore", invalid="ignore"):
        K[valid] = N[valid] / L[valid]
        dK[valid] = K[valid] * np.sqrt(
            (dN[valid] / N[valid]) ** 2 + (dL[valid] / L[valid]) ** 2
        )
    return edges, centers, K, dK, valid


def plot_observable(obs_name, rows, K_incl, dK_incl):
    meta = OBS_META[obs_name]
    edges, centers, K, dK, valid = compute_kfactor(rows)
    widths = np.diff(edges)

    L = np.array([r["LOPS_yield_pb"] for r in rows])
    dL = np.array([r["LOPS_error_pb"] for r in rows])
    N = np.array([r["NLOPS_yield_pb"] for r in rows])
    dN = np.array([r["NLOPS_error_pb"] for r in rows])

    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(7, 7), sharex=True,
        gridspec_kw={"height_ratios": [2, 1], "hspace": 0.06},
    )

    ax1.step(edges, np.append(L, L[-1]), where="post", color="tab:blue",
              label="LO+PS (Pythia8, direct attach)", linewidth=1.6)
    ax1.errorbar(centers, L, yerr=dL, fmt="none", ecolor="tab:blue",
                 elinewidth=1.0, capsize=2, alpha=0.8)
    ax1.step(edges, np.append(N, N[-1]), where="post", color="tab:green",
              label="NLO+PS (MC@NLO+Pythia8)", linewidth=1.6)
    ax1.errorbar(centers, N, yerr=dN, fmt="none", ecolor="tab:green",
                 elinewidth=1.0, capsize=2, alpha=0.8)
    ax1.set_ylabel(f"d$\\sigma$ / bin  [pb / {widths[0]:.3g} unit bin]")
    ax1.set_yscale("log")
    ax1.set_title(meta["title"] + r":  $pp \to t\bar{t}$ @ 13 TeV, differential K-factor")
    ax1.legend(frameon=False)

    ax2.errorbar(centers[valid], K[valid], yerr=dK[valid], fmt="o",
                 color="tab:red", ecolor="tab:red", markersize=4,
                 elinewidth=1.0, capsize=2, label="K(x) = NLO+PS / LO+PS")
    ax2.axhline(1.0, color="gray", linestyle=":", linewidth=1.0, label="K = 1")
    ax2.axhline(K_incl, color="black", linestyle="--", linewidth=1.0,
                label=f"inclusive K = {K_incl:.3f} $\\pm$ {dK_incl:.3f}")
    ax2.fill_between(edges, K_incl - dK_incl, K_incl + dK_incl,
                      color="black", alpha=0.08, step="post")
    ax2.set_xlabel(meta["xlabel"])
    ax2.set_ylabel("K(x)")
    ax2.legend(frameon=False, fontsize=8, loc="best")

    fig.tight_layout()
    out_pdf = os.path.join(FIG_DIR, f"{obs_name}_kfactor.pdf")
    out_png = os.path.join(FIG_DIR, f"{obs_name}_kfactor.png")
    fig.savefig(out_pdf)
    fig.savefig(out_png, dpi=150)
    plt.close(fig)
    print(f"[plot] wrote {out_pdf} and {out_png}")

    return edges, centers, K, dK, valid


def write_csv(obs_name, edges, centers, K, dK, valid):
    path = os.path.join(DATA_DIR, f"{obs_name}_kfactor.csv")
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["bin_low", "bin_high", "bin_center", "K", "K_err", "valid"])
        for i in range(len(centers)):
            w.writerow([edges[i], edges[i + 1], centers[i],
                        K[i] if valid[i] else "", dK[i] if valid[i] else "",
                        int(valid[i])])
    print(f"[csv] wrote {path}")


def main():
    L, dL, N, dN, K_incl, dK_incl = inclusive_kfactor()
    print("=" * 70)
    print("Inclusive (integrated) K-factor: NLO+PS / LO+PS")
    print(f"  sigma(LO+PS)  = {L:.4f} +/- {dL:.4f} pb")
    print(f"  sigma(NLO+PS) = {N:.4f} +/- {dN:.4f} pb")
    print(f"  K = {K_incl:.4f} +/- {dK_incl:.4f}")
    print("=" * 70)

    summary_rows = []
    for obs_name in BIN_EDGES:
        rows = load_csv(obs_name)
        edges, centers, K, dK, valid = plot_observable(obs_name, rows, K_incl, dK_incl)
        write_csv(obs_name, edges, centers, K, dK, valid)
        if valid.any():
            kmin, kmax, kmean = np.nanmin(K[valid]), np.nanmax(K[valid]), np.nanmean(K[valid])
            print(f"  {obs_name:12s}: K range [{kmin:.3f}, {kmax:.3f}], "
                  f"mean {kmean:.3f}, {valid.sum()}/{len(valid)} bins valid")
            summary_rows.append((obs_name, kmin, kmax, kmean))

    print("=" * 70)
    print("Interpretation: if K(x) is flat and consistent with the inclusive")
    print("K-factor across an observable, the parton shower does not induce")
    print("an additional shape distortion beyond the overall NLO/LO rate")
    print("difference for that variable. Bins where K(x) departs from the")
    print("inclusive line indicate shower/matching-driven shape effects on")
    print("top of the rate correction (e.g. hard-radiation tails only")
    print("accessible at NLO, or shower-induced migration near LO's")
    print("kinematic edges such as p_T^ttbar -> 0 or Delta_phi -> pi).")


if __name__ == "__main__":
    main()
