"""
Finer bin-edge definitions for the NEW LO-vs-NLO-fixed-order-only
comparison (`lo_vs_nlo_finebin`), kept in a SEPARATE module from
`binning.py` so the original Tier-2 LO/NLO/NLO+PS comparison (and its
already-produced plots/CSVs under output/figures/*.png,
output/data/*.csv) is never touched, re-run, or overwritten.

Design rationale (see progress note / final report for full explanation
with the actual per-bin raw-count diagnostics that drove each choice):
each observable's bin count was explored by re-histogramming the actual
10000-event LO and NLO fixed-order samples at several candidate bin
counts and checking how many bins fall below ~5 raw (unweighted) events
-- a rough "is this bin dominated by Poisson noise rather than real
shape" threshold given only 10000 events per sample. Where a full
halving of bin width (doubling of bin count) pushed a large fraction of
bins into that sparse regime, a more moderate increase was chosen
instead:

- pt_ttbar:    20 -> 25 bins (25 GeV -> 20 GeV wide). NOT fully doubled
  to 40 bins/12.5 GeV: the NLO real-emission tail falls very steeply
  (already only ~3-14 raw events per bin above ~300 GeV at the CURRENT
  25 GeV binning), and at 40 bins, 11/40 bins (28%) had <5 raw NLO
  events -- judged too noisy. At 25 bins (20 GeV), only 5/25 bins (20%,
  all above ~350 GeV) fall below 5 events, and that sparse region is a
  genuine low-statistics tail regardless of binning choice, not an
  artifact of over-binning.
- dphi_ttbar:  20 -> 40 bins (0.157 rad -> 0.0785 rad wide). Full
  doubling is fine here: even at 40 bins every NLO bin has >= 9 raw
  events (0 bins below 5).
- pt_top_lead: 24 -> 32 bins (25 GeV -> 18.75 GeV wide). NOT fully
  doubled to 48 bins/12.5 GeV: that pushed 7/48 (LO) and 6/48 (NLO)
  bins below 5 raw events (~13-15%). At 32 bins, only 3/32 bins (~9%)
  are that sparse for either sample.
- m_ttbar:     40 -> 60 bins (26.5 GeV -> 17.67 GeV wide). NOT fully
  doubled to 80 bins/13.25 GeV: that pushed 9/80 (LO) and 8/80 (NLO)
  bins below 5 raw events (~11%), concentrated above ~1000 GeV. At 60
  bins, only 4/60 (LO) and 3/60 (NLO) bins (~5-7%) are that sparse.
- y_t:         24 -> 48 bins (0.25 -> 0.125 wide). Full doubling is
  fine here: the y_t distribution is broad and smooth, minimum raw
  count per bin is still >= 22 events even at 48 bins (0 bins below 5).

All ranges are unchanged from `binning.py` (only the bin COUNT changes),
so the physical coverage is identical and any single-bin comparison
against the coarser Tier-2 plot is a strict refinement, not a different
window.
"""

import numpy as np

FINE_BIN_EDGES = {
    "pt_ttbar": np.linspace(0.0, 500.0, 26),      # 25 bins, 20.0 GeV wide
    "dphi_ttbar": np.linspace(0.0, np.pi, 41),     # 40 bins, ~0.0785 rad wide
    "pt_top_lead": np.linspace(0.0, 600.0, 33),    # 32 bins, 18.75 GeV wide
    "m_ttbar": np.linspace(340.0, 1400.0, 61),     # 60 bins, ~17.67 GeV wide
    "y_t": np.linspace(-3.0, 3.0, 49),             # 48 bins, 0.125 wide
}


def bin_centers(edges):
    return 0.5 * (edges[:-1] + edges[1:])
