"""
Tier-2 differential-distribution plots: LO vs NLO overlay, for both the
absolute dsigma/dX histogram and an area-normalized (shape-only) version,
for all five observables specified in the task. Each figure has a lower
ratio panel (NLO/LO differential K-factor) except for pT(ttbar) and
Delta-phi, where LO is a delta function.

The K-factor ratio panel's uncertainty band is a *joint/correlated* 7-point
scale envelope: at each of the 7 (muR,muF) grid points, LO and NLO are
each re-evaluated at that same scale (paired via PAIRED_SCALE_IDS) and
their ratio taken; the band is the min/max of those 7 paired ratios. This
varies both numerator and denominator together bin-by-bin, unlike simply
dividing the NLO-only scale envelope by the LO central value.

Reads: analysis/parsed/lo_events.npz, analysis/parsed/nlo_events.npz
Writes: output/figures/*.pdf, output/figures/*.png, output/csv/*.csv
"""
import csv
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

CSV_DIR = "output/csv"
os.makedirs(CSV_DIR, exist_ok=True)

LO = np.load("analysis/parsed/lo_events.npz")
NLO = np.load("analysis/parsed/nlo_events.npz")

N_LO = int(LO["n_events"])
N_NLO = int(NLO["n_events"])

LO_SEVEN_IDS = ["4", "9", "19", "23", "28", "38", "43"]
NLO_SEVEN_IDS = ["1001", "1002", "1003", "1004", "1005", "1007", "1009"]

# Same 7 (muR,muF) grid points, paired LO id <-> NLO id (ids differ, scale
# choice is the same). Verified against each script's own <initrwgt> mapping:
#   (0.5,0.5): LO 4  <-> NLO 1009
#   (0.5,1.0): LO 9  <-> NLO 1003
#   (1.0,0.5): LO 19 <-> NLO 1007
#   (1.0,1.0): LO 23 <-> NLO 1001  (central)
#   (1.0,2.0): LO 28 <-> NLO 1004
#   (2.0,1.0): LO 38 <-> NLO 1002
#   (2.0,2.0): LO 43 <-> NLO 1005
PAIRED_SCALE_IDS = [
    ("4", "1009"), ("9", "1003"), ("19", "1007"), ("23", "1001"),
    ("28", "1004"), ("38", "1002"), ("43", "1005"),
]

GREEN = (0 / 255, 120 / 255, 0 / 255)
BLUE = (0 / 255, 0 / 255, 200 / 255)
PURPLE = (130 / 255, 0 / 255, 140 / 255)

LABEL_TEXT = (r"$\sqrt{s}=13$ TeV, $m_t=172.5$ GeV, $\mu_R=\mu_F=H_T/2$"
              "\nLO: NNPDF23_lo_as_0130_qed  |  NLO: NNPDF23_nlo_as_0119_qed")

OBS = [
    dict(key="pt_ttbar", bins=40, range=(0, 400), xlabel=r"$p_T(t\bar t)$ [GeV]",
         ylabel=r"$d\sigma/dp_T(t\bar t)$ [pb/GeV]", logy=True, ratio=False,
         title=r"$p_T$ of the $t\bar t$ system"),
    dict(key="dphi", bins=40, range=(0, np.pi), xlabel=r"$\Delta\phi(t,\bar t)$ [rad]",
         ylabel=r"$d\sigma/d\Delta\phi$ [pb/rad]", logy=True, ratio=False,
         title=r"Azimuthal separation $\Delta\phi(t,\bar t)$"),
    dict(key="pt_t", bins=40, range=(0, 800), xlabel=r"$p_T(t)$ [GeV]",
         ylabel=r"$d\sigma/dp_T(t)$ [pb/GeV]", logy=True, ratio=True,
         title=r"$p_T$ of the top quark"),
    dict(key="m_ttbar", bins=40, range=(300, 1500), xlabel=r"$m(t\bar t)$ [GeV]",
         ylabel=r"$d\sigma/dm(t\bar t)$ [pb/GeV]", logy=True, ratio=True,
         title=r"Invariant mass of the $t\bar t$ pair"),
    dict(key="y_t", bins=40, range=(-3, 3), xlabel=r"$y(t)$",
         ylabel=r"$d\sigma/dy(t)$ [pb]", logy=False, ratio=True,
         title=r"Top-quark rapidity"),
]


def weighted_hist(values, weights, edges):
    """Return (sum_per_bin, sumsq_per_bin) using physical (already 1/N-scaled)
    per-event weights."""
    s, _ = np.histogram(values, bins=edges, weights=weights)
    s2, _ = np.histogram(values, bins=edges, weights=weights ** 2)
    return s, s2


def dsigma(values, xwgt, n_events, edges):
    w = xwgt / n_events
    s, s2 = weighted_hist(values, w, edges)
    widths = np.diff(edges)
    val = s / widths
    err = np.sqrt(s2) / widths
    return val, err


def dsigma_variant(values, wgt_id_array, n_events, edges):
    w = wgt_id_array / n_events
    s, _ = np.histogram(values, bins=edges, weights=w)
    widths = np.diff(edges)
    return s / widths


def scale_band(values, npz, ids, n_events, edges):
    variants = np.array([dsigma_variant(values, npz[f"scale_{i}"], n_events, edges) for i in ids])
    return variants.min(axis=0), variants.max(axis=0)


def joint_kfactor_band(key, edges, widths, normalize):
    """K-factor envelope from a *correlated* 7-point scale variation: at each
    of the 7 (muR,muF) grid points, evaluate LO and NLO at that SAME scale
    (via PAIRED_SCALE_IDS), take their ratio, then min/max across the 7
    paired ratios. Unlike dividing the NLO-only envelope by the LO central
    value, this varies both numerator and denominator together bin-by-bin."""
    ratios = []
    for lo_id, nlo_id in PAIRED_SCALE_IDS:
        lv = dsigma_variant(LO[key], LO[f"scale_{lo_id}"], N_LO, edges)
        nv = dsigma_variant(NLO[key], NLO[f"scale_{nlo_id}"], N_NLO, edges)
        if normalize:
            lv = lv / (lv * widths).sum()
            nv = nv / (nv * widths).sum()
        with np.errstate(divide="ignore", invalid="ignore"):
            ratios.append(np.where(lv > 0, nv / lv, np.nan))
    ratios = np.array(ratios)
    return np.nanmin(ratios, axis=0), np.nanmax(ratios, axis=0)


def step_edges(edges, val):
    """Return x,y arrays suitable for a step ('post') style plot."""
    x = np.repeat(edges, 2)[1:-1]
    y = np.repeat(val, 2)
    return x, y


def make_figure(o, normalize):
    key = o["key"]
    edges = np.linspace(o["range"][0], o["range"][1], o["bins"] + 1)
    widths = np.diff(edges)
    centers = 0.5 * (edges[:-1] + edges[1:])

    lo_val, lo_err = dsigma(LO[key], LO["xwgt"], N_LO, edges)
    nlo_val, nlo_err = dsigma(NLO[key], NLO["xwgt"], N_NLO, edges)
    band_lo, band_hi = scale_band(NLO[key], NLO, NLO_SEVEN_IDS, N_NLO, edges)
    lo_band_lo, lo_band_hi = scale_band(LO[key], LO, LO_SEVEN_IDS, N_LO, edges)

    if normalize:
        lo_norm = (lo_val * widths).sum()
        nlo_norm = (nlo_val * widths).sum()
        lo_val_p, lo_err_p = lo_val / lo_norm, lo_err / lo_norm
        nlo_val_p, nlo_err_p = nlo_val / nlo_norm, nlo_err / nlo_norm
        # normalize each scale-variant band independently by its own integral (shape-only band)
        variants = np.array([dsigma_variant(NLO[key], NLO[f"scale_{i}"], N_NLO, edges)
                              for i in NLO_SEVEN_IDS])
        variant_norms = (variants * widths[None, :]).sum(axis=1, keepdims=True)
        variants_shape = variants / variant_norms
        band_lo_p = variants_shape.min(axis=0)
        band_hi_p = variants_shape.max(axis=0)

        lo_variants = np.array([dsigma_variant(LO[key], LO[f"scale_{i}"], N_LO, edges)
                                 for i in LO_SEVEN_IDS])
        lo_variant_norms = (lo_variants * widths[None, :]).sum(axis=1, keepdims=True)
        lo_variants_shape = lo_variants / lo_variant_norms
        lo_band_lo_p = lo_variants_shape.min(axis=0)
        lo_band_hi_p = lo_variants_shape.max(axis=0)

        lo_val, lo_err = lo_val_p, lo_err_p
        nlo_val, nlo_err = nlo_val_p, nlo_err_p
        band_lo, band_hi = band_lo_p, band_hi_p
        lo_band_lo, lo_band_hi = lo_band_lo_p, lo_band_hi_p
        ylabel = "Normalized " + o["ylabel"].split("[")[0].strip() + " (shape, area=1)"
    else:
        ylabel = o["ylabel"]

    has_ratio = o["ratio"]
    if has_ratio:
        fig, (ax, axr) = plt.subplots(2, 1, figsize=(7, 7), sharex=True,
                                       gridspec_kw=dict(height_ratios=[3, 1], hspace=0.06))
    else:
        fig, ax = plt.subplots(1, 1, figsize=(7, 5.5))
        axr = None

    # NLO scale band
    bx = np.repeat(edges, 2)[1:-1]
    blo = np.repeat(band_lo, 2)
    bhi = np.repeat(band_hi, 2)
    ax.fill_between(bx, blo, bhi, step=None, color=BLUE, alpha=0.20,
                     label="NLO 7-pt scale envelope", linewidth=0)

    # LO scale band
    lo_blo = np.repeat(lo_band_lo, 2)
    lo_bhi = np.repeat(lo_band_hi, 2)
    ax.fill_between(bx, lo_blo, lo_bhi, step=None, color=GREEN, alpha=0.20,
                     label="LO 7-pt scale envelope", linewidth=0)

    xlo, ylo = step_edges(edges, lo_val)
    xnlo, ynlo = step_edges(edges, nlo_val)
    ax.step(edges[:-1], lo_val, where="post", color=GREEN, lw=1.8, label="LO")
    ax.step(edges[:-1], nlo_val, where="post", color=BLUE, lw=1.8, label="NLO")
    ax.errorbar(centers, lo_val, yerr=lo_err, fmt="none", ecolor=GREEN, elinewidth=1.0, capsize=0)
    ax.errorbar(centers, nlo_val, yerr=nlo_err, fmt="none", ecolor=BLUE, elinewidth=1.0, capsize=0)

    if o["logy"]:
        ax.set_yscale("log")
        pos = np.concatenate([lo_val[lo_val > 0], nlo_val[nlo_val > 0],
                               band_hi[band_hi > 0], lo_band_hi[lo_band_hi > 0]])
        if len(pos):
            ax.set_ylim(pos.min() * 0.3, pos.max() * 5)
    ax.set_xlim(o["range"])
    ax.set_ylabel(ylabel)
    ax.set_title(o["title"])
    ax.legend(loc="best", fontsize=9, frameon=False)
    ax.text(0.02, 0.98, LABEL_TEXT, transform=ax.transAxes, fontsize=8,
            va="top", ha="left")

    if key == "pt_ttbar":
        content = (LO["xwgt"].sum() / N_LO) / widths[0]
        ax.annotate(f"LO: entire cross section in bin 1\n"
                    f"({content:.2f} pb/GeV, exact delta fn. at 0)",
                    xy=(edges[1] * 0.5, lo_val[0]), xytext=(edges[1] * 3, lo_val[0] * 0.3),
                    fontsize=7.5, color=GREEN,
                    arrowprops=dict(arrowstyle="->", color=GREEN, lw=0.8))
    if key == "dphi":
        content = (LO["xwgt"].sum() / N_LO) / widths[-1]
        ax.annotate(f"LO: entire cross section in last bin\n"
                    f"({content:.2f} pb/rad, exact delta fn. at $\\pi$)",
                    xy=(edges[-2] + 0.5 * widths[-1], lo_val[-1]),
                    xytext=(edges[-2] - 1.6, lo_val[-1] * 0.3),
                    fontsize=7.5, color=GREEN,
                    arrowprops=dict(arrowstyle="->", color=GREEN, lw=0.8))

    if has_ratio:
        with np.errstate(divide="ignore", invalid="ignore"):
            ratio = np.where(lo_val > 0, nlo_val / lo_val, np.nan)
            ratio_err = np.where(lo_val > 0,
                                  np.abs(ratio) * np.sqrt((nlo_err / np.where(nlo_val != 0, nlo_val, np.nan)) ** 2
                                                   + (lo_err / lo_val) ** 2), np.nan)
            ratio_err = np.abs(ratio_err)
        joint_band_lo, joint_band_hi = joint_kfactor_band(key, edges, widths, normalize)
        axr.fill_between(bx, np.repeat(joint_band_lo, 2), np.repeat(joint_band_hi, 2),
                          color=PURPLE, alpha=0.20, linewidth=0,
                          label="Joint 7-pt scale envelope (LO+NLO correlated)")
        axr.step(edges[:-1], ratio, where="post", color="black", lw=1.4)
        axr.errorbar(centers, ratio, yerr=ratio_err, fmt="none", ecolor="black",
                     elinewidth=1.0, capsize=0)
        axr.axhline(1.0, color="gray", lw=1.0, ls="--")
        axr.set_ylabel("NLO/LO")
        axr.set_xlabel(o["xlabel"])
        axr.legend(loc="best", fontsize=7, frameon=False)
        finite = np.concatenate([ratio[np.isfinite(ratio)],
                                  joint_band_lo[np.isfinite(joint_band_lo)],
                                  joint_band_hi[np.isfinite(joint_band_hi)]])
        if len(finite):
            lo_lim = max(0, np.nanmin(finite) - 0.3)
            hi_lim = np.nanmax(finite) + 0.3
            axr.set_ylim(lo_lim, hi_lim)
    else:
        ax.set_xlabel(o["xlabel"])
        ratio = np.full_like(lo_val, np.nan)
        joint_band_lo = np.full_like(lo_val, np.nan)
        joint_band_hi = np.full_like(lo_val, np.nan)

    fig.tight_layout()
    tag = "shape" if normalize else "absolute"
    base = f"output/figures/{key}_{tag}"
    fig.savefig(base + ".pdf")
    fig.savefig(base + ".png", dpi=200)
    plt.close(fig)
    print(f"saved {base}.pdf / .png")

    csv_path = f"{CSV_DIR}/{key}_{tag}.csv"
    with open(csv_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["bin_low", "bin_high", "bin_center",
                    "lo_val", "lo_err", "lo_scale_env_low", "lo_scale_env_high",
                    "nlo_val", "nlo_err", "nlo_scale_env_low", "nlo_scale_env_high",
                    "kfactor", "kfactor_joint_scale_env_low", "kfactor_joint_scale_env_high"])
        for i in range(len(centers)):
            w.writerow([edges[i], edges[i + 1], centers[i],
                        lo_val[i], lo_err[i], lo_band_lo[i], lo_band_hi[i],
                        nlo_val[i], nlo_err[i], band_lo[i], band_hi[i],
                        ratio[i], joint_band_lo[i], joint_band_hi[i]])
    print(f"saved {csv_path}")


def main():
    for o in OBS:
        make_figure(o, normalize=False)
        make_figure(o, normalize=True)


if __name__ == "__main__":
    main()
