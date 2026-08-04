"""
Minimal pure-python HepMC2 (IO_GenEvent) parser for the Run 3 (NLO+PS,
MC@NLO + Pythia8) sample.

No external HepMC/LHE python bindings (pyhepmc, pylhe) were available in
this environment (no network-installable wheel found for either package
at analysis time), so this is a small hand-written parser of the plain
-text HepMC2 format, following the documented HepMC2 "E"/"V"/"P" record
layout. Written once here and reused by analyze_nlops.py.

Top-quark momentum extraction
------------------------------
Pythia8 decays the top quarks in this sample (confirmed by inspection:
no stable, status==1, |pdg|==6 particles exist in the file; instead each
top undergoes many same-flavour "recoil update" copies through the
shower, each with end_vtx pointing to a vertex whose only outgoing
particle is again |pdg|==6, until the final copy's decay vertex produces
genuine decay products, e.g. outs_pdg == [24, 5] for a top -> W+ b decay).
We take the *last* same-flavour copy (the one whose decay vertex output
is NOT a pure {+6} or {-6} recoil copy) as "the physical top/antitop
4-momentum" for building pT^t, m_ttbar, y_t, pT^ttbar, and Delta_phi_ttbar
-- this is the closest analogue to the stable, undecayed top recorded at
LO/NLO parton level.

Which listed weight is "nominal" -- NOT always the first one
--------------------------------------------------------------
The HepMC "E" line lists n_wgt weights, and which index is "the" nominal
event weight is determined by the per-file "N" (weight-name) line, NOT
by a fixed position -- this differs between samples in this study:

- Run 3 (NLO+PS): N line names are "0","1",...,"Weight" style groupings
  where the FIRST entry (index 0) was verified byte-for-byte identical to
  the last-named "Weight" entry, so `weight_index="first"` (the default,
  preserved for backward compatibility with analyze_nlops.py) is correct
  there.
- Run 4 (LO+PS): the N line instead reads
  N 146 "1" "10" "100" ... "145" "Weight" -- i.e. 145 systematic-
  reweighting variations (named "1".."145", a side effect of `use_syst
  True` having been left on for that run, see run4_LOPS progress notes)
  come FIRST, and the genuine nominal weight is LAST, named "Weight".
  Verified directly: for Run 4, the first-listed weight varies
  event-by-event (e.g. 662.48, 674.10, 572.29, ... pb -- one of the 145
  scale/PDF variations, out of scope for this task per the user's
  explicit "ignore reweight info" instruction) while the LAST-listed
  weight is exactly constant at 520.365 pb for all 10000 events (matching
  the LHE XWGTUP exactly, and the quoted sigma_LO = 520.4 pb), confirming
  it is the correct nominal weight for that sample.

Because of this, `iter_hepmc_events` takes an explicit `weight_index`
argument ("first" or "last") rather than hard-coding one convention --
callers must state which one applies to the file being read, verified
against that file's own "N" line, not assumed from another run.
"""

from __future__ import annotations

import gzip
from dataclasses import dataclass


@dataclass
class HepMCEvent:
    weight: float  # nominal signed MC@NLO event weight (named "0"/"Weight")
    n_weights: int
    top: tuple  # (px, py, pz, e, m)
    antitop: tuple


def _open(path: str):
    if path.endswith(".gz"):
        return gzip.open(path, "rt")
    return open(path, "r")


def _extract_top_before_decay(particles: dict, vertex_out: dict):
    """particles: barcode -> dict(pdg, p=(px,py,pz,e,m), status, end_vtx)
    vertex_out: vertex_barcode -> list of outgoing particle barcodes.

    Returns (top_p, antitop_p) as (px,py,pz,e,m) tuples, or raises
    ValueError if not found (so a malformed/unexpected event structure is
    surfaced rather than silently skipped).
    """
    top_final = None
    atop_final = None

    for bc, p in particles.items():
        if p["pdg"] not in (6, -6):
            continue
        end_vtx = p["end_vtx"]
        if end_vtx == 0:
            # a truly stable top (unexpected, but handle: this IS the
            # final momentum since it never decays)
            outs_pdg = None
        else:
            outs = vertex_out.get(end_vtx, [])
            outs_pdg = [particles[o]["pdg"] for o in outs]

        is_pure_recoil_copy = outs_pdg == [p["pdg"]]

        if outs_pdg is None or not is_pure_recoil_copy:
            # this is the last copy before real decay (or a stable top)
            if p["pdg"] == 6:
                top_final = p["p"]
            else:
                atop_final = p["p"]

    if top_final is None or atop_final is None:
        raise ValueError("Could not identify final top/antitop momenta in event")

    return top_final, atop_final


def iter_hepmc_events(path: str, weight_index: str = "first"):
    """Yield HepMCEvent objects, one per event ('E ' record) in the file.

    weight_index: "first" (index 0 of the E line's weight list) or "last"
        (the final entry) -- which one is the genuine nominal weight is
        file-specific (see module docstring); the caller must state which
        applies after checking that file's own "N" weight-name line, not
        assume one convention across samples. Default "first" preserves
        the original behavior used by analyze_nlops.py (Run 3), where it
        was verified correct for that file.
    """
    if weight_index not in ("first", "last"):
        raise ValueError('weight_index must be "first" or "last"')

    with _open(path) as f:
        particles = None
        vertex_out = None
        cur_vertex = None
        weight = None
        n_weights = None

        def flush():
            if particles is None:
                return None
            top_p, atop_p = _extract_top_before_decay(particles, vertex_out)
            return HepMCEvent(
                weight=weight, n_weights=n_weights, top=top_p, antitop=atop_p
            )

        for line in f:
            if line.startswith("E "):
                prev = flush()
                if prev is not None:
                    yield prev
                particles = {}
                vertex_out = {}
                cur_vertex = None

                toks = line.split()
                n_rand = int(toks[11])
                idx = 12 + n_rand
                n_wgt = int(toks[idx])
                if weight_index == "first":
                    weight = float(toks[idx + 1])
                else:  # "last"
                    weight = float(toks[idx + n_wgt])
                n_weights = n_wgt
                continue

            if line.startswith("V "):
                toks = line.split()
                cur_vertex = int(toks[1])
                vertex_out[cur_vertex] = []
                continue

            if line.startswith("P "):
                toks = line.split()
                barcode = int(toks[1])
                pdg = int(toks[2])
                px, py, pz, e, m = map(float, toks[3:8])
                status = int(toks[8])
                end_vtx = int(toks[11])
                particles[barcode] = dict(
                    pdg=pdg, p=(px, py, pz, e, m), status=status, end_vtx=end_vtx
                )
                vertex_out[cur_vertex].append(barcode)
                continue

        prev = flush()
        if prev is not None:
            yield prev
