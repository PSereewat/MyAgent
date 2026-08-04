"""
NEW comparison (separate from the original 3-way LO/NLO/NLO+PS Tier 2
study and from the LO+PS-vs-NLO+PS study): LO fixed-order side of a
LO-vs-NLO-fixed-order-only overlay, using FINER bin edges
(`analysis/binning_finebin.py`) than the original Tier 2 defaults
(`analysis/binning.py`).

Input: run1_LO/pp_ttbar/Events/run_01/unweighted_events.lhe.gz (same
10000-event LO sample already used for the original study -- NOT
regenerated).

Normalization mode: ABSOLUTE YIELD (pb per bin, not shape-normalized) --
same convention as the original Tier 2 plots. Stated explicitly per
skill normalization-conventions.md.

Error convention: MC STATISTICAL uncertainty only (`sqrt(sum(w_i**2))`
per bin) -- no scale-variation band. This matches the original Tier 2
`make_plots.py` convention: that script only ever plots
`h["error_pb"]` (the statistical error from `weighted_histogram`) and
never reads/overlays the 7-point scale-variation numbers that
`analyze_nlo.py` separately computes for the Tier-1 rate table. Confirmed
by direct inspection of `make_plots.py` (no scale-envelope arrays are
loaded or plotted there) rather than assumed.

Negative-weight status (independently verified from the actual XWGTUP
values, not assumed): 0 negative-weight events, weight constant at
520.365 pb for every event (identical finding to the original
`analyze_lo.py`, since this is the same LHE file).

Bug found and fixed here (not present in this fine-bin version, but
present in the ORIGINAL `output/data/dphi_ttbar.csv`/`dphi_ttbar.png`):
`np.digitize` silently drops events whose value is exactly equal to the
last bin edge into an "overflow" bucket. Since `delta_phi_folded` caps
its output at exactly `math.pi` by construction, and essentially every
LO event's folded delta-phi evaluates to the bit-for-bit double value of
`math.pi`, the ORIGINAL 20-bin `weighted_histogram` call only counted
1290/10000 LO events in the last (peak) bin instead of the true ~10000.
This script uses `weighting.weighted_histogram_edge_safe` (a pure
addition to `weighting.py`, not a change to the existing
`weighted_histogram` function that the original scripts still use
unmodified) to fix this for the fine-binned comparison. See that
function's docstring for the full diagnostic.
"""

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from lhe_utils import iter_lhe_events, get_ttbar_final_state
from kinematics import pt, phi, rapidity, delta_phi_folded, invariant_mass, pair_pt
from weighting import weighted_histogram_edge_safe, negative_weight_fraction
from binning_finebin import FINE_BIN_EDGES, bin_centers

LHE_PATH = "run1_LO/pp_ttbar/Events/run_01/unweighted_events.lhe.gz"
OUT_DATA_DIR = "output/data/lo_vs_nlo_finebin"
os.makedirs(OUT_DATA_DIR, exist_ok=True)


def main():
    weights_raw = []
    obs = {k: [] for k in FINE_BIN_EDGES}
    n_events = 0
    n_bad = 0

    for ev in iter_lhe_events(LHE_PATH):
        n_events += 1
        try:
            top, atop = get_ttbar_final_state(ev)
        except ValueError:
            n_bad += 1
            continue

        p_top = (top.px, top.py, top.pz, top.e)
        p_atop = (atop.px, atop.py, atop.pz, atop.e)

        weights_raw.append(ev.weight)
        obs["pt_ttbar"].append(pair_pt(p_top, p_atop))
        obs["dphi_ttbar"].append(
            delta_phi_folded(phi(top.px, top.py), phi(atop.px, atop.py))
        )
        obs["pt_top_lead"].append(max(pt(top.px, top.py), pt(atop.px, atop.py)))
        obs["m_ttbar"].append(invariant_mass(p_top, p_atop))
        obs["y_t"].append(rapidity(top.pz, top.e))

    N_gen = n_events
    weights_raw = np.asarray(weights_raw)
    w_scaled = weights_raw / N_gen  # w_i = weight_i * L / N_gen, L=1 pb^-1

    negcheck = negative_weight_fraction(weights_raw)
    sigma = w_scaled.sum()
    err = np.sqrt((w_scaled**2).sum())

    print(f"[LO finebin] N_gen = {N_gen}, N_bad (failed ttbar extraction) = {n_bad}")
    print(f"[LO finebin] Negative-weight check: f_minus = {negcheck['f_minus']:.6f} "
          f"({negcheck['n_negative']}/{negcheck['n_total']}) -- expect exactly 0 for plain LO")
    print(f"[LO finebin] weight min/max = {weights_raw.min():.6f} / {weights_raw.max():.6f} pb "
          f"(should be identical -- constant unit weight)")
    print(f"[LO finebin] sigma (self-summed from LHE weights) = {sigma:.4f} +- {err:.4f} pb")

    pt_ttbar_arr = np.asarray(obs["pt_ttbar"])
    dphi_arr = np.asarray(obs["dphi_ttbar"])
    max_pt_ttbar = pt_ttbar_arr.max()
    min_dphi = dphi_arr.min()
    n_exact_pi = int(np.sum(dphi_arr == np.pi))
    print(f"[LO finebin] physics check: max(pT_ttbar) over all events = {max_pt_ttbar:.3e} GeV "
          f"(expect ~0, tree-level back-to-back)")
    print(f"[LO finebin] physics check: min(dphi_ttbar) over all events = {min_dphi:.10f} rad "
          f"(expect pi = {np.pi:.10f}); {n_exact_pi}/{n_events} events exactly at pi "
          "(bit-for-bit) -- these MUST all land in the last dphi_ttbar bin, verified below")

    hist_results = {}
    for obs_name, edges in FINE_BIN_EDGES.items():
        vals = np.asarray(obs[obs_name])
        w_for_hist = np.full(len(vals), weights_raw[0] / N_gen)
        res = weighted_histogram_edge_safe(vals, w_for_hist, edges)
        hist_results[obs_name] = res

    # Explicit verification that the edge-safe fix worked: all n_exact_pi
    # events must be captured in the last dphi_ttbar bin's n_raw.
    dphi_last_n_raw = int(hist_results["dphi_ttbar"]["n_raw"][-1])
    print(f"[LO finebin] dphi_ttbar last-bin n_raw = {dphi_last_n_raw} "
          f"(expect >= {n_exact_pi}, i.e. all exact-pi events captured, "
          f"vs. the ORIGINAL buggy Tier-2 result of only 1290/10000)")
    assert dphi_last_n_raw == n_events - n_bad, (
        "dphi_ttbar edge-safe fix did not capture all events in the last bin -- "
        f"got {dphi_last_n_raw}, expected {n_events - n_bad}"
    )

    out = {
        "run": "LO",
        "lhe_path": LHE_PATH,
        "N_gen": N_gen,
        "n_bad_ttbar_extraction": n_bad,
        "sigma_pb_self_summed": sigma,
        "sigma_err_pb_self_summed": err,
        "weight_const_pb": float(weights_raw[0]),
        "f_minus": negcheck["f_minus"],
        "n_negative": negcheck["n_negative"],
        "physics_check_max_pt_ttbar_GeV": max_pt_ttbar,
        "physics_check_min_dphi_ttbar_rad": min_dphi,
        "physics_check_n_exact_pi": n_exact_pi,
        "histograms": {
            k: {
                "bin_edges": FINE_BIN_EDGES[k].tolist(),
                "bin_centers": bin_centers(FINE_BIN_EDGES[k]).tolist(),
                "yield_pb": v["yield"].tolist(),
                "error_pb": v["error"].tolist(),
                "neff": v["neff"].tolist(),
                "n_raw": v["n_raw"].tolist(),
            }
            for k, v in hist_results.items()
        },
    }

    out_path = os.path.join(OUT_DATA_DIR, "lo_finebin_results.json")
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"[LO finebin] wrote {out_path}")


if __name__ == "__main__":
    main()
