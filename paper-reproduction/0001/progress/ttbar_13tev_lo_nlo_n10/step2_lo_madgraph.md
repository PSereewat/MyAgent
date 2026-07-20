# Step 2 (LO): MadGraph5 Event Generation — pp -> ttbar at 13 TeV (Leading Order, N=10)

## Status: SUCCESS

## Overview

Leading-order (pure QCD, tree-level) event generation for $pp \to t\bar{t}$ at $\sqrt{s} = 13$ TeV,
Run 1 of the two-run table in Section 3 of `ttbar_production.md`, using MadGraph5_aMC@NLO's built-in
`sm` model (no UFO import needed, no `[QCD]` NLO tag). Deliberately small statistics run: N = 10 events.

## Compiled Process Directory

A process directory already existed at `events/pp_ttbar_lo_13tev`, compiled previously via
`generate p p > t t~` / `output process_output` with model `sm` (LO, no NLO tag). It had NOT yet been
launched — its `run_card.dat` still had default settings (nevents=10000, pdlabel=nn23lo1,
dynamical_scale_choice=-1, MT=173.0). This directory was reused as the `--process` input to
`madgraph-launch` (no recompilation needed since the process/model already matched requirements).

## Step: Launch

```
magnus run madgraph-launch -- \
  --process events/pp_ttbar_lo_13tev \
  --commands "done
set nevents 10
set ebeam1 6500
set ebeam2 6500
set param_card MASS 6 172.5
set param_card DECAY 6 Auto
set pdlabel lhapdf
set lhaid 247000
set dynamical_scale_choice 3
set fixed_ren_scale False
set fixed_fac_scale False
done" \
  --output events/pp_ttbar_lo_13tev
```

- Job ID: `27fdadf0df8a3891`
- Result: `success = true`
- Run name: `run_01`
- Tag: `tag_1`
- Warning reported by blueprint: `'fail' detected in stdout (non-fatal, e.g. LHAPDF systematics)` —
  non-fatal, standard LHAPDF systematics-weight message; run completed normally with the correct
  settings (verified below). Identical benign warning was seen in the sibling reproduction directory
  (paper-reproduction/0000) for the same process/PDF combination.

## Settings Used (verified from `run_card.dat`, `param_card.dat`, and the LHE banner)

| Setting | Value |
|---|---|
| Process | `p p > t t~` (LO, no `[QCD]` tag) |
| Model | `sm` (MG5 built-in Standard Model) |
| Collider | $pp$, $\sqrt{s} = 13$ TeV (`ebeam1 = ebeam2 = 6500.0` GeV) |
| PDF set | `NNPDF23_lo_as_0130_qed` (`pdlabel = lhapdf`, `lhaid = 247000`) |
| Renorm./fact. scale | Dynamic, $\mu_R = \mu_F = H_T/2$ (`dynamical_scale_choice = 3`, `fixed_ren_scale = False`, `fixed_fac_scale = False`) |
| Top mass | `MASS 6 = 172.5` GeV (verified in param_card: `6 1.725000e+02 # mt`) |
| Top width | `DECAY 6 Auto` (auto-computed: `1.476401` GeV, verified in param_card: `DECAY 6 1.476401e+00 # wt`) |
| Number of events requested | 10 (`nevents = 10`) |
| Shower / detector | None (parton-level only, tops undecayed in the LHE record — DECAY block auto-width is for the width parameter only, not applied as a decay in the LO parton-level sample) |

## Cross Section

Cross section: **522.3 +- 4.897 pb** (reported by the launch blueprint). This matches the cross section
obtained in the sibling reproduction (paper-reproduction/0000) for the same process/settings at N=100,
as expected since the cross section value itself is independent of the number of unweighted events
requested (it is the total integrated cross section from phase-space integration, not derived from the
10-event sample). Recorded here purely for run-verification purposes — per task instructions, no further
physics interpretation/analysis of this value is performed at this step.

## Events Generated

- Number of events in LHE file: **10** (verified by counting `<event>` tags in the decompressed file)
- Format: parton-level, unweighted, LHE (Les Houches Event) format
- Verified in raw LHE event records: all 10 events contain a top (PDG 6) and antitop (PDG -6) each with
  mass 172.5 GeV (`0.17250000000E+03`) as final-state particles (status 1, undecayed) — matching the
  analysis requirement to read final-state PDG ±6 four-momenta directly from the LHE file.

## Output Directory Structure

```
events/pp_ttbar_lo_13tev/
├── Cards/
│   ├── param_card.dat
│   ├── run_card.dat
│   └── proc_card_mg5.dat
├── Events/
│   └── run_01/
│       ├── unweighted_events.lhe.gz        <- final parton-level LHE output (10 events)
│       └── run_01_tag_1_banner.txt         <- full run configuration/banner
├── SubProcesses/
├── Source/
├── bin/
├── lib/
├── HTML/
├── index.html
└── madevent.tar.gz
```

## Final LHE File Path

```
/Users/phongsakornsereewat/MyAgent/paper-reproduction/0001/events/pp_ttbar_lo_13tev/Events/run_01/unweighted_events.lhe.gz
```

Verified: `gzip -t` integrity check passed; decompressed file contains exactly 10 `<event>` blocks with
truth-level top/antitop four-momenta (parton-level, no shower/detector applied).

## Warnings / Issues

- Blueprint-reported non-fatal warning: `'fail' detected in stdout (non-fatal, e.g. LHAPDF systematics)`
  — same benign message seen in the successful sibling run (paper-reproduction/0000), no impact on
  correctness of the generated events or physics settings.
- No other warnings encountered. No `param_card_warnings` (no duplicate PDG entries) were reported.
- No recompilation was necessary since the pre-existing process directory already used the correct
  process definition (`p p > t t~`) and model (`sm`, LO); only the launch step (run_card/param_card
  settings) needed correcting from the stale defaults.
