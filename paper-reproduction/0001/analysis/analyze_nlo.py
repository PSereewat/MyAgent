"""
Run 2 (NLO fixed-order) analysis: Tier 1 rate + 7-point scale variation +
Tier 2 differential observables for pp -> ttbar [QCD].

Input: run2_NLO/pp_ttbar_nlo/Events/run_01/events.lhe.gz
Normalization mode: ABSOLUTE YIELD (pb), same as Run 1 -- see
analyze_lo.py docstring and skill normalization-conventions.md.

NLO/negative-weight status independently verified from the actual XWGTUP
values (never assumed from upstream): found f_minus = 19.88% negative-
weight events (1988/10000). This was NOT flagged/highlighted in the
upstream task description (which only called out Run 3's 22.92%) --
recorded here explicitly per the skill's "flag discrepancy" rule, since
NLO fixed-order aMC@NLO samples generically carry negative weights from
real-emission subtraction terms, same physical origin as in Run 3.

7-point scale variation
------------------------
The LHE file's <initrwgt> header block stores an explicit MG5 "systematics"
reweighting group (tag=0, dyn=3) with 9 named weight IDs corresponding to
all (muR, muF) in {0.5,1,2} x {0.5,1,2}:
    1001: (1,1)      1002: (2,1)      1003: (0.5,1)
    1004: (1,2)      1005: (2,2)      1006: (0.5,2)
    1007: (1,0.5)    1008: (2,0.5)    1009: (0.5,0.5)
The requested 7-point set drops the two "extreme" combinations
(muR,muF)=(0.5,2) [id 1006] and (2,0.5) [id 1008]. Each event's <rwgt>
block carries the reweighted XWGTUP-equivalent for each id; summing
each id's values over all events (divided by N_gen, exactly as for the
nominal weight) gives sigma(muR,muF) directly from the same event
sample -- this is NOT a fabricated/derived-from-scratch reweighting, it
is MG5's own stored per-event reweight information, used directly per
the skill's instruction to prefer already-computed systematics output
over hand-deriving it, just restricted here to the requested 7-point
subset instead of MG5's own reported 9-point envelope (which the
run's summary.txt already reports directly, and is cross-checked below).
"""

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from lhe_utils import iter_lhe_events, get_ttbar_final_state, parse_initrwgt
from kinematics import pt, phi, rapidity, delta_phi_folded, invariant_mass, pair_pt
from weighting import weighted_histogram_edge_safe as weighted_histogram, negative_weight_fraction, kish_neff
from binning import BIN_EDGES, bin_centers

LHE_PATH = "run2_NLO/pp_ttbar_nlo/Events/run_01/events.lhe.gz"
OUT_DATA_DIR = "output/data"
os.makedirs(OUT_DATA_DIR, exist_ok=True)

SEVEN_POINT = [(0.5, 1.0), (1.0, 0.5), (1.0, 1.0), (1.0, 2.0), (2.0, 1.0), (0.5, 0.5), (2.0, 2.0)]


def main():
    rwgt_map = parse_initrwgt(LHE_PATH)
    # Keep only the tag==0 group's ids (the primary/central dynamical
    # scale-choice-3 group) and build (muR,muF) -> weight_id lookup.
    muRmuF_to_id = {}
    for wid, info in rwgt_map.items():
        if info["tag"] == 0:
            muRmuF_to_id[(info["muR"], info["muF"])] = wid
    print(f"[NLO] Parsed {len(rwgt_map)} total reweight ids from <initrwgt>; "
          f"{len(muRmuF_to_id)} in the tag=0 (central) scale-variation group.")

    missing = [c for c in SEVEN_POINT if c not in muRmuF_to_id]
    if missing:
        raise RuntimeError(f"Missing requested 7-point scale combos in LHE reweight header: {missing}")

    seven_point_ids = {c: muRmuF_to_id[c] for c in SEVEN_POINT}
    nine_point_ids = dict(muRmuF_to_id)  # all 9

    weights_raw = []
    rwgt_sums = {wid: 0.0 for wid in nine_point_ids.values()}
    obs = {k: [] for k in BIN_EDGES}
    n_events = 0
    n_bad = 0
    n_rwgt_missing = 0

    for ev in iter_lhe_events(LHE_PATH, with_rwgt=True):
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

        if not ev.rwgt:
            n_rwgt_missing += 1
        else:
            for wid in rwgt_sums:
                rwgt_sums[wid] += ev.rwgt.get(wid, 0.0)

    N_gen = n_events
    weights_raw = np.asarray(weights_raw)
    w_scaled = weights_raw / N_gen

    negcheck = negative_weight_fraction(weights_raw)
    sigma_central = w_scaled.sum()
    err_central = np.sqrt((w_scaled**2).sum())
    neff_total = kish_neff(w_scaled)

    print(f"[NLO] N_gen = {N_gen}, N_bad (failed ttbar extraction) = {n_bad}, "
          f"N missing rwgt block = {n_rwgt_missing}")
    print(f"[NLO] Negative-weight check (independently verified from XWGTUP): "
          f"f_minus = {negcheck['f_minus']:.6f} ({negcheck['n_negative']}/{negcheck['n_total']})")
    print(f"[NLO] Neff (general Kish formula, total sample) = {neff_total:.1f} "
          f"out of N_gen = {N_gen}")
    print(f"[NLO] sigma (self-summed central XWGTUP) = {sigma_central:.4f} +- {err_central:.4f} pb")

    # 7-point envelope (from stored rwgt weights, same event sample)
    sigma_by_combo = {c: rwgt_sums[wid] / N_gen for c, wid in seven_point_ids.items()}
    sigma_7pt_central = sigma_by_combo[(1.0, 1.0)]
    sigma_7pt_max = max(sigma_by_combo.values())
    sigma_7pt_min = min(sigma_by_combo.values())
    delta_plus_7pt = sigma_7pt_max - sigma_7pt_central
    delta_minus_7pt = sigma_7pt_central - sigma_7pt_min

    print("[NLO] 7-point (muR,muF) cross sections [pb] (from stored LHE rwgt weights):")
    for c in SEVEN_POINT:
        print(f"       (muR={c[0]}, muF={c[1]}): {sigma_by_combo[c]:.4f} pb")
    print(f"[NLO] 7-point envelope: {sigma_7pt_central:.4f} "
          f"+{delta_plus_7pt:.4f} ({100*delta_plus_7pt/sigma_7pt_central:.2f}%) "
          f"-{delta_minus_7pt:.4f} ({100*delta_minus_7pt/sigma_7pt_central:.2f}%)")

    # cross-check: 9-point envelope, should match MG5's own summary.txt
    # report (6.934e2 pb +10.4%/-10.9% quoted there for run_01's res_0
    # iteration; final quoted 700.0+-4.2 pb central value is the
    # generation-level integration result, a distinct but consistent
    # quantity -- see progress notes).
    sigma_by_combo_9 = {}
    for wid, info in nine_point_ids.items():
        pass
    sigma_9pt_vals = [rwgt_sums[wid] / N_gen for wid in nine_point_ids.values()]
    sigma_9pt_central = rwgt_sums[muRmuF_to_id[(1.0, 1.0)]] / N_gen
    d_plus_9 = max(sigma_9pt_vals) - sigma_9pt_central
    d_minus_9 = sigma_9pt_central - min(sigma_9pt_vals)
    print(f"[NLO] cross-check, 9-point envelope: {sigma_9pt_central:.4f} "
          f"+{100*d_plus_9/sigma_9pt_central:.2f}% -{100*d_minus_9/sigma_9pt_central:.2f}% "
          f"(compare to MG5-reported 6.934e2 pb +10.4%/-10.9% in summary.txt)")

    # Tier-2 histograms (nominal central weight)
    hist_results = {}
    for obs_name, edges in BIN_EDGES.items():
        vals = np.asarray(obs[obs_name])
        res = weighted_histogram(vals, w_scaled, edges)
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
        "scale_variation_7pt": {
            "combos_pb": {f"{c[0]}_{c[1]}": sigma_by_combo[c] for c in SEVEN_POINT},
            "central_pb": sigma_7pt_central,
            "delta_plus_pb": delta_plus_7pt,
            "delta_minus_pb": delta_minus_7pt,
            "delta_plus_pct": 100 * delta_plus_7pt / sigma_7pt_central,
            "delta_minus_pct": 100 * delta_minus_7pt / sigma_7pt_central,
        },
        "scale_variation_9pt_crosscheck": {
            "central_pb": sigma_9pt_central,
            "delta_plus_pct": 100 * d_plus_9 / sigma_9pt_central,
            "delta_minus_pct": 100 * d_minus_9 / sigma_9pt_central,
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

    out_path = os.path.join(OUT_DATA_DIR, "nlo_results.json")
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"[NLO] wrote {out_path}")


if __name__ == "__main__":
    main()
