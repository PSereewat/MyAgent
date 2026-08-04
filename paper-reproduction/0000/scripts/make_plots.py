"""
Tier 2 plots: LO vs NLO differential cross sections for pp > ttbar at
13 TeV, parton level, from output/data/{observable}.json (produced by
analysis/make_histograms.py).

Conventions:
  - LO: green step histogram.
  - NLO: blue step histogram, with statistical error bars
    (error = sqrt(sum(w_i**2))/binwidth) and a shaded 7-point
    (muR,muF) scale-uncertainty band.
  - Lower ratio panel (NLO/LO differential K-factor) for pT_t, m_ttbar,
    y_t. Omitted for pT_ttbar and Delta_phi_ttbar because LO is a delta
    function there (ratio is undefined/meaningless) -- the LO
    delta-function bin content is instead stated explicitly in the
    figure caption, per spec.
  - Bins where a histogrammed value is <= 0 cannot be shown on a log
    y-axis; those points are left as gaps in the step line (never
    fabricated/interpolated) and are called out in the caption/progress
    report with their physical origin (see progress report for details).

All paths relative to the repository working directory.
"""

from __future__ import annotations

import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

OUTDIR = "output/figures"
os.makedirs(OUTDIR, exist_ok=True)

COND_LABEL = (
    r"$\sqrt{s}=13$ TeV, $m_t=172.5$ GeV, $\mu_R=\mu_F=H_T/2$" + "\n"
    "LO PDF: NNPDF23_lo_as_0130_qed  |  NLO PDF: NNPDF23_nlo_as_0119_qed"
)

LO_COLOR = "tab:green"
NLO_COLOR = "tab:blue"
BAND_COLOR = "tab:blue"


def load(name):
    with open(f"output/data/{name}.json") as f:
        return json.load(f)


def step_xy(edges, values):
    """Return (x, y) arrays for a proper post-style step plot that
    includes the final bin's right edge."""
    x = np.append(edges[:-1], edges[-1])
    y = np.append(values, values[-1])
    return x, y


def plot_observable(
    name,
    xlabel,
    ylabel,
    logy,
    has_ratio,
    outfile_stub,
    title,
    caption_note=None,
):
    d = load(name)
    edges = np.array(d["bin_edges"])
    centers = np.array(d["bin_centers"])

    lo_y = np.array(d["LO"]["dsigma_dX"])
    lo_e = np.array(d["LO"]["error"])
    nlo_y = np.array(d["NLO"]["dsigma_dX"])
    nlo_e = np.array(d["NLO"]["error"])
    band_up = nlo_y + np.array(d["NLO"]["scale_band_up"])
    band_down = nlo_y + np.array(d["NLO"]["scale_band_down"])

    if has_ratio:
        fig, (ax1, ax2) = plt.subplots(
            2, 1, figsize=(7.2, 7.5), sharex=True,
            gridspec_kw={"height_ratios": [3, 1], "hspace": 0.06},
        )
    else:
        fig, ax1 = plt.subplots(1, 1, figsize=(7.2, 6.0))
        ax2 = None

    # --- upper panel ---
    lo_plot = np.where(lo_y > 0, lo_y, np.nan)
    nlo_plot = np.where(nlo_y > 0, nlo_y, np.nan)

    x_lo, y_lo = step_xy(edges, lo_plot)
    x_nlo, y_nlo = step_xy(edges, nlo_plot)

    # scale band (only where central NLO value is positive, log-safe)
    band_up_plot = np.where(nlo_y > 0, np.maximum(band_up, 1e-300), np.nan)
    band_down_plot = np.where(nlo_y > 0, band_down, np.nan)
    if logy:
        floor = np.nanmin(nlo_plot) * 1e-3 if np.any(nlo_y > 0) else 1e-10
        band_down_plot = np.where(band_down_plot > 0, band_down_plot, floor)

    ax1.fill_between(
        centers, band_down_plot, band_up_plot, step="mid",
        color=BAND_COLOR, alpha=0.25, linewidth=0,
        label="NLO 7-pt scale envelope",
    )
    ax1.step(x_lo, y_lo, where="post", color=LO_COLOR, linewidth=1.6, label="LO")
    ax1.step(x_nlo, y_nlo, where="post", color=NLO_COLOR, linewidth=1.6, label="NLO")

    lo_mask = lo_y > 0
    nlo_mask = nlo_y > 0
    ax1.errorbar(
        centers[lo_mask], lo_y[lo_mask], yerr=lo_e[lo_mask],
        fmt="none", ecolor=LO_COLOR, elinewidth=1, capsize=1.5, alpha=0.8,
    )
    ax1.errorbar(
        centers[nlo_mask], nlo_y[nlo_mask], yerr=nlo_e[nlo_mask],
        fmt="none", ecolor=NLO_COLOR, elinewidth=1, capsize=1.5, alpha=0.8,
    )

    if logy:
        ax1.set_yscale("log")
    ax1.set_ylabel(ylabel)
    ax1.set_title(title, fontsize=11)
    ax1.legend(loc="best", fontsize=9)
    ax1.text(
        0.02, 0.03, COND_LABEL, transform=ax1.transAxes,
        fontsize=7.5, va="bottom", ha="left",
        bbox=dict(boxstyle="round", facecolor="white", edgecolor="0.7", alpha=0.85),
    )

    if has_ratio:
        ratio = np.array([np.nan if v is None else v for v in d["ratio_NLO_over_LO"]])
        ratio_err = np.array([np.nan if v is None else abs(v) for v in d["ratio_error"]])
        finite_mask = np.isfinite(ratio) & np.isfinite(ratio_err)
        ax2.errorbar(
            centers[finite_mask], ratio[finite_mask], yerr=ratio_err[finite_mask],
            fmt="o", color="black", markersize=3, elinewidth=1, capsize=1.5,
        )
        ax2.axhline(1.0, color="gray", linestyle="--", linewidth=1)
        ax2.set_ylabel("NLO / LO")
        ax2.set_xlabel(xlabel)
        finite = ratio[np.isfinite(ratio)]
        if len(finite) > 0:
            lo_lim = max(0, np.nanpercentile(finite, 2) - 0.3)
            hi_lim = np.nanpercentile(finite, 98) + 0.3
            ax2.set_ylim(lo_lim, hi_lim)
    else:
        ax1.set_xlabel(xlabel)

    ax1.set_xlim(edges[0], edges[-1])

    if caption_note:
        fig.text(0.02, -0.02, caption_note, fontsize=7.5, wrap=True, va="top")

    fig.tight_layout()
    pdf_path = f"{OUTDIR}/{outfile_stub}.pdf"
    png_path = f"{OUTDIR}/{outfile_stub}.png"
    fig.savefig(pdf_path, bbox_inches="tight", dpi=200)
    fig.savefig(png_path, bbox_inches="tight", dpi=200)
    plt.close(fig)
    print(f"Saved {pdf_path} and {png_path}")


def main():
    # --- pT_ttbar ---
    d = load("pt_ttbar")
    lo_bin0 = d["LO"]["dsigma_dX"][0]
    lo_bin0_count = d["LO"]["raw_count"][0]
    plot_observable(
        "pt_ttbar",
        xlabel=r"$p_T^{t\bar t}$ [GeV]",
        ylabel=r"$d\sigma/dp_T^{t\bar t}$ [pb/GeV]",
        logy=True,
        has_ratio=False,
        outfile_stub="pt_ttbar",
        title=r"$p_T^{t\bar t}$ distribution, $pp\to t\bar t$ @ 13 TeV",
        caption_note=(
            f"LO is an exact delta function at $p_T^{{t\\bar t}}=0$ (all "
            f"{lo_bin0_count}/100000 LO events, back-to-back 2->2 kinematics): "
            f"first-bin (0-10 GeV) entry only, "
            f"$d\\sigma/dp_T$={lo_bin0:.4f} pb/GeV (=$\\sigma_{{LO}}$/binwidth). "
            f"NLO shows a genuine nonzero tail from real QCD emission. Ratio "
            f"panel omitted (LO is a delta function, ratio undefined). NLO "
            f"bin 10-20 GeV is negative "
            f"({d['NLO']['dsigma_dX'][1]:.3f}+/-{d['NLO']['error'][1]:.3f} pb/GeV, "
            f"f_minus={d['NLO']['f_minus'][1]:.2f}) -- a known fixed-order-NLO "
            f"feature immediately next to the Born (pT->0) boundary from "
            f"incomplete real/virtual cancellation, not a bug; omitted from "
            f"the log-scale line as a gap."
        ),
    )

    # --- Delta_phi_ttbar ---
    d = load("dphi_ttbar")
    lo_last = d["LO"]["dsigma_dX"][-1]
    lo_last_count = d["LO"]["raw_count"][-1]
    plot_observable(
        "dphi_ttbar",
        xlabel=r"$\Delta\phi_{t\bar t}$ [rad]",
        ylabel=r"$d\sigma/d\Delta\phi_{t\bar t}$ [pb/rad]",
        logy=True,
        has_ratio=False,
        outfile_stub="dphi_ttbar",
        title=r"$\Delta\phi_{t\bar t}$ distribution, $pp\to t\bar t$ @ 13 TeV",
        caption_note=(
            f"LO is an exact delta function at $\\Delta\\phi_{{t\\bar t}}=\\pi$ "
            f"(all {lo_last_count}/100000 LO events): last-bin entry only, "
            f"$d\\sigma/d\\Delta\\phi$={lo_last:.2f} pb/rad (=$\\sigma_{{LO}}$/binwidth). "
            f"NLO shows a genuine nonzero tail below pi from real emission. "
            f"Ratio panel omitted (LO is a delta function). The second-to-last "
            f"bin ({d['bin_edges'][-3]:.3f}-{d['bin_edges'][-2]:.3f} rad, "
            f"immediately below the pi-containing last bin) is negative and "
            f"statistically consistent with zero within its (comparable-"
            f"magnitude) error "
            f"({d['NLO']['dsigma_dX'][-2]:.2f}+/-{d['NLO']['error'][-2]:.2f} pb/rad, "
            f"Neff={d['NLO']['neff'][-2]:.2f}) -- heavy positive/negative-weight "
            f"cancellation immediately below the LO boundary; omitted from the "
            f"log-scale line."
        ),
    )

    # --- pT_t ---
    plot_observable(
        "pt_t",
        xlabel=r"$p_T^{t}$ [GeV]",
        ylabel=r"$d\sigma/dp_T^{t}$ [pb/GeV]",
        logy=True,
        has_ratio=True,
        outfile_stub="pt_t",
        title=r"Top-quark $p_T$ distribution, $pp\to t\bar t$ @ 13 TeV",
        caption_note=(
            "Highest-pT tail bins (740-760, 780-800 GeV) have very low raw "
            "statistics (3 and 6 NLO events respectively) and are omitted "
            "from the log-scale line where their central value is <=0; ratio "
            "points are correspondingly absent there."
        ),
    )

    # --- m_ttbar ---
    plot_observable(
        "m_ttbar",
        xlabel=r"$m_{t\bar t}$ [GeV]",
        ylabel=r"$d\sigma/dm_{t\bar t}$ [pb/GeV]",
        logy=True,
        has_ratio=True,
        outfile_stub="m_ttbar",
        title=r"$t\bar t$ invariant-mass distribution, $pp\to t\bar t$ @ 13 TeV",
        caption_note=(
            "First bin (300-330 GeV) is exactly zero for both LO and NLO "
            "(0 raw events each) because it lies entirely below the "
            "kinematic threshold $m_{t\\bar t}\\geq 2m_t=345$ GeV -- a "
            "physical zero, not a statistics artifact."
        ),
    )

    # --- y_t ---
    plot_observable(
        "y_t",
        xlabel=r"$y_t$",
        ylabel=r"$d\sigma/dy_t$ [pb]",
        logy=False,
        has_ratio=True,
        outfile_stub="y_t",
        title=r"Top-quark rapidity distribution, $pp\to t\bar t$ @ 13 TeV",
        caption_note=None,
    )


if __name__ == "__main__":
    main()
