"""
Shared bin-edge definitions for the 5 Tier-2 differential observables, so
that LO, NLO fixed-order, and NLO+PS are histogrammed identically and can
be directly overlaid. Absolute-yield mode (pb per bin, no shape
normalization) is used throughout -- see the provenance/normalization
note in each analyze_*.py script.
"""

import numpy as np

BIN_EDGES = {
    # pT of the ttbar system [GeV]. LO: delta function at 0 (all events in
    # the first bin). NLO/NLO+PS: nonzero tail from real emission/shower.
    "pt_ttbar": np.linspace(0.0, 500.0, 21),  # 20 bins, 25 GeV wide
    # Delta_phi(t,tbar) folded into [0, pi] [rad]. LO: delta function at
    # pi (all events in the last bin).
    "dphi_ttbar": np.linspace(0.0, np.pi, 21),  # 20 bins
    # pT of the leading top (max(pT_t, pT_tbar)) [GeV].
    "pt_top_lead": np.linspace(0.0, 600.0, 25),  # 24 bins, 25 GeV wide
    # m_ttbar [GeV]. Threshold is 2*172.5 = 345 GeV.
    "m_ttbar": np.linspace(340.0, 1400.0, 41),  # 40 bins, 26.5 GeV wide
    # top rapidity y_t.
    "y_t": np.linspace(-3.0, 3.0, 25),  # 24 bins, 0.25 wide
}


def bin_centers(edges):
    return 0.5 * (edges[:-1] + edges[1:])
