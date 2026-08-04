"""
Template: unified LO/NLO event weighting, per-bin yields and errors, and
effective-sample-size (Neff) diagnostics.

See references/normalization-conventions.md for the full explanation of
why the reduced closed-form Neff formula (N*(1-2*f_minus)**2) is NOT used
here as the general rule -- it silently gives wrong answers when
negative-weight events don't share the same magnitude as positive ones,
which is common in real merged/reweighted NLO samples. This template
always computes the general (Kish) formula from the actual weights, and
only uses the reduced form as an optional cross-check.
"""

from __future__ import annotations

import numpy as np


def detect_negative_weights(weights) -> dict:
    """Independently verify whether a sample actually has negative
    weights, rather than trusting an upstream 'this is NLO' claim."""

    w = np.asarray(weights, dtype=float)
    n_total = len(w)
    n_negative = int(np.sum(w < 0))
    f_minus = n_negative / n_total if n_total > 0 else float("nan")

    return {
        "n_total": n_total,
        "n_negative": n_negative,
        "f_minus": f_minus,
        "has_negative_weights": n_negative > 0,
    }


def event_weight(weight_i: np.ndarray, L: float, N_gen: int) -> np.ndarray:
    """Unified LO/NLO per-event weight for absolute-yield mode.

    weight_i: raw per-event weight from the generator (constant = sigma
        for a plain unit-weight LO sample; signed and non-constant for
        NLO). Units are whatever the generator reports (confirm/state,
        typically pb).
    L: integrated luminosity, in units consistent with weight_i (e.g. if
        weight_i is in pb, L should be in pb^-1).
    N_gen: number of generated events used to compute weight_i (i.e. the
        denominator such that sum(weight_i)/N_gen = sigma).
    """
    weight_i = np.asarray(weight_i, dtype=float)
    return weight_i * L / N_gen


def kish_neff(w: np.ndarray) -> float:
    """General effective-sample-size formula. Always correct regardless
    of the weight distribution. This is what should be reported."""
    w = np.asarray(w, dtype=float)
    denom = np.sum(w**2)
    if denom == 0:
        return 0.0
    return float(np.sum(w) ** 2 / denom)


def reduced_form_neff(n: int, f_minus: float) -> float:
    """Closed-form Neff assuming ALL events share the same weight
    magnitude (pure +w0/-w0). Only use this as a cross-check against
    kish_neff when weight magnitudes visibly look uniform -- never
    report this as the primary result. See references/
    normalization-conventions.md for a worked example of how badly this
    can diverge from the correct value when magnitudes are not uniform.
    """
    return n * (1 - 2 * f_minus) ** 2


def bin_events(
    values: np.ndarray,
    weights: np.ndarray,
    bin_edges: np.ndarray,
    L: float,
    N_gen: int,
    neff_disagreement_warn_threshold: float = 0.2,
) -> dict:
    """Histogram weighted events into bins, with correct errors and Neff
    diagnostics per bin.

    Returns a dict with per-bin arrays: yield, error, f_minus, neff,
    neff_reduced_form, and a flag for bins where the reduced-form
    estimate disagrees with the general formula by more than
    `neff_disagreement_warn_threshold` (relative) -- a sign that weight
    magnitudes are not uniform in that bin and any code elsewhere that
    might be using the reduced form should not be trusted there.
    """
    values = np.asarray(values, dtype=float)
    raw_weights = np.asarray(weights, dtype=float)

    if len(values) != len(raw_weights):
        raise ValueError("values and weights must be the same length.")

    w_scaled = event_weight(raw_weights, L, N_gen)

    n_bins = len(bin_edges) - 1
    yields = np.zeros(n_bins)
    errors = np.zeros(n_bins)
    f_minus_per_bin = np.full(n_bins, np.nan)
    neff_per_bin = np.zeros(n_bins)
    neff_reduced_per_bin = np.zeros(n_bins)
    disagreement_flag = np.zeros(n_bins, dtype=bool)

    bin_idx = np.digitize(values, bin_edges) - 1

    for i in range(n_bins):
        mask = bin_idx == i
        w_bin = w_scaled[mask]
        n_in_bin = len(w_bin)

        if n_in_bin == 0:
            # Explicit zero, not a fabricated/interpolated value.
            yields[i] = 0.0
            errors[i] = 0.0
            f_minus_per_bin[i] = float("nan")
            neff_per_bin[i] = 0.0
            neff_reduced_per_bin[i] = 0.0
            continue

        yields[i] = np.sum(w_bin)
        errors[i] = np.sqrt(np.sum(w_bin**2))

        raw_w_bin = raw_weights[mask]
        n_neg = int(np.sum(raw_w_bin < 0))
        f_minus = n_neg / n_in_bin
        f_minus_per_bin[i] = f_minus

        neff_general = kish_neff(w_bin)
        neff_reduced = reduced_form_neff(n_in_bin, f_minus)
        neff_per_bin[i] = neff_general
        neff_reduced_per_bin[i] = neff_reduced

        if neff_general > 0:
            rel_diff = abs(neff_reduced - neff_general) / neff_general
            if rel_diff > neff_disagreement_warn_threshold:
                disagreement_flag[i] = True

    if np.any(disagreement_flag):
        print(
            "[nlo_event_weights] WARNING: reduced-form Neff disagrees "
            f"with the general formula by >{neff_disagreement_warn_threshold*100:.0f}% "
            f"in {int(disagreement_flag.sum())} bin(s) -- weight magnitudes "
            "are not uniform there. The general-formula Neff (reported) is "
            "correct; do not substitute the reduced form for those bins."
        )

    return {
        "yield": yields,
        "error": errors,
        "f_minus": f_minus_per_bin,
        "neff": neff_per_bin,
        "neff_reduced_form": neff_reduced_per_bin,
        "reduced_form_disagreement": disagreement_flag,
    }


if __name__ == "__main__":
    # Smoke test reproducing the discrepancy documented in
    # normalization-conventions.md: equal-magnitude weights vs. a
    # realistic mixed-magnitude NLO-like sample.

    print("=== Equal-magnitude weights (reduced form should match) ===")
    w_equal = np.array([1.0] * 7 + [-1.0] * 3)
    info = detect_negative_weights(w_equal)
    print(info)
    print("Kish Neff:      ", kish_neff(w_equal))
    print("Reduced-form:   ", reduced_form_neff(info["n_total"], info["f_minus"]))

    print()
    print("=== Mixed-magnitude weights (reduced form should NOT match) ===")
    rng = np.random.default_rng(0)
    pos = rng.exponential(scale=1.0, size=900)
    neg = -rng.exponential(scale=1.3, size=100)
    w_mixed = np.concatenate([pos, neg])
    info2 = detect_negative_weights(w_mixed)
    print(info2)
    print("Kish Neff:      ", kish_neff(w_mixed))
    print("Reduced-form:   ", reduced_form_neff(info2["n_total"], info2["f_minus"]))

    print()
    print("=== bin_events end-to-end smoke test ===")
    values = rng.uniform(0, 100, size=1000)
    bin_edges = np.linspace(0, 100, 6)
    result = bin_events(values, w_mixed, bin_edges, L=100.0, N_gen=1000)
    for k, v in result.items():
        print(k, "=", v)
