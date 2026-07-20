"""
Tier-1 summary: cross sections, K-factor, 7-point scale envelopes,
negative-weight fraction / Neff for NLO. Reads the .npz files produced
by analyze_lo.py / analyze_nlo.py. Prints a plain-text summary table and
writes it to analysis/tier1_summary.txt (also used verbatim in the
progress report).
"""
import numpy as np

LO = np.load("analysis/parsed/lo_events.npz")
NLO = np.load("analysis/parsed/nlo_events.npz")

# Authoritative MC run numbers (from run summaries, per spec Step 2)
SIGMA_LO_RUN = 520.4
SIGMA_LO_RUN_ERR = 0.7669
SIGMA_LO_BANNER = 520.365  # MGGenerationInfo integrated weight

SIGMA_NLO_RUN = 700.0
SIGMA_NLO_RUN_ERR = 4.2

LO_SEVEN_IDS = ["4", "9", "19", "23", "28", "38", "43"]
LO_LABELS = {
    "4": "(0.5,0.5)", "9": "(0.5,1.0)", "19": "(1.0,0.5)", "23": "(1.0,1.0)*",
    "28": "(1.0,2.0)", "38": "(2.0,1.0)", "43": "(2.0,2.0)",
}
NLO_SEVEN_IDS = ["1001", "1002", "1003", "1004", "1005", "1007", "1009"]
NLO_LABELS = {
    "1001": "(1.0,1.0)*", "1002": "(2.0,1.0)", "1003": "(0.5,1.0)",
    "1004": "(1.0,2.0)", "1005": "(2.0,2.0)", "1007": "(1.0,0.5)", "1009": "(0.5,0.5)",
}


def envelope(npz, ids, central_id, n_events):
    sums = {i: npz[f"scale_{i}"].sum() / n_events for i in ids}
    central = sums[central_id]
    up = max(sums.values()) - central
    down = central - min(sums.values())
    pct_up = 100 * up / central
    pct_down = 100 * down / central
    return sums, central, pct_up, pct_down


def main():
    n_lo = int(LO["n_events"])
    n_nlo = int(NLO["n_events"])

    lo_sums, lo_central, lo_up, lo_down = envelope(LO, LO_SEVEN_IDS, "23", n_lo)
    nlo_sums, nlo_central, nlo_up, nlo_down = envelope(NLO, NLO_SEVEN_IDS, "1001", n_nlo)

    xwgt_lo = LO["xwgt"]
    xwgt_nlo = NLO["xwgt"]
    sigma_lo_evt = xwgt_lo.sum() / n_lo
    sigma_nlo_evt = xwgt_nlo.sum() / n_nlo
    # simple MC error estimate from the event sample itself (cross-check only)
    err_lo_evt = np.sqrt(((xwgt_lo - sigma_lo_evt) ** 2).sum()) / n_lo
    err_nlo_evt = np.sqrt(((xwgt_nlo - sigma_nlo_evt) ** 2).sum()) / n_nlo

    f_minus = float(NLO["f_minus"])
    n_eff = float(NLO["n_eff"])
    n_neg = int(NLO["n_neg"])

    k_factor_run = SIGMA_NLO_RUN / SIGMA_LO_RUN
    k_factor_evt = sigma_nlo_evt / sigma_lo_evt

    lines = []
    lines.append("=" * 78)
    lines.append("Tier-1 summary: pp -> t t~ at 13 TeV, LO vs NLO QCD")
    lines.append("=" * 78)
    lines.append("")
    lines.append(f"{'':28s}{'LO':>20s}{'NLO':>20s}")
    lines.append(f"{'sigma [pb] (run summary)':28s}"
                 f"{f'{SIGMA_LO_RUN:.4f} +- {SIGMA_LO_RUN_ERR:.4f}':>20s}"
                 f"{f'{SIGMA_NLO_RUN:.4f} +- {SIGMA_NLO_RUN_ERR:.4f}':>20s}")
    lines.append(f"{'sigma [pb] (banner, high-prec)':28s}{f'{SIGMA_LO_BANNER:.4f}':>20s}{'':>20s}")
    lines.append(f"{'sigma [pb] (avg event weight)':28s}"
                 f"{f'{sigma_lo_evt:.4f} +- {err_lo_evt:.4f}':>20s}"
                 f"{f'{sigma_nlo_evt:.4f} +- {err_nlo_evt:.4f}':>20s}")
    lines.append(f"{'7-pt scale envelope [%]':28s}"
                 f"{f'+{lo_up:.2f} / -{lo_down:.2f}':>20s}"
                 f"{f'+{nlo_up:.2f} / -{nlo_down:.2f}':>20s}")
    lines.append(f"{'7-pt central sigma [pb]':28s}{f'{lo_central:.4f}':>20s}{f'{nlo_central:.4f}':>20s}")
    lines.append(f"{'K-factor (run summary)':28s}{'':>20s}{f'{k_factor_run:.4f}':>20s}")
    lines.append(f"{'K-factor (event avg)':28s}{'':>20s}{f'{k_factor_evt:.4f}':>20s}")
    lines.append(f"{'Negative-weight fraction':28s}{'0.000%':>20s}{f'{100*f_minus:.3f}%':>20s}")
    lines.append(f"{'N_eff (NLO only)':28s}{'':>20s}{f'{n_eff:.1f} (of {n_nlo})':>20s}")
    n_wgt_lo = int(LO["n_wgt_ids_per_event"])
    n_wgt_nlo = int(NLO["n_wgt_ids_per_event"])
    lines.append(f"{'<wgt> entries per event':28s}{n_wgt_lo:>20d}{n_wgt_nlo:>20d}")
    lines.append("")

    narrower = (nlo_up < lo_up) and (nlo_down < lo_down)
    lines.append(f"NLO scale band narrower than LO scale band on BOTH sides: {narrower}")
    if not narrower:
        lines.append("*** FLAG: NLO scale band is NOT narrower than LO on at least one side! ***")
    lines.append("")

    lines.append("-" * 78)
    lines.append("LO 7-point breakdown (sigma [pb] at each (muR,muF), sum(w_i)/N):")
    for i in LO_SEVEN_IDS:
        lines.append(f"  id={i:>4s}  {LO_LABELS[i]:>14s}  sigma = {lo_sums[i]:10.4f} pb")
    lines.append("")
    lines.append("NLO 7-point breakdown (sigma [pb] at each (muR,muF), sum(w_i)/N):")
    for i in NLO_SEVEN_IDS:
        lines.append(f"  id={i:>4s}  {NLO_LABELS[i]:>14s}  sigma = {nlo_sums[i]:10.4f} pb")
    lines.append("-" * 78)

    lines.append("")
    lines.append("Physics sanity checks:")
    pt_ttbar_lo_max = np.abs(LO["pt_ttbar"]).max()
    dphi_lo = LO["dphi"]
    dphi_lo_min = dphi_lo.min()
    lines.append(f"  LO max |pT(ttbar)|          = {pt_ttbar_lo_max:.3e} GeV  (expect ~0, exact delta function)")
    lines.append(f"  LO min Delta-phi            = {dphi_lo_min:.10f} rad (pi = {np.pi:.10f})")
    pt_ttbar_nlo = NLO["pt_ttbar"]
    lines.append(f"  NLO pT(ttbar) > 1 GeV frac  = {100*np.mean(pt_ttbar_nlo>1.0):.2f}% (nonzero tail present: {np.any(pt_ttbar_nlo>1.0)})")
    dphi_nlo = NLO["dphi"]
    lines.append(f"  NLO Delta-phi < 3.0 frac    = {100*np.mean(dphi_nlo<3.0):.2f}% (nonzero tail below pi present: {np.any(dphi_nlo<3.0)})")
    k_ok = 1.3 <= k_factor_run <= 1.6
    lines.append(f"  K-factor in [1.3,1.6]?      = {k_ok}  (K={k_factor_run:.4f})")
    lines.append(f"  Negative-weight frac != 0?  = {f_minus>0}  (f_minus={f_minus:.5f})")

    text = "\n".join(lines)
    print(text)
    with open("analysis/tier1_summary.txt", "w") as f:
        f.write(text + "\n")


if __name__ == "__main__":
    main()
