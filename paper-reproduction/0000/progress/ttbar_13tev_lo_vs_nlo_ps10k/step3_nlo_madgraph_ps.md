# Step 3 (incremental) — Pythia8-Showered (MC@NLO) NLO Sample: pp > ttbar @ 13 TeV

Status: **BLOCKED** (Pythia8 parton shower did not actually run; MC@NLO matching was not performed)

## What was requested

Relaunch the existing compiled NLO process directory (`events/nlo/pp_ttbar_13TeV_nlo`, `p p > t t~ [QCD]`, `loop_sm`, no recompile) with `shower=Pythia8` enabled (State 1) and `nevents=10000`, all other settings identical to the original fixed-order run, writing output to `events/nlo/pp_ttbar_13TeV_nlo_ps10k`.

## What actually happened

The `madgraph-launch` blueprint job completed and reported `success: true` at the wrapper level (because the wrapper only checks for a parsed "Results Summary" cross section block, not whether the shower actually ran). However, inspection of the full MG5 stdout log shows the Pythia8 shower **was never executed**:

```
3. Shower the generated events              shower = OFF
...
INFO: will run in mode: noshower
INFO: Your parton-shower choice is not available for running. Events will be
generated for the associated parton shower. Remember that NLO events without
showering are NOT physical.
INFO: modify parameter parton_shower of the run_card.dat to Pythia8
...
INFO: Generating events without running the shower.
...
WARNING: You have chosen not to run a parton shower. NLO events without
showering are NOT physical. Please, shower the Les Houches events before using
them for physics analyses.
```

Despite issuing `shower=Pythia8` exactly per this pipeline's documented syntax (`src/skills/madgraph-nlo-simulator/SKILL.md` and `references/madgraph_reference.md`), and despite `Cards/amcatnlo_configuration.txt` having `pythia8_path = /opt/MG5_aMC_v3_7_0/HEPTools/pythia8` configured, MG5 reported the Pythia8 shower option as "not available for running" and fell back to `noshower` mode — i.e. it generated plain NLO fixed-order LHE events (identical in kind to the original 100k run, just at reduced statistics) and skipped the shower step entirely. This appears to be an environment/infrastructure limitation of the Magnus cloud container's MG5 v3.7.0 installation (the aMC@NLO Pythia8-shower interface is not functional there), not a syntax error in the launch command. A repository-wide search found no prior example anywhere in `paper-reproduction/` of a successfully produced `tag_1_pythia8_events.hepmc.gz` from an NLO run, consistent with this being a persistent limitation rather than a one-off fluke.

**Confirmed: no `tag_1_pythia8_events.hepmc.gz` (or any `*hepmc*`/`*pythia8*` event file) exists anywhere under `events/nlo/pp_ttbar_13TeV_nlo_ps10k/Events/run_02/`.** Directory listing of `Events/run_02/`:
```
.full_summary.txt  RunMaterial.tar.gz  alllogs_0.html  alllogs_1.html  alllogs_2.html
events.lhe.gz  res_0.txt  res_1.txt  res_2.txt  run_02_tag_1_banner.txt  summary.txt
```
No HepMC file. MC@NLO matching to Pythia8 did not occur.

## Failing command

```bash
magnus run madgraph-launch -- \
  --process events/nlo/pp_ttbar_13TeV_nlo \
  --commands "shower=Pythia8
done
set nevents 10000
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
done" \
  --output events/nlo/pp_ttbar_13TeV_nlo_ps10k
```
Magnus job ID: `61a4bc4c7e425d87`. The job itself did not crash (exit code 0, wrapper-level `success: true`, `run_name: run_02`), which is why this failure mode is easy to miss — the actual failure is embedded in the MG5 stdout log, not in the job's return status.

## Byproduct (not the deliverable requested)

A plain fixed-order NLO LHE sample was generated as a side effect (this is NOT MC@NLO-matched / showered, so it does not satisfy the request, but is recorded here for completeness):

| Item | Value |
|---|---|
| Run name | `run_02` |
| Events generated | 10,000 |
| Cross section (integration) | 7.023e+02 +- 4.5e+00 pb |
| Scale envelope (9-point, from LHE) | 6.899e+02 pb +9.7% / -10.7% |
| Negative-weight fraction | 22.92% (2,292 / 10,000 events) — computed directly from `XWGTUP` over the full LHE file |
| Top quarks (PDG 6/-6) | Present, status=1 (stable/undecayed) at LHE level, as expected — but this is parton-level only, not showered |
| LHE file | `events/nlo/pp_ttbar_13TeV_nlo_ps10k/Events/run_02/events.lhe.gz` |
| HepMC file | **absent** — shower did not run |

Note the negative-weight fraction (22.92%) differs somewhat from the original 100k fixed-order run (19.98%); given the ~4x smaller sample here this is consistent with MC statistical fluctuation and does not by itself indicate a problem — but it cannot be attributed to "MC@NLO matching effects" since no matching/showering actually took place in this run either.

## Recommendation

This requires an infrastructure fix (installing/repairing a working Pythia8 shower interface for aMC@NLO in the Magnus cloud MG5 container) before a genuine MC@NLO-matched, Pythia8-showered sample can be produced. No change to the launch command syntax is expected to resolve this, since the documented syntax was used exactly as specified in this pipeline's own skill reference. Flagging for the coordinator/infrastructure owner rather than retrying with a different command.

## Files

- Script: `scripts/mg5_ttbar_13TeV_nlo_ps10k.mg5`
- Output dir (byproduct, unshowered): `events/nlo/pp_ttbar_13TeV_nlo_ps10k`
- LHE file (byproduct, unshowered): `events/nlo/pp_ttbar_13TeV_nlo_ps10k/Events/run_02/events.lhe.gz`
