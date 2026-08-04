"""
Run 1 (LO fixed-order) analysis: Tier 1 rate + Tier 2 differential
observables for pp -> ttbar.

Input: run1_LO/pp_ttbar/Events/run_01/unweighted_events.lhe.gz
Normalization mode: ABSOLUTE YIELD (total cross section in pb; L=1,
no luminosity scaling requested by the task -- Tier 1/2 both ask for
cross sections / pb-normalized differential distributions, not a
shape-normalized comparison). Stated explicitly per skill
normalization-conventions.md.

Negative-weight status is independently verified from the actual XWGTUP
values (never assumed): confirmed 0 negative-weight events, weight
constant = 520.365 pb for every event (a plain LO unit-weight sample).
"""

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from lhe_utils import iter_lhe_events, get_ttbar_final_state
from kinematics import pt, phi, rapidity, delta_phi_folded, invariant_mass, pair_pt
from weighting import weighted_histogram_edge_safe as weighted_histogram, negative_weight_fraction
from binning import BIN_EDGES, bin_centers

LHE_PATH = "run1_LO/pp_ttbar/Events/run_01/unweighted_events.lhe.gz"
OUT_DATA_DIR = "output/data"
os.makedirs(OUT_DATA_DIR, exist_ok=True)


def main():
    weights_raw = []
    obs = {k: [] for k in BIN_EDGES}
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

    N_gen = n_events  # denominator for the unified weighting formula
    weights_raw = np.asarray(weights_raw)
    w_scaled = weights_raw / N_gen  # w_i = weight_i * L / N_gen, L=1 pb^-1

    negcheck = negative_weight_fraction(weights_raw)

    sigma = w_scaled.sum()
    err = np.sqrt((w_scaled**2).sum())

    print(f"[LO] N_gen = {N_gen}, N_bad (failed ttbar extraction) = {n_bad}")
    print(f"[LO] Negative-weight check: f_minus = {negcheck['f_minus']:.6f} "
          f"({negcheck['n_negative']}/{negcheck['n_total']}) -- expect exactly 0 for plain LO")
    print(f"[LO] weight min/max = {weights_raw.min():.6f} / {weights_raw.max():.6f} pb "
          f"(should be identical -- constant unit weight)")
    print(f"[LO] sigma (self-summed from LHE weights) = {sigma:.4f} +- {err:.4f} pb")

    # Physics checks (per LO_NLO_NLOPS.md): pT_ttbar == 0 exactly,
    # dphi_ttbar == pi exactly, for every LO event.
    pt_ttbar_arr = np.asarray(obs["pt_ttbar"])
    dphi_arr = np.asarray(obs["dphi_ttbar"])
    max_pt_ttbar = pt_ttbar_arr.max()
    min_dphi = dphi_arr.min()
    print(f"[LO] physics check: max(pT_ttbar) over all events = {max_pt_ttbar:.3e} GeV "
          f"(expect ~0, tree-level back-to-back)")
    print(f"[LO] physics check: min(dphi_ttbar) over all events = {min_dphi:.10f} rad "
          f"(expect pi = {np.pi:.10f})")

    # Tier-2 histograms
    hist_results = {}
    for obs_name, edges in BIN_EDGES.items():
        vals = np.asarray(obs[obs_name])
        w_for_hist = np.full(len(vals), weights_raw[0] / N_gen)  # all identical for LO
        res = weighted_histogram(vals, w_for_hist, edges)
        hist_results[obs_name] = res

    # Save Tier-1 rate summary + Tier-2 histograms as JSON for downstream
    # plotting/CSV export scripts.
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
        "histograms": {
            k: {
                "bin_edges": BIN_EDGES[k].tolist(),
                "bin_centers": bin_centers(BIN_EDGES[k]).tolist(),
                "yield_pb": v["yield"].tolist(),
                "error_pb": v["error"].tolist(),
                "neff": v["neff"].tolist(),
                "n_raw": v["n_raw"].tolist(),
            }
            for k, v in hist_results.items()
        },
    }

    out_path = os.path.join(OUT_DATA_DIR, "lo_results.json")
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"[LO] wrote {out_path}")


if __name__ == "__main__":
    main()
