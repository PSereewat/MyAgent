"""
Tier 2: differential distributions (parton level), LO vs NLO, from the
cached per-event arrays produced by extract_observables.py.

Normalization mode: ABSOLUTE differential cross section (not shape-
normalized) -- dsigma/dX in pb/GeV (or pb/rad, or pb for y_t which is
dimensionless), i.e. the "absolute yield" formula from
references/normalization-conventions.md with the luminosity factor L
omitted because the target quantity is a cross section, not an event
count at a given luminosity:

    w_i = weight_i / N_gen
    dsigma/dX (bin) = sum(w_i in bin) / bin_width
    error(bin)      = sqrt(sum(w_i**2 in bin)) / bin_width

For NLO, weight_i is the signed XWGTUP -- negative-weight events are never
dropped, consistent with the skill's hard rule.

For each observable, also computes the bin-by-bin 7-point (muR,muF) scale
envelope for NLO (same envelope definition as Tier 1, applied per bin
instead of to the total rate), and, where requested, the NLO/LO ratio
(differential K-factor) with propagated uncertainty.

Writes one JSON + one CSV per observable to output/data/.
"""

from __future__ import annotations

import csv
import json
import math

import numpy as np

from parse_lhe import ENVELOPE_LABELS

N_GEN = 100_000


def kish_neff(w):
    w = np.asarray(w, dtype=float)
    denom = np.sum(w**2)
    if denom == 0:
        return 0.0
    return float(np.sum(w) ** 2 / denom)


def bin_indices(values, bin_edges):
    """Bin index per value, matching numpy.histogram's convention exactly:
    half-open bins [edges[i], edges[i+1]) except the LAST bin, which is
    closed on both ends [edges[-2], edges[-1]]. This matters here because
    the LO sample sits as a delta function exactly AT the upper edge of
    the Delta_phi_ttbar range (pi) and (trivially) at the lower edge of
    the pT_ttbar range (0) -- a naive np.digitize(...)-1 with no
    right-edge special-case silently drops every one of those events from
    the last bin. Values outside [edges[0], edges[-1]] get index -1
    (excluded, matching np.histogram's out-of-range handling)."""
    n_bins = len(bin_edges) - 1
    idx = np.searchsorted(bin_edges, values, side="right") - 1
    idx[values == bin_edges[-1]] = n_bins - 1
    out_of_range = (idx < 0) | (idx >= n_bins)
    idx[out_of_range] = -1
    return idx


def histogram_weighted(values, weights, bin_edges):
    """Returns per-bin yield (sum w / binwidth), error (sqrt(sum w^2) /
    binwidth), raw count, f_minus, and Neff -- using the general Kish
    formula, never the reduced closed form. Bins with zero raw events
    get yield=error=0 explicitly (never fabricated/interpolated)."""
    values = np.asarray(values, dtype=float)
    weights = np.asarray(weights, dtype=float)
    valid = ~np.isnan(values)
    values = values[valid]
    weights = weights[valid]

    n_bins = len(bin_edges) - 1
    idx = bin_indices(values, bin_edges)

    yields = np.zeros(n_bins)
    errors = np.zeros(n_bins)
    counts = np.zeros(n_bins, dtype=int)
    f_minus = np.full(n_bins, np.nan)
    neff = np.zeros(n_bins)

    for i in range(n_bins):
        mask = idx == i
        n_in = int(np.sum(mask))
        counts[i] = n_in
        if n_in == 0:
            continue
        w = weights[mask]
        bw = bin_edges[i + 1] - bin_edges[i]
        yields[i] = np.sum(w) / bw
        errors[i] = np.sqrt(np.sum(w**2)) / bw
        f_minus[i] = np.sum(w < 0) / n_in
        neff[i] = kish_neff(w)

    return {
        "yield": yields,
        "error": errors,
        "count": counts,
        "f_minus": f_minus,
        "neff": neff,
    }


def envelope_per_bin(values, env_weight_dict, bin_edges):
    """env_weight_dict: {label: array}. Returns dict label -> yield array
    (sum w / binwidth per bin), plus up/down envelope arrays relative to
    the central_1_1 label."""
    n_bins = len(bin_edges) - 1
    totals = {}
    values = np.asarray(values, dtype=float)
    valid = ~np.isnan(values)
    idx_full = bin_indices(np.where(valid, values, bin_edges[0] - 1.0), bin_edges)

    for lab, w in env_weight_dict.items():
        w = np.asarray(w, dtype=float)
        yields = np.zeros(n_bins)
        for i in range(n_bins):
            mask = valid & (idx_full == i)
            n_in = int(np.sum(mask))
            if n_in == 0:
                continue
            bw = bin_edges[i + 1] - bin_edges[i]
            yields[i] = np.sum(w[mask]) / bw
        totals[lab] = yields

    central = totals["central_1_1"]
    up = np.zeros(n_bins)
    down = np.zeros(n_bins)
    for i in range(n_bins):
        vals = np.array([totals[lab][i] for lab in env_weight_dict])
        if central[i] != 0:
            up[i] = (vals.max() - central[i])
            down[i] = (vals.min() - central[i])
        else:
            up[i] = vals.max()
            down[i] = vals.min()
    return totals, up, down


def build_observable(
    name, lo, nlo, bin_edges, want_ratio, unit_label
):
    # Unified LO/NLO weighting formula (normalization-conventions.md),
    # absolute-cross-section special case: w_i = weight_i / N_gen (L
    # omitted because the target is dsigma/dX in pb, not events/luminosity).
    lo_hist = histogram_weighted(lo[name], lo["xwgtup"] / N_GEN, bin_edges)
    nlo_hist = histogram_weighted(nlo[name], nlo["xwgtup"] / N_GEN, bin_edges)

    nlo_env = {lab: nlo[f"env_{lab}"] / N_GEN for lab in ENVELOPE_LABELS}
    _, nlo_up, nlo_down = envelope_per_bin(nlo[name], nlo_env, bin_edges)

    result = {
        "observable": name,
        "unit": unit_label,
        "bin_edges": bin_edges.tolist(),
        "bin_centers": (0.5 * (bin_edges[:-1] + bin_edges[1:])).tolist(),
        "bin_widths": (bin_edges[1:] - bin_edges[:-1]).tolist(),
        "LO": {
            "dsigma_dX": lo_hist["yield"].tolist(),
            "error": lo_hist["error"].tolist(),
            "raw_count": lo_hist["count"].tolist(),
        },
        "NLO": {
            "dsigma_dX": nlo_hist["yield"].tolist(),
            "error": nlo_hist["error"].tolist(),
            "raw_count": nlo_hist["count"].tolist(),
            "f_minus": [None if math.isnan(x) else x for x in nlo_hist["f_minus"]],
            "neff": nlo_hist["neff"].tolist(),
            "scale_band_up": nlo_up.tolist(),
            "scale_band_down": nlo_down.tolist(),
        },
    }

    if want_ratio:
        lo_y = lo_hist["yield"]
        lo_e = lo_hist["error"]
        nlo_y = nlo_hist["yield"]
        nlo_e = nlo_hist["error"]
        ratio = np.full(len(lo_y), np.nan)
        ratio_err = np.full(len(lo_y), np.nan)
        for i in range(len(lo_y)):
            if lo_y[i] != 0 and nlo_y[i] != 0:
                ratio[i] = nlo_y[i] / lo_y[i]
                rel_lo = lo_e[i] / lo_y[i]
                rel_nlo = nlo_e[i] / nlo_y[i]
                ratio_err[i] = ratio[i] * math.sqrt(rel_lo**2 + rel_nlo**2)
        result["ratio_NLO_over_LO"] = [None if math.isnan(x) else x for x in ratio]
        result["ratio_error"] = [None if math.isnan(x) else x for x in ratio_err]

    return result


def save_csv(result, path):
    is_ratio = "ratio_NLO_over_LO" in result
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        header = [
            "bin_low", "bin_high", "bin_center",
            "LO_dsigma_dX", "LO_error", "LO_raw_count",
            "NLO_dsigma_dX", "NLO_error", "NLO_raw_count",
            "NLO_f_minus", "NLO_neff", "NLO_scale_band_up", "NLO_scale_band_down",
        ]
        if is_ratio:
            header += ["ratio_NLO_over_LO", "ratio_error"]
        writer.writerow(header)
        edges = result["bin_edges"]
        n = len(result["bin_centers"])
        for i in range(n):
            row = [
                edges[i], edges[i + 1], result["bin_centers"][i],
                result["LO"]["dsigma_dX"][i], result["LO"]["error"][i], result["LO"]["raw_count"][i],
                result["NLO"]["dsigma_dX"][i], result["NLO"]["error"][i], result["NLO"]["raw_count"][i],
                result["NLO"]["f_minus"][i], result["NLO"]["neff"][i],
                result["NLO"]["scale_band_up"][i], result["NLO"]["scale_band_down"][i],
            ]
            if is_ratio:
                row += [result["ratio_NLO_over_LO"][i], result["ratio_error"][i]]
            writer.writerow(row)


def main():
    lo = dict(np.load("analysis/cache/lo_events.npz"))
    nlo = dict(np.load("analysis/cache/nlo_events.npz"))

    specs = [
        ("pt_ttbar", np.linspace(0, 400, 41), False, "pb/GeV"),
        ("dphi_ttbar", np.linspace(0, math.pi, 41), False, "pb/rad"),
        ("pt_t", np.linspace(0, 800, 41), True, "pb/GeV"),
        ("m_ttbar", np.linspace(300, 1500, 41), True, "pb/GeV"),
        ("y_t", np.linspace(-3, 3, 41), True, "pb"),
    ]

    for name, edges, want_ratio, unit in specs:
        result = build_observable(name, lo, nlo, edges, want_ratio, unit)
        json_path = f"output/data/{name}.json"
        csv_path = f"output/data/{name}.csv"
        with open(json_path, "w") as f:
            json.dump(result, f, indent=2)
        save_csv(result, csv_path)
        print(f"{name}: wrote {json_path} and {csv_path}")
        print(f"  LO total raw count in histogram range = {sum(result['LO']['raw_count'])} / {len(lo['xwgtup'])}")
        print(f"  NLO total raw count in histogram range = {sum(result['NLO']['raw_count'])} / {len(nlo['xwgtup'])}")

    # explicit LO delta-function checks
    lo_pt_ttbar = lo["pt_ttbar"]
    lo_dphi = lo["dphi_ttbar"]
    print()
    print("=== LO delta-function validation ===")
    print(f"pT_ttbar: min={np.nanmin(lo_pt_ttbar):.6e}, max={np.nanmax(lo_pt_ttbar):.6e} GeV "
          f"(expect ~0 within float tolerance)")
    print(f"Delta_phi_ttbar: min={np.nanmin(lo_dphi):.10f}, max={np.nanmax(lo_dphi):.10f} rad "
          f"(expect ~pi = {math.pi:.10f})")

    print()
    print("=== NLO nonzero-tail validation ===")
    nlo_pt_ttbar = nlo["pt_ttbar"]
    nlo_dphi = nlo["dphi_ttbar"]
    frac_pt_above_10 = np.mean(nlo_pt_ttbar > 10)
    frac_dphi_below_3 = np.mean(nlo_dphi < 3.0)
    print(f"NLO fraction of events with pT_ttbar > 10 GeV: {frac_pt_above_10*100:.2f}%")
    print(f"NLO fraction of events with Delta_phi_ttbar < 3.0 rad: {frac_dphi_below_3*100:.2f}%")


if __name__ == "__main__":
    main()
