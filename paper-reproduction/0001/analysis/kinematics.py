"""
Kinematic-variable helpers for the LO/NLO/NLO+PS ttbar comparison.
Works on plain (px, py, pz, e) 4-tuples so it is agnostic to whether the
momentum came from an LHEParticle or a HepMC particle.
"""

from __future__ import annotations

import math


def pt(px: float, py: float) -> float:
    return math.hypot(px, py)


def phi(px: float, py: float) -> float:
    return math.atan2(py, px)


def rapidity(pz: float, e: float) -> float:
    # y = 0.5 * ln[(E+pz)/(E-pz)]
    num = e + pz
    den = e - pz
    if den <= 0 or num <= 0:
        # Numerically degenerate (should not happen for massive, on-shell
        # tops with E > |pz|); guard rather than raise NaN silently.
        return float("nan")
    return 0.5 * math.log(num / den)


def delta_phi_folded(phi1: float, phi2: float) -> float:
    """|phi1 - phi2| folded into [0, pi]."""
    d = abs(phi1 - phi2)
    d = d % (2 * math.pi)
    if d > math.pi:
        d = 2 * math.pi - d
    return d


def invariant_mass(p1, p2) -> float:
    """p1, p2 are (px, py, pz, e) tuples."""
    px = p1[0] + p2[0]
    py = p1[1] + p2[1]
    pz = p1[2] + p2[2]
    e = p1[3] + p2[3]
    m2 = e * e - px * px - py * py - pz * pz
    if m2 < 0:
        return -math.sqrt(-m2)  # flag numerically-negative m^2 as negative mass
    return math.sqrt(m2)


def pair_pt(p1, p2) -> float:
    px = p1[0] + p2[0]
    py = p1[1] + p2[1]
    return math.hypot(px, py)
