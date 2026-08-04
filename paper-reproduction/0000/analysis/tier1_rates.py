"""
Tier 1: total cross sections, K-factor, and 7-point scale-uncertainty
envelope for the LO and NLO ttbar 13 TeV samples.

Reads the cached per-event arrays produced by extract_observables.py
(analysis/cache/{lo,nlo}_events.npz) -- no re-parsing of the LHE files.

sigma = sum(weight_i) / N_gen  (pb), the unified LO/NLO weighting formula
from the pheno-analyzer skill's normalization-conventions.md, with the
"absolute cross section" special case L=1 (units pb, not events/luminosity).

Writes output/data/tier1_summary.json.
"""

from __future__ import annotations

import json

import numpy as np

from parse_lhe import ENVELOPE_LABELS

N_GEN_LO = 100_000
N_GEN_NLO = 100_000

# MC-integration cross sections + errors as reported by the generator run
# summaries (progress/ttbar_13tev_lo_vs_nlo/step{2,3}_*.md), used for the
# headline sigma +/- MC-error line. Cross-checked below against our own
# sum-of-weights computation from the LHE files.
SIGMA_LO_REPORTED = (519.9, 0.162)  # pb
SIGMA_NLO_REPORTED = (697.0, 2.3)  # pb


def kish_neff(w):
    w = np.asarray(w, dtype=float)
    denom = np.sum(w**2)
    if denom == 0:
        return 0.0
    return float(np.sum(w) ** 2 / denom)


def envelope(env_weights: dict, n_gen: int):
    """env_weights: {label: array of per-event weights for that (muR,muF)}.
    Returns (central, totals_dict, up_pct, down_pct)."""
    totals = {lab: float(np.sum(w)) / n_gen for lab, w in env_weights.items()}
    central = totals["central_1_1"]
    deltas_pct = {lab: 100.0 * (t - central) / central for lab, t in totals.items()}
    up_pct = max(deltas_pct.values())
    down_pct = min(deltas_pct.values())
    return central, totals, deltas_pct, up_pct, down_pct


def analyze(cache_path: str, n_gen: int, label: str):
    d = np.load(cache_path)
    xwgtup = d["xwgtup"]

    n_events = len(xwgtup)
    n_neg = int(np.sum(xwgtup < 0))
    f_minus = n_neg / n_events

    sigma = float(np.sum(xwgtup)) / n_gen
    mc_err = float(np.sqrt(np.sum(xwgtup**2))) / n_gen
    neff = kish_neff(xwgtup / n_gen)

    env_weights = {lab: d[f"env_{lab}"] for lab in ENVELOPE_LABELS}
    central, totals, deltas_pct, up_pct, down_pct = envelope(env_weights, n_gen)

    print(f"=== {label} ===")
    print(f"  N_gen = {n_gen}, N_events_in_file = {n_events}")
    print(f"  sigma (sum(XWGTUP)/N_gen) = {sigma:.4f} pb, MC error (sqrt(sum(w^2))/N_gen) = {mc_err:.4f} pb")
    print(f"  negative-weight fraction (independent recount) = {f_minus*100:.4f}% ({n_neg}/{n_events})")
    print(f"  Neff (Kish, general formula) = {neff:.1f}")
    print(f"  central-scale (muR=muF=1) total from id-central weights = {central:.4f} pb "
          f"(cross-check vs sum(XWGTUP)/N_gen = {sigma:.4f} pb)")
    print(f"  7-point scale envelope: {up_pct:+.2f}% / {down_pct:+.2f}% around central")
    for lab, pct in sorted(deltas_pct.items(), key=lambda kv: kv[1]):
        print(f"    {lab:16s}: total={totals[lab]:10.4f} pb  delta={pct:+7.3f}%")

    return {
        "label": label,
        "n_gen": n_gen,
        "n_events_in_file": n_events,
        "sigma_pb": sigma,
        "mc_error_pb": mc_err,
        "neff": neff,
        "f_minus": f_minus,
        "n_negative": n_neg,
        "central_scale_total_pb": central,
        "scale_envelope_totals_pb": totals,
        "scale_envelope_deltas_pct": deltas_pct,
        "scale_envelope_up_pct": up_pct,
        "scale_envelope_down_pct": down_pct,
    }


def main():
    lo = analyze("analysis/cache/lo_events.npz", N_GEN_LO, "LO")
    nlo = analyze("analysis/cache/nlo_events.npz", N_GEN_NLO, "NLO")

    k_factor = nlo["sigma_pb"] / lo["sigma_pb"]
    print()
    print(f"K-factor = sigma_NLO / sigma_LO = {nlo['sigma_pb']:.4f} / {lo['sigma_pb']:.4f} = {k_factor:.4f}")
    if not (1.3 <= k_factor <= 1.6):
        print(f"  *** FLAG: K-factor {k_factor:.4f} is OUTSIDE the expected 1.3-1.6 sanity range ***")
    else:
        print(f"  K-factor within expected 1.3-1.6 sanity range: PASS")

    lo_band_width = lo["scale_envelope_up_pct"] - lo["scale_envelope_down_pct"]
    nlo_band_width = nlo["scale_envelope_up_pct"] - nlo["scale_envelope_down_pct"]
    print()
    print(f"LO scale band total width = {lo_band_width:.3f} pct points "
          f"({lo['scale_envelope_up_pct']:+.2f}/{lo['scale_envelope_down_pct']:+.2f})")
    print(f"NLO scale band total width = {nlo_band_width:.3f} pct points "
          f"({nlo['scale_envelope_up_pct']:+.2f}/{nlo['scale_envelope_down_pct']:+.2f})")
    if nlo_band_width < lo_band_width:
        print("  NLO band narrower than LO band: PASS")
    else:
        print("  *** FLAG: NLO scale band is NOT narrower than LO scale band -- problem, needs investigation ***")

    # Cross-check against generator-reported MC-integration cross sections
    print()
    for label, reported, computed in [
        ("LO", SIGMA_LO_REPORTED, lo["sigma_pb"]),
        ("NLO", SIGMA_NLO_REPORTED, nlo["sigma_pb"]),
    ]:
        rel_diff = 100 * (computed - reported[0]) / reported[0]
        print(
            f"{label}: generator-reported sigma = {reported[0]} +/- {reported[1]} pb; "
            f"our sum-of-weights sigma = {computed:.4f} pb (rel. diff {rel_diff:+.3f}%)"
        )

    summary = {
        "LO": lo,
        "NLO": nlo,
        "K_factor": k_factor,
        "K_factor_in_sane_range": bool(1.3 <= k_factor <= 1.6),
        "LO_scale_band_width_pct": lo_band_width,
        "NLO_scale_band_width_pct": nlo_band_width,
        "NLO_band_narrower_than_LO": bool(nlo_band_width < lo_band_width),
        "generator_reported": {
            "LO_sigma_pb": SIGMA_LO_REPORTED[0],
            "LO_mc_err_pb": SIGMA_LO_REPORTED[1],
            "NLO_sigma_pb": SIGMA_NLO_REPORTED[0],
            "NLO_mc_err_pb": SIGMA_NLO_REPORTED[1],
        },
    }
    with open("output/data/tier1_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    print("\nWrote output/data/tier1_summary.json")


if __name__ == "__main__":
    main()
