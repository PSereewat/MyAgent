"""
Run 4 (LO+PS, bare LO matrix element directly attached to a Pythia8
shower, no MC@NLO matching) analysis: Tier 1 rate + Tier 2 differential
observables, read directly from the showered/hadronized HEPMC file (the
primary deliverable for this run, per the task spec) -- same convention
as analyze_nlops.py (Run 3) for the observable definitions and binning,
so this is visually/methodologically consistent with the earlier Tier 2
plots.

This is part of the NEW LO+PS-vs-NLO+PS comparison (separate from the
original LO/NLO/NLO+PS 3-way study in ../LO_NLO_NLOPS.md); it does not
modify or overwrite any of that study's existing outputs.

Input: run4_LOPS/pp_ttbar_lops_run/Events/run_01/tag_1_pythia8_events.hepmc.gz
Normalization mode: ABSOLUTE YIELD (pb) -- same convention as Runs 1/2/3.

Scope note: `use_syst=True` was left on during Run 4's generation (see
run4_LOPS/progress/step5_madgraph_lops.md), so this HEPMC file carries
145 extra scale/PDF systematic-reweighting weights per event alongside
the nominal one. Per the user's explicit instruction for THIS task
("if you notice one of the input files happens to contain reweight info,
ignore it, it's out of scope"), none of those 145 variation weights are
read or used anywhere below -- only the single nominal weight.

Weight convention -- INDEPENDENTLY VERIFIED, and DIFFERENT from Run 3's
-------------------------------------------------------------------------
Read directly from the file's own "N" (weight-name) line:
    N 146 "1" "10" "100" ... "145" "Weight"
i.e. the 145 systematic-variation weights are listed FIRST, and the
genuine nominal weight is LAST, named "Weight" -- the OPPOSITE ordering
from Run 3's file (where the first-listed weight, named "0", was already
the nominal one). Confirmed by direct inspection:
  - First-listed weight varies event-by-event (662.48, 674.10, 572.29,
    ... pb for the first few events) -- one of the out-of-scope
    systematic variations.
  - Last-listed weight is exactly constant at 520.365 pb for all 10000
    events (matches the LHE XWGTUP field exactly, and the quoted
    sigma_LO+PS = 520.4 pb), and there are zero negative weights --
    consistent with a plain unweighted LO sample.
Unlike Run 3's HepMC file, this last (nominal) weight is NOT already
divided by N_gen -- it is the raw per-event weight (identical to LHE
XWGTUP), so w_i = weight_i / N_gen must be applied here, exactly as in
analyze_lo.py's LHE-based convention. This is called out explicitly
because blindly reusing Run 3's "already-normalized, use directly"
convention here would silently overcount the cross section by a factor
of N_gen = 10000.

Negative-weight status independently verified from the actual HepMC
weights (not just trusted from the task's "all unit/constant weight, no
negative weights" claim): confirmed 0/10000 negative, weight constant at
520.365 pb -- consistent with the task-supplied value and with a plain LO
sample (never filtering negative-weight events is moot here since there
are none, but the check was still performed independently per the
skill's hard rule).
"""

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from hepmc_utils import iter_hepmc_events
from kinematics import pt, phi, rapidity, delta_phi_folded, invariant_mass, pair_pt
from weighting import weighted_histogram, negative_weight_fraction, kish_neff
from binning import BIN_EDGES, bin_centers

HEPMC_PATH = "run4_LOPS/pp_ttbar_lops_run/Events/run_01/tag_1_pythia8_events.hepmc.gz"
OUT_DATA_DIR = "output/data/lops_vs_nlops"
os.makedirs(OUT_DATA_DIR, exist_ok=True)


def main():
    weights_raw = []  # raw nominal weight (= LHE XWGTUP), NOT yet /N_gen
    obs = {k: [] for k in BIN_EDGES}
    n_events = 0

    for ev in iter_hepmc_events(HEPMC_PATH, weight_index="last"):
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

    N_gen = n_events
    weights_raw = np.asarray(weights_raw)

    negcheck = negative_weight_fraction(weights_raw)
    print(f"[LO+PS] N_gen (events read from HEPMC) = {N_gen}")
    print(f"[LO+PS] Negative-weight check (independently verified from HepMC nominal "
          f"'Weight'-named entry, NOT the first-listed systematic-variation entry): "
          f"f_minus = {negcheck['f_minus']:.6f} ({negcheck['n_negative']}/{negcheck['n_total']}) "
          f"-- task-supplied claim was 'all unit/constant weight, no negative weights'; confirmed.")
    print(f"[LO+PS] weight min/max = {weights_raw.min():.6f} / {weights_raw.max():.6f} pb "
          f"(should be identical -- constant unit weight, plain LO)")

    w_scaled = weights_raw / N_gen  # w_i = weight_i * L / N_gen, L = 1 pb^-1
    sigma = w_scaled.sum()
    err = np.sqrt((w_scaled**2).sum())
    neff_total = kish_neff(w_scaled)

    print(f"[LO+PS] Neff (general Kish formula, total sample) = {neff_total:.1f} "
          f"out of N_gen = {N_gen} (expect Neff == N_gen exactly for constant-weight LO)")
    print(f"[LO+PS] sigma (self-summed from HepMC nominal weights) = {sigma:.4f} +- {err:.4f} pb "
          f"(task-quoted generation-level value: 520.4 +- 0.7669 pb)")

    # Physics sanity check: LO+PS should show NONZERO pT_ttbar and
    # dphi_ttbar < pi from shower resummation alone (unlike bare LO, where
    # pT_ttbar == 0 and dphi_ttbar == pi exactly for every event).
    pt_ttbar_arr = np.asarray(obs["pt_ttbar"])
    dphi_arr = np.asarray(obs["dphi_ttbar"])
    print(f"[LO+PS] physics check: pT_ttbar over all events: min={pt_ttbar_arr.min():.3f}, "
          f"mean={pt_ttbar_arr.mean():.3f}, max={pt_ttbar_arr.max():.3f} GeV "
          f"(expect nonzero, unlike bare fixed-order LO's exact 0)")
    print(f"[LO+PS] physics check: dphi_ttbar over all events: min={dphi_arr.min():.6f}, "
          f"mean={dphi_arr.mean():.6f}, max={dphi_arr.max():.6f} rad "
          f"(expect max at/near pi={np.pi:.6f} but a spread below it, unlike bare "
          f"fixed-order LO's exact delta function at pi)")

    hist_results = {}
    for obs_name, edges in BIN_EDGES.items():
        vals = np.asarray(obs[obs_name])
        res = weighted_histogram(vals, w_scaled, edges)
        hist_results[obs_name] = res

    out = {
        "run": "LO+PS",
        "hepmc_path": HEPMC_PATH,
        "weight_index_used": "last (named 'Weight'; verified nominal, NOT the first-listed "
                              "systematic-variation entry -- see module docstring)",
        "N_gen": N_gen,
        "sigma_pb_self_summed": sigma,
        "sigma_err_pb_self_summed": err,
        "neff_total": neff_total,
        "f_minus": negcheck["f_minus"],
        "n_negative": negcheck["n_negative"],
        "physics_check_pt_ttbar_GeV": {
            "min": float(pt_ttbar_arr.min()),
            "mean": float(pt_ttbar_arr.mean()),
            "max": float(pt_ttbar_arr.max()),
        },
        "physics_check_dphi_ttbar_rad": {
            "min": float(dphi_arr.min()),
            "mean": float(dphi_arr.mean()),
            "max": float(dphi_arr.max()),
        },
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

    out_path = os.path.join(OUT_DATA_DIR, "lops_results.json")
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"[LO+PS] wrote {out_path}")


if __name__ == "__main__":
    main()
