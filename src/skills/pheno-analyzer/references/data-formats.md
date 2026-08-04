# Data format handling reference

## HEPData tables (experimental data)

HEPData YAML tables typically have this structure (per-bin independent
variable ranges, dependent variable values with error terms):

```yaml
independent_variables:
  - header: {name: 'M(T)', units: GEV}
    values:
      - {low: 250, high: 320}
      - {low: 320, high: 500}
      ...
dependent_variables:
  - header: {name: 'Observed events'}
    values:
      - {value: 15}
      - {value: 452}
      ...
```

Parse with `pyyaml`. Always check: number of bins in independent and
dependent variable blocks match; bin edges are monotonic; and units are
recorded (GeV vs TeV mismatches are a common, easy-to-miss source of
order-of-magnitude errors). See `templates/parse_hepdata.py`.

If the observed data, background, and uncertainty are given directly in
the prompt as a table (rather than a HEPData file), treat that table with
the same rigor — check row/column consistency before using it.

## Delphes ROOT output

Read with `uproot` + `awkward` (Scikit-HEP), not `ROOT`/PyROOT unless
already available and requested — `uproot` avoids a heavy ROOT
dependency and is what the broader ColliderAgent event-analyzer stack
already uses in its expert-mode fallback.

```python
import uproot
import awkward as ak

f = uproot.open("delphes_output.root")
tree = f["Delphes"]
electrons_pt = tree["Electron/Electron.PT"].array()
jets_pt = tree["Jet/Jet.PT"].array()
met = tree["MissingET/MissingET.MET"].array()
```

Branch names depend on the Delphes card used (ATLAS vs CMS cards differ
in object collection names in some configurations) — confirm branch
names against the actual file with `tree.keys()` rather than assuming a
fixed schema.

## LHCO format

Plain-text, one row per reconstructed object per event, with a fixed
column layout (event header line, then object rows with type code,
eta, phi, pt, jmass, ntrk, btag, hadem). Parse line-by-line or with a
small fixed-width/whitespace-split parser — there is no standard Python
library for this, so a hand-written parser is expected, but it should be
written once as a template and reused, not reinvented per task.

## MadAnalysis5 histogram/cutflow output

MadAnalysis5 normal-mode output includes a cutflow table (event count
surviving each cut, in order) and histogram files (typically ROOT or a
MadAnalysis-specific text/YODA-like format depending on configuration).
Read the cutflow table to get `N_gen` and the count after final
selection; this is what feeds the normalization step in
`normalization-conventions.md`. Do not recompute selection efficiency by
re-applying cuts to raw events if a validated cutflow table already
exists upstream — use the upstream number and note where it came from.

## General rule

Whichever format is being read, print/log a small sanity summary
immediately after parsing (row counts, bin counts, min/max values,
any NaN or negative-count entries) before using the data downstream. A
malformed parse that silently produces plausible-looking numbers is
worse than one that crashes loudly.
