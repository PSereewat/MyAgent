# Step 3: Numerical Analysis and Plotting — LO vs NLO ttbar @ 13 TeV

## Status: SUCCESS

All Tier-1, Tier-2 and Tier-3 deliverables from `ttbar_lo_vs_nlo_prompt.md` were
produced from the actual event samples (no illustrative/placeholder numbers).
All acceptance criteria in Section 5 of the spec are satisfied.

---

## 1. Scripts

- `analysis/lhe_utils.py` — shared, dependency-free LHE parsing utilities
  (streaming event-block iterator, particle-record parser, `<rwgt>` id
  extractor, top/antitop kinematics -> Tier-2 observables).
- `analysis/analyze_lo.py` — parses
  `events/pp_ttbar_lo_13tev/Events/run_01/unweighted_events.lhe.gz`,
  computes the 5 Tier-2 observables and the LO 7-point scale weights per
  event, saves `analysis/parsed/lo_events.npz`.
- `analysis/analyze_nlo.py` — parses
  `events/pp_ttbar_nlo_13tev/Events/run_01/events.lhe.gz`, same outputs,
  saves `analysis/parsed/nlo_events.npz`. Includes the negative-weight /
  Neff computation and an in-script cross-check that the `tag=0`
  scale-variation group reproduces each event's own `XWGTUP` exactly.
- `analysis/tier1_summary.py` — loads both `.npz` files, computes sigma,
  K-factor, the 7-point scale envelopes, negative-weight fraction / Neff,
  and physics sanity checks. Writes `analysis/tier1_summary.txt`.
- `scripts/make_plots.py` — builds all 10 requested figures (5 observables
  x {absolute, shape-normalized}), each PDF+PNG, to `output/figures/`.

Run order: `python3 analysis/analyze_lo.py && python3 analysis/analyze_nlo.py
&& python3 analysis/tier1_summary.py && python3 scripts/make_plots.py`
(all commands run from the repo working directory).

---

## 2. Weight-ID mapping used (verified directly from each file's own header)

### LO (`unweighted_events.lhe.gz`)

Header has 145 `<weight id>` entries: 44 in `"Central scale variation"` (9
(muR,muF) points x 4 dynamical-scale choices) + 101 PDF-replica entries
(unused here). Restricting to `DYN_SCALE="3"` (the run's actual
`dynamical_scale_choice=3`, i.e. HT/2) gives 9 ids, verified directly by
reading the `<initrwgt>` block (contrary to a documentation caveat in the
step-2 progress file, **id 23 IS present** as a distinct, non-degenerate
weight for (MUR=1.0, MUF=1.0, DYN_SCALE=3), and its per-event value was
checked to equal the event's own `XWGTUP` exactly on event 1):

| id | (muR, muF) |
|---|---|
| 4  | (0.5, 0.5) |
| 9  | (0.5, 1.0) |
| 14 | (0.5, 2.0) — excluded from 7-point (corner) |
| 19 | (1.0, 0.5) |
| 23 | (1.0, 1.0) — central, == XWGTUP |
| 28 | (1.0, 2.0) |
| 33 | (2.0, 0.5) — excluded from 7-point (corner) |
| 38 | (2.0, 1.0) |
| 43 | (2.0, 2.0) |

7-point set used: `{4, 9, 19, 23, 28, 38, 43}`.

### NLO (`events.lhe.gz`)

Header (`<initrwgt>`) contains **3 weightgroups**, `'scale_variation 0 3'`
(ids 1001-1009), `'scale_variation 4 3'` (ids 1010-1018), `'scale_variation
6 3'` (ids 1019-1027) — all at `dyn=3`, each a 9-point (muR,muF) grid, but
tagged with different internal aMC@NLO "order" tags (0, 4, 6). **These are
NOT independent pieces to be summed**: a direct check on 200 sampled
events confirmed that `id=1001` (tag=0, muR=1,muF=1) reproduces each
event's own signed `XWGTUP` to the ~5-significant-figure precision of the
LHE `<wgt>` field (200/200 events matched). This means the `tag=0` group
already carries the complete per-event scale-variation weight (Born,
virtual and real/counter-event contributions correctly summed
internally); `tag=4` and `tag=6` are internal per-order decomposition
pieces not needed for this analysis. All NLO Tier-1/Tier-2 scale-envelope
work therefore uses **only the tag=0 group**:

| id | (muR, muF) |
|---|---|
| 1001 | (1.0, 1.0) — central, == XWGTUP |
| 1002 | (2.0, 1.0) |
| 1003 | (0.5, 1.0) |
| 1004 | (1.0, 2.0) |
| 1005 | (2.0, 2.0) |
| 1006 | (0.5, 2.0) — excluded from 7-point (corner) |
| 1007 | (1.0, 0.5) |
| 1008 | (2.0, 0.5) — excluded from 7-point (corner) |
| 1009 | (0.5, 0.5) |

7-point set used: `{1001, 1002, 1003, 1004, 1005, 1007, 1009}`.

**Weight normalization convention** (important, documented explicitly
because it deviates from a literal reading of the spec's bin formula):
both the LO and NLO LHE files are *quasi-unweighted*, i.e. `XWGTUP` is
constant in magnitude for every event (LO: exactly 520.365 pb for all
10000 events; NLO: exactly ±1149.983 pb for all 10000 events, sign only
varying). This is the standard LHEF convention where `sigma = <XWGTUP>`
(average over events), not `sum(XWGTUP)`. To get physically-normalized
`dsigma/dX` in pb/GeV (etc.), every per-event weight used in histogramming
was first divided by `N_events` (`w_i = XWGTUP_i / N`) before applying the
spec's `dsigma/dX|bin = sum(w_i in bin)/binwidth` and
`delta = sqrt(sum(w_i^2 in bin))/binwidth` formulas. Applying the literal
formula without this rescaling would overstate cross sections by a factor
of `N_events` (10000x). Same rescaling applied to each of the 7 scale
variants before building bin-by-bin envelopes.

---

## 3. Tier-1 Summary Table

|                                    | LO                   | NLO                    |
|---|---|---|
| sigma [pb] (run summary)          | 520.4000 ± 0.7669    | 700.0000 ± 4.2000      |
| sigma [pb] (banner, high-prec)    | 520.3650             | —                      |
| sigma [pb] (event-avg cross-check)| 520.3650 ± 0.0000    | 693.8997 ± 9.1704      |
| 7-pt scale envelope [%]           | +30.26 / −21.73      | +10.50 / −11.01        |
| 7-pt central sigma [pb]           | 520.3650             | 693.9055               |
| K-factor (run-summary sigmas)     | —                    | **1.3451**             |
| K-factor (event-avg sigmas)       | —                    | 1.3335                 |
| Negative-weight fraction          | 0.000%               | **19.830%**            |
| N_eff = N(1-2 f_-)^2 (NLO only)   | —                    | 3640.9 (of N=10000)    |
| `<wgt>` entries per event         | 145                  | 27                     |

**NLO scale band narrower than LO scale band on BOTH sides: TRUE**
(+10.50/−11.01% vs +30.26/−21.73%; NLO band is roughly a factor ~2-3
narrower on each side). No bug flag needed.

Full breakdown of the 7 individual (muR,muF) cross sections at each order
is in `analysis/tier1_summary.txt`.

K-factor is 1.3451 (using the official run-summary central values) —
inside the spec's expected 1.3-1.6 sanity range.

---

## 4. Tier-2 Differential Distributions

All 5 observables produced in both absolute (`dsigma/dX`, pb-normalized)
and shape (area-normalized to 1) versions, LO (green, RGB 0,120,0) vs NLO
(blue, RGB 0,0,200) overlay with per-bin statistical error bars, NLO
7-point scale-uncertainty band (shaded blue), ratio panel (NLO/LO
differential K-factor) for pT(t), m(ttbar), y(t); no ratio panel for
pT(ttbar) and Delta-phi since LO is a delta function there.

Binning used exactly as specified (40 bins each): pT(ttbar) in [0,400]
GeV (log-y), Delta-phi in [0,pi] (log-y), pT(t) in [0,800] GeV (log-y),
m(ttbar) in [300,1500] GeV (log-y), y(t) in [-3,3] (linear-y).

### Figure files (all under `output/figures/`, PDF+PNG each)

| Observable | Absolute | Shape |
|---|---|---|
| pT(ttbar) | `pt_ttbar_absolute.pdf/.png` | `pt_ttbar_shape.pdf/.png` |
| Delta-phi | `dphi_absolute.pdf/.png` | `dphi_shape.pdf/.png` |
| pT(t) | `pt_t_absolute.pdf/.png` | `pt_t_shape.pdf/.png` |
| m(ttbar) | `m_ttbar_absolute.pdf/.png` | `m_ttbar_shape.pdf/.png` |
| y(t) | `y_t_absolute.pdf/.png` | `y_t_shape.pdf/.png` |

### LO delta-function bin contents (stated explicitly per spec Step 3)

- pT(ttbar): entire LO cross section (520.365 pb) lands in bin 1 ([0,10)
  GeV), giving `dsigma/dpT = 52.04 pb/GeV` there and 0 elsewhere (exactly,
  to floating-point precision — max |pT(ttbar)| over all 10000 LO events
  is `0.000e+00` GeV).
- Delta-phi: entire LO cross section lands in the last bin ([pi-pi/40,
  pi]), giving `dsigma/dDeltaphi = 6625.49 pb/rad` there and 0 elsewhere
  (min Delta-phi over all LO events = 3.1415926536 rad = pi to double
  precision).

Both are annotated directly on the corresponding figures.

### Shape-normalization convention

For the shape plots, LO and NLO histograms are each independently
divided by their own integral over the displayed range (so both curves
integrate to 1); the NLO scale-envelope band variants are likewise each
normalized by their own integral (a genuine "shape-only" 7-point band,
decoupled from the overall rate/K-factor change).

---

## 5. Tier-3 Technical Checks

1. **Negative-weight fraction (NLO)**: 1983/10000 = **19.830%**
   (`f_minus = 0.19830`), nonzero as physically expected for a fixed-order
   ttbar NLO calculation (O(10-20%) typical) — confirms this is a genuine
   NLO (not LO-relabeled) sample. LO fraction is exactly 0%, as expected.
2. **Effective sample size**: `N_eff = N*(1-2*f_minus)^2 = 10000 *
   (1-0.3966)^2 = 3640.9`. Reported alongside `f_minus` per the negative-
   weight handling convention, though the per-bin statistical errors
   quoted in the histograms/report are computed directly as
   `sqrt(sum(w_i^2))` from the actual signed per-event weights (which
   already correctly accounts for cancellation at the event level; no
   `sqrt(N)`-style shortcut was used anywhere, so no additional Neff
   correction is layered on top of the per-bin errors — Neff is reported
   as the standard cross-check statistic requested by the agent
   instructions).
3. **`<wgt>` entries per event**: LO = 145 (44 scale + 101 PDF-replica),
   NLO = 27 (3 tag-groups x 9-point scale grid; PDF variation not
   requested/present in this NLO run). Both nonzero, confirming scale
   reweighting ran in both samples.
4. **Virtual (loop) contribution confirmed**: `Cards/proc_card_mg5.dat`
   shows `import model loop_sm`, `set OLP MadLoop`,
   `generate p p > t t~ [QCD]`. The run logs
   (`Events/run_01/alllogs_0.html`) contain repeated `MadLoop`,
   `MadLoopParams`, `OLP` references and numerous nonzero
   `Virtual = 0.xxxxE...` numeric entries (i.e. the one-loop virtual
   matrix element was evaluated point-by-point during integration, not
   skipped/zero). `run_settings` in the banner show `order = NLO`,
   `fixed_order = OFF`, `shower = OFF` — this is aMC@NLO's standard
   NLO-accuracy, quasi-unweighted parton-level (unshowered) event output
   (MC@NLO-method events ready for showering, shower step simply not
   run), consistent with "parton-level NLO events, top quarks stable" as
   specified. `res_0.txt` shows the full per-channel Born+virtual+real
   integration breakdown (ABS total 1128.15 pb vs signed total 694.4 pb),
   consistent with the ~700 pb central NLO cross section once virtual and
   real (with subtraction) pieces are summed.

---

## 6. Physics Sanity Checks (spec Section 5)

| Check | Result |
|---|---|
| LO exactly at pT(ttbar)=0 | PASS — max |pT(ttbar)| over 10000 LO events = 0.000e+00 GeV |
| LO exactly at Delta-phi=pi | PASS — min Delta-phi over 10000 LO events = 3.1415926536 rad (= pi to double precision) |
| NLO nonvanishing pT(ttbar) tail | PASS — 27.59% of NLO events have pT(ttbar) > 1 GeV, spectrum populated up to ~800 GeV |
| NLO nonvanishing Delta-phi tail below pi | PASS — 15.55% of NLO events have Delta-phi < 3.0 rad, full tail down to ~0 populated |
| K-factor in [1.3, 1.6] | PASS — K = 1.3451 (run-summary sigmas) |
| Nonzero negative-weight fraction at NLO | PASS — 19.830% |
| NLO scale band narrower than LO | PASS — +10.50/−11.01% (NLO) vs +30.26/−21.73% (LO) |

All acceptance criteria satisfied. No blocking issues encountered.

---

## 7. Assumptions / Notes

- Weight-rescaling by `1/N_events` applied throughout for physical
  dsigma/dX normalization (see Section 2); documented explicitly since it
  is not literally spelled out in the spec's bin formula but is required
  given this run's quasi-unweighted LHE convention.
- NLO scale-variation reweighting uses only the `tag=0` weightgroup (ids
  1001-1009); the `tag=4`/`tag=6` groups (ids 1010-1027) are internal
  aMC@NLO order-decomposition pieces, verified redundant with `tag=0` for
  the purpose of the total per-event weight (see Section 2), not used.
- Overflow/underflow outside the specified histogram ranges is small
  (<1% of events for pT(t), m(ttbar), y(t); 0.3-0.4% for NLO pT(ttbar)/
  m(ttbar)) and is simply excluded from the displayed/normalized
  histograms, as is standard.
- Some low-statistics tail bins (e.g. pT(t) ratio panel around 550 GeV)
  show large NLO/LO ratio fluctuations purely from low LO bin occupancy;
  this is expected MC noise in the tail, not a bug, and is visible/
  quantified via the error bars in the corresponding figures.

---

## 8. Negative-Weight Fraction and Neff (headline, for quick reference)

- **f_minus (NLO) = 19.830%** (1983/10000 events)
- **N_eff (NLO) = 3640.9** (of N=10000)
- LO negative-weight fraction = 0% (as expected at LO)
