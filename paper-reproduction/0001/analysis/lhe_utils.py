"""
Shared LHE (Les Houches Event) file parsing utilities for the LO / NLO
pp -> ttbar comparison (see ../LO_NLO_NLOPS.md).

Follows the unified LO/NLO event-weighting convention documented in the
pheno-analyzer skill (references/normalization-conventions.md):

    w_i = weight_i * L / N_gen

For total cross sections (no luminosity scaling requested), we use
L = 1 (i.e. report pb, not an absolute event count at some luminosity),
so w_i = weight_i / N_gen and sigma = sum(w_i).

Negative-weight status is verified directly from the actual per-event
XWGTUP field, never assumed from an upstream label.
"""

from __future__ import annotations

import gzip
import re
from dataclasses import dataclass, field
from typing import Iterator


@dataclass
class LHEParticle:
    pdg: int
    status: int
    mother1: int
    mother2: int
    px: float
    py: float
    pz: float
    e: float
    m: float


@dataclass
class LHEEvent:
    weight: float
    scale: float
    aqed: float
    aqcd: float
    particles: list = field(default_factory=list)
    rwgt: dict = field(default_factory=dict)  # weight_id (str) -> value


def _open(path: str):
    if path.endswith(".gz"):
        return gzip.open(path, "rt")
    return open(path, "r")


def parse_initrwgt(path: str) -> dict:
    """Parse the <initrwgt> header block (if present) to get a mapping
    weight_id (str) -> dict(tag=int, dyn=int, muR=float, muF=float).

    Returns an empty dict if no initrwgt block is present (e.g. a plain
    LO sample generated with use_syst=False, which stores no per-event
    reweighting information at all).
    """
    with _open(path) as f:
        content = f.read(400_000)  # header is always near the top

    if "<initrwgt>" not in content:
        return {}

    block_match = re.search(r"<initrwgt>(.*?)</initrwgt>", content, re.S)
    if not block_match:
        return {}
    block = block_match.group(1)

    weights = {}
    for m in re.finditer(
        r"<weight id='(\d+)'>\s*tag=\s*(-?\d+)\s*dyn=\s*(-?\d+)\s*"
        r"muR=([0-9.Ee+-]+)\s*muF=([0-9.Ee+-]+)\s*</weight>",
        block,
    ):
        wid, tag, dyn, muR, muF = m.groups()
        weights[wid] = dict(tag=int(tag), dyn=int(dyn), muR=float(muR), muF=float(muF))
    return weights


def iter_lhe_events(path: str, with_rwgt: bool = False) -> Iterator[LHEEvent]:
    """Yield LHEEvent objects, one per <event>...</event> block.

    If with_rwgt is True, also parse the per-event <rwgt> block (scale
    variation weights); otherwise this is skipped for speed.
    """
    with _open(path) as f:
        in_event = False
        header = None
        particles = []
        rwgt_text = None
        collecting_rwgt = False
        rwgt_buffer = []

        for line in f:
            stripped = line.strip()

            if stripped == "<event>":
                in_event = True
                header = None
                particles = []
                rwgt_buffer = []
                collecting_rwgt = False
                continue

            if stripped == "</event>":
                in_event = False
                nup, idprup, xwgtup, scalup, aqedup, aqcdup = header
                ev = LHEEvent(
                    weight=xwgtup,
                    scale=scalup,
                    aqed=aqedup,
                    aqcd=aqcdup,
                    particles=particles,
                )
                if with_rwgt and rwgt_buffer:
                    rwgt_text = "".join(rwgt_buffer)
                    for wm in re.finditer(
                        r"<wgt id='(\S+?)'>\s*([0-9.Ee+-]+)\s*</wgt>", rwgt_text
                    ):
                        ev.rwgt[wm.group(1)] = float(wm.group(2))
                yield ev
                continue

            if not in_event:
                continue

            if header is None:
                # first line inside <event>: NUP IDPRUP XWGTUP SCALUP AQEDUP AQCDUP
                parts = stripped.split()
                nup = int(parts[0])
                idprup = int(parts[1])
                xwgtup = float(parts[2])
                scalup = float(parts[3])
                aqedup = float(parts[4])
                aqcdup = float(parts[5])
                header = (nup, idprup, xwgtup, scalup, aqedup, aqcdup)
                continue

            if stripped.startswith("<rwgt>"):
                collecting_rwgt = True
                rwgt_buffer.append(line)
                continue
            if collecting_rwgt:
                rwgt_buffer.append(line)
                if stripped.startswith("</rwgt>"):
                    collecting_rwgt = False
                continue

            if stripped.startswith("<"):
                # some other tag (e.g. <mgrwt>, </event> handled above) - skip
                continue

            if stripped.startswith("#"):
                # aMC@NLO annotation line (e.g. "#aMCatNLO ..."), not a
                # particle record -- skip.
                continue

            # particle line
            parts = stripped.split()
            if len(parts) < 11:
                continue
            pdg = int(parts[0])
            status = int(parts[1])
            mother1 = int(parts[2])
            mother2 = int(parts[3])
            px, py, pz, e, m = map(float, parts[6:11])
            particles.append(
                LHEParticle(pdg, status, mother1, mother2, px, py, pz, e, m)
            )


def get_ttbar_final_state(ev: LHEEvent):
    """Return (top, antitop) LHEParticle objects (status==1, pdg==+-6).

    Raises ValueError if not exactly one of each is found (should never
    happen for pp -> ttbar at LO/NLO with stable-top LHE output, but we
    check rather than assume).
    """
    tops = [p for p in ev.particles if p.status == 1 and p.pdg == 6]
    atops = [p for p in ev.particles if p.status == 1 and p.pdg == -6]
    if len(tops) != 1 or len(atops) != 1:
        raise ValueError(
            f"Expected exactly one final-state t and one t~, got "
            f"{len(tops)} t and {len(atops)} t~"
        )
    return tops[0], atops[0]
