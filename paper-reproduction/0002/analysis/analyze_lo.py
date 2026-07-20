"""
Parse the LO ttbar LHE file, compute Tier-2 observables per event and
extract the 7-point (mu_R, mu_F) scale-variation weights (DYN_SCALE=3
subset of the "Central scale variation" weightgroup), and save
everything to a compact .npz for downstream Tier-1/Tier-2 analysis and
plotting.

Weight-id mapping verified directly from this run's own <initrwgt>
header (ids at DYN_SCALE="3"):
  id  4 : MUR=0.5 MUF=0.5
  id  9 : MUR=0.5 MUF=1.0
  id 14 : MUR=0.5 MUF=2.0   <- excluded from 7-point envelope (corner)
  id 19 : MUR=1.0 MUF=0.5
  id 23 : MUR=1.0 MUF=1.0   (central; equals event's own XWGTUP)
  id 28 : MUR=1.0 MUF=2.0
  id 33 : MUR=2.0 MUF=0.5   <- excluded from 7-point envelope (corner)
  id 38 : MUR=2.0 MUF=1.0
  id 43 : MUR=2.0 MUF=2.0

7-point set used = {4, 9, 19, 23, 28, 38, 43}
(drops the two opposite-extreme corners (0.5,2.0)=id14 and (2.0,0.5)=id33)
"""
import numpy as np
from lhe_utils import iter_event_blocks, parse_particles, parse_rwgt_ids, top_kinematics, compute_observables

LHE_PATH = "events/pp_ttbar_lo_13tev/Events/run_01/unweighted_events.lhe.gz"
OUT_PATH = "analysis/parsed/lo_events.npz"

SEVEN_POINT_IDS = ["4", "9", "19", "23", "28", "38", "43"]
SEVEN_POINT_LABELS = {
    "4": "muR=0.5,muF=0.5", "9": "muR=0.5,muF=1.0", "19": "muR=1.0,muF=0.5",
    "23": "muR=1.0,muF=1.0 (central)", "28": "muR=1.0,muF=2.0",
    "38": "muR=2.0,muF=1.0", "43": "muR=2.0,muF=2.0",
}


def main():
    n_events = 0
    xwgt_list = []
    scale_w = {k: [] for k in SEVEN_POINT_IDS}
    pt_ttbar_l, dphi_l, pt_t_l, m_ttbar_l, y_t_l = [], [], [], [], []
    n_missing_top = 0
    n_wgt_ids_seen = None

    for block in iter_event_blocks(LHE_PATH):
        nup, idprup, xwgtup, scalup, aqedup, aqcdup, particles = parse_particles(block)
        t, tbar = top_kinematics(particles)
        if t is None or tbar is None:
            n_missing_top += 1
            continue
        obs = compute_observables(t, tbar)

        rw = parse_rwgt_ids(block, SEVEN_POINT_IDS)
        if n_wgt_ids_seen is None:
            # count total wgt id entries in this event's <rwgt> block
            start = block.find("<rwgt>")
            end = block.find("</rwgt>")
            n_wgt_ids_seen = block[start:end].count("id=")

        n_events += 1
        xwgt_list.append(xwgtup)
        for k in SEVEN_POINT_IDS:
            scale_w[k].append(rw.get(k, xwgtup if k == "23" else float("nan")))
        pt_ttbar_l.append(obs["pt_ttbar"])
        dphi_l.append(obs["dphi"])
        pt_t_l.append(obs["pt_t"])
        m_ttbar_l.append(obs["m_ttbar"])
        y_t_l.append(obs["y_t"])

    xwgt = np.array(xwgt_list)
    n = len(xwgt)
    sigma_from_events = xwgt.sum() / n

    print(f"[LO] events parsed: {n_events}, missing-top events: {n_missing_top}")
    print(f"[LO] total wgt-id entries per event (header count): {n_wgt_ids_seen}")
    print(f"[LO] sigma from event-weight average: {sigma_from_events:.4f} pb (N={n})")
    print(f"[LO] negative-weight events: {int((xwgt<0).sum())} / {n} "
          f"= {100*(xwgt<0).sum()/n:.3f}%")

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
        **{f"scale_{k}": np.array(scale_w[k]) for k in SEVEN_POINT_IDS},
    )
    print(f"[LO] saved -> {OUT_PATH}")


if __name__ == "__main__":
    main()
