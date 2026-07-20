# Step 2 (LO): MadGraph5 Event Generation — pp -> ttbar at 13 TeV (Leading Order, N=10)

## Status: SUCCESS

## Overview

Leading-order (pure QCD, tree-level) event generation for $pp \to t\bar{t}$ at $\sqrt{s} = 13$ TeV,
using MadGraph5_aMC@NLO's built-in `sm` model (no UFO import, no `[QCD]` NLO tag). N = 10 events
requested, as specified in the task.

## Reuse of a Previously Verified Run

A process directory at `events/pp_ttbar_lo_13tev` already existed, compiled with
`import model sm` / `generate p p > t t~` / `output events/pp_ttbar_lo_13tev`, and had already been
launched (`Events/run_01/`) with settings that exactly match every requirement of this task
(process, model, PDF, scale choice, top mass/width, ebeam, nevents). This prior run was documented
in the sibling progress file `progress/ttbar_13tev_lo_nlo_n10/step2_lo_madgraph.md` (job ID
`27fdadf0df8a3891`, launched via `magnus run madgraph-launch`).

Rather than resubmitting an identical job (same process directory, same physics settings, same
event count) and overwriting an already-verified good result, this step independently re-verified
`run_01` end-to-end against every requirement below and confirms it is a correct, complete answer to
this task. No new compile or launch job was submitted.

### Original compile/launch commands (for record)

```
magnus run madgraph-compile -- \
  --model sm \
  --process "p p > t t~" \
  --output events/pp_ttbar_lo_13tev

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

- Job ID (compile+launch, prior execution): `27fdadf0df8a3891`
- Run name: `run_01`
- Tag: `tag_1`

Standalone equivalent documented at `scripts/mg5_ttbar_13TeV_lo.mg5`.

## Independent Verification Performed in This Step

All checks below were re-run directly against the files on disk in this session (not merely copied
from the prior progress file):

```
gzip -t events/pp_ttbar_lo_13tev/Events/run_01/unweighted_events.lhe.gz   -> OK (no errors)
gzip -dc ... | grep -c "<event>"                                          -> 10
```

Settings cross-checked in `Cards/run_card.dat` and confirmed identically present in
`Events/run_01/run_01_tag_1_banner.txt`:

| Setting | Value found | Matches requirement |
|---|---|---|
| `nevents` | `10` | Yes |
| `ebeam1` | `6500.0` GeV | Yes |
| `ebeam2` | `6500.0` GeV | Yes |
| `pdlabel` | `lhapdf` | Yes |
| `lhaid` | `247000` | Yes (NNPDF23_lo_as_0130_qed) |
| `dynamical_scale_choice` | `3` | Yes ($\mu_R=\mu_F=H_T/2$) |
| `fixed_ren_scale` | `False` | Yes |
| `fixed_fac_scale` | `False` | Yes |

`Cards/param_card.dat`:
- `MASS` block: `6  1.725000e+02  # mt` -> top mass = 172.5 GeV, matches requirement.
- `DECAY` block: `DECAY  6  1.476401e+00  # wt` -> auto-computed width from `set param_card DECAY 6 Auto`, matches requirement.

`Cards/proc_card_mg5.dat`:
```
import model sm
generate p p > t t~
```
Confirms plain LO process, no `[QCD]` NLO tag, no UFO import — matches requirement.

## Cross Section

Cross section reported in the run banner: **522.309 pb** (`Integrated weight (pb) : 522.309`).
Recorded here purely for run-verification purposes — no physics interpretation of this value is
performed at this step (that is deferred to the downstream analysis step).

## Events Generated

- Number of events in LHE file: **10** (verified by counting `<event>` tags in the decompressed file
  in this session).
- Format: parton-level, unweighted, LHE (Les Houches Event) format, gzip-compressed.
- No parton shower, no detector simulation applied (parton-level LHE output only), per task
  requirements.

## Output Directory Structure

```
events/pp_ttbar_lo_13tev/
├── Cards/
│   ├── param_card.dat
│   ├── run_card.dat
│   └── proc_card_mg5.dat
├── Events/
│   └── run_01/
│       ├── unweighted_events.lhe.gz        <- final parton-level LHE output (10 events, verified)
│       └── run_01_tag_1_banner.txt         <- full run configuration/banner (settings verified)
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

## Warnings / Issues

- None encountered during this verification step. A benign, non-fatal warning
  (`'fail' detected in stdout (non-fatal, e.g. LHAPDF systematics)`) was reported by the
  `madgraph-launch` blueprint during the original launch job (see
  `progress/ttbar_13tev_lo_nlo_n10/step2_lo_madgraph.md` for details); it has no impact on the
  correctness of the generated events or physics settings, as confirmed by the independent
  verification performed here.
- The documentation script `scripts/mg5_ttbar_13TeV_lo.mg5` did not previously exist in this
  directory and was created in this step for reproducibility.
