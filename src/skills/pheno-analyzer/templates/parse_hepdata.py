"""
Template: parse a HEPData-style YAML table into simple numpy arrays.

Use this as a starting point when reading experimental data tables
(observed events, SM background, uncertainties) for a profile-likelihood
fit. Adapt field names to the specific table's schema, but keep the
sanity checks -- they exist because silent schema mismatches produce
plausible-looking but wrong numbers.
"""

from __future__ import annotations

import numpy as np
import yaml


def load_hepdata_table(path: str, dependent_var_index: int = 0) -> dict:
    """Load a HEPData YAML table.

    Returns a dict with keys: bin_low, bin_high, value, error_plus,
    error_minus (all numpy arrays of equal length).
    """
    with open(path, "r") as f:
        data = yaml.safe_load(f)

    indep = data["independent_variables"][0]["values"]
    dep = data["dependent_variables"][dependent_var_index]["values"]

    if len(indep) != len(dep):
        raise ValueError(
            f"Independent ({len(indep)}) and dependent ({len(dep)}) "
            "variable lengths do not match -- schema mismatch, do not proceed."
        )

    bin_low = np.array([v.get("low", np.nan) for v in indep], dtype=float)
    bin_high = np.array([v.get("high", np.nan) for v in indep], dtype=float)
    value = np.array([v["value"] for v in dep], dtype=float)

    error_plus = np.full(len(dep), np.nan)
    error_minus = np.full(len(dep), np.nan)
    for i, v in enumerate(dep):
        errs = v.get("errors", [])
        if errs:
            e = errs[0]
            if "symerror" in e:
                error_plus[i] = error_minus[i] = float(e["symerror"])
            else:
                error_plus[i] = float(e.get("asymerror", {}).get("plus", np.nan))
                error_minus[i] = float(e.get("asymerror", {}).get("minus", np.nan))

    # Sanity checks -- fail loudly rather than silently propagating garbage.
    if np.any(np.isnan(bin_low)) or np.any(np.isnan(bin_high)):
        raise ValueError("Missing bin edges in independent_variables block.")
    if not np.all(np.diff(bin_low) >= 0):
        raise ValueError("Bin edges are not monotonically increasing.")
    if np.any(value < 0):
        raise ValueError("Negative observed/background values -- check units/schema.")

    print(
        f"[parse_hepdata] Loaded {len(value)} bins from {path}: "
        f"range [{bin_low[0]}, {bin_high[-1]}], "
        f"value range [{value.min():.4g}, {value.max():.4g}]"
    )

    return {
        "bin_low": bin_low,
        "bin_high": bin_high,
        "value": value,
        "error_plus": error_plus,
        "error_minus": error_minus,
    }


def load_manual_table(rows: list[dict]) -> dict:
    """For cases where data is given directly in the prompt as a table
    rather than a HEPData file, e.g.:

        rows = [
            {"bin_low": 320, "bin_high": 500, "n_obs": 1203, "b_sm": 1243, "db": 160},
            {"bin_low": 500, "bin_high": 1000, "n_obs": 452, "b_sm": 485, "db": 77},
            {"bin_low": 1000, "bin_high": 3200, "n_obs": 15, "b_sm": 23.4, "db": 6.2},
        ]

    Still run the same consistency checks as the HEPData loader.
    """
    bin_low = np.array([r["bin_low"] for r in rows], dtype=float)
    bin_high = np.array([r["bin_high"] for r in rows], dtype=float)
    n_obs = np.array([r["n_obs"] for r in rows], dtype=float)
    b_sm = np.array([r["b_sm"] for r in rows], dtype=float)
    db = np.array([r["db"] for r in rows], dtype=float)

    if not np.all(np.diff(bin_low) >= 0):
        raise ValueError("Bin edges are not monotonically increasing.")
    if np.any(n_obs < 0) or np.any(b_sm < 0) or np.any(db < 0):
        raise ValueError("Negative counts/uncertainties -- check the input table.")

    print(
        f"[parse_hepdata] Loaded {len(rows)} manually-specified bins: "
        f"range [{bin_low[0]}, {bin_high[-1]}]"
    )

    return {"bin_low": bin_low, "bin_high": bin_high, "n_obs": n_obs, "b_sm": b_sm, "db": db}
