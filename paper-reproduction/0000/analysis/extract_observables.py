"""
Single pass over each LHE file: extract the nominal weight, the 7-point
scale-envelope weights, and the five Tier-2 kinematic observables
(pT_ttbar, Delta_phi_ttbar, pT_t, m_ttbar, y_t) for every event.

Also verifies, independently, the negative-weight status of each sample
directly from the parsed XWGTUP values (does not trust the upstream
progress-report numbers).

Saves per-event numpy arrays to analysis/cache/{lo,nlo}_events.npz for
reuse by the Tier-1 rate script and the Tier-2 histogram/plotting script,
so the (slow) LHE parse only has to run once per sample.

All paths are relative to the repo working directory.
"""

from __future__ import annotations

import math
import time

import numpy as np

from parse_lhe import iter_lhe_events, LO_POSITIONS, NLO_POSITIONS, ENVELOPE_LABELS

LABELS = list(ENVELOPE_LABELS.keys())  # fixed order, includes "central_1_1"

LO_PATH = "events/lo/pp_ttbar_13TeV_lo/Events/run_01/unweighted_events.lhe.gz"
NLO_PATH = "events/nlo/pp_ttbar_13TeV_nlo/Events/run_01/events.lhe.gz"


def four_vector_sum(px1, py1, pz1, E1, px2, py2, pz2, E2):
    return px1 + px2, py1 + py2, pz1 + pz2, E1 + E2


def process_file(path: str, positions: dict, label: str) -> dict:
    t0 = time.time()
    n_events = 0
    n_missing_tops = 0

    xwgtup_list = []
    env_lists = {lab: [] for lab in LABELS}

    pt_ttbar_list = []
    dphi_ttbar_list = []
    pt_t_list = []
    m_ttbar_list = []
    y_t_list = []

    for xwgtup, wgts, particles in iter_lhe_events(path, positions):
        n_events += 1

        top = None
        atop = None
        for pdg, status, px, py, pz, E, mass in particles:
            if status == 1 and pdg == 6:
                top = (px, py, pz, E, mass)
            elif status == 1 and pdg == -6:
                atop = (px, py, pz, E, mass)

        if top is None or atop is None:
            n_missing_tops += 1
            # Cannot build observables for this event; skip observable
            # arrays but still record weight for the rate sums separately
            # (handled by caller via xwgtup_list / env_lists, which we
            # still append so Tier-1 totals stay complete).
            xwgtup_list.append(xwgtup)
            for lab in LABELS:
                env_lists[lab].append(wgts.get(lab, float("nan")))
            pt_ttbar_list.append(float("nan"))
            dphi_ttbar_list.append(float("nan"))
            pt_t_list.append(float("nan"))
            m_ttbar_list.append(float("nan"))
            y_t_list.append(float("nan"))
            continue

        px_t, py_t, pz_t, E_t, m_t = top
        px_a, py_a, pz_a, E_a, m_a = atop

        # pT_ttbar: vector sum of the two 4-momenta
        px_sum, py_sum, pz_sum, E_sum = four_vector_sum(
            px_t, py_t, pz_t, E_t, px_a, py_a, pz_a, E_a
        )
        pt_ttbar = math.hypot(px_sum, py_sum)

        # Delta_phi_ttbar folded into [0, pi]
        phi_t = math.atan2(py_t, px_t)
        phi_a = math.atan2(py_a, px_a)
        dphi = abs(phi_t - phi_a)
        if dphi > math.pi:
            dphi = 2 * math.pi - dphi

        # pT_t
        pt_t = math.hypot(px_t, py_t)

        # m_ttbar: invariant mass of the ttbar system
        m2 = E_sum**2 - px_sum**2 - py_sum**2 - pz_sum**2
        m_ttbar = math.sqrt(m2) if m2 > 0 else 0.0

        # y_t: top rapidity
        y_t = 0.5 * math.log((E_t + pz_t) / (E_t - pz_t))

        xwgtup_list.append(xwgtup)
        for lab in LABELS:
            env_lists[lab].append(wgts.get(lab, float("nan")))
        pt_ttbar_list.append(pt_ttbar)
        dphi_ttbar_list.append(dphi)
        pt_t_list.append(pt_t)
        m_ttbar_list.append(m_ttbar)
        y_t_list.append(y_t)

    dt = time.time() - t0
    print(
        f"[{label}] parsed {n_events} events in {dt:.1f}s "
        f"({n_missing_tops} missing top/antitop pairs)"
    )

    out = {
        "n_events": n_events,
        "n_missing_tops": n_missing_tops,
        "xwgtup": np.array(xwgtup_list, dtype=float),
        "pt_ttbar": np.array(pt_ttbar_list, dtype=float),
        "dphi_ttbar": np.array(dphi_ttbar_list, dtype=float),
        "pt_t": np.array(pt_t_list, dtype=float),
        "m_ttbar": np.array(m_ttbar_list, dtype=float),
        "y_t": np.array(y_t_list, dtype=float),
    }
    for lab in LABELS:
        out[f"env_{lab}"] = np.array(env_lists[lab], dtype=float)
    return out


def main():
    print("Processing LO sample...")
    lo = process_file(LO_PATH, LO_POSITIONS, "LO")
    print("Processing NLO sample...")
    nlo = process_file(NLO_PATH, NLO_POSITIONS, "NLO")

    np.savez_compressed("analysis/cache/lo_events.npz", **lo)
    np.savez_compressed("analysis/cache/nlo_events.npz", **nlo)

    # Independent negative-weight verification, directly from parsed XWGTUP
    for label, d in [("LO", lo), ("NLO", nlo)]:
        w = d["xwgtup"]
        n_neg = int(np.sum(w < 0))
        f_minus = n_neg / len(w)
        print(
            f"[{label}] independent negative-weight check: "
            f"{n_neg}/{len(w)} = {100*f_minus:.4f}% negative"
        )

    print("Cached to analysis/cache/lo_events.npz and analysis/cache/nlo_events.npz")


if __name__ == "__main__":
    main()
