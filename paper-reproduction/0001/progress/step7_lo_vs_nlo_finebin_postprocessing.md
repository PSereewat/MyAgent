# Step 7 — LO vs NLO fixed-order comparison, finer binning (NEW, additional deliverable)

## Status: COMPLETE

Scope: a NEW, additional LO-vs-NLO-fixed-order-only comparison (no
NLO+PS, no LO+PS) for the same 5 differential observables as the
original Tier 2 study, using finer bin edges than
`analysis/binning.py`'s defaults, with MC statistical error bars only.
None of the pre-existing plots/CSVs from the original 3-way
LO/NLO/NLO+PS study (`output/figures/{pt_ttbar,dphi_ttbar,pt_top_lead,
m_ttbar,y_t}.{png,pdf}`, `output/data/{same}.csv`) or the LO+PS-vs-NLO+PS
study (`output/figures/lops_vs_nlops/`, `output/data/lops_vs_nlops/`)
were touched, re-run, or overwritten — verified by file mtimes
(unchanged, `Jul 26 20:14`) after this task's scripts ran.

## Analysis scripts created

- `analysis/binning_finebin.py` (NEW) — finer `FINE_BIN_EDGES` dict for
  this comparison only; original `analysis/binning.py` untouched.
- `analysis/weighting.py` (MODIFIED, additive only) — added a new
  function `weighted_histogram_edge_safe`, which wraps the existing
  `weighted_histogram` with a fix for a floating-point bin-boundary bug
  (see "Bug found" below). The pre-existing `weighted_histogram`,
  `kish_neff`, and `negative_weight_fraction` functions were not changed
  in any way, so the original `analyze_lo.py`/`analyze_nlo.py`/
  `analyze_nlops.py`/`analyze_lops.py` scripts (which import only the
  unmodified functions) behave identically to before if re-run.
- `analysis/analyze_lo_finebin.py` (NEW) — LO fixed-order side, reusing
  `lhe_utils.py`/`kinematics.py` unmodified, writes
  `output/data/lo_vs_nlo_finebin/lo_finebin_results.json`.
- `analysis/analyze_nlo_finebin.py` (NEW) — NLO fixed-order side, same
  reuse pattern, writes
  `output/data/lo_vs_nlo_finebin/nlo_finebin_results.json`. No
  scale-variation reweighting was computed here (out of scope per the
  task; see "Normalization/error convention" below).
- `analysis/make_plots_lo_vs_nlo_finebin.py` (NEW) — 5 overlay plots +
  5 CSVs.

## Normalization mode and error convention (confirmed, not assumed)

**Absolute yield mode** (pb per bin, not shape-normalized), `w_i =
weight_i * L / N_gen` with `L = 1 pb^-1` — identical convention to the
original Tier 2 study.

**MC statistical uncertainty only, no scale-variation band** — this was
confirmed explicitly (not assumed) by directly inspecting the original
`analysis/make_plots.py`: that script only ever reads and plots
`h["error_pb"]` (`sqrt(sum(w_i**2))` per bin) for each observable; it
never loads or overlays the separate 7-point `(muR,muF)` scale-variation
numbers that `analysis/analyze_nlo.py` computes purely for the Tier-1
rate table (`output/data/nlo_results.json`'s `scale_variation_7pt`
block). So "MC statistical uncertainty only" was already the existing
convention for the differential (Tier 2) plots, confirmed rather than
assumed, and no scale-variation computation was performed for this new
comparison either.

## Bin widths/counts chosen, and why (per observable)

Bin counts were chosen by re-histogramming the actual 10000-event LO and
NLO fixed-order samples at several candidate bin counts and checking how
many bins fall below ~5 raw (unweighted) events per bin — a rough
threshold for "dominated by Poisson noise rather than real shape" given
only 10000 events per sample (see `analysis/binning_finebin.py`
docstring for the full numeric diagnostics).

| Observable | Original (binning.py) | New (binning_finebin.py) | Chose full double? |
|---|---|---|---|
| `pt_ttbar` | 20 bins, 25 GeV | **25 bins, 20 GeV** | No — moderate. At 40 bins/12.5 GeV, 11/40 (28%) NLO bins had <5 raw events; at 25 bins, only 5/25 (20%), all above ~350 GeV (a genuine low-statistics tail regardless of binning). |
| `dphi_ttbar` | 20 bins, 0.157 rad | **40 bins, 0.0785 rad** | Yes — full double. Even at 40 bins every NLO bin has >=9 raw events (0 bins <5). |
| `pt_top_lead` | 24 bins, 25 GeV | **32 bins, 18.75 GeV** | No — moderate. At 48 bins/12.5 GeV, 7/48 (LO) and 6/48 (NLO) bins had <5 raw events (~13-15%); at 32 bins, only 3/32 (~9%) for either sample. |
| `m_ttbar` | 40 bins, 26.5 GeV | **60 bins, 17.67 GeV** | No — moderate. At 80 bins/13.25 GeV, 9/80 (LO) and 8/80 (NLO) bins had <5 raw events (~11%), concentrated above ~1000 GeV; at 60 bins, only 4/60 (LO) and 3/60 (NLO) (~5-7%). |
| `y_t` | 24 bins, 0.25 | **48 bins, 0.125** | Yes — full double. Distribution is broad/smooth; minimum raw count per bin is still >=22 events even at 48 bins (0 bins <5). |

All ranges are unchanged (only bin count changes), so this is a strict
refinement of the same window, not a different one.

## Bug found (pre-existing, in the ORIGINAL Tier 2 output — flagged explicitly, not silently reproduced)

While verifying that the finer `dphi_ttbar` binning correctly captures
the LO delta-function spike at `Delta_phi = pi`, I found that the
**original** `analysis/weighting.py:weighted_histogram` (used by the
existing `analyze_lo.py`/`analyze_nlo.py`, still in place, unmodified)
silently drops events whose value is exactly bit-for-bit equal to the
last bin edge, because `np.digitize`'s convention (`edges[i-1] <= x <
edges[i]`) treats `x == edges[-1]` as overflow.

`delta_phi_folded` caps its output at exactly `math.pi` by construction,
and virtually every event's folded delta-phi evaluates to the exact
double-precision value of `math.pi` (confirmed directly by re-reading
both LHE files: **8710/10000 LO events and 5642/10000 NLO events** in
this fine-bin sample; the original 20/40-bin edges showed 8710/10000 LO
and 8020/10000 NLO similarly at bit-for-bit `pi`). As a result, **the
existing `output/data/dphi_ttbar.csv` and `output/figures/dphi_ttbar.png`
undercount the LO delta-function peak by a factor of ~7.75x** (the
original last-bin `n_raw` is only 1290/10000, not the true ~10000 —
verified directly from the existing JSON/CSV, not modified as part of
this task). This is a genuine pre-existing bug in the original Tier-2
deliverable, discovered independently while building this new
comparison. It is reported here rather than fixed in place (per
instructions not to touch the original outputs) and rather than silently
reproduced in the new fine-bin comparison.

**Fix applied for this new deliverable only**: `weighting.py` gained a
new, additive function `weighted_histogram_edge_safe`, which nudges any
value exactly equal to the last bin edge to just inside the last bin
before histogramming (values genuinely beyond the last edge, which
cannot occur for `delta_phi_folded` but could in principle for other
observables, are still correctly dropped as overflow — only the
exact-equality edge case is fixed). Verified explicitly: this fine-bin
LO histogram's last `dphi_ttbar` bin now has `n_raw = 10000` (all
events captured, asserted programmatically in
`analyze_lo_finebin.py`), vs. the original buggy 1290/10000.

**Recommendation**: whoever owns the original Tier 2 deliverable should
consider re-running `analyze_lo.py`/`analyze_nlo.py` with the
`weighted_histogram_edge_safe` fix (or an equivalent one) to correct
`output/data/dphi_ttbar.csv` and `output/figures/dphi_ttbar.png` — not
done here since the task explicitly said not to touch those files.

## Independent NLO/negative-weight verification (per skill hard rule)

Re-verified directly from the actual `events.lhe.gz` XWGTUP values for
this task (not assumed from the prior study's finding, even though it's
the same file):
- **LO**: 0/10000 negative-weight events, weight constant at 520.365 pb.
- **NLO fixed-order**: **f_minus = 19.88% (1988/10000)** — matches the
  prior study's independent finding and `output/data/nlo_results.json`
  exactly (same file, same result, as expected). `Neff` (general Kish
  formula) = **3628.9** out of 10000 raw events. Self-summed
  `sigma = 692.7498 +/- 11.4998 pb` (sample statistical error,
  `sqrt(sum(w_i**2))`), consistent with the generation-level quoted
  `700.0 +/- 4.2 pb` within the sample's finite MC statistics (same
  ~1% discrepancy already documented in the original study, from
  treating the 10000-event unweighted sample's own variance vs. the
  much-higher-effective-statistics phase-space integration grid).
- No negative-weight events were dropped from any histogram —
  `weighted_histogram`/`weighted_histogram_edge_safe` sum every event's
  scaled weight, positive or negative, into its bin.

## Per-bin statistical errors and Neff

Reported per-bin in every CSV (`LO_error_pb`, `LO_neff`, `LO_n_raw`,
`NLO_error_pb`, `NLO_neff`, `NLO_n_raw`) — computed as
`error = sqrt(sum(w_i**2))` and `Neff = (sum(w_i))**2 / sum(w_i**2)`
(general Kish formula), never the reduced closed form. `f_minus` per bin
is also stored in the raw JSON (`nlo_finebin_results.json`,
`f_minus_per_bin` field) though not duplicated in the CSV (matching the
original Tier 2 CSV's column set, which likewise carries `neff`/`n_raw`
but not per-bin `f_minus`).

## Physics sanity check

- **LO `pt_ttbar`**: `max(pT_ttbar) = 0.000e+00 GeV` exactly over all
  10000 events — all mass in the first bin ([0, 20) GeV). Confirmed in
  the plot: LO is a clean single-bin spike at zero, unaffected by the
  bin-width change (any bin starting exactly at 0 captures this
  correctly; the finer 20 GeV first bin does not split the spike).
- **LO `dphi_ttbar`**: `min(dphi_ttbar) = 3.1415926536 rad` (`= pi` to
  double precision) over all 10000 events, confirmed via the edge-safe
  histogram that **all 10000** events land in the last (peak) bin
  (`n_raw = 10000`, asserted programmatically) — the delta-function
  behavior holds cleanly with the finer 40-bin edges, and moreover this
  is now the FIRST correct rendering of this behavior in this study
  (see "Bug found" above; the original 20-bin plot undercounted this
  peak by ~7.75x).
- **NLO fixed-order**: both `pt_ttbar` and `dphi_ttbar` show the
  expected nonzero real-emission tail away from the LO delta functions,
  clearly visible in both figures even at the finer binning. The
  `pt_ttbar` tail above ~350 GeV and the `m_ttbar` tail above ~1000 GeV
  do show visibly noisier, fluctuation-dominated bins (single-digit raw
  counts, large relative error bars) — this is flagged explicitly as a
  genuine low-statistics tail given only 10000 events, not hidden or
  smoothed over; it was the deciding factor in choosing moderate (not
  fully doubled) bin counts for `pt_ttbar`, `pt_top_lead`, and `m_ttbar`.
- `pt_top_lead`, `m_ttbar`, `y_t`: NLO systematically above LO across
  most of the range (K-factor-like enhancement, consistent with
  sigma_NLO/sigma_LO ~1.33-1.35), `y_t` symmetric about 0 as expected.
  No anomalies beyond the expected tail-region statistical noise noted
  above.

## Fit convergence / boundary flags

No likelihood fit was performed for this task (pure kinematic-comparison
plots + CSVs, per the task spec) — not applicable.

## Zero-yield bins

None encountered for any of the 5 observables within the plotted ranges
for either LO or NLO (`n_raw` > 0 in every bin) — the sparsest bins
(far `pt_ttbar`/`m_ttbar` tails) have small but nonzero raw counts, as
shown in the CSVs and flagged above.

## Output files

Plots (PDF + PNG), in a dedicated subdirectory so the original Tier 2
plots and the `lops_vs_nlops/` plots are untouched:
- `output/figures/lo_vs_nlo_finebin/pt_ttbar_lo_vs_nlo_finebin.{pdf,png}`
- `output/figures/lo_vs_nlo_finebin/dphi_ttbar_lo_vs_nlo_finebin.{pdf,png}`
- `output/figures/lo_vs_nlo_finebin/pt_top_lead_lo_vs_nlo_finebin.{pdf,png}`
- `output/figures/lo_vs_nlo_finebin/m_ttbar_lo_vs_nlo_finebin.{pdf,png}`
- `output/figures/lo_vs_nlo_finebin/y_t_lo_vs_nlo_finebin.{pdf,png}`

CSVs (bin edges/centers, LO yield+error+neff+n_raw, NLO
yield+error+neff+n_raw per bin):
- `output/data/lo_vs_nlo_finebin/pt_ttbar_lo_vs_nlo_finebin.csv`
- `output/data/lo_vs_nlo_finebin/dphi_ttbar_lo_vs_nlo_finebin.csv`
- `output/data/lo_vs_nlo_finebin/pt_top_lead_lo_vs_nlo_finebin.csv`
- `output/data/lo_vs_nlo_finebin/m_ttbar_lo_vs_nlo_finebin.csv`
- `output/data/lo_vs_nlo_finebin/y_t_lo_vs_nlo_finebin.csv`

Raw per-run JSON (Tier-1 rate + full histogram data):
- `output/data/lo_vs_nlo_finebin/lo_finebin_results.json`
- `output/data/lo_vs_nlo_finebin/nlo_finebin_results.json`
