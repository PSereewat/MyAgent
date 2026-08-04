"""
Template: extract a 1D or 2D exclusion contour by scanning the
profile-likelihood test statistic over a parameter grid and solving for
the 2-sigma (or 5-sigma discovery) crossing, per
references/statistical-methods.md.

Depends on profile_likelihood_fit.py's Channel/profile_nll/global_best_fit.
"""

from __future__ import annotations

import numpy as np
from scipy.optimize import brentq

# from profile_likelihood_fit import Channel, global_best_fit, test_statistic


def find_1d_exclusion(
    g_grid: np.ndarray,
    q_of_g,
    threshold: float = 3.84,
) -> float | None:
    """Given a monotonically-varying test statistic q_of_g(g) over
    g_grid, find the g value where q crosses `threshold` (default 3.84 =
    95% CL one-sided, 1 dof). Returns None if no crossing is found in
    range -- report that explicitly rather than extrapolating."""

    q_vals = np.array([q_of_g(g) for g in g_grid])
    crossing_idx = np.where(np.diff(np.sign(q_vals - threshold)))[0]

    if len(crossing_idx) == 0:
        print(
            "[exclusion_contour_scan] WARNING: no threshold crossing found "
            f"in scanned range [{g_grid[0]}, {g_grid[-1]}]. Widen the scan "
            "range rather than reporting an extrapolated limit."
        )
        return None

    i = crossing_idx[0]

    def f(g):
        return q_of_g(g) - threshold

    return brentq(f, g_grid[i], g_grid[i + 1])


def scan_2d_exclusion(
    param1_grid: np.ndarray,
    param2_grid: np.ndarray,
    q_of_params,  # callable(p1, p2) -> test statistic
    threshold: float = 3.84,
) -> np.ndarray:
    """Evaluate q on a 2D grid; returns the grid of q values for external
    contour plotting (e.g. matplotlib contour at level=threshold).

    Regenerating signal at every 2D grid point is expensive -- only do
    this directly if the signal does not follow a simple analytic scaling
    in both parameters (see statistical-methods.md on when a power-law
    rescale is/isn't valid). Otherwise compute at a coarse grid of
    directly-generated points and interpolate, but validate the
    interpolation against a few held-out points before trusting it.
    """

    Q = np.full((len(param1_grid), len(param2_grid)), np.nan)
    for i, p1 in enumerate(param1_grid):
        for j, p2 in enumerate(param2_grid):
            Q[i, j] = q_of_params(p1, p2)

    if np.any(np.isnan(Q)):
        raise ValueError(
            "Some grid points failed to evaluate -- do not plot a contour "
            "with missing/NaN entries silently interpolated over."
        )

    return Q
