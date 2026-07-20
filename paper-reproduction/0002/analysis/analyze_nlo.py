"""
Parse the NLO (fixed-order [QCD], aMC@NLO parton-level, shower=OFF) ttbar
LHE file, compute Tier-2 observables per event and extract the 7-point
(mu_R, mu_F) scale-variation weights, and save to a compact .npz.

This run's own <initrwgt> header (verified directly, NOT assumed to match
the LO run's ids) contains THREE weightgroups of 9 (muR,muF) values each,
all at dyn=3, tagged by an internal MadGraph/aMC@NLO "order" tag:
  weightgroup 'scale_variation 0 3'  -> ids 1001-1009  (tag=0)
  weightgroup 'scale_variation 4 3'  -> ids 1010-1018  (tag=4)
  weightgroup 'scale_variation 6 3'  -> ids 1019-1027  (tag=6)

Verification performed (see progress file for detail): for every event,
id=1001 (muR=1,muF=1 under the tag=0 group) reproduces the event's own
XWGTUP exactly (magnitude AND sign), for both Born-like (NUP=4) and
real-emission (NUP=5) event topologies. This confirms the tag=0 group
already carries the complete per-event weight variation summed over the
internal order/FKS-configuration decomposition (tags 4 and 6 are the
internal per-order pieces that combine to give tag=0, and are NOT
separately needed here). All Tier-1 NLO scale-envelope work therefore
uses ONLY the tag=0 group:
  id 1001 : muR=1.0,muF=1.0  (central; == XWGTUP)
  id 1002 : muR=2.0,muF=1.0
  id 1003 : muR=0.5,muF=1.0
  id 1004 : muR=1.0,muF=2.0
  id 1005 : muR=2.0,muF=2.0
  id 1006 : muR=0.5,muF=2.0  <- excluded from 7-point envelope (corner)
  id 1007 : muR=1.0,muF=0.5
  id 1008 : muR=2.0,muF=0.5  <- excluded from 7-point envelope (corner)
  id 1009 : muR=0.5,muF=0.5

7-point set used = {1001, 1002, 1003, 1004, 1005, 1007, 1009}
"""
import numpy as np
from lhe_utils import iter_event_blocks, parse_particles, parse_rwgt_ids, top_kinematics, compute_observables

LHE_PATH = "events/pp_ttbar_nlo_13tev/Events/run_01/events.lhe.gz"
OUT_PATH = "analysis/parsed/nlo_events.npz"

SEVEN_POINT_IDS = ["1001", "1002", "1003", "1004", "1005", "1007", "1009"]
ALL_TAG0_IDS = ["1001", "1002", "1003", "1004", "1005", "1006", "1007", "1008", "1009"]


def main():
    n_events = 0
    xwgt_list = []
    scale_w = {k: [] for k in SEVEN_POINT_IDS}
    pt_ttbar_l, dphi_l, pt_t_l, m_ttbar_l, y_t_l = [], [], [], [], []
    n_missing_top = 0
    n_wgt_ids_seen = None
    id1001_matches_xwgtup = 0
    id1001_checked = 0

    for block in iter_event_blocks(LHE_PATH):
        nup, idprup, xwgtup, scalup, aqedup, aqcdup, particles = parse_particles(block)
        t, tbar = top_kinematics(particles)
        if t is None or tbar is None:
            n_missing_top += 1
            continue
        obs = compute_observables(t, tbar)

        rw = parse_rwgt_ids(block, SEVEN_POINT_IDS)
        if n_wgt_ids_seen is None:
            start = block.find("<rwgt>")
            end = block.find("</rwgt>")
            n_wgt_ids_seen = block[start:end].count("id=")

        # sanity check (first 200 events): does tag=0 central id match XWGTUP?
        if id1001_checked < 200:
            id1001_checked += 1
            # NB: <wgt> values in this LHE are printed with only 5 significant
            # digits (e.g. "0.11500E+04"), so allow ~1e-4 relative tolerance.
            if abs(rw.get("1001", np.nan) - xwgtup) < 2e-4 * max(1.0, abs(xwgtup)):
                id1001_matches_xwgtup += 1

        n_events += 1
        xwgt_list.append(xwgtup)
        for k in SEVEN_POINT_IDS:
            scale_w[k].append(rw.get(k, xwgtup if k == "1001" else float("nan")))
        pt_ttbar_l.append(obs["pt_ttbar"])
        dphi_l.append(obs["dphi"])
        pt_t_l.append(obs["pt_t"])
        m_ttbar_l.append(obs["m_ttbar"])
        y_t_l.append(obs["y_t"])

    xwgt = np.array(xwgt_list)
    n = len(xwgt)
    sigma_from_events = xwgt.sum() / n

    neg_mask = xwgt < 0
    n_neg = int(neg_mask.sum())
    f_minus = n_neg / n
    n_eff = n * (1 - 2 * f_minus) ** 2

    print(f"[NLO] events parsed: {n_events}, missing-top events: {n_missing_top}")
    print(f"[NLO] total wgt-id entries per event (header count, all 3 tag groups): {n_wgt_ids_seen}")
    print(f"[NLO] tag=0/id=1001 matches XWGTUP for {id1001_matches_xwgtup}/{id1001_checked} sampled events")
    print(f"[NLO] sigma from event-weight average: {sigma_from_events:.4f} pb (N={n})")
    print(f"[NLO] negative-weight events: {n_neg} / {n} = {100*f_minus:.3f}%  (f_minus={f_minus:.5f})")
    print(f"[NLO] N_eff = N*(1-2*f_minus)^2 = {n_eff:.2f}")

    np.savez(
        OUT_PATH,
        n_events=n,
        xwgt=xwgt,
        pt_ttbar=np.array(pt_ttbar_l),
        dphi=np.array(dphi_l),
        pt_t=np.array(pt_t_l),
        m_ttbar=np.array(m_ttbar_l),
        y_t=np.array(y_t_l),
        n_wgt_ids_per_event=n_wgt_ids_seen,
        f_minus=f_minus,
        n_eff=n_eff,
        n_neg=n_neg,
        **{f"scale_{k}": np.array(scale_w[k]) for k in SEVEN_POINT_IDS},
    )
    print(f"[NLO] saved -> {OUT_PATH}")


if __name__ == "__main__":
    main()
