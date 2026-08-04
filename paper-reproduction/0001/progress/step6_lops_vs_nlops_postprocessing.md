# Step 6 — LO+PS vs NLO+PS Comparison (NEW, separate from the original LO/NLO/NLO+PS study)

## Status: COMPLETE

Scope: this is a new, standalone comparison added after the original 3-way
LO/NLO/NLO+PS study (`../LO_NLO_NLOPS.md`, Tier 1/2/3 already complete
under `output/` and `analysis/` — none of that work was touched or
redone). Purpose: isolate the pure parton-shower/resummation effect
(LO+PS vs NLO+PS) from the NLO rate correction, using statistical (MC)
error bars only — **no scale/theory uncertainty band**, per the user's
explicit, already-agreed scope decision (see task instructions). No
scale-variation reweight data was computed or read from either sample,
even though Run 4's HepMC file happens to contain unused systematic
reweight info (see below) — confirmed out of scope and ignored.

## Analysis scripts created/modified

- `analysis/analyze_lops.py` (NEW) — Run 4 (LO+PS) Tier 1 rate + Tier 2
  histograms, read directly from the showered/hadronized HEPMC file
  `run4_LOPS/pp_ttbar_lops_run/Events/run_01/tag_1_pythia8_events.hepmc.gz`.
- `analysis/hepmc_utils.py` (MODIFIED, backward-compatible) — added an
  explicit `weight_index` parameter ("first" or "last") to
  `iter_hepmc_events`. Default remains `"first"`, preserving the exact
  behavior `analyze_nlops.py` (Run 3) already relies on. `analyze_lops.py`
  passes `weight_index="last"` explicitly (see "Weight convention"
  finding below). No other existing script's behavior changed.
- `analysis/make_plots_lops_vs_nlops.py` (NEW) — produces the 5 overlay
  plots and 5 CSVs for this comparison, reusing `analysis/binning.py`'s
  `BIN_EDGES` (same bin edges as the original Tier 2 plots) and asserting
  bin-edge equality between the LO+PS and NLO+PS histograms before
  plotting, so this is a guaranteed apples-to-apples overlay.
- Reused as-is (no changes): `analysis/kinematics.py`, `analysis/weighting.py`,
  `analysis/binning.py`, and the existing `output/data/nlops_results.json`
  (Run 3, NLO+PS — not regenerated, per task instruction).

## Important finding: Run 4's HepMC weight convention differs from Run 3's

Independently verified (not assumed) by reading each file's own `N`
(weight-name) line and the actual weight values:

- **Run 3 (NLO+PS)**: first-listed weight (index 0) is byte-identical to
  the last-named `"Weight"` entry — already established and unchanged
  from the original study.
- **Run 4 (LO+PS)**: the `N` line reads
  `N 146 "1" "10" "100" ... "145" "Weight"` — i.e. 145 systematic
  scale/PDF reweighting variations (a side effect of `use_syst=True`
  being left on during generation, see `run4_LOPS/progress/step5_madgraph_lops.md`)
  are listed **first**, and the genuine nominal weight is **last**,
  named `"Weight"`. Confirmed directly: the first-listed weight varies
  event-by-event (e.g. 662.48, 674.10, 572.29 pb for the first three
  events — one of the out-of-scope systematic variations), while the
  **last**-listed weight is exactly constant at 520.365 pb across all
  10000 events (matches the LHE `XWGTUP` field exactly, matches the
  quoted sigma_LO+PS = 520.4 pb, and shows zero negative weights).

  Had `analyze_lops.py` reused Run 3's "read the first weight" convention
  unmodified, it would have silently used one of the (out-of-scope)
  systematic-variation weights as the nominal cross section, corrupting
  every downstream number. This was caught by the "independently verify
  weight status from the actual file" rule and is why `hepmc_utils.py`
  was extended with an explicit `weight_index` parameter rather than
  reusing the hard-coded assumption.

  Additionally, Run 4's nominal HepMC weight is the **raw** per-event
  weight (identical to LHE `XWGTUP`, i.e. **not yet divided by `N_gen`**)
  — unlike Run 3's HepMC weight, which the original study found was
  *already* pre-divided by `N_gen` inside the file. So `analyze_lops.py`
  applies `w_i = weight_i / N_gen` explicitly (same convention as
  `analyze_lo.py`'s LHE-based reading), while `analyze_nlops.py` does not
  divide again. This distinction is stated explicitly in both scripts'
  docstrings so a future reader does not silently transplant one
  convention onto the other file.

## Negative-weight / NLO status, independently verified

- **LO+PS (Run 4)**: independently confirmed 0/10000 negative weights,
  weight constant at 520.365 pb for every event (matches the task's "all
  unit/constant weight, no negative weights" claim). `Neff = 10000.0`
  (exactly `N_gen`, as expected for constant-weight events),
  `sigma = 520.3650 +/- 5.2037 pb` self-summed (task-quoted generation
  value: 520.4 +/- 0.7669 pb — the small discrepancy in the quoted MC
  integration error vs. this analysis's naive `sqrt(sum(w_i**2))` is
  expected: the official run-level MC error comes from MadGraph's phase-
  space-integration variance estimate, not from treating the final
  unweighted sample as if each event had an independent Poisson-like
  weight error; both are consistent statements about the same constant-
  weight sample).
- **NLO+PS (Run 3)**: reused directly from the existing
  `output/data/nlops_results.json` (not recomputed): `f_minus = 22.92%`
  (2292/10000, matches the task-supplied value and the original study's
  own independent verification), `Neff = 2933.3` out of `N_gen = 10000`
  raw events (i.e. roughly 3.4x fewer effective events than LO+PS's full
  10000, due to negative-weight cancellation), `sigma = 689.41 +/- ...`
  pb self-summed (consistent with the officially quoted 702.3 +/- 4.5 pb
  within the sample's own finite statistics, as already documented in the
  original study).

## Normalization mode

**Absolute yield mode** (pb per bin, not shape-normalized) throughout,
matching the original Tier 2 convention (`w_i = weight_i * L / N_gen`,
`L = 1 pb^-1`). Stated once and applied uniformly to both samples; never
mixed with shape-normalized mode anywhere in this task.

## Pre-plot self-check (performed)

LO+PS `pt_ttbar` bin 0 (0-25 GeV): 2713 raw events, hand-computed yield
`2713 * (520.365/10000) = 141.175025` pb, matching the pipeline's output
`141.1750245` pb exactly.

## Per-observable results and physics comments

All 5 observables use the identical bin edges as the original Tier 2
plots (`analysis/binning.py`), asserted equal between LO+PS and NLO+PS
before plotting.

1. **p_T^{ttbar}**: Both samples show clearly nonzero p_T^{ttbar} from
   shower resummation (LO+PS: mean 69.0 GeV, max 748.3 GeV over the full
   sample — confirming the shower alone generates recoil even though the
   bare LO matrix element would give an exact delta function at 0).
   Visually, NLO+PS sits above LO+PS through the bulk (peak region, up to
   ~100-150 GeV), consistent with its ~30% higher inclusive cross
   section. In the tail (150-500 GeV), however, the two curves converge
   and their statistical error bars overlap for essentially every bin;
   integrated yield above 100/150/200/300 GeV is actually *slightly
   higher* for LO+PS than for NLO+PS in absolute pb (e.g. >150 GeV:
   LO+PS = 52.30 +/- 1.65 pb vs NLO+PS = 43.15 +/- 3.21 pb, a ~2.5 sigma
   difference in the opposite direction from the naive expectation).
   **This is the opposite of the qualitative expectation stated in the
   task** (that LO+PS's tail should look softer/less populated than
   NLO+PS's, since NLO+PS's hardest emission is ME-accurate). Given
   NLO+PS's much-reduced effective statistics in the tail (Neff ~2933 out
   of 10000 raw events overall, and even fewer effective events land in
   these high-pT bins once negative-weight cancellation is accounted
   for), this could reflect genuine MC@NLO subtraction/damping structure
   in the intermediate-pT region (a documented feature where negative S-
   event weights partially cancel positive contributions before the true
   ME-driven hard tail asymptotically takes over at even higher pT than
   probed here), or it could simply be MC noise in an under-populated
   tail region. The sample size here (10000 raw events per run) cannot
   distinguish between these explanations — reported as observed, not
   forced to match the naive expectation.

2. **Delta_phi_{ttbar}**: Both samples show Delta_phi < pi (decorrelation
   from shower radiation; LO+PS mean 2.594 rad vs pi = 3.142 rad, max
   3.1416 — never exactly pi, confirming shower-level decorrelation even
   for LO+PS). Shape-wise the two curves track each other closely across
   the *entire* range including the maximally-decorrelated low-Delta_phi
   bins, with NLO+PS sitting consistently above LO+PS by roughly its
   overall rate normalization. No statistically clear extra decorrelation
   from NLO+PS is visible beyond the overall rate difference in this
   sample.

3. **p_T^{t,lead}**: Same qualitative pattern as p_T^{ttbar} — NLO+PS
   above LO+PS in the peak/bulk region (50-250 GeV), curves converge
   within errors from ~300 GeV up to 600 GeV, with the >450 GeV
   integrated yield again slightly *lower* for NLO+PS than LO+PS (2.55
   +/- 0.78 pb vs 3.69 +/- 0.44 pb). Same caveat as (1) applies: the
   expected "harder NLO+PS tail" is not clearly visible in this
   statistics-limited sample.

4. **m_{ttbar}**: Shapes are broadly similar across the whole mass range,
   with NLO+PS sitting above LO+PS by close to the overall K-factor-like
   normalization from ~350 GeV up to ~1000 GeV; above ~1000 GeV both
   curves become dominated by large statistical fluctuations (few raw
   events per bin) and no shape difference can be resolved.

5. **y_t**: Nearly identical shape between LO+PS and NLO+PS across the
   full rapidity range, with NLO+PS uniformly above LO+PS by
   approximately the overall rate ratio — as expected, since top rapidity
   is set by the hard-process kinematics/PDFs and is not expected to be
   strongly affected by whether the shower is attached to a bare-LO or
   NLO-matched matrix element.

## Fit convergence / boundary flags

No likelihood fit was performed for this task (pure kinematic-comparison
plots + CSVs only, per the task spec) — not applicable.

## Zero-yield bins

None encountered in either sample for any of the 5 observables within
the plotted ranges (`n_raw` > 0 in essentially every bin; the extreme
high-mass/high-pT tail bins have small but nonzero raw counts, as shown
in the CSVs).

## Output files

Plots (PDF + PNG), in a dedicated subdirectory so the original Tier 2
plots under `output/figures/*.png` are untouched:
- `output/figures/lops_vs_nlops/pt_ttbar_lops_vs_nlops.{pdf,png}`
- `output/figures/lops_vs_nlops/dphi_ttbar_lops_vs_nlops.{pdf,png}`
- `output/figures/lops_vs_nlops/pt_top_lead_lops_vs_nlops.{pdf,png}`
- `output/figures/lops_vs_nlops/m_ttbar_lops_vs_nlops.{pdf,png}`
- `output/figures/lops_vs_nlops/y_t_lops_vs_nlops.{pdf,png}`

CSVs (bin edges/centers, LO+PS yield+error+neff+n_raw, NLO+PS
yield+error+neff+n_raw per bin), in the same dedicated subdirectory so
the original `output/data/{pt_ttbar,dphi_ttbar,pt_top_lead,m_ttbar,y_t}.csv`
files are untouched:
- `output/data/lops_vs_nlops/pt_ttbar_lops_vs_nlops.csv`
- `output/data/lops_vs_nlops/dphi_ttbar_lops_vs_nlops.csv`
- `output/data/lops_vs_nlops/pt_top_lead_lops_vs_nlops.csv`
- `output/data/lops_vs_nlops/m_ttbar_lops_vs_nlops.csv`
- `output/data/lops_vs_nlops/y_t_lops_vs_nlops.csv`

Raw per-run JSON (Tier-1 rate + full histogram data):
- `output/data/lops_vs_nlops/lops_results.json` (Run 4, NEW, this task)
- `output/data/nlops_results.json` (Run 3, reused as-is, not modified)
