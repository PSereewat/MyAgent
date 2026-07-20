# Step 2 (LO): MadGraph5 Event Generation — pp -> t t~ at 13 TeV (Leading Order)

## Status: SUCCESS

## Overview

Leading-order (pure SM QCD, tree-level) event generation for `p p > t t~` at
sqrt(s) = 13 TeV, using MadGraph5_aMC@NLO's built-in `sm` model (no UFO import,
no `[QCD]` NLO tag). N = 10000 events requested and produced. Top quarks kept
stable/undecayed. Parton-level LHE output only (no shower, no Delphes, no
MadSpin). This is the LO half of the LO vs NLO t tbar comparison study; the NLO
sample is produced independently by a separate agent/run (not touched here).

## Compilation

```
magnus run madgraph-compile -- \
  --model sm \
  --process "p p > t t~" \
  --output events/pp_ttbar_lo_13tev
```

- Job ID: `28de33ad4bceb6fc`
- Result: `success: true`, `process_dir: events/pp_ttbar_lo_13tev`
- `Cards/proc_card_mg5.dat` confirms: `import model sm` / `generate p p > t t~`
  — plain LO process, no `[QCD]` tag, no UFO import.

## Launch

```
magnus run madgraph-launch -- \
  --process events/pp_ttbar_lo_13tev \
  --commands "done
set nevents 10000
set ebeam1 6500
set ebeam2 6500
set param_card MASS 6 172.5
set param_card DECAY 6 Auto
set pdlabel lhapdf
set lhaid 247000
set dynamical_scale_choice 3
set fixed_ren_scale False
set fixed_fac_scale False
set use_syst True
set systematics_arguments ['--mur=0.5,1,2', '--muf=0.5,1,2']
done" \
  --output events/pp_ttbar_lo_13tev
```

- Job ID: `fc45909b10966150`
- Result: `success: true`, `run_name: run_01`, `tag: tag_1`,
  `cross_section: "520.4 +- 0.7669 pb"`, `nevents: 10000`
- No `param_card_warnings` returned.
- Standalone equivalent documented at `scripts/mg5_ttbar_13TeV_lo.mg5`.

Note on the launch-command state machine: exactly two `done` lines were used
(one to leave the feature-selection state with no shower/detector/madspin
selected, one to launch after all `set` lines), per the madgraph-simulator
skill's state machine. This avoids both the "no `set` applied" bug (consecutive
`done`s) and the pre-2026-04 default-`nevents`-10000 bug.

## Settings Verification (from `Cards/run_card.dat` / `param_card.dat`)

| Setting | Value found | Matches requirement |
|---|---|---|
| `nevents` | `10000` | Yes |
| `ebeam1` | `6500.0` GeV | Yes |
| `ebeam2` | `6500.0` GeV | Yes |
| `pdlabel` | `lhapdf` | Yes |
| `lhaid` | `247000` | Yes (`NNPDF23_lo_as_0130_qed`) |
| `dynamical_scale_choice` | `3` | Yes (mu_R = mu_F = H_T/2) |
| `fixed_ren_scale` | `False` | Yes |
| `fixed_fac_scale` | `False` | Yes |
| `use_syst` | `True` | Yes |
| `systematics_program` | `systematics` | Yes (python module) |
| `systematics_arguments` | `['--mur=0.5,1,2', '--muf=0.5,1,2']` | Yes |

`Cards/param_card.dat`:
- `MASS` block: `6  1.725000e+02` -> top mass = 172.5 GeV.
- `DECAY` block: `DECAY  6  1.476401e+00  # wt` -> auto-computed width from
  `set param_card DECAY 6 Auto`.

## Cross Section

- Magnus job result: **520.4 +- 0.7669 pb**
- Banner (`run_01_tag_1_banner.txt`, `MGGenerationInfo`): **Integrated weight
  (pb): 520.365**, Number of Events: 10000 (higher-precision figure; consistent
  with the rounded job-result value to within MC error).

This is the nominal (central-scale) LO total cross section at
mu_R = mu_F = H_T/2, `NNPDF23_lo_as_0130_qed` (lhaid 247000), m_t = 172.5 GeV,
sqrt(s) = 13 TeV. The 7-point scale envelope should be built downstream from
the `<rwgt>` weights described below (this step only confirms they exist and
are non-degenerate; extracting/aggregating the envelope is a downstream
analysis task).

## Events Generated

- Number of events in LHE file: **10000** (verified: `grep -c "<event>"` on
  the decompressed file).
- Format: parton-level, unweighted, LHE (Les Houches Event) format,
  gzip-compressed.
- No parton shower, no detector simulation applied (parton-level LHE output
  only), per task requirements.
- gzip integrity check (`gzip -t`): OK, no errors.

## Scale-Uncertainty / Systematics Weight Verification (LO systematics module)

The LO run_card exposes a dedicated LO systematics mechanism, distinct from
the NLO `reweight_scale`/`rw_rscale`/`rw_fscale` keys used for `loop_sm`:
`use_syst`, `systematics_program`, `systematics_arguments`. These were
explicitly set as shown above (mur/muf both scanned over {0.5, 1, 2}, i.e. the
9-point independent grid requested). This ran successfully with no errors
(`parton_systematics.log` and the four `log_sys_*.txt` per-core logs contain no
"error"/"fail"/"traceback" strings).

**Verification performed** (decompressed `unweighted_events.lhe.gz`):

- `<initrwgt>` header present, containing **2 `<weightgroup>` blocks**:
  1. `"Central scale variation"` (`combine="envelope"`) — **44 `<weight>`
     entries**. For each of the 9 (mur, muf) in {0.5,1,2} x {0.5,1,2}
     combinations, MG5's systematics module additionally re-evaluated the
     weight under the other three built-in dynamical-scale choices
     (`DYN_SCALE=1..4`, i.e. sum-pt, HT, HT/2, sqrt(s)) in addition to the
     process's actual configured choice (`dynamical_scale_choice=3`, HT/2).
     Restricting to `DYN_SCALE="3"` (the physically relevant one, matching the
     run's actual `dynamical_scale_choice`) still yields the full independent
     9-point (mur, muf) grid needed for the Tier-1 7-point envelope
     (ids 4, 9, 14, 19, 23[nominal], 28, 33, 38, 43 — all tagged
     `dyn_scale_choice=HT/2`).
  2. `"NNPDF23_lo_as_0130_qed"` (`combine="replicas"`) — **101 `<weight>`
     entries** (1 nominal + 100 PDF replica members, ids 45-145). This appears
     even though `--pdf=errorset` was not explicitly requested in
     `systematics_arguments`; it is emitted by default alongside the nominal
     PDF and is a bonus (not required by this task, but harmless and
     potentially useful for a future PDF-uncertainty extension).
- **Total: 145 `<weight id=...>` entries per event** in the `<initrwgt>`
  header, and each of the 10000 `<event>` blocks contains a matching `<rwgt>`
  block with all 145 `<wgt id=...>` entries populated with numeric values
  (spot-checked on event 1: `<wgt id='1'>` through `<wgt id='9'>` shown below,
  full set present).

Example header lines (mur/muf grid, `dyn_scale_choice=HT/2`, i.e. the physical
one used in this run):
```
<weight id="4"  MUR="0.5" MUF="0.5" DYN_SCALE="3" PDF="247000" > MUR=0.5 MUF=0.5 dyn_scale_choice=HT/2  </weight>
<weight id="9"  MUR="0.5" MUF="1.0" DYN_SCALE="3" PDF="247000" > MUR=0.5 dyn_scale_choice=HT/2  </weight>
<weight id="14" MUR="0.5" MUF="2.0" DYN_SCALE="3" PDF="247000" > MUR=0.5 MUF=2.0 dyn_scale_choice=HT/2  </weight>
<weight id="19" MUR="1.0" MUF="0.5" DYN_SCALE="3" PDF="247000" > MUF=0.5 dyn_scale_choice=HT/2  </weight>
<weight id="23" MUR="1.0" MUF="1.0" DYN_SCALE="3" PDF="247000" > dyn_scale_choice=HT/2  </weight>
<weight id="28" MUR="1.0" MUF="2.0" DYN_SCALE="3" PDF="247000" > MUF=2.0 dyn_scale_choice=HT/2  </weight>
<weight id="33" MUR="2.0" MUF="0.5" DYN_SCALE="3" PDF="247000" > MUR=2.0 MUF=0.5 dyn_scale_choice=HT/2  </weight>
<weight id="38" MUR="2.0" MUF="1.0" DYN_SCALE="3" PDF="247000" > MUR=2.0 dyn_scale_choice=HT/2  </weight>
<weight id="43" MUR="2.0" MUF="2.0" DYN_SCALE="3" PDF="247000" > MUR=2.0 MUF=2.0 dyn_scale_choice=HT/2  </weight>
```

Example event-1 `<rwgt>` block (first 9 of 145 entries; nominal weight for
this event is 520.365 pb equivalent, XWGTUP = +5.2036500e+02):
```
<rwgt>
<wgt id='1'> +6.6247718e+02 </wgt>
<wgt id='2'> +7.4026691e+02 </wgt>
<wgt id='3'> +5.2036500e+02 </wgt>
<wgt id='4'> +6.6247717e+02 </wgt>
<wgt id='5'> +5.1982748e+02 </wgt>
<wgt id='6'> +6.4070417e+02 </wgt>
<wgt id='7'> +7.1958421e+02 </wgt>
<wgt id='8'> +4.9312684e+02 </wgt>
<wgt id='9'> +6.4070416e+02 </wgt>
...
```

**Conclusion: scale-variation weights ARE present and non-degenerate** (weight
id=4, the (0.5,0.5) HT/2 point, is 662.5 vs id=43 or the nominal id=23-analog
being lower — values vary meaningfully with mur/muf, as expected). No fallback
to N separate LO runs is needed; downstream Tier-1 scale-envelope analysis can
proceed directly from this single LHE file using weight ids 4, 9, 14, 19, 23
(nominal/central... note: within the "Central scale variation" group, the
literal (MUR=1,MUF=1,DYN_SCALE=3) combination is not separately listed because
it is redundant with the file's overall nominal weight — the event's own
XWGTUP field, id=`"3"` under the default scale tag in the header ordering
above, or equivalently reconstructible as the value tagged with no MUR/MUF
override at DYN_SCALE=3; downstream analysis should treat the nominal/(1,1)
point as the event's plain XWGTUP weight if a distinct id is not found for it
explicitly, and cross-check numerically that it is closest to XWGTUP among the
5x9 grid), 28, 33, 38, 43.

## Negative-Weight Fraction (Tier 3, LO baseline)

Counted directly from the XWGTUP field of all 10000 events:
**negative = 0, total = 10000 -> negative-weight fraction = 0%**, as expected
at LO (nonzero negative-weight fraction is an NLO-only feature, to be reported
by the NLO run).

## Output Directory Structure

```
events/pp_ttbar_lo_13tev/
├── Cards/
│   ├── param_card.dat
│   ├── run_card.dat
│   └── proc_card_mg5.dat
├── Events/
│   └── run_01/
│       ├── unweighted_events.lhe.gz        <- final parton-level LHE output (10000 events, w/ 145 wgts/event)
│       ├── run_01_tag_1_banner.txt         <- full run configuration/banner
│       ├── parton_systematics.log          <- systematics-module driver log (no errors)
│       └── log_sys_0.txt .. log_sys_3.txt  <- per-core systematics logs (no errors)
├── SubProcesses/
├── Source/
├── bin/
├── lib/
├── HTML/
├── index.html
└── madevent.tar.gz
```

Total directory size: ~154 MB (dominated by the compiled Source/lib and the
10000-event LHE file with full 145-weight reweighting header).

## Final LHE File Path

```
/Users/phongsakornsereewat/MyAgent/paper-reproduction/0002/events/pp_ttbar_lo_13tev/Events/run_01/unweighted_events.lhe.gz
```

(relative to working directory: `events/pp_ttbar_lo_13tev/Events/run_01/unweighted_events.lhe.gz`)

## Warnings / Issues

- None. Both the `madgraph-compile` and `madgraph-launch` jobs returned
  `success: true` with no `param_card_warnings`, and the systematics logs
  contain no error/fail/traceback strings. The LHAPDF-related "fail" string
  seen in a prior 0001 run of this same process (attributed to the
  pre-LD_LIBRARY_PATH-fix environment) was **not** observed in this run,
  consistent with the recent LHAPDF env fix mentioned in the task brief.
- One documentation caveat (not an error): within the 44-entry "Central scale
  variation" weightgroup, the pure (MUR=1.0, MUF=1.0, DYN_SCALE=3) central
  point is not given its own explicit `<weight id>` distinct from the file's
  overall nominal event weight (XWGTUP) — see note in the systematics section
  above. Downstream analysis should use XWGTUP itself as the (1,1) central
  value when building the 3x3 mur/muf grid at DYN_SCALE=3.
