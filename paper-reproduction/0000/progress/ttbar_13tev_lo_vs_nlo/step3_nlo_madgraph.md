# Step 3 — NLO QCD MadGraph5_aMC@NLO Event Generation: pp > ttbar @ 13 TeV

Status: **SUCCESS**

## Summary

| Item | Value |
|---|---|
| Process | `p p > t t~ [QCD]` (NLO QCD, top quarks stable/undecayed) |
| Model | `loop_sm` (MG5 built-in NLO-capable SM, no custom UFO) |
| Collider | pp, sqrt(s) = 13 TeV (ebeam1 = ebeam2 = 6500 GeV) |
| m_t (param_card MASS 6) | 172.5 GeV (explicitly set; UFO default was 173.0 GeV) |
| PDF set | `NNPDF23_nlo_as_0119_qed`, LHAPDF ID **244800** (`pdlabel = lhapdf`) |
| Scale choice | dynamic, `dynamical_scale_choice = 3` (H_T/2), `fixed_ren_scale = False`, `fixed_fac_scale = False` |
| Requested events | 100,000 (no reduction needed) |
| Generated events | 100,000 (`Number of events generated: 100000`) |
| Cross section (integration) | 6.970e+02 +- 2.3e+00 pb |
| Scale envelope (from LHE, 9-point) | central 6.904e+02 pb, +9.2% / -10.4% |
| Negative-weight fraction | 19.98% (19,984 / 100,000 events) |
| `<wgt>` scale-variation entries/event | 27 (ids 1001-1027; see below) |
| Shower/Detector | None (fixed-order, parton-level only, per spec) |

## Compilation (Step 1)

- Command: `magnus run madgraph-compile -- --model loop_sm --process "p p > t t~ [QCD]" --output events/nlo/pp_ttbar_13TeV_nlo`
- Job ID: `210cd508b763b2ba`, result `success: true`
- Compiled process directory: `events/nlo/pp_ttbar_13TeV_nlo`
- Confirmed NLO-capable model content in the compiled process:
  - `bin/internal/ufomodel/CT_couplings.py`, `bin/internal/ufomodel/CT_vertices.py` present
  - R2 counterterm Fortran source compiled into `Source/DHELAS/` (`R2_QQ_1_0.f`, `R2_GG_1_0.f`, etc.)
  - Compiled with `FixedOrderAnalysis`, `MCatNLO`, `SubProcesses` (P0_*) directories characteristic of an aMC@NLO NLO output, not a LO-only `madevent` output.

## Event Generation (Step 2, launch)

- Command (`--commands` body, state machine: 1 `done` then State-2 settings then final `done`):
```
done
set nevents 100000
set ebeam1 6500
set ebeam2 6500
set pdlabel lhapdf
set lhaid 244800
set dynamical_scale_choice 3
set fixed_ren_scale False
set fixed_fac_scale False
set req_acc_FO -1
set param_card MASS 6 172.5
set reweight_scale True
set rw_rscale 1.0, 2.0, 0.5
set rw_fscale 1.0, 2.0, 0.5
set store_rwgt_info True
done
```
(`reweight_PDF` deliberately left at its default `False` — not requested for this study.)

- Job ID: `363ac4c9e606e492`, result `success: true`
- Result payload: `{"cross_section": "6.970e+02 +- 2.3e+00 pb", "nevents": 100000, "run_name": "run_01", "output_dir": "events/nlo/pp_ttbar_13TeV_nlo"}`
- Run name: `run_01`

Verified from `run_01_tag_1_banner.txt` (dumped `run_card.dat`) that every requested setting was actually applied (not silently swallowed after the final `done`):
```
6500.0  = ebeam1
6500.0  = ebeam2
lhapdf  = pdlabel
244800  = lhaid
3       = dynamical_scale_choice
False   = fixed_ren_scale
False   = fixed_fac_scale
1.0, 2.0, 0.5 = rw_rscale
1.0, 2.0, 0.5 = rw_fscale
True    = reweight_scale
False   = reweight_pdf
True    = store_rwgt_info
order = NLO
```
and MASS 6 = 172.5 GeV was confirmed directly in generated LHE event kinematics (top/antitop mass column reads `0.17250000000000000E+03`).

## Confirmation of genuine loop/virtual evaluation

From `Events/run_01/.full_summary.txt` (produced by aggregating the per-channel run logs):
```
  Number of loop ME evaluations (by MadLoop): 37945
    Stability unknown:                   0
    Stable PS point:                     37945
    Unstable PS point (and rescued):     0
    Unstable PS point (and not rescued): 0
    Only double precision used:          37945
    Quadruple precision used:            0
    Reduction methods used:
      > CutTools (double precision)      37945

  Timing profile for <Virtuals> :
    Overall fraction of time         14.311 %
```
From `Events/run_01/alllogs_0.html` (per-channel MadLoop initialization log):
```
INFO: MadLoop read these parameters from ../MadLoop5_resources/MadLoopParams.dat
-------------------------------------------------------------------------
|              You are using CutTools - Version 1.9.3                  |
|              Authors: G. Ossola, C. Papadopoulos, R. Pittau          |
|              Published in JHEP 0803:042,2008                         |
```
The run_card (banner) also shows `order = NLO`. Together these confirm: the one-loop virtual matrix elements were actually evaluated via MadLoop with CutTools reduction (37,945 loop ME evaluations, all numerically stable in double precision, zero unstable/rescued points), real emission handled via MadFKS subtraction, and the run proceeded as a genuine `[QCD]` NLO calculation — not a LO-only fallback.

## Cross section and scale summary (`Events/run_01/summary.txt`)

```
   --------------------------------------------------------------
      Summary:
      Process p p > t t~ [QCD]
      Run at p-p collider (6500.0 + 6500.0 GeV)
      Number of events generated: 100000
      Total cross section: 6.970e+02 +- 2.3e+00 pb
   --------------------------------------------------------------
      Scale variation (computed from LHE events):
          Dynamical_scale_choice 3 (envelope of 9 values):
              6.904e+02 pb  +9.2% -10.4%
   --------------------------------------------------------------
```
(nevents = 100,000 >= 10,000, so the human-readable envelope summary was printed as expected; no reduction of event count was necessary.)

## LHE `<wgt>` scale-variation entries

Header `<initrwgt>` in `Events/run_01/events.lhe.gz` defines **27** weight entries per event, `id='1001'` through `id='1027'`, organized as **three** `weightgroup` blocks (`combine='envelope'`), each containing the same 3x3 = 9-point (muR, muF) in factors of {0.5, 1.0, 2.0} grid, all tagged `dyn=3` (dynamical_scale_choice 3 = H_T/2):

- `weightgroup name='scale_variation 0 3'` → ids 1001-1009
- `weightgroup name='scale_variation 4 3'` → ids 1010-1018
- `weightgroup name='scale_variation 6 3'` → ids 1019-1027

Each group's 9 combinations (muR, muF) in units of the central scale: (1,1), (2,1), (0.5,1), (1,2), (2,2), (0.5,2), (1,0.5), (2,0.5), (0.5,0.5). The 7-point envelope required downstream (excluding the two opposite-extreme corners (2,0.5) and (0.5,2)) is a subset of each 9-point grid and can be extracted directly from the corresponding `<wgt>` entries without a rerun. Example first event: `<wgt id='1001'>` (central, muR=muF=1) = 1149.9, ranging up to `<wgt id='1009'>` (muR=muF=0.5) = 1466.1 for that single event.

Every `<event>` block carries a full `<rwgt>` block with all 27 `<wgt id='...'>` entries — confirmed directly by inspection of the first LHE event and the `<initrwgt>` header (`init` line PDF columns read `244800 244800`, confirming LHAPDF ID 244800 was used for both beams).

## Negative-weight fraction

Computed directly from the nominal event weight (`XWGTUP`, 3rd field of each `<event>` header line) over all 100,000 generated events in `events.lhe.gz`:

- Total events: 100,000
- Negative-weight events: 19,984
- **Negative-weight fraction: 19.98%**

This is nonzero and within the expected O(10-30%) range for fixed-order NLO QCD ttbar production quoted in the pipeline reference docs, confirming the run is a genuine NLO calculation (a LO-only run would show exactly 0% negative weights).

## Confirmation top quarks are undecayed

Inspected raw LHE particle records. Example first event (initial state gg -> t t~):
```
   21 -1    0    0  501  502  ...   (gluon, incoming)
   21 -1    0    0  502  503  ...   (gluon, incoming)
    6  1    1    2  501    0  ...   (top, status=1 stable, mass=172.5 GeV)
   -6  1    1    2    0  503  ...   (antitop, status=1 stable, mass=172.5 GeV)
```
PDG codes 6 and -6 both appear with LHE status code `1` (final-state, stable) and no daughter/decay records — confirmed by a full-file scan that finds `{6, -6}` as the only final-state-stable particle set aside from light QCD radiation partons in real-emission events. No decay chain syntax and no MadSpin were used (per spec).

## Output directory structure

```
events/nlo/pp_ttbar_13TeV_nlo/
├── Cards/
│   ├── param_card.dat          (MASS 6 = 172.5 GeV)
│   ├── run_card.dat            (pdlabel=lhapdf, lhaid=244800, dynamical_scale_choice=3, reweight_scale=True, ...)
│   └── ...
├── Events/
│   └── run_01/
│       ├── events.lhe.gz               (98 MB, 100,000 events, LHE, 27 <wgt>/event)
│       ├── run_01_tag_1_banner.txt     (full run_card/param_card/proc_card dump)
│       ├── summary.txt                 (cross section + scale-variation envelope)
│       ├── .full_summary.txt           (adds MadLoop/CutTools stability + timing profile)
│       ├── res_0.txt, res_1.txt, res_2.txt   (per-channel integration results)
│       └── alllogs_0.html, alllogs_1.html, alllogs_2.html  (full per-channel run logs)
├── SubProcesses/, Source/, bin/, MCatNLO/, FixedOrderAnalysis/, HTML/, lib/
```

Total process directory size: 1.7 GB (dominated by the 98 MB compressed LHE file plus compiled Fortran object/library trees).

## Warnings / issues

- No compile or launch errors. No `param_card_warnings` returned.
- No Pythia8 shower and no Delphes detector simulation were run, per the fixed-order/parton-level requirement of this study — `Events/run_01/` contains only the LHE file (no `.hepmc.gz`, no `.root`, no `.lhco.gz`).
- Minor expected numerical difference between the total-cross-section-from-integration value (697.0 pb) and the central-scale value re-derived from the unweighted LHE event sample (690.4 pb, from the 9-point envelope's central `id='1001'` weights) — both are standard aMC@NLO outputs and consistent within their respective MC uncertainties; use whichever is appropriate for the analysis (envelope midpoint recommended for the scale-band comparison, integration value + MC error for the headline sigma_NLO).

## Downstream note (event-analyzer / plotting agents)

**Use the signed per-event weight (`event.weight`, i.e. `XWGTUP` from the LHE `<event>` header, id-less nominal weight) to fill all histograms.** Do not filter or drop negative-weight events (19.98% of the sample) — they carry genuine physical information and must be summed with their sign when computing bin contents and their squares when computing statistical errors. For the 7-point scale envelope, use the `<wgt id='1001'>` through `<wgt id='1009'>` (or any consistent one of the three equivalent 9-point groups, e.g. `1001`-`1009`) per-event weights, restricted to the 7 combinations excluding `(muR,muF)=(2,0.5)` and `(0.5,2)`.
