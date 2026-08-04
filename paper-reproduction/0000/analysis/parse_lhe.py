"""
Shared LHE parsing utilities for the ttbar 13 TeV LO-vs-NLO comparison.

Independently verified (not trusted blindly) against the actual
<initrwgt> headers of both files:

LO file (events/lo/pp_ttbar_13TeV_lo/Events/run_01/unweighted_events.lhe.gz):
  145 <wgt> entries per event, ids 1-145, in fixed sequential order matching
  the <initrwgt> header. The DYN_SCALE="3" (HT/2, the actual central scale
  used for this run) subset is ids 4,9,14,19,23,28,33,38,43, i.e.
    id  4 -> (muR,muF) = (0.5,0.5)
    id  9 -> (0.5,1.0)
    id 14 -> (0.5,2.0)   [envelope corner -- EXCLUDED]
    id 19 -> (1.0,0.5)
    id 23 -> (1.0,1.0)   [[central]] -- verified equal to XWGTUP for the
                          first event (519.85200 == 519.852)
    id 28 -> (1.0,2.0)
    id 33 -> (2.0,0.5)   [envelope corner -- EXCLUDED]
    id 38 -> (2.0,1.0)
    id 43 -> (2.0,2.0)

NLO file (events/nlo/pp_ttbar_13TeV_nlo/Events/run_01/events.lhe.gz):
  27 <wgt> entries per event, ids 1001-1027, organized as THREE redundant
  9-point (muR,muF) groups (ids 1001-1009, 1010-1018, 1019-1027), all
  tagged dyn=3 (HT/2). We use the first group, ids 1001-1009:
    id 1001 -> (1.0,1.0)  [[central]] -- verified equal to XWGTUP for the
                           first event (0.11499E+04 == 1149.9064, agrees to
                           the printed precision)
    id 1002 -> (2.0,1.0)
    id 1003 -> (0.5,1.0)
    id 1004 -> (1.0,2.0)
    id 1005 -> (2.0,2.0)
    id 1006 -> (0.5,2.0)   [envelope corner -- EXCLUDED]
    id 1007 -> (1.0,0.5)
    id 1008 -> (2.0,0.5)   [envelope corner -- EXCLUDED]
    id 1009 -> (0.5,0.5)

Both mappings were confirmed directly from the raw <initrwgt> weightgroup
text in each file (not assumed from the upstream progress reports).

The 7-point envelope used everywhere in this analysis is the same 7
(muR,muF) combinations for both samples:
  (1,1) [central], (0.5,0.5), (0.5,1), (1,0.5), (1,2), (2,1), (2,2)
excluding the two opposite-extreme corners (0.5,2) and (2,0.5).

Because both files write <wgt> entries in a fixed, sequential order that
exactly matches the <initrwgt> header (verified by inspection), we track
position-in-rwgt-block (1st wgt line, 2nd wgt line, ...) rather than
re-parsing the id string from every single line -- this is a large speed
win given up to 145 wgt lines/event x 100,000 events.
"""

from __future__ import annotations

import gzip
from typing import Dict, Iterator, Tuple, List

# label -> (LO position, NLO position) within the sequential rwgt block.
# LO positions == LO ids (1-indexed, sequential). NLO positions == (id - 1000).
ENVELOPE_LABELS = {
    "central_1_1": (23, 1),
    "mur0.5_muf0.5": (4, 9),
    "mur0.5_muf1": (9, 3),
    "mur1_muf0.5": (19, 7),
    "mur1_muf2": (28, 4),
    "mur2_muf1": (38, 2),
    "mur2_muf2": (43, 5),
}

LO_POSITIONS = {pos: label for label, (pos, _) in ENVELOPE_LABELS.items()}
NLO_POSITIONS = {pos: label for label, (_, pos) in ENVELOPE_LABELS.items()}


def iter_lhe_events(
    path: str, wanted_positions: Dict[int, str]
) -> Iterator[Tuple[float, Dict[str, float], List[Tuple[int, int, float, float, float, float, float]]]]:
    """Stream-parse an LHE(.gz) file event by event.

    Yields (xwgtup, wgts, particles) where:
      xwgtup: nominal signed event weight (3rd field of the event header line)
      wgts: dict {label: value} for the requested envelope positions found
            in this event's <rwgt> block
      particles: list of (pdg, status, px, py, pz, E, mass) tuples, one per
                 NUP particle line, in file order
    """
    opener = gzip.open if path.endswith(".gz") else open
    with opener(path, "rt") as f:
        state = "seek"
        nup = 0
        nread = 0
        xwgtup = 0.0
        particles: List[Tuple[int, int, float, float, float, float, float]] = []
        wgts: Dict[str, float] = {}
        wgt_counter = 0

        for raw_line in f:
            # NLO file indents its XML tags (e.g. "  <event>"), LO file
            # does not -- strip leading whitespace before tag checks so
            # both formats are handled identically.
            line = raw_line.lstrip()

            if state == "seek":
                if line.startswith("<event"):
                    state = "header"
                continue

            if state == "header":
                parts = line.split()
                nup = int(parts[0])
                xwgtup = float(parts[2])
                particles = []
                nread = 0
                state = "particles"
                continue

            if state == "particles":
                parts = line.split()
                pdg = int(parts[0])
                status = int(parts[1])
                px = float(parts[6])
                py = float(parts[7])
                pz = float(parts[8])
                E = float(parts[9])
                mass = float(parts[10])
                particles.append((pdg, status, px, py, pz, E, mass))
                nread += 1
                if nread == nup:
                    state = "postparticles"
                continue

            if state == "postparticles":
                if line.startswith("<rwgt>"):
                    state = "rwgt"
                    wgt_counter = 0
                    wgts = {}
                elif line.startswith("</event>"):
                    state = "seek"
                    yield xwgtup, {}, particles
                continue

            if state == "rwgt":
                if line.startswith("<wgt"):
                    wgt_counter += 1
                    if wgt_counter in wanted_positions:
                        val_str = line.split(">", 1)[1].split("<", 1)[0].strip()
                        wgts[wanted_positions[wgt_counter]] = float(val_str)
                    continue
                if line.startswith("</rwgt>"):
                    state = "postrwgt"
                continue

            if state == "postrwgt":
                if line.startswith("</event>"):
                    state = "seek"
                    yield xwgtup, wgts, particles
                continue
