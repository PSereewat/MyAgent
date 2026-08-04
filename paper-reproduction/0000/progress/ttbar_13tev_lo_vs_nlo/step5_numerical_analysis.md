# Step 5: LO-vs-NLO QCD Numerical Analysis and Plotting -- pp > ttbar @ 13 TeV

## Status: SUCCESS

## Post-hoc presentation change, then reverted (net effect: no change from original delivery)

After initial delivery, a follow-up request asked that NLO bins with a
negative central `dsigma/dX` value (a known fixed-order-NLO subtraction
artifact near an LO/Born kinematic boundary, documented below) be made
visible on the log-scale figures via an open/hollow marker at `|value|`
instead of vanishing as a gap. This was implemented in
`scripts/make_plots.py` (affecting `pt_ttbar`, `dphi_ttbar`, `pt_t`) and
the three affected figures were regenerated.

A second follow-up then asked to **revert** that change and restore the
original rendering exactly. This was done: the marker/hatch/legend/
caption-note special-casing was fully removed from
`scripts/make_plots.py` (no `Rectangle` import, no negative-value
marker logic, no "open marker"/"crimson"/"downward-triangle" text
remaining anywhere in the script -- verified by grep), captions restored
to their original wording, and all five figures regenerated again. The
net effect versus the original Step 5 delivery is **no change**: negative
NLO bins (`pt_ttbar` [10,20) GeV = -0.885427928 pb/GeV, `dphi_ttbar`
[2.9845,3.0631) rad = -9.516690957956326 pb/rad, `pt_t` [740,760) GeV =
-0.0005749532 pb/GeV) are once again silently omitted as gaps on the log
axis, exactly as in the first version of these plots.

`analysis/make_histograms.py` and all `output/data/*.json`/`*.csv` files
were never touched by either the add or the revert -- confirmed by file
hash comparison before and after both changes; they still hold the true
signed values quoted above.

**Files regenerated in the final (reverted) state** (PDF+PNG each;
`output/data/*` untouched throughout):
- `output/figures/pt_ttbar.pdf` / `.png`
- `output/figures/dphi_ttbar.pdf` / `.png`
- `output/figures/pt_t.pdf` / `.png`
- `output/figures/m_ttbar.pdf` / `.png` and `output/figures/y_t.pdf` / `.png` were also regenerated (script runs all five in one pass) but were never visually different in the first place, since neither has a negative bin.

Purely internal LO-vs-NLO comparison, no external/HEPData comparison, no
exclusion limit, no profile-likelihood fit, no BSM scan. All numbers below
come from directly parsing the two raw LHE files listed in the task
(no MadAnalysis5 step involved -- top quarks are stable/undecayed at
parton level).

## Skill compliance

Read `pheno-analyzer` `SKILL.md` and all `references/` files
(`normalization-conventions.md`, `statistical-methods.md`,
`validation-checklist.md`, `data-formats.md`) before writing any code.
The statistical-methods likelihood machinery was intentionally NOT
invoked (out of scope per the task). The unified LO/NLO event-weighting
formula and the general (Kish) `Neff` formula from
`normalization-conventions.md` / `templates/nlo_event_weights.py` were
used throughout.

## Independent verification performed (not trusted blindly from upstream)

1. **Weight-id mapping for the 7-point scale envelope** -- parsed the raw
   `<initrwgt>` header of both LHE files directly (not the upstream
   progress-report claims):
   - LO (`events/lo/pp_ttbar_13TeV_lo/Events/run_01/unweighted_events.lhe.gz`):
     145 `<wgt>` entries per event, sequential ids 1-145, in the same order
     as the header. The `DYN_SCALE="3"` (HT/2) subset is ids
     4,9,14,19,23,28,33,38,43, exactly as the upstream report claimed --
     **confirmed independently**. id 23 = (muR,muF)=(1,1) central, verified
     numerically equal to `XWGTUP` for the first event (519.85200 pb both).
   - NLO (`events/nlo/pp_ttbar_13TeV_nlo/Events/run_01/events.lhe.gz`):
     27 `<wgt>` entries per event as **three redundant** 9-point groups
     (ids 1001-1009, 1010-1018, 1019-1027), all `dyn=3`. Used the first
     group (ids 1001-1009). id 1001 = (muR,muF)=(1,1) central, verified
     numerically equal to `XWGTUP` for the first event (1149.9 pb both,
     agreeing to the 5 significant figures printed in the `<wgt>` tag).
   - 7-point envelope used for both samples: (1,1) central, (0.5,0.5),
     (0.5,1), (1,0.5), (1,2), (2,1), (2,2) -- excluding the two
     opposite-extreme corners (0.5,2) and (2,0.5), per spec.
2. **Negative-weight fraction, NLO** -- recomputed directly from `XWGTUP`
   over all 100,000 parsed NLO events: **19,984/100,000 = 19.9840%**,
   exactly matching the upstream report's 19.98%. Confirmed genuinely
   nonzero (not a fabricated/assumed value) and LO's 0/100,000 = 0.0000%
   also independently confirmed.
3. All 100,000 events in both files were successfully parsed with exactly
   one top (`pdg==6, status==1`) and one antitop (`pdg==-6, status==1`)
   found per event (0 missing top/antitop pairs in either file).

## Analysis scripts

- `analysis/parse_lhe.py` -- shared streaming LHE parser (state machine,
  no full-file regex) plus the verified id/position mapping documented
  above, with the reasoning for each mapping recorded inline.
- `analysis/extract_observables.py` -- single pass over each LHE file;
  computes pT_ttbar, Delta_phi_ttbar, pT_t, m_ttbar, y_t and the 7
  envelope weights per event; caches to `analysis/cache/{lo,nlo}_events.npz`.
  Runtime: LO 4.9s, NLO 3.7s for 100k events each.
- `analysis/tier1_rates.py` -- total cross sections, K-factor, 7-point
  scale envelope on the total rate; writes `output/data/tier1_summary.json`.
- `analysis/make_histograms.py` -- Tier-2 differential distributions
  (absolute `dsigma/dX`), bin-by-bin scale envelope, NLO/LO ratio;
  writes `output/data/{observable}.json` and `.csv`.
- `scripts/make_plots.py` -- Tier-2 figures (PDF+PNG) to `output/figures/`.

All paths in the scripts are relative to the repo working directory, as
required.

## Normalization mode

**Absolute differential cross section** (`dsigma/dX` in pb/GeV, pb/rad,
or pb), not shape-normalized. This is the unified weighting formula from
`normalization-conventions.md`, `w_i = weight_i * L / N_gen`, with the
luminosity factor `L` omitted (equivalently, absorbed into the definition
of a cross section rather than an event count at fixed luminosity) because
the target quantity is `dsigma/dX` itself, not "events per bin per
luminosity". `N_gen = 100,000` for both samples (all generated events, as
confirmed by the LHE event counts). This mode was applied uniformly to
Tier 1 (total sigma) and Tier 2 (differential distributions); never mixed
with shape-normalized mode.

A bug was caught and fixed during development: the first implementation
of `histogram_weighted` divided by bin width but not by `N_gen`,
producing yields too large by a factor of 1e5. Caught via the skill's
required pre-plot hand-computed cross-check (see below) before any figure
was finalized.

A second bug was caught and fixed: `np.digitize(...)-1` with no
right-edge handling silently drops every event that lands exactly on the
rightmost bin edge. Since the LO sample is an exact delta function
*at* `Delta_phi_ttbar = pi` (the rightmost edge of that observable's
range), the naive binning was silently dropping 87% of LO events from the
histogram (`12,520/100,000` counted instead of `100,000/100,000`). Fixed
by replicating `numpy.histogram`'s bin-edge convention (last bin closed
on both ends) in a dedicated `bin_indices()` helper, verified after the
fix that all `100,000/100,000` LO events land in the correct bin for both
`pT_ttbar` (first bin, at 0) and `Delta_phi_ttbar` (last bin, at pi).

## Pre-plot self-check (skill-required sanity cross-check)

Recomputed `pT_t` LO bin 5 (100-120 GeV) by hand from raw cached arrays
independently of the pipeline code: raw count 11,570, `dsigma/dX =
sum(XWGTUP)/N_gen/binwidth = 3.0073438` pb/GeV -- matched the pipeline
output (`3.0073438...`) exactly.

## Tier 1: rates and uncertainties

| | LO | NLO |
|---|---|---|
| sigma [pb] +/- MC err (generator-reported, run summary) | 519.9 +/- 0.162 | 697.0 +/- 2.3 |
| sigma [pb] (our sum(XWGTUP)/N_gen cross-check) | 519.8520 | 690.3118 |
| relative difference (cross-check vs. reported) | -0.009% | -0.960% |
| Scale envelope (7-pt, around central) | +30.23% / -21.72% | +9.23% / -10.43% |
| Scale-band total width | 51.95 pct pts | 19.66 pct pts |
| K-factor (using generator-reported sigma) | 697.0/519.9 = **1.3407** | |
| K-factor (using our sum-of-weights cross-check) | 690.3118/519.8520 = **1.3279** | |
| Negative-weight fraction | 0.0000% (0/100,000) | 19.9840% (19,984/100,000) |
| `<wgt>` entries per event | 145 (ids 1-145; 9-pt dyn=3 subset used) | 27 (ids 1001-1027; first 9-pt group used) |
| Neff (Kish, general formula) | 100,000.0 | 36,038.4 |

The NLO `sigma` discrepancy between the generator-reported MC-integration
value (697.0 pb) and our sum-of-weights value from the unweighted LHE
sample (690.3 pb, -0.96% relative) is the same, already-documented and
expected effect noted in the upstream Step 3 report: the MC-integration
result additionally includes phase-space regions/precision beyond what a
finite 100k-event unweighted sample resolves exactly; both are standard
aMC@NLO outputs and consistent within their respective MC uncertainties.
The headline sigma_NLO used for the K-factor and reported here is the
generator's MC-integration value; the sum-of-weights K-factor is reported
alongside as a cross-check -- both land in the 1.3-1.6 sane range.

**All Tier-1 validation checks: PASS**
- K-factor (1.3279-1.3407, depending on which sigma_NLO is used) is
  within the expected 1.3-1.6 range: **PASS**.
- NLO scale band (19.66 pct-point total width) is substantially narrower
  than the LO scale band (51.95 pct-point total width): **PASS**, no flag
  needed.

Full numeric envelope tables (all 7 (muR,muF) points, not just the up/down
extremes) are in `output/data/tier1_summary.json`.

## Tier 2: differential distributions

All five required observables were built from the two-particle
(t, tbar) 4-momenta read directly from LHE status-1 records with PDG
codes 6/-6.

| Observable | Binning | y-axis | Ratio panel | Figures |
|---|---|---|---|---|
| pT_ttbar | 40 bins, [0,400] GeV | log | omitted (LO delta fn) | `output/figures/pt_ttbar.{pdf,png}` |
| Delta_phi_ttbar | 40 bins, [0,pi] | log | omitted (LO delta fn) | `output/figures/dphi_ttbar.{pdf,png}` |
| pT_t | 40 bins, [0,800] GeV | log | yes | `output/figures/pt_t.{pdf,png}` |
| m_ttbar | 40 bins, [300,1500] GeV | log | yes | `output/figures/m_ttbar.{pdf,png}` |
| y_t | 40 bins, [-3,3] | linear | yes | `output/figures/y_t.{pdf,png}` |

Underlying binned data (bin edges, dsigma/dX, errors, LO and NLO
separately, per-bin `f_minus`/`Neff`/scale-band for NLO, and NLO/LO ratio
where applicable) saved as both JSON and CSV under `output/data/`:
`pt_ttbar.{json,csv}`, `dphi_ttbar.{json,csv}`, `pt_t.{json,csv}`,
`m_ttbar.{json,csv}`, `y_t.{json,csv}`.

### pT_ttbar
- LO: exact delta function at pT_ttbar=0 -- **all 100,000/100,000** LO
  events land in the first bin (0-10 GeV); `dsigma/dpT = 51.9852 pb/GeV`
  (= sigma_LO / 10 GeV bin width), stated explicitly in the figure caption.
- NLO: genuine nonzero tail confirmed -- 24.41% of NLO events have
  pT_ttbar > 10 GeV, extending out past 350 GeV.
- One bin (10-20 GeV) is negative: -0.885 +/- 0.091 pb/GeV
  (f_minus=0.56, Neff=95.0, raw count 6242). This sits immediately next
  to the Born (pT->0) kinematic boundary and reflects a well-known
  fixed-order-NLO feature (incomplete real/virtual/subtraction
  cancellation locally near a Sudakov-shoulder-like boundary), not a
  parsing or normalization error -- confirmed by checking the bin's raw
  event count and f_minus (not a low-statistics fluke; both positive and
  negative event populations are substantial and nearly cancel). Omitted
  from the log-scale line as a gap since it cannot be shown on log axes;
  the exact value is preserved in the JSON/CSV.

### Delta_phi_ttbar
- LO: exact delta function at Delta_phi_ttbar=pi (verified `min=max=
  3.1415926536` rad to float precision) -- **all 100,000/100,000** LO
  events in the last bin; `dsigma/dDeltaphi = 6618.96 pb/rad`, stated
  explicitly in the figure caption.
- NLO: genuine nonzero tail confirmed -- 15.71% of NLO events have
  Delta_phi_ttbar < 3.0 rad.
- The second-to-last bin (2.985-3.063 rad, immediately below the
  pi-containing last bin) is negative and statistically consistent with
  zero within its comparable-magnitude error
  (-9.52 +/- 10.50 pb/rad, Neff=0.82), reflecting heavy
  positive/negative-weight cancellation immediately below the LO
  kinematic boundary. Omitted from the log-scale line as a gap.

### pT_t, m_ttbar, y_t
- Ratio (differential K-factor) panels included with propagated
  uncertainty and a horizontal reference line at 1.
- `m_ttbar` first bin (300-330 GeV) is exactly zero raw count for BOTH LO
  and NLO -- this is a **physical zero**, not a statistics artifact: the
  bin lies entirely below the kinematic threshold `m_ttbar >= 2*m_t =
  345 GeV`.
- `pT_t` highest tail bins (740-760 GeV: 3 raw NLO events; 780-800 GeV:
  6 raw NLO events) have very low statistics and their central NLO value
  is non-positive in the 780-800 GeV bin (exact statistical cancellation,
  Neff=0) -- omitted from the log-scale display and from the ratio panel
  there; not fabricated or interpolated.
- Differential K-factor is broadly consistent with the total K-factor
  (~1.3) at low/moderate pT_t, m_ttbar, and central y_t, rising above 1.3
  in the statistics-limited tails (large error bars there, as expected).

## Tier 3: technical evidence of a correct NLO calculation

1. **Negative-weight fraction**: recomputed directly from `XWGTUP` over
   all 100,000 NLO events -- **19,984/100,000 = 19.9840%**, matching (not
   just quoting) the upstream 19.98% figure.
2. **`<wgt>` variation entries per NLO event**: 27, ids 1001-1027,
   organized as three redundant 9-point (muR,muF) `weightgroup` blocks
   (`scale_variation 0 3`, `scale_variation 4 3`, `scale_variation 6 3`),
   all tagged `dyn=3` (HT/2) -- verified directly from the `<initrwgt>`
   header text (reproduced in `analysis/parse_lhe.py` docstring).
3. **Virtual/loop evaluation confirmed**: per the Step 3 progress report
   (`progress/ttbar_13tev_lo_vs_nlo/step3_nlo_madgraph.md`), `.full_summary.txt`
   reports 37,945 loop ME evaluations via MadLoop with CutTools reduction
   (0 unstable/rescued points), and `alllogs_0.html` shows CutTools v1.9.3
   initialization. The banner confirms `order = NLO` and
   `store_rwgt_info = True`/`reweight_scale = True` (re-verified directly
   from `run_01_tag_1_banner.txt` lines 157, 168, 329 in this session).

## Physics validation checks (explicit pass/fail)

| Check | Result |
|---|---|
| LO events land exactly at pT_ttbar=0 and Delta_phi_ttbar=pi | **PASS** (100,000/100,000 events each, float-exact: pT_ttbar min=max=0.0, Delta_phi_ttbar min=max=3.1415926536 rad) |
| NLO shows nonvanishing tails in both pT_ttbar and Delta_phi_ttbar | **PASS** (24.41% of NLO events with pT_ttbar>10 GeV; 15.71% with Delta_phi_ttbar<3.0 rad) |
| NLO negative-weight fraction is nonzero | **PASS** (19.9840%, independently recomputed) |
| NLO scale band narrower than LO scale band | **PASS** (19.66 vs. 51.95 percentage-point total width) |
| K-factor in the 1.3-1.6 range | **PASS** (1.3279-1.3407 depending on sigma_NLO source) |

No check failed; nothing needs to be flagged as physically wrong.

## Fit convergence / boundary status

Not applicable -- no profile-likelihood fit or minimizer was run for this
task, per the explicit scope restriction in the prompt.

## Issues, assumptions, and zero/non-convergent items

- No zero-yield bins were silently substituted; every zero (`m_ttbar`
  first bin, `pT_t` last bin, LO bins outside the delta-function bin for
  `pT_ttbar`/`Delta_phi_ttbar`) is reported as exactly zero with its
  physical/statistical origin identified above.
- Two code bugs were found and fixed during development (missing
  `N_gen` division; bin-edge inclusivity for the delta-function bins) --
  both described above under "Normalization mode", along with the
  cross-checks that caught them.
- `reweight_PDF` was not enabled for the NLO run (only scale variation),
  consistent with the task's Tier requirements (no PDF-uncertainty
  deliverable was requested).
- The three redundant NLO scale-variation weightgroups (ids 1001-1009,
  1010-1018, 1019-1027) are numerically identical in content (same
  (muR,muF) grid, same `dyn=3` tag); only the first group was used. This
  redundancy was noted, not treated as an inconsistency requiring
  resolution.

## Negative-weight fraction / Neff summary (NLO)

- Total sample: `f_minus = 19.9840%` (19,984/100,000), `Neff` (Kish,
  general formula, on the total-rate weights) = **36,038.4** (out of
  100,000 raw events) -- i.e., the effective statistical power of the NLO
  sample is reduced to about 36% of its raw event count by
  positive/negative weight cancellation.
- Per-bin `f_minus`, `Neff`, and the bin statistical error
  (`sqrt(sum(w_i**2))/binwidth`) are all recorded together (never
  `f_minus` alone) in every `output/data/{observable}.json` /
  `.csv` file, per the skill's hard rule.

## File paths (all absolute)

Scripts:
- `/Users/phongsakornsereewat/ColliderAgenttry/paper-reproduction/0000/analysis/parse_lhe.py`
- `/Users/phongsakornsereewat/ColliderAgenttry/paper-reproduction/0000/analysis/extract_observables.py`
- `/Users/phongsakornsereewat/ColliderAgenttry/paper-reproduction/0000/analysis/tier1_rates.py`
- `/Users/phongsakornsereewat/ColliderAgenttry/paper-reproduction/0000/analysis/make_histograms.py`
- `/Users/phongsakornsereewat/ColliderAgenttry/paper-reproduction/0000/scripts/make_plots.py`

Figures:
- `/Users/phongsakornsereewat/ColliderAgenttry/paper-reproduction/0000/output/figures/pt_ttbar.pdf` / `.png`
- `/Users/phongsakornsereewat/ColliderAgenttry/paper-reproduction/0000/output/figures/dphi_ttbar.pdf` / `.png`
- `/Users/phongsakornsereewat/ColliderAgenttry/paper-reproduction/0000/output/figures/pt_t.pdf` / `.png`
- `/Users/phongsakornsereewat/ColliderAgenttry/paper-reproduction/0000/output/figures/m_ttbar.pdf` / `.png`
- `/Users/phongsakornsereewat/ColliderAgenttry/paper-reproduction/0000/output/figures/y_t.pdf` / `.png`

Data:
- `/Users/phongsakornsereewat/ColliderAgenttry/paper-reproduction/0000/output/data/tier1_summary.json`
- `/Users/phongsakornsereewat/ColliderAgenttry/paper-reproduction/0000/output/data/pt_ttbar.{json,csv}`
- `/Users/phongsakornsereewat/ColliderAgenttry/paper-reproduction/0000/output/data/dphi_ttbar.{json,csv}`
- `/Users/phongsakornsereewat/ColliderAgenttry/paper-reproduction/0000/output/data/pt_t.{json,csv}`
- `/Users/phongsakornsereewat/ColliderAgenttry/paper-reproduction/0000/output/data/m_ttbar.{json,csv}`
- `/Users/phongsakornsereewat/ColliderAgenttry/paper-reproduction/0000/output/data/y_t.{json,csv}`

Cache (intermediate, not a final deliverable but reusable):
- `/Users/phongsakornsereewat/ColliderAgenttry/paper-reproduction/0000/analysis/cache/lo_events.npz`
- `/Users/phongsakornsereewat/ColliderAgenttry/paper-reproduction/0000/analysis/cache/nlo_events.npz`
