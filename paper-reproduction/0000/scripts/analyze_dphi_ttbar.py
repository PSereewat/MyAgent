#!/usr/bin/env python3
"""
Analyze Delta_phi(t, tbar) distributions from LHE parton-level event files.

Reproduces Section 4 ("Numerical Analysis") of ttbar_production.md:
  - Reads the top (PDG +6) and antitop (PDG -6) final-state (status 1) four
    momenta from each <event> block in an LHE file (plain .lhe or .lhe.gz).
  - Computes phi_t, phi_tbar via atan2(py, px), then
        Delta_phi_ttbar = |phi_t - phi_tbar|, folded into [0, pi]
    via: if the raw absolute difference > pi, replace with 2*pi - it.
  - Fills a weighted 20-bin histogram over [0, pi] using each event's LHE
    weight, normalizes by bin width to get dsigma/dDeltaphi (pb/rad), and
    computes the statistical error per bin as sqrt(sum w_i^2)/bin_width.
  - Writes the binned data to output/data/ and (optionally, if both LO and
    NLO files are supplied) makes the combined LO(green)+NLO(blue) step plot
    to output/figures/. With only one run available, that single curve is
    plotted alone so the script can be re-run unchanged once the companion
    run's LHE file exists.

LHE weight normalization note
------------------------------
MadGraph5_aMC@NLO LHE files use IDWTUP = -4 (or +-4) convention: the raw
per-event weight XWGTUP stored in each <event> block, when SUMMED over all
N generated events and divided by N, reproduces the total cross section
quoted in the <init> block (XSECUP) -- i.e.
    sigma = (1/N) * sum_i XWGTUP_i
This holds even for a fully "unweighted" LO sample, where every XWGTUP_i is
identical and equal to XSECUP itself (verified for the LO run used here:
XWGTUP = XSECUP = 522.309 pb for all 100 events). This convention is used
specifically because it generalizes seamlessly to NLO samples where
XWGTUP_i can differ event-by-event and be negative.

Therefore the "event weight" w_i used in the differential cross section
formula
    dsigma/dDeltaphi ~= sum_{bin} w_i / bin_width
is taken here to be the *normalized* weight w_i = XWGTUP_i / N_events, so
that sum_i w_i (over all events, all bins) reproduces the generator-quoted
total cross section XSECUP -- this is the physically meaningful quantity
and is the basis of the sanity check reported in the progress notes.

Usage
-----
    python3 scripts/analyze_dphi_ttbar.py \\
        --lo events/pp_ttbar_lo_13tev/Events/run_01/unweighted_events.lhe.gz \\
        --nlo events/pp_ttbar_nlo_13tev/Events/run_01/unweighted_events.lhe.gz \\
        --outdir .

If --nlo is omitted (as in the current LO-only situation), only the LO
curve is produced and the NLO curve is left for a future re-run.
"""

import argparse
import gzip
import json
import math
import os
import re
import sys

import numpy as np

N_BINS = 20
PHI_MIN, PHI_MAX = 0.0, math.pi
BIN_EDGES = np.linspace(PHI_MIN, PHI_MAX, N_BINS + 1)
BIN_WIDTH = (PHI_MAX - PHI_MIN) / N_BINS  # pi/20


def _open_maybe_gzip(path):
    if path.endswith(".gz"):
        return gzip.open(path, "rt")
    return open(path, "r")


def parse_lhe_events(path):
    """Yield (weight, particles) for each <event> block in an LHE file.

    particles is a list of dicts with keys: pdg, status, px, py, pz, E, m
    (only the fields needed downstream are parsed).
    """
    with _open_maybe_gzip(path) as f:
        text = f.read()

    event_blocks = re.findall(r"<event>(.*?)</event>", text, re.DOTALL)
    for block in event_blocks:
        lines = [ln.strip() for ln in block.strip().splitlines() if ln.strip()]
        if not lines:
            continue
        header = lines[0].split()
        nup = int(header[0])
        weight = float(header[2])

        particles = []
        for ln in lines[1 : 1 + nup]:
            fields = ln.split()
            pdg = int(fields[0])
            status = int(fields[1])
            px, py, pz, E, m = (float(x) for x in fields[6:11])
            particles.append(
                {"pdg": pdg, "status": status, "px": px, "py": py, "pz": pz, "E": E, "m": m}
            )
        yield weight, particles


def compute_delta_phi_ttbar(particles):
    """Return Delta_phi_ttbar (folded to [0, pi]) for one event's particle list.

    Requires exactly one final-state (status==1) top (PDG==6) and one
    final-state (status==1) antitop (PDG==-6). Raises if not found (parton
    -level ttbar events should always have exactly this pair as the
    outgoing final-state particles, since the tops are undecayed).
    """
    top = None
    atop = None
    for p in particles:
        if p["status"] != 1:
            continue
        if p["pdg"] == 6:
            top = p
        elif p["pdg"] == -6:
            atop = p

    if top is None or atop is None:
        raise ValueError("Event missing final-state top and/or antitop (PDG +-6, status 1).")

    phi_t = math.atan2(top["py"], top["px"])
    phi_tbar = math.atan2(atop["py"], atop["px"])

    dphi = abs(phi_t - phi_tbar)
    if dphi > math.pi:
        dphi = 2.0 * math.pi - dphi
    return dphi


def build_histogram(lhe_path):
    """Read an LHE file and return a dict with binned dsigma/dDeltaphi data.

    Returns a dict with keys:
      n_events, sum_raw_weight, sum_norm_weight (== cross section pb),
      bin_edges, bin_centers, dsigma_ddphi (pb/rad), error (pb/rad),
      raw_bin_weight_sum (pb, pre bin-width-division), dphi_values (rad).
    """
    raw_weights = []
    dphi_values = []

    for weight, particles in parse_lhe_events(lhe_path):
        raw_weights.append(weight)
        dphi_values.append(compute_delta_phi_ttbar(particles))

    n_events = len(raw_weights)
    if n_events == 0:
        raise ValueError(f"No events found in {lhe_path}")

    raw_weights = np.array(raw_weights, dtype=float)
    dphi_values = np.array(dphi_values, dtype=float)

    # Normalize LHE weights so that sum(norm_weights) == generator cross
    # section (IDWTUP = +-4 convention; see module docstring).
    norm_weights = raw_weights / n_events

    bin_idx = np.digitize(dphi_values, BIN_EDGES[1:-1], right=False)

    sum_w = np.zeros(N_BINS)
    sum_w2 = np.zeros(N_BINS)
    for i in range(N_BINS):
        mask = bin_idx == i
        sum_w[i] = norm_weights[mask].sum()
        sum_w2[i] = np.sum(norm_weights[mask] ** 2)

    dsigma_ddphi = sum_w / BIN_WIDTH
    error = np.sqrt(sum_w2) / BIN_WIDTH

    bin_centers = 0.5 * (BIN_EDGES[:-1] + BIN_EDGES[1:])

    return {
        "lhe_path": lhe_path,
        "n_events": n_events,
        "sum_raw_weight": float(raw_weights.sum()),
        "sum_norm_weight": float(norm_weights.sum()),
        "bin_edges": BIN_EDGES.tolist(),
        "bin_centers": bin_centers.tolist(),
        "bin_width": BIN_WIDTH,
        "dsigma_ddphi_pb_per_rad": dsigma_ddphi.tolist(),
        "error_pb_per_rad": error.tolist(),
    }


def save_data(hist, outdir, label):
    data_dir = os.path.join(outdir, "output", "data")
    os.makedirs(data_dir, exist_ok=True)

    json_path = os.path.join(data_dir, f"dphi_ttbar_{label}.json")
    with open(json_path, "w") as f:
        json.dump(hist, f, indent=2)

    csv_path = os.path.join(data_dir, f"dphi_ttbar_{label}.csv")
    with open(csv_path, "w") as f:
        f.write("bin_low,bin_high,bin_center,dsigma_ddphi_pb_per_rad,error_pb_per_rad\n")
        edges = hist["bin_edges"]
        centers = hist["bin_centers"]
        y = hist["dsigma_ddphi_pb_per_rad"]
        yerr = hist["error_pb_per_rad"]
        for i in range(N_BINS):
            f.write(f"{edges[i]:.6f},{edges[i+1]:.6f},{centers[i]:.6f},{y[i]:.8f},{yerr[i]:.8f}\n")

    return json_path, csv_path


def make_plot(hists_by_label, outdir):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(7, 5.5))

    colors = {"LO": "green", "NLO": "blue"}
    y_max = 0.0

    for label in ("LO", "NLO"):
        if label not in hists_by_label:
            continue
        hist = hists_by_label[label]
        edges = np.array(hist["bin_edges"])
        y = np.array(hist["dsigma_ddphi_pb_per_rad"])
        yerr = np.array(hist["error_pb_per_rad"])
        centers = np.array(hist["bin_centers"])

        y_max = max(y_max, float(np.max(y)))

        # Step-function line
        ax.step(edges, np.append(y, y[-1]), where="post", color=colors[label],
                linestyle="-", linewidth=1.8, label=label)
        # Error bars at bin centers
        ax.errorbar(centers, y, yerr=yerr, fmt="none", ecolor=colors[label],
                     elinewidth=1.2, capsize=2)

    ax.set_xlabel(r"$\Delta\phi_{t\bar{t}}$ [rad]")
    ax.set_ylabel(r"$d\sigma/d\Delta\phi_{t\bar{t}}$ [pb/rad]")
    ax.set_xlim(PHI_MIN, PHI_MAX)
    ax.set_ylim(0.0, 1.1 * y_max if y_max > 0 else 1.0)
    ax.legend(loc="upper left")
    ax.set_title(r"$pp \to t\bar{t}$ at $\sqrt{s}=13$ TeV: $\Delta\phi_{t\bar{t}}$ distribution")
    fig.tight_layout()

    fig_dir = os.path.join(outdir, "output", "figures")
    os.makedirs(fig_dir, exist_ok=True)
    png_path = os.path.join(fig_dir, "dphi_ttbar_lo_nlo.png")
    pdf_path = os.path.join(fig_dir, "dphi_ttbar_lo_nlo.pdf")
    fig.savefig(png_path, dpi=200)
    fig.savefig(pdf_path)
    plt.close(fig)

    return png_path, pdf_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lo", type=str, default=None, help="Path to LO unweighted_events.lhe(.gz)")
    parser.add_argument("--nlo", type=str, default=None, help="Path to NLO unweighted_events.lhe(.gz)")
    parser.add_argument("--outdir", type=str, default=".",
                         help="Base output directory (output/data, output/figures created under it)")
    args = parser.parse_args()

    if args.lo is None and args.nlo is None:
        parser.error("At least one of --lo or --nlo must be supplied.")

    hists_by_label = {}

    if args.lo:
        print(f"[LO] Reading {args.lo} ...")
        hist_lo = build_histogram(args.lo)
        json_path, csv_path = save_data(hist_lo, args.outdir, "LO")
        hists_by_label["LO"] = hist_lo
        print(f"[LO] n_events={hist_lo['n_events']}  "
              f"sum_raw_weight={hist_lo['sum_raw_weight']:.4f} pb  "
              f"sum_norm_weight (cross section cross-check)={hist_lo['sum_norm_weight']:.4f} pb")
        print(f"[LO] Data saved to: {json_path}, {csv_path}")

    if args.nlo:
        if os.path.exists(args.nlo):
            print(f"[NLO] Reading {args.nlo} ...")
            hist_nlo = build_histogram(args.nlo)
            json_path, csv_path = save_data(hist_nlo, args.outdir, "NLO")
            hists_by_label["NLO"] = hist_nlo
            print(f"[NLO] n_events={hist_nlo['n_events']}  "
                  f"sum_raw_weight={hist_nlo['sum_raw_weight']:.4f} pb  "
                  f"sum_norm_weight (cross section cross-check)={hist_nlo['sum_norm_weight']:.4f} pb")
            neg = sum(1 for w, _ in parse_lhe_events(args.nlo) if w < 0)
            n_tot = hist_nlo["n_events"]
            print(f"[NLO] Negative-weight fraction: {100.0*neg/n_tot:.2f}% ({neg}/{n_tot})")
            print(f"[NLO] Data saved to: {json_path}, {csv_path}")
        else:
            print(f"[NLO] Path {args.nlo} does not exist yet -- skipping NLO curve "
                  f"(expected while the NLO run remains blocked).", file=sys.stderr)

    if not hists_by_label:
        print("No histograms produced (no valid input files found).", file=sys.stderr)
        sys.exit(1)

    png_path, pdf_path = make_plot(hists_by_label, args.outdir)
    print(f"Plot saved to: {png_path}, {pdf_path}")


if __name__ == "__main__":
    main()
