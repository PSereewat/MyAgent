"""
Shared low-level LHE (Les Houches Event) parsing utilities for the
LO vs NLO ttbar comparison analysis.

Designed to be dependency-free (no lxml/uproot needed) and to work
directly off gzip or plain-text LHE files with a streaming, line-based
approach (keeps memory bounded even for large NLO files).
"""
import gzip
import io
import math


def open_lhe(path):
    """Return a text-mode file object for a plain or gzip LHE file."""
    if path.endswith(".gz"):
        return gzip.open(path, "rt", errors="replace")
    return open(path, "r", errors="replace")


def iter_event_blocks(path):
    """Yield the raw text of each <event>...</event> block (inclusive)."""
    f = open_lhe(path)
    try:
        buf = []
        in_event = False
        for line in f:
            if "<event>" in line:
                in_event = True
                buf = [line]
                continue
            if in_event:
                buf.append(line)
                if "</event>" in line:
                    yield "".join(buf)
                    in_event = False
                    buf = []
    finally:
        f.close()


def parse_event_header(block):
    """Return (nup, idprup, xwgtup, scalup, aqedup, aqcdup) from the first
    non-tag line of an <event> block."""
    lines = block.splitlines()
    for line in lines[1:]:
        s = line.strip()
        if not s or s.startswith("<") or s.startswith("#"):
            continue
        parts = s.split()
        nup = int(parts[0])
        idprup = int(parts[1])
        xwgtup = float(parts[2])
        scalup = float(parts[3])
        aqedup = float(parts[4])
        aqcdup = float(parts[5])
        return nup, idprup, xwgtup, scalup, aqedup, aqcdup, lines
    raise ValueError("no header line found in event block")


def parse_particles(block):
    """Return list of dicts for each particle line: pdgid, status, px,py,pz,E,mass."""
    nup, idprup, xwgtup, scalup, aqedup, aqcdup, lines = parse_event_header(block)
    particles = []
    count = 0
    started = False
    for line in lines:
        s = line.strip()
        if not s:
            continue
        if s.startswith("<") or s.startswith("#"):
            if started:
                break
            continue
        parts = s.split()
        if not started:
            # this is the header line itself
            started = True
            continue
        if count >= nup:
            break
        # standard LHE particle line: IDUP ISTUP MOTHUP1 MOTHUP2 ICOLUP1 ICOLUP2 PX PY PZ E M VTIMUP SPINUP
        pdgid = int(parts[0])
        status = int(parts[1])
        px = float(parts[6])
        py = float(parts[7])
        pz = float(parts[8])
        E = float(parts[9])
        mass = float(parts[10])
        particles.append(dict(pdgid=pdgid, status=status, px=px, py=py, pz=pz, E=E, mass=mass))
        count += 1
    return nup, idprup, xwgtup, scalup, aqedup, aqcdup, particles


def parse_rwgt_ids(block, wanted_ids):
    """Extract a dict {id_str: value} for the requested wgt ids from the
    <rwgt>...</rwgt> block of a single event. wanted_ids: iterable of str."""
    start = block.find("<rwgt>")
    end = block.find("</rwgt>")
    if start == -1 or end == -1:
        return {}
    seg = block[start:end]
    out = {}
    wanted = set(wanted_ids)
    # crude but fast manual scan for "id='NNN'> VALUE </wgt>" or "id=\"NNN\">..."
    idx = 0
    while True:
        i = seg.find("id=", idx)
        if i == -1:
            break
        j = i + 3
        quote = seg[j]
        k = seg.find(quote, j + 1)
        wid = seg[j + 1:k]
        m = seg.find(">", k)
        n = seg.find("<", m)
        val_str = seg[m + 1:n].strip()
        if wid in wanted:
            out[wid] = float(val_str)
        idx = n
    return out


def top_kinematics(particles):
    """Given particle list, find final-state top (pdg 6) and antitop (pdg -6),
    status==1 (stable, since madgraph run keeps them undecayed). Returns
    (t, tbar) dicts or None if not found."""
    t = None
    tbar = None
    for p in particles:
        if p["status"] != 1:
            continue
        if p["pdgid"] == 6 and t is None:
            t = p
        elif p["pdgid"] == -6 and tbar is None:
            tbar = p
    return t, tbar


def compute_observables(t, tbar):
    """Compute the Tier-2 observables from top and antitop 4-momenta."""
    px_sum = t["px"] + tbar["px"]
    py_sum = t["py"] + tbar["py"]
    pz_sum = t["pz"] + tbar["pz"]
    E_sum = t["E"] + tbar["E"]

    pt_ttbar = math.hypot(px_sum, py_sum)
    m2 = E_sum ** 2 - px_sum ** 2 - py_sum ** 2 - pz_sum ** 2
    m_ttbar = math.sqrt(max(m2, 0.0))

    pt_t = math.hypot(t["px"], t["py"])

    phi_t = math.atan2(t["py"], t["px"])
    phi_tbar = math.atan2(tbar["py"], tbar["px"])
    dphi = abs(phi_t - phi_tbar)
    if dphi > math.pi:
        dphi = 2 * math.pi - dphi

    # rapidity of the top quark
    E, pz = t["E"], t["pz"]
    y_t = 0.5 * math.log((E + pz) / (E - pz))

    return dict(pt_ttbar=pt_ttbar, dphi=dphi, pt_t=pt_t, m_ttbar=m_ttbar, y_t=y_t)
