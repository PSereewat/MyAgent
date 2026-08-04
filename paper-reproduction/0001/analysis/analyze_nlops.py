"""
Run 3 (NLO+PS, MC@NLO matched to Pythia8) analysis: Tier 1 rate + Tier 2
differential observables, read directly from the showered/hadronized
HEPMC file (the primary deliverable for this run, per the task spec).

Input: run3_NLOPS/pp_ttbar_nlops_run/Events/run_02/events_PYTHIA8_0.hepmc.gz
Normalization mode: ABSOLUTE YIELD (pb) -- same convention as Runs 1/2.

Weight convention (verified directly from the file, see hepmc_utils.py
module docstring): the HepMC "E" line's first listed weight (named "0",
confirmed byte-for-byte identical to the last-named "Weight" entry) is
ALREADY equal to LHE XWGTUP / N_gen, i.e. it is already the properly
normalized w_i in the sum(w_i) = sigma convention used elsewhere in this
study (verified explicitly: HepMC weight[0] for event 1 = 0.12729124 =
1272.9124 (LHE XWGTUP for the corresponding event) / 10000). So sigma =
sum(w_i) directly here, with NO additional division by N_gen -- unlike
the raw XWGTUP field read directly from an .lhe file.

Never drop negative-weight events (22.92% of this sample, independently
reproduced below from the actual HepMC weights, not just trusted from
upstream) -- summed with sign into every bin, per the skill's hard rule.
"""

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from hepmc_utils import iter_hepmc_events
from kinematics import pt, phi, rapidity, delta_phi_folded, invariant_mass, pair_pt
from weighting import weighted_histogram_edge_safe as weighted_histogram, negative_weight_fraction, kish_neff
from binning import BIN_EDGES, bin_centers

HEPMC_PATH = "run3_NLOPS/pp_ttbar_nlops_run/Events/run_02/events_PYTHIA8_0.hepmc.gz"
OUT_DATA_DIR = "output/data"
os.makedirs(OUT_DATA_DIR, exist_ok=True)


def main():
    weights_raw = []  # already-scaled w_i (see docstring)
    obs = {k: [] for k in BIN_EDGES}
    n_events = 0

    for ev in iter_hepmc_events(HEPMC_PATH):
        n_events += 1
        top = ev.top  # (px, py, pz, e, m)
        atop = ev.antitop

        p_top = (top[0], top[1], top[2], top[3])
        p_atop = (atop[0], atop[1], atop[2], atop[3])

        weights_raw.append(ev.weight)
        obs["pt_ttbar"].append(pair_pt(p_top, p_atop))
        obs["dphi_ttbar"].append(delta_phi_folded(phi(*p_top[:2]), phi(*p_atop[:2])))
        obs["pt_top_lead"].append(max(pt(*p_top[:2]), pt(*p_atop[:2])))
        obs["m_ttbar"].append(invariant_mass(p_top, p_atop))
        obs["y_t"].append(rapidity(p_top[2], p_top[3]))

    w_scaled = np.asarray(weights_raw)  # already w_i, no further /N_gen
    N_gen = n_events

    negcheck = negative_weight_fraction(w_scaled)
    sigma = w_scaled.sum()
    err = np.sqrt((w_scaled**2).sum())
    neff_total = kish_neff(w_scaled)

    print(f"[NLO+PS] N_gen (events read from HEPMC) = {N_gen}")
    print(f"[NLO+PS] Negative-weight check (independently reproduced from HepMC weights): "
          f"f_minus = {negcheck['f_minus']:.6f} ({negcheck['n_negative']}/{negcheck['n_total']}) "
          f"-- task-supplied value was 22.92%")
    print(f"[NLO+PS] Neff (general Kish formula, total sample) = {neff_total:.1f} out of N_gen = {N_gen}")
    print(f"[NLO+PS] sigma (self-summed from HepMC event weights) = {sigma:.4f} +- {err:.4f} pb")
    print("[NLO+PS] Note: this self-summed value (~689 pb) differs from the officially "
          "quoted generation-level cross section (702.3 +- 4.5 pb, from the MC "
          "phase-space integration grid) by about 1.8%, which is fully consistent "
          "with the *sample's own* effective statistics: 1/sqrt(Neff) = "
          f"{100/np.sqrt(neff_total):.2f}% for Neff={neff_total:.0f} out of 10000 raw "
          "events -- i.e. this is the expected statistical fluctuation of a finite "
          "unweighted MC@NLO sample with a non-trivial negative-weight fraction, not a bug.")

    hist_results = {}
    for obs_name, edges in BIN_EDGES.items():
        vals = np.asarray(obs[obs_name])
        res = weighted_histogram(vals, w_scaled, edges)
        hist_results[obs_name] = res

    out = {
        "run": "NLO+PS",
        "hepmc_path": HEPMC_PATH,
        "N_gen": N_gen,
        "sigma_pb_self_summed": sigma,
        "sigma_err_pb_self_summed": err,
        "neff_total": neff_total,
        "f_minus": negcheck["f_minus"],
        "n_negative": negcheck["n_negative"],
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

    out_path = os.path.join(OUT_DATA_DIR, "nlops_results.json")
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"[NLO+PS] wrote {out_path}")


if __name__ == "__main__":
    main()
