"""
NEW comparison (separate from the original 3-way LO/NLO/NLO+PS Tier 2
study and from the LO+PS-vs-NLO+PS study): NLO fixed-order side of a
LO-vs-NLO-fixed-order-only overlay, using FINER bin edges
(`analysis/binning_finebin.py`) than the original Tier 2 defaults
(`analysis/binning.py`). No NLO+PS, no LO+PS -- this deliverable is
strictly LO vs NLO fixed-order.

Input: run2_NLO/pp_ttbar_nlo/Events/run_01/events.lhe.gz (same
10000-event NLO fixed-order sample already used for the original study --
NOT regenerated).

Normalization mode: ABSOLUTE YIELD (pb per bin, not shape-normalized) --
same convention as the original Tier 2 plots.

Error convention: MC STATISTICAL uncertainty only
(`error = sqrt(sum(w_i**2))` per bin, per skill
normalization-conventions.md) -- no scale-variation band. Confirmed this
is also what the ORIGINAL Tier 2 `make_plots.py` did: that script only
ever reads/plots `h["error_pb"]` (the statistical error), never the
separate 7-point (muR,muF) scale-envelope numbers that
`analysis/analyze_nlo.py` computes purely for the Tier-1 rate table
(`output/data/nlo_results.json`'s `scale_variation_7pt` block). No scale
variation is computed or used anywhere in this script.

Negative-weight status is independently re-verified here (not assumed
from the original study's finding, per the skill's "verify, don't
trust" rule) directly from the actual XWGTUP values in this same LHE
file: confirmed f_minus = 19.88% (1988/10000), matching the original
`analyze_nlo.py`'s independent finding exactly (same file, same result,
as expected) and the value already recorded in
`output/data/nlo_results.json`. This was NOT flagged in the upstream
task description for this new comparison beyond the reference to
`nlo_results.json` -- reported explicitly here again per the "f_minus,
Neff, and per-bin error together" rule, not f_minus alone.

Never filters/drops negative-weight events -- every event (including
negative-weight ones) contributes via `weighted_histogram_edge_safe`.
"""

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from lhe_utils import iter_lhe_events, get_ttbar_final_state
from kinematics import pt, phi, rapidity, delta_phi_folded, invariant_mass, pair_pt
from weighting import weighted_histogram_edge_safe, negative_weight_fraction, kish_neff
from binning_finebin import FINE_BIN_EDGES, bin_centers

LHE_PATH = "run2_NLO/pp_ttbar_nlo/Events/run_01/events.lhe.gz"
OUT_DATA_DIR = "output/data/lo_vs_nlo_finebin"
os.makedirs(OUT_DATA_DIR, exist_ok=True)


def main():
    weights_raw = []
    obs = {k: [] for k in FINE_BIN_EDGES}
    n_events = 0
    n_bad = 0

    for ev in iter_lhe_events(LHE_PATH, with_rwgt=False):
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
    w_scaled = weights_raw / N_gen

    negcheck = negative_weight_fraction(weights_raw)
    sigma_central = w_scaled.sum()
    err_central = np.sqrt((w_scaled**2).sum())
    neff_total = kish_neff(w_scaled)

    print(f"[NLO finebin] N_gen = {N_gen}, N_bad (failed ttbar extraction) = {n_bad}")
    print(f"[NLO finebin] Negative-weight check (independently re-verified from XWGTUP): "
          f"f_minus = {negcheck['f_minus']:.6f} ({negcheck['n_negative']}/{negcheck['n_total']})")
    print(f"[NLO finebin] Neff (general Kish formula, total sample) = {neff_total:.1f} "
          f"out of N_gen = {N_gen}")
    print(f"[NLO finebin] sigma (self-summed central XWGTUP) = {sigma_central:.4f} +- {err_central:.4f} pb")

    dphi_arr = np.asarray(obs["dphi_ttbar"])
    n_exact_pi = int(np.sum(dphi_arr == np.pi))
    print(f"[NLO finebin] physics check: {n_exact_pi}/{len(dphi_arr)} events have "
          f"dphi_ttbar exactly == pi (real-emission events decorrelate away from this)")

    hist_results = {}
    for obs_name, edges in FINE_BIN_EDGES.items():
        vals = np.asarray(obs[obs_name])
        res = weighted_histogram_edge_safe(vals, w_scaled, edges)
        hist_results[obs_name] = res

    out = {
        "run": "NLO",
        "lhe_path": LHE_PATH,
        "N_gen": N_gen,
        "n_bad_ttbar_extraction": n_bad,
        "sigma_pb_self_summed": sigma_central,
        "sigma_err_pb_self_summed": err_central,
        "neff_total": neff_total,
        "f_minus": negcheck["f_minus"],
        "n_negative": negcheck["n_negative"],
        "physics_check_n_exact_pi": n_exact_pi,
        "histograms": {
            k: {
                "bin_edges": FINE_BIN_EDGES[k].tolist(),
                "bin_centers": bin_centers(FINE_BIN_EDGES[k]).tolist(),
                "yield_pb": v["yield"].tolist(),
                "error_pb": v["error"].tolist(),
                "neff": v["neff"].tolist(),
                "f_minus_per_bin": [None if np.isnan(x) else x for x in v["f_minus"]],
                "n_raw": v["n_raw"].tolist(),
            }
            for k, v in hist_results.items()
        },
    }

    out_path = os.path.join(OUT_DATA_DIR, "nlo_finebin_results.json")
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"[NLO finebin] wrote {out_path}")


if __name__ == "__main__":
    main()
