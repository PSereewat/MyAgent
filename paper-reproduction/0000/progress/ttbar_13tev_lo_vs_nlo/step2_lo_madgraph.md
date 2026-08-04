# Step 2 (LO): MadGraph5 Event Generation — pp -> ttbar at 13 TeV (Leading Order)

## Status: SUCCESS

Full-statistics run (100,000 events, no reduction needed) with LO systematics
(scale-reweighting) module enabled, producing a 3x3 mu_R/mu_F envelope at the
requested dynamical scale (HT/2) plus PDF-replica weights as a bonus.

## Overview

Leading-order (pure QCD, tree-level) event generation for $pp \to t\bar{t}$ at
$\sqrt{s} = 13$ TeV, using MadGraph5_aMC@NLO's built-in `sm` model (no UFO import
needed, no `[QCD]` NLO tag). Top quarks are left stable/undecayed in the hard
process (`p p > t t~`, no decay-chain syntax, no MadSpin). No Pythia8 shower, no
Delphes — pure parton-level fixed-order output. Run executed via the Magnus cloud
blueprints `madgraph-compile` and `madgraph-launch`.

## Script

- Documentation script (equivalent standalone MG5 command sequence, for
  reproducibility): `scripts/mg5_ttbar_13TeV_lo.mg5`
  (absolute: `/Users/phongsakornsereewat/ColliderAgenttry/paper-reproduction/0000/scripts/mg5_ttbar_13TeV_lo.mg5`)
- Actual execution: `magnus run madgraph-compile` followed by `magnus run madgraph-launch`.

## Step 1: Compile

```
magnus run madgraph-compile -- \
  --model sm \
  --process "p p > t t~" \
  --output events/lo/pp_ttbar_13TeV_lo
```

- Job ID: `e1de6df7f41f9378`
- Result: `success = true`
- Process directory: `/Users/phongsakornsereewat/ColliderAgenttry/paper-reproduction/0000/events/lo/pp_ttbar_13TeV_lo`

### Default run_card inspection (before overriding)

Inspected the freshly-compiled `Cards/run_card.dat` before launch to get the exact
key names/syntax for this MG5 version:
- `use_syst = True` (already on by default)
- `systematics_program = systematics` (python module, default)
- `systematics_arguments` default: `['--mur=0.5,1,2', '--muf=0.5,1,2', '--pdf=errorset']`
- Default `pdlabel = nn23lo1`, `lhaid = 230000` — overridden below.
- Default `MASS 6 = 173.0 GeV` in `Cards/param_card.dat` — overridden to 172.5 GeV.

## Step 2: Launch

```
magnus run madgraph-launch -- \
  --process events/lo/pp_ttbar_13TeV_lo \
  --commands "done
set nevents 100000
set ebeam1 6500
set ebeam2 6500
set param_card MASS 6 172.5
set pdlabel lhapdf
set lhaid 247000
set dynamical_scale_choice 3
set fixed_ren_scale False
set fixed_fac_scale False
set use_syst True
set systematics_program systematics
set systematics_arguments ['--mur=0.5,1,2', '--muf=0.5,1,2']
done" \
  --output events/lo/pp_ttbar_13TeV_lo
```

- Job ID: `c227c2bd4ab9e307`
- Result: `success = true`
- Run name: `run_01`, tag: `tag_1`
- Cross section (blueprint-reported): `519.9 +- 0.162 pb`
- Banner-reported integrated weight: `519.852 pb` (consistent)
- Ran as a background job (~120s inline timeout exceeded, completed a few minutes
  later); no errors, no failure.

## Settings Used (verified from `run_01_tag_1_banner.txt`)

| Setting | Value |
|---|---|
| Process | `p p > t t~` (LO, no `[QCD]` tag) — top and antitop left stable |
| Model | `sm` (MG5 built-in Standard Model) |
| Collider | $pp$, $\sqrt{s} = 13$ TeV (`ebeam1 = ebeam2 = 6500.0` GeV, verified line 161-162) |
| PDF set | `NNPDF23_lo_as_0130_qed` (`pdlabel = lhapdf`, `lhaid = 247000`, verified line 174-175) |
| Renorm./fact. scale | Dynamic, $\mu_R = \mu_F = H_T/2$ (`dynamical_scale_choice = 3` line 186, `fixed_ren_scale = False` / `fixed_fac_scale = False` line 181-182) |
| Top mass | `MASS 6 = 172.5` GeV (verified banner line 278: `6 1.725000e+02 # mt`) |
| Number of events requested/generated | 100,000 (no reduction needed) |
| Systematics module | `use_syst = True`, `systematics_program = systematics`, `systematics_arguments = ['--mur=0.5,1,2', '--muf=0.5,1,2']` (verified banner lines 263-266) |
| Shower / detector | None (parton-level only, fixed-order) |

## Scale-Reweighting Verification (Tier 1 / Tier 3 requirement)

The LHE `<initrwgt>` header (lines 329-479 of the decompressed file) contains:

- A `"Central scale variation"` `weightgroup` (`combine="envelope"`) with **44**
  `<weight>` entries. These sweep the 3x3 mu_R/mu_F grid `{0.5,1,2}x{0.5,1,2}`
  independently across MadGraph's four preselected dynamical-scale choices
  (`DYN_SCALE="1"` sum-pT, `="2"` HT, `="3"` HT/2, `="4"` sqrt(s)), since the
  systematics module varies all preselected dynamical choices by default even
  though only `--mur`/`--muf` were passed explicitly.
- The subset with `DYN_SCALE="3"` (i.e. matching the run's actual central choice,
  HT/2) contains exactly the 9 combinations needed for the study's 7-point
  envelope: weight ids **4, 9, 14, 19, 23, 28, 33, 38, 43** =
  (MUR,MUF) = (0.5,0.5), (0.5,1), (0.5,2), (1,0.5), (1,1), (1,2), (2,0.5), (2,1), (2,2).
  Downstream analysis should use these 9 ids and drop the two opposite-extreme
  corners (0.5,2)=id14 and (2,0.5)=id33 to form the 7-point envelope.
- A bonus `"NNPDF23_lo_as_0130_qed"` `weightgroup` (`combine="replicas"`) with
  **101** entries (central + 100 replica members) — not required by the task but
  harmless/available for future PDF-uncertainty studies.
- **145 total `<wgt>` entries per event**, confirmed by parsing the first
  `<event>` block's `<rwgt>` section (id 1 through 145). Spot-checked; every
  event carries the same 145-entry `<rwgt>` structure (uniform `<initrwgt>`
  header applies pipeline-wide).

This confirms the systematics/scale-reweighting module ran and stored genuine
per-event variation weights (not just a plain unweighted sample) — the LHE file
does carry multiple `<wgt>` per event as required.

## Top-Quark Stability Verification

Parsed all 100,000 `<event>` blocks. Every event has exactly 4 particles: two
initial-state partons (status `-1`, PDG in `{-4,-3,-2,-1,1,2,3,4,21}` — light
quarks/antiquarks and gluons, as expected for QCD-initiated $t\bar t$ production)
and exactly two final-state particles (status `1`) with PDG codes **6** and
**-6** — the top and antitop directly, with no further decay products (no b
quarks, no leptons, no W bosons in the event record). Sample first event:

```
21 -1   (initial gluon)
21 -1   (initial gluon)
 6  1   (final-state top,     mass 1.7250000000e+02 GeV)
-6  1   (final-state antitop, mass 1.7250000000e+02 GeV)
```

This confirms top quarks are stable/undecayed in the output, as required
(no decay-chain syntax was used at compile time, no MadSpin was enabled).

## Negative-Weight Check (for LO/NLO comparison context)

Spot-checked the first 2,000 events: **0 negative-weight events**, as expected
for a pure tree-level LO calculation (negative weights are an NLO real/virtual
subtraction artifact, not present at LO). This is the expected baseline the
companion NLO run (Step 3) should be compared against.

## Events Generated

- Number of events in LHE file: **100,000** (verified: `grep -c "<event>"` on
  the decompressed file, and by full Python parse of all `<event>...</event>`
  blocks)
- Format: parton-level, unweighted (central weight), LHE (Les Houches Event)
  format, with per-event scale/PDF `<rwgt>` variation weights attached
  (see above)
- `gzip -t` integrity check on `unweighted_events.lhe.gz`: **passed**

## Output Directory Structure

```
events/lo/pp_ttbar_13TeV_lo/
├── Cards/
│   ├── param_card.dat          <- MASS 6 = 172.5 GeV
│   ├── run_card.dat            <- pdlabel=lhapdf, lhaid=247000, dynamical_scale_choice=3,
│   │                               use_syst=True, systematics_arguments=[--mur=..,--muf=..]
│   └── proc_card_mg5.dat
├── Events/
│   └── run_01/
│       ├── unweighted_events.lhe.gz     <- final parton-level LHE output (100,000 events, 103 MB)
│       ├── run_01_tag_1_banner.txt      <- full run configuration/banner
│       ├── log_sys_0.txt ... log_sys_39.txt   <- per-job systematics reweighting logs (40 parallel jobs)
│       └── parton_systematics.log
├── SubProcesses/
├── Source/
├── bin/
├── lib/
├── HTML/
├── index.html
├── crossx.html
└── madevent.tar.gz
```

## Final LHE File Path

```
/Users/phongsakornsereewat/ColliderAgenttry/paper-reproduction/0000/events/lo/pp_ttbar_13TeV_lo/Events/run_01/unweighted_events.lhe.gz
```

## Warnings / Issues

- None. Compile and launch both succeeded on the first attempt (no retries
  needed for this session). `--pdf` flag was not used — `NNPDF23_lo_as_0130_qed`
  (LHAPDF ID 247000) was already available to the LO `pdlabel=lhapdf` / `lhaid`
  mechanism without a separate install step (consistent with prior sessions'
  finding that the container's LHAPDF PDF sets are pre-installed even though
  the `lhapdf-config` CLI binary used by the `--pdf` blueprint flag is not on
  `PATH`).
- No `param_card_warnings` (no duplicate PDG entries) were reported by the
  blueprint.
- The 44-entry scale weightgroup is a superset of the requested 3x3 grid
  (it additionally sweeps the 3 other preselected dynamical-scale choices);
  this is default `systematics` module behavior and is harmless — the required
  9-point (DYN_SCALE=3) subset needed for the 7-point mu_R/mu_F envelope is
  present and identified above by weight id.
