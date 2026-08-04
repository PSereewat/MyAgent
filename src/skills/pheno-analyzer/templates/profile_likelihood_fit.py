"""
Template: binned profile-likelihood fit with one Gaussian-constrained
nuisance parameter per bin, following the convention in
references/statistical-methods.md.

For anything beyond this single-parameter-of-interest, per-bin-nuisance
setup (e.g. correlated systematics, shape uncertainties, many nuisance
parameters), prefer building the model in `pyhf` instead of extending
this by hand.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import minimize


@dataclass
class Channel:
    """One analysis channel (e.g. ATLAS or CMS mono-tau selection)."""

    n_obs: np.ndarray  # observed counts per bin
    b_sm: np.ndarray  # SM background prediction per bin
    db: np.ndarray  # background uncertainty per bin (symmetric)
    s_ref: np.ndarray  # signal yield per bin AT THE REFERENCE coupling value
    scaling_power: float  # n such that s_i(g) = g**n * s_ref_i

    def signal(self, g: float) -> np.ndarray:
        return (g**self.scaling_power) * self.s_ref


def neg_log_likelihood_channel(g: float, theta: np.ndarray, ch: Channel) -> float:
    b = ch.b_sm
    db = ch.db
    n = ch.n_obs
    s = ch.signal(g)

    mu = b * (1 + theta) + s
    mu = np.clip(mu, 1e-12, None)  # guard against log(0) / negative mu

    poisson_term = -(n * np.log(mu) - mu)
    with np.errstate(divide="ignore"):
        frac_unc = np.where(b > 0, db / b, np.inf)
    constraint_term = np.where(
        np.isfinite(frac_unc), 0.5 * (theta / frac_unc) ** 2, 0.0
    )

    return float(np.sum(poisson_term) + np.sum(constraint_term))


def profile_nll(g: float, channels: list[Channel]) -> tuple[float, list[np.ndarray]]:
    """Minimize -lnL over nuisance parameters theta for fixed g.
    Returns (min -lnL, list of best-fit theta arrays per channel)."""

    theta_hats = []
    total = 0.0
    for ch in channels:
        n_bins = len(ch.n_obs)
        x0 = np.zeros(n_bins)

        def obj(theta, ch=ch):
            return neg_log_likelihood_channel(g, theta, ch)

        res = minimize(obj, x0, method="L-BFGS-B")
        if not res.success:
            print(
                f"[profile_likelihood_fit] WARNING: nuisance-parameter "
                f"minimization did not converge at g={g}: {res.message}"
            )
        theta_hats.append(res.x)
        total += res.fun

    return total, theta_hats


def global_best_fit(channels: list[Channel], g_bounds=(0.0, 10.0)) -> dict:
    """Find g_hat minimizing the combined -lnL over g (profiling theta at
    each step). Enforces g >= 0 by default -- adjust g_bounds if the
    physical model allows negative couplings."""

    def obj(g_arr):
        g = float(g_arr[0])
        nll, _ = profile_nll(g, channels)
        return nll

    x0 = np.array([max(g_bounds[0], 1.0)])
    res = minimize(obj, x0, method="L-BFGS-B", bounds=[g_bounds])

    if not res.success:
        print(f"[profile_likelihood_fit] WARNING: global fit did not converge: {res.message}")

    g_hat = float(res.x[0])
    on_boundary = np.isclose(g_hat, g_bounds[0]) or np.isclose(g_hat, g_bounds[1])
    if on_boundary:
        print(
            f"[profile_likelihood_fit] NOTE: best-fit g_hat={g_hat:.4g} is on "
            "the boundary of the allowed range -- report this, don't treat "
            "it as an unconstrained converged minimum."
        )

    return {"g_hat": g_hat, "nll_hat": float(res.fun), "converged": res.success, "on_boundary": on_boundary}


def test_statistic(g: float, channels: list[Channel], fit_result: dict) -> float:
    """q(g) = -2 * [ lnL(g, theta_hat(g)) - lnL(g_hat, theta_hat(g_hat)) ]"""
    nll_g, _ = profile_nll(g, channels)
    return 2.0 * (nll_g - fit_result["nll_hat"])


if __name__ == "__main__":
    # Minimal smoke test with the CMS mono-tau table from
    # arXiv:2603.14553 supplemental material sec. 3.1 (illustrative only --
    # replace s_ref with actual simulated signal yields for a real task).
    ch = Channel(
        n_obs=np.array([1203, 452, 15], dtype=float),
        b_sm=np.array([1243, 485, 23.4], dtype=float),
        db=np.array([160, 77, 6.2], dtype=float),
        s_ref=np.array([50.0, 30.0, 5.0], dtype=float),  # placeholder
        scaling_power=4.0,
    )
    fit = global_best_fit([ch])
    print("Best fit:", fit)
    q_at_zero = test_statistic(0.0, [ch], fit)
    print(f"q(g=0) = {q_at_zero:.3f}  (significance ~ sqrt(q) = {np.sqrt(max(q_at_zero, 0)):.3f})")
