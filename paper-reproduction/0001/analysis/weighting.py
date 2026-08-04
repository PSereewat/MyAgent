"""
Unified LO/NLO event-weighting and weighted-histogram utilities, adapted
from the pheno-analyzer skill's templates/nlo_event_weights.py (same
formulas, copied locally so the analysis/ directory here is
self-contained and portable, per the "all paths relative to the working
directory" output requirement).

Convention used throughout this study (see ../LO_NLO_NLOPS.md and the
per-run progress files): all yields reported here are absolute total
cross sections in pb (i.e. L = 1 pb^-1, no luminosity scaling), so
w_i = weight_i / N_gen, and sigma = sum(w_i) over all generated events
(including negative-weight ones -- never dropped).
"""

from __future__ import annotations

import numpy as np


def kish_neff(w) -> float:
    """General (Kish) effective-sample-size formula -- always correct
    regardless of the weight distribution. This is what gets reported,
    never the reduced closed form N*(1-2*f_minus)**2."""
    w = np.asarray(w, dtype=float)
    denom = np.sum(w**2)
    if denom == 0:
        return 0.0
    return float(np.sum(w) ** 2 / denom)


def negative_weight_fraction(weights) -> dict:
    w = np.asarray(weights, dtype=float)
    n_total = len(w)
    n_negative = int(np.sum(w < 0))
    f_minus = n_negative / n_total if n_total > 0 else float("nan")
    return {"n_total": n_total, "n_negative": n_negative, "f_minus": f_minus}


def weighted_histogram(values, weights, bin_edges):
    """Histogram already-scaled per-event weights `weights` (i.e. w_i,
    with any 1/N_gen normalization already applied by the caller) into
    the given bin_edges.

    Returns dict with per-bin: yield (sum of w_i), error (sqrt(sum
    w_i**2)), neff (general Kish formula), f_minus, n_raw (unweighted
    event count in bin).
    """
    values = np.asarray(values, dtype=float)
    w = np.asarray(weights, dtype=float)
    if len(values) != len(w):
        raise ValueError("values and weights must have the same length")

    n_bins = len(bin_edges) - 1
    out = {
        "yield": np.zeros(n_bins),
        "error": np.zeros(n_bins),
        "neff": np.zeros(n_bins),
        "f_minus": np.full(n_bins, np.nan),
        "n_raw": np.zeros(n_bins, dtype=int),
    }

    bin_idx = np.digitize(values, bin_edges) - 1

    for i in range(n_bins):
        mask = bin_idx == i
        w_bin = w[mask]
        n_in_bin = len(w_bin)
        out["n_raw"][i] = n_in_bin
        if n_in_bin == 0:
            continue  # explicit zero, not fabricated
        out["yield"][i] = np.sum(w_bin)
        out["error"][i] = np.sqrt(np.sum(w_bin**2))
        out["neff"][i] = kish_neff(w_bin)
        out["f_minus"][i] = np.mean(w_bin < 0)

    return out


def overflow_safe_bin_edges(lo, hi, nbins):
    return np.linspace(lo, hi, nbins + 1)


def weighted_histogram_edge_safe(values, weights, bin_edges):
    """Same as `weighted_histogram`, but fixes a specific silent-drop bug
    discovered while preparing the lo_vs_nlo_finebin comparison:
    `np.digitize` (right=False, the default used by `weighted_histogram`)
    sends any value exactly equal to the last bin edge to the OVERFLOW
    bucket (index == n_bins), not the last real bin -- because digitize's
    convention is `edges[i-1] <= x < edges[i]`, so `x == edges[-1]` fails
    every interval and is treated as `x >= edges[-1]`.

    This matters in practice: `Delta_phi_ttbar` is folded into exactly
    [0, pi] by construction (see kinematics.delta_phi_folded), and for
    the LO sample essentially every event's folded delta-phi evaluates to
    the bit-for-bit double-precision value of `math.pi` (confirmed:
    8710/10000 LO events, 8020/10000 NLO events in the original 20/40-bin
    edges respectively). With the plain `weighted_histogram`, all of
    those events are silently dropped from the last bin (verified: only
    1290/10000 LO events appeared in the existing
    `output/data/dphi_ttbar.csv` last bin, not the expected ~10000) --
    this is a genuine pre-existing bug in the original Tier-2
    `dphi_ttbar` histogram, discovered independently while building this
    fine-binned comparison, and reported explicitly rather than silently
    reproduced here.

    Fix: any value exactly equal to the last bin edge is placed in the
    last bin instead of being discarded as overflow. Values genuinely
    above the last edge (which cannot occur for delta_phi_folded, whose
    range is capped at pi by construction, but could occur for an
    observable without a hard physical ceiling) are still correctly
    treated as overflow and dropped -- this only fixes the exact-equality
    edge case, it does not silently swallow real out-of-range values.
    """
    values = np.asarray(values, dtype=float)
    w = np.asarray(weights, dtype=float)
    if len(values) != len(w):
        raise ValueError("values and weights must have the same length")

    n_bins = len(bin_edges) - 1
    values_safe = np.where(values == bin_edges[-1],
                            np.nextafter(bin_edges[-1], -np.inf),
                            values)
    return weighted_histogram(values_safe, w, bin_edges)
