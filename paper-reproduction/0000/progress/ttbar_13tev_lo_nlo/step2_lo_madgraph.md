# Step 2 (LO): MadGraph5 Event Generation — pp -> ttbar at 13 TeV (Leading Order)

## Status: SUCCESS

**RERUN 2026-07-17 (session 5, user request):** re-launched at `nevents=10000` (up from
the task spec's 100) on the same compiled process directory. Job `05b4f3bb63eaf650`,
run `run_02`, cross section 520 ± 0.6095 pb, `events/pp_ttbar_lo_13tev/Events/run_02/
unweighted_events.lhe.gz`. Settings otherwise identical to the `run_01` run documented
below, which remains on disk for reference. See `progress/run_manifest.yaml` and
`step4_analysis.md` for the final combined-analysis results.

## Overview

Leading-order (pure QCD, tree-level) event generation for $pp \to t\bar{t}$ at $\sqrt{s} = 13$ TeV, using
MadGraph5_aMC@NLO's built-in `sm` model (no UFO import needed, no `[QCD]` NLO tag). Run executed via the
Magnus cloud blueprints `madgraph-compile` and `madgraph-launch`.

## Script

- Documentation script (equivalent standalone MG5 command sequence, for reproducibility):
  `/Users/phongsakornsereewat/MyAgent/paper-reproduction/0000/scripts/mg5_ttbar_13TeV_lo.mg5`
- Actual execution: `magnus run madgraph-compile` followed by `magnus run madgraph-launch` (see commands below).

## Step 1: Compile

```
magnus run madgraph-compile -- \
  --model sm \
  --process "p p > t t~" \
  --output events/pp_ttbar_lo_13tev
```

- Job ID: `330389d4a982b933`
- Result: `success = true`
- Process directory: `/Users/phongsakornsereewat/MyAgent/paper-reproduction/0000/events/pp_ttbar_lo_13tev`

## Step 2: Launch

```
magnus run madgraph-launch -- \
  --process events/pp_ttbar_lo_13tev \
  --commands "done
set nevents 100
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

- Job ID: `d0a646023c8b881c`
- Result: `success = true`
- Run name: `run_01`
- Tag: `tag_1`
- Warning reported by blueprint: `'fail' detected in stdout (non-fatal, e.g. LHAPDF systematics)` — non-fatal, standard LHAPDF systematics-weight message; run completed normally with the correct settings (verified below).

### Note on PDF installation

An initial attempt passed `--pdf NNPDF23_lo_as_0130_qed` to trigger download/installation of the LHAPDF set,
but the cloud container's `lhapdf-config` binary was not found on `PATH`
(`FileNotFoundError: [Errno 2] No such file or directory: 'lhapdf-config'`, job `51b15aa43f5dd1ad`, failed).
The set `NNPDF23_lo_as_0130_qed` (LHAPDF ID 247000) turned out to already be pre-installed in the container
(mirroring the NLO sibling set `NNPDF23_nlo_as_0119_qed`, ID 244800, used in the companion NLO run), so the
`--pdf` flag was dropped and `set pdlabel lhapdf` / `set lhaid 247000` alone were sufficient. The re-run
succeeded.

## Settings Used (verified from `run_01_tag_1_banner.txt`)

| Setting | Value |
|---|---|
| Process | `p p > t t~` (LO, no `[QCD]` tag) |
| Model | `sm` (MG5 built-in Standard Model) |
| Collider | $pp$, $\sqrt{s} = 13$ TeV (`ebeam1 = ebeam2 = 6500.0` GeV) |
| PDF set | `NNPDF23_lo_as_0130_qed` (`pdlabel = lhapdf`, `lhaid = 247000`) |
| Renorm./fact. scale | Dynamic, $\mu_R = \mu_F = H_T/2$ (`dynamical_scale_choice = 3`, `fixed_ren_scale = False`, `fixed_fac_scale = False`) |
| Top mass | `MASS 6 = 172.5` GeV (verified in banner: `6 1.725000e+02 # mt`) |
| Top width | `DECAY 6 Auto` (auto-computed: `1.476401` GeV, verified in banner) |
| Number of events requested | 100 (`nevents = 100`) |
| Shower / detector | None (parton-level only) |

## Cross Section

Cross section: 522.3 +- 4.897 pb (reported by the launch blueprint; recorded here purely for run-verification
purposes — per task instructions, no further physics interpretation/analysis of this value is performed at
this step).

## Events Generated

- Number of events in LHE file: **100** (verified by counting `<event>` tags in the decompressed file)
- Format: parton-level, unweighted, LHE (Les Houches Event) format

## Output Directory Structure

```
events/pp_ttbar_lo_13tev/
├── Cards/
│   ├── param_card.dat
│   ├── run_card.dat
│   └── proc_card_mg5.dat
├── Events/
│   └── run_01/
│       ├── unweighted_events.lhe.gz        <- final parton-level LHE output (100 events)
│       └── run_01_tag_1_banner.txt         <- full run configuration/banner
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
/Users/phongsakornsereewat/MyAgent/paper-reproduction/0000/events/pp_ttbar_lo_13tev/Events/run_01/unweighted_events.lhe.gz
```

Verified: `gzip -t` integrity check passed; decompressed file contains exactly 100 `<event>` blocks with
truth-level top/antitop four-momenta (parton-level, no shower/detector applied).

## Warnings / Issues

- Initial `--pdf` download attempt failed due to missing `lhapdf-config` in the cloud container (see note
  above); resolved by relying on the pre-installed PDF set and omitting `--pdf`.
- Blueprint-reported non-fatal warning: `'fail' detected in stdout (non-fatal, e.g. LHAPDF systematics)`.
- No other warnings encountered. No `param_card_warnings` (no duplicate PDG entries) were reported.
