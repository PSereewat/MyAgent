"""
Template: standard plotting conventions for kinematic distributions and
exclusion contours, matching the style used in ColliderAgent's own
benchmark figures (arXiv:2603.14553, Fig. 2 / Fig. S1).

Always save both the figure AND the underlying numerical data (see
save_result_bundle) -- an image alone is not sufficient provenance.
"""

from __future__ import annotations

import json

import matplotlib.pyplot as plt
import numpy as np


def plot_kinematic_distribution(
    bin_edges: np.ndarray,
    values: np.ndarray,
    label: str,
    reference_values: np.ndarray | None = None,
    reference_label: str = "reference",
    xlabel: str = "",
    ylabel: str = "events / bin",
    logy: bool = True,
    outpath: str = "distribution.png",
) -> None:
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.step(bin_edges[:-1], values, where="post", color="red", label=label)
    if reference_values is not None:
        ax.step(
            bin_edges[:-1],
            reference_values,
            where="post",
            color="black",
            label=reference_label,
        )
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    if logy:
        ax.set_yscale("log")
    ax.legend()
    fig.tight_layout()
    fig.savefig(outpath, dpi=150)
    plt.close(fig)
    print(f"[plot] Saved {outpath}")


def plot_exclusion_contour_2d(
    param1_grid: np.ndarray,
    param2_grid: np.ndarray,
    q_grid: np.ndarray,
    threshold: float,
    xlabel: str,
    ylabel: str,
    reference_curve: tuple[np.ndarray, np.ndarray] | None = None,
    reference_label: str = "reference",
    shade_excluded: bool = True,
    outpath: str = "exclusion_contour.png",
) -> None:
    fig, ax = plt.subplots(figsize=(6, 5))
    P1, P2 = np.meshgrid(param1_grid, param2_grid, indexing="ij")

    cs = ax.contour(P1, P2, q_grid, levels=[threshold], colors="red")
    ax.clabel(cs, inline=True, fmt="ColliderAgent")

    if shade_excluded:
        ax.contourf(
            P1, P2, q_grid, levels=[threshold, q_grid.max()], colors=["red"], alpha=0.15
        )

    if reference_curve is not None:
        ax.plot(reference_curve[0], reference_curve[1], color="black", label=reference_label)

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.legend()
    fig.tight_layout()
    fig.savefig(outpath, dpi=150)
    plt.close(fig)
    print(f"[plot] Saved {outpath}")


def save_result_bundle(outpath_json: str, **data) -> None:
    """Save all numerical results backing a plot as JSON -- required by
    the validation checklist (never ship a plot without its data)."""

    def _default(o):
        if isinstance(o, np.ndarray):
            return o.tolist()
        raise TypeError(f"Not JSON serializable: {type(o)}")

    with open(outpath_json, "w") as f:
        json.dump(data, f, indent=2, default=_default)
    print(f"[plot] Saved result bundle {outpath_json}")
