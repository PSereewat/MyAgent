# Step 2 (NLO): MadGraph5_aMC@NLO Event Generation — pp -> ttbar at 13 TeV (NLO QCD)

## FINAL STATUS (2026-07-17, session 4): SUCCESS

The NLO run completed successfully. **Job `74e2475509b630d1`**, commit `6baf787`.

- **LHE file**: `events/pp_ttbar_nlo_13tev/Events/run_11/events.lhe.gz`
  (verified: `gzip -t` passes, 100 `<event>` blocks, `<init>` block confirms
  `IDWTUP=-4`, `XSECUP=699.9608 pb`, `XERRUP=4.237205 pb`, PDF ID `244800`
  = `NNPDF23_nlo_as_0119_qed`, beam energies `6500.0 + 6500.0` GeV — all
  matching the requested settings).
- **Cross section**: 699.96 ± 4.24 pb (generator-quoted, from MG5's own
  multi-channel integration). Note: the *sample* average of the 100 raw LHE
  weights is 804.99 pb, not 699.96 pb — this is expected small-N sampling
  noise, not a bug (see step4_analysis.md for the explanation: NLO weights
  here take only two discrete magnitudes, ±1149.983 pb, and the realized
  fraction of negative-weight events, 15/100, fluctuates statistically
  around the ~19.6% needed to reproduce 699.96 pb exactly — well within
  1-2σ for N=100 binomial sampling).
- **Negative-weight fraction**: 15% (15/100 events), as expected for NLO.
- **Events generated**: 100/100 requested.

### Root causes found and fixed this session (in order)

The block below ("session 3" and earlier) had correctly fixed two earlier
blockers (Ninja/OneLOop dead URL; broken-symlink archiving; stale
`madgraph-launch` blueprint registry pointer) but left one still open: a
reproducible `handling_lhe_events.f:174: Error: Can't open included file
'./run_card.inc'` failure during MG5's own internal compilation of the NLO
subprocess directories. This session diagnosed and fixed that remaining
issue, in three iterations:

1. **`nb_core=1` (commit `ee1e402`)** — forced fully serial subprocess
   compilation. This *did* avoid the race (no failures observed), but also
   serialized the entire run (compile + survey + integrate + generate), not
   just the compile step, making it impractically slow (killed after ~2hr
   with no completion — likely would have finished eventually, but was not
   a viable fix).
2. **Delayed-`make` wrapper (commits `88cbf4c`, `7ed4176`)** — shadowed
   `make` with a shim that sleeps before delegating to the real `make`,
   hypothesizing a timing race between MG5's file-propagation step and the
   start of parallel compilation. **Instrumented diagnostics disproved this
   hypothesis**: `run_card.inc` was confirmed *missing* in the failing
   subprocess directory (`P0_gg_ttx`) both immediately at wrapper invocation
   and after a full 30s delay, while `Source/` compilation had already
   completed. So it isn't a timing race at all — the propagation step
   itself is simply missing/unreliable in MG5's own orchestration for some
   subprocess directories.
3. **Background run_card.inc sync thread (commits `d2f252c`, `6baf787`,
   `960468a`) — THE ACTUAL FIX.** A daemon thread polls every 50ms for the
   canonical `run_card.inc` (first found under `Source/` or
   `SubProcesses/`) and proactively copies it into every `SubProcesses/P*/`
   subdirectory that doesn't have it yet, plus `SubProcesses/` itself (a
   later "collect_events" step compiles `collect_events.f` /
   `handling_lhe_events.f` directly there, not inside a `P*/` subdir — this
   required a second iteration, commit `6baf787`, after the first version
   fixed the original 3-subprocess race but hit this next narrow gap).
   `nb_core` was restored to the full core count (`960468a`'s commit
   message and `d2f252c` explain over-parallelization was never actually
   the cause). A separate latent bug was also found and fixed in the same
   session (commit `960468a`): `_parse_results_summary` only recognized
   the LO madevent "Results Summary for run: ... tag: ..." format, so the
   first fully-successful NLO run (this one) was initially misreported as
   `"success": false` ("MG5 reported 'fail' in stdout") purely due to a
   result-parsing gap, not an actual failure — fixed by adding patterns for
   aMC@NLO's distinct "Summary: ... Total cross section: ... / Number of
   events generated: ..." block.

See `scripts/run_madgraph_launch.py` (`_start_run_card_sync_thread`,
`_is_nlo_process_dir`, `_parse_results_summary`) for the final implementation.

Total launch attempts across all sessions before success: 12 (job IDs
`6d4a546671c9bba6`, `25585e62a2555da7`, `702e64b65e1f337c`,
`26f11984255ee767`, `3cc2f63a6d7f4730`, `291863fa141d2b2b`,
`09fb72b4fb1289ac`, `abfa5d749eb4ff17` [killed, nb_core=1], `1eea4dd43fdef845`
[delayed-make wrapper, failed], `4f87505c59838819` [instrumented delayed-make,
failed, gave the key diagnostic evidence], `bdb6bbdd7f763a5a` [sync thread v1,
got much further — reached "Collecting events" — but hit the
`SubProcesses/`-itself gap], `74e2475509b630d1` [sync thread v2, **SUCCESS**]).

---

## STATUS AS OF 2026-07-17 (session 3, retry after blueprint-registry fix): STILL BLOCKED — NEW ROOT CAUSE IDENTIFIED (historical — superseded above)

**The blueprint-registry misconfiguration flagged as the root cause after session 2 has now been
CONFIRMED FIXED**: `magnus blueprint get madgraph-launch` now shows
`namespace="PSereewat"`, `repo_name="MyAgent"` (`updated_at: 2026-07-17T11:18:15.126688`), and 3
consecutive launch retries this session (job IDs `3cc2f63a6d7f4730`, `291863fa141d2b2b`,
`09fb72b4fb1289ac`) each had their own job log inspected and each confirmed the FIXED script ran:
```
CPU cores (sched_getaffinity, capped): 10
set nb_core 10
```
(not the old uncapped `192`). So both previously-diagnosed issues — the `nb_core` over-subscription
code fix AND the stale blueprint-registry pointer — are now both genuinely confirmed fixed and in
effect.

**Despite this, all 3 retries this session failed again with the IDENTICAL
`handling_lhe_events.f:174: Error: Can't open included file './run_card.inc'` race**, now during
`Compiling on 10 cores` (not 192). This is a **new finding**: capping `nb_core` to 10 does NOT
eliminate the race. It is not merely a function of core-count over-subscription; the race persists
even at the modest, declared-quota-matched parallelism of 3 subprocess directories x 10 cores. Victim
subprocess varied non-deterministically across the 3 retries this session (`P0_uux_ttx`,
`P0_uux_ttx`, `P0_gg_ttx`), consistent with a genuine timing race in MG5's own internal
`compile_dir`/multiprocessing logic for parallel-compiling the 3 NLO subprocess directories
(`P0_gg_ttx`, `P0_uux_ttx`, `P0_uxu_ttx`), rather than anything specific to the over-subscribed core
count. This looks like a bug/fragility internal to the MG5_aMC_v3_7_0 installation's parallel
`Source/run_card.inc` generation + per-subprocess-directory propagation, not something fixable from
`scripts/run_madgraph_launch.py` alone. See "Session 3" section below for full details, job IDs, and
brief code-path investigation (Source/makefile rule `run_card.inc: ../Cards/run_card.dat`; each
subprocess dir's `handling_lhe_events.f` does `include './run_card.inc'`, and MG5 Python-side compile
orchestration must symlink/copy the regenerated file into each `P0_*` subprocess directory before
invoking `make` in parallel — this synchronization step appears to be racy).

**No further retries were attempted after 3/3 failures this session (per the 2-3 attempt cap in
task instructions). Total failures across all sessions: 7 (4 prior + 3 this session), all with the
identical error signature, now confirmed independent of both previously-suspected causes.**

---

## Session 3 detail (2026-07-17, this retry) — full job log evidence

Process directory reused (not recompiled): `events/pp_ttbar_nlo_13tev` (from compile job
`90094d080d1f05e6`, model `loop_sm`, process `p p > t t~ [QCD]`).

Launch command used (identical all 3 attempts):
```
magnus run madgraph-launch -- \
  --process events/pp_ttbar_nlo_13tev \
  --commands "done
set nevents 100
set ebeam1 6500
set ebeam2 6500
set pdlabel lhapdf
set lhaid 244800
set dynamical_scale_choice 3
set fixed_ren_scale False
set fixed_fac_scale False
set req_acc_FO -1
set param_card MASS 6 172.5
set param_card DECAY 6 Auto
done" \
  --output events/pp_ttbar_nlo_13tev
```

| Attempt | Job ID | `capped` core count confirmed in log? | Victim subprocess | Result |
|---|---|---|---|---|
| 1 | `3cc2f63a6d7f4730` | Yes (`capped: 10`, `set nb_core 10`) | `P0_uux_ttx` | FAILED (run_card.inc race) |
| 2 | `291863fa141d2b2b` | Yes (`capped: 10`, `set nb_core 10`) | `P0_uux_ttx` | FAILED (run_card.inc race) |
| 3 | `09fb72b4fb1289ac` | Yes (`capped: 10`, `set nb_core 10`) | `P0_gg_ttx` | FAILED (run_card.inc race) |

Representative error (identical across all 3, only victim subprocess name differs):
```
gfortran -O -ffixed-line-length-132 -fno-automatic -c -I. -I.../lib/ handling_lhe_events.f
handling_lhe_events.f:174: Error: Can't open included file './run_card.inc'
make: *** [makefile:105: handling_lhe_events.o] Error 1
```
All 3 attempts reached `Compiling directories... / Compiling on 10 cores` before failing (i.e. the
survey step, `compute_widths 6`, and all `set` parameter commands succeeded first, same as session
2).

**No LHE file was produced. No cross section was obtained. No negative-weight fraction available.**
The `events/pp_ttbar_nlo_13tev/Events/run_0{5,6,7}/` directories contain only debug logs from these
3 failed attempts (`run_05_tag_1_debug.log`, `run_06_tag_1_debug.log`, `run_07_tag_1_debug.log`), no
`unweighted_events.lhe.gz`.

**Recommended next steps (outside this agent's scope — requires MG5 installation/container-level
investigation, not a `scripts/run_madgraph_launch.py` fix):**
- Investigate whether this is a known upstream MG5_aMC@NLO bug (check launchpad bug tracker for
  `handling_lhe_events.f` + `run_card.inc` + parallel compile).
- Try forcing serial subprocess compilation (`nb_core 1`) as a diagnostic (would confirm the race is
  concurrency-related at all, even at low N) — not attempted this session since `nb_core` cannot be
  overridden via `--commands` (only via the launch script's hardcoded pre-`launch` `set nb_core`
  line, which the blueprint does not currently expose as a parameter).
- Consider a container-image-level fix/upgrade to the MG5_aMC@NLO version, or a script-level
  workaround that pre-touches/symlinks `run_card.inc` into each `SubProcesses/P0_*` directory before
  invoking `launch`, if this is confirmed to be a known synchronization bug in MG5's own
  `compile_dir` Pool-based parallelization.

---

## Prior status (session 2, earlier 2026-07-17): STILL BLOCKED

**Root cause #3 (run_card.inc parallel-compile race) is NOT actually fixed yet from the operator's
perspective, even though the code fix (`nb_core = min(len(os.sched_getaffinity(0)), 10)`) IS present
and correct in `scripts/run_madgraph_launch.py` on `origin/main` of `PSereewat/MyAgent` (confirmed
commit `1464c94`, local checkout fully in sync with origin/main).**

**Definitive diagnosis: the `madgraph-launch` Magnus blueprint registry entry still points to the
stale repo `namespace="HET-AGI"`, `repo_name="ColliderAgent"` (confirmed via `magnus blueprint get
madgraph-launch`, `updated_at: 2026-07-17T07:48:51.990320`), which does NOT contain the `nb_core`
cap fix. Unlike `madgraph-compile` (already correctly repointed to `namespace="PSereewat"`,
`repo_name="MyAgent"`, confirmed via `magnus blueprint get madgraph-compile`), `madgraph-launch` was
never repointed.** This session's retry (launch job `26f11984255ee767`) reproduced the identical
`run_card.inc` race failure a 4th time, and — per the explicit diagnostic check requested for this
retry — the job's own log (`magnus job logs 26f11984255ee767`) was inspected and shows the OLD,
uncapped print statement:
```
CPU cores (sched_getaffinity): 192
================ MG5 Launch Script ================
set nb_core 192
launch process_output
...
```
NOT the new fix's expected `CPU cores (sched_getaffinity, capped): 10`. This conclusively proves the
job executed the stale/unfixed script from `HET-AGI/ColliderAgent`, not the fixed
`PSereewat/MyAgent` version — confirming the previously-flagged "secondary observation" (stale
blueprint pointer) is in fact the **actual remaining root cause** of this block, not merely a
non-causal hygiene issue as previously (incorrectly) assessed.

**Failure signature this session (job `26f11984255ee767`, victim `P0_gg_ttx` this time, 4th distinct
victim across 4 attempts — `P0_uxu_ttx`, `P0_uux_ttx`, `P0_gg_ttx`, `P0_gg_ttx` again — consistent
with the same timing race):**
```
gfortran -O -ffixed-line-length-132 -fno-automatic -c -I. -I.../lib/ handling_lhe_events.f
handling_lhe_events.f:174: Error: Can't open included file './run_card.inc'
make: *** [makefile:105: handling_lhe_events.o] Error 1
```

**No further retries were attempted this session** (per instruction to investigate and report rather
than retry blindly beyond 2-3 attempts; only 1 retry was needed to obtain the conclusive log
evidence above). No LHE file exists; no cross section obtained. Run 1 (LO) remains complete and
unaffected.

**Required remediation (infra/blueprint-registry access, still out of this agent's scope): update
the `madgraph-launch` Magnus blueprint registry entry's `namespace`/`repo_name` from
`HET-AGI`/`ColliderAgent` to `PSereewat`/`MyAgent` (matching the already-corrected
`madgraph-compile` entry), so that the job pulls `scripts/run_madgraph_launch.py` containing the
`nb_core` cap fix (commit `1464c94`). The code-level fix itself has been re-verified present and
correct; it simply is not being picked up because the blueprint points at the wrong source repo.**

---

## Prior session history (2026-07-17, earlier in the day) — preserved for context

### Status at that time: PARTIALLY BLOCKED — compile succeeded (root causes #1/#2 confirmed fixed); launch
failed on a NEW, distinct issue: a reproducible race condition in MG5's parallel NLO subprocess
compilation.

## Overview

This session (2026-07-17) retried the compile+launch sequence for $pp \to t\bar{t}$ [QCD] at
$\sqrt{s} = 13$ TeV using MadGraph5_aMC@NLO's `loop_sm` model, via the Magnus cloud blueprints
`madgraph-compile` and `madgraph-launch`. This is compile attempt #6 overall / launch attempt
#1-3 (launch had never previously been reached).

**Good news: Step 1 (Compile) now succeeds.** The `madgraph-compile` blueprint registry was
confirmed correctly pointed at `namespace="PSereewat"`, `repo_name="MyAgent"`, `commit_sha="HEAD"`
(`updated_at: 2026-07-17T09:01:16.376330`) before this session's attempt, and the job's own
reported script (recovered from job logs) confirmed both fixes are present and active:
```
set nb_core 192
set ninja None
set OLP MadLoop
import model loop_sm
generate p p > t t~ [QCD]
output process_output
```
Compilation completed successfully with no Ninja/OneLOop install attempt and no broken-symlink
archiving crash.

**Bad news: Step 3 (Launch) now fails on a new, previously-unseen issue** — a Fortran compilation
race condition during MG5's own internal parallel build of the NLO subprocess directories, unrelated
to both previously-documented root causes.

## Step 1: Compile — SUCCESS

```
magnus run madgraph-compile -- \
  --model loop_sm \
  --process "p p > t t~ [QCD]" \
  --output events/pp_ttbar_nlo_13tev
```

- **Job ID: `90094d080d1f05e6`**
- Result: `success = true`, `"message": "Process compiled successfully."`
- `process_dir`: `events/pp_ttbar_nlo_13tev`
- Verified locally: `events/pp_ttbar_nlo_13tev/` contains `Cards/`, `Events/`, `SubProcesses/`,
  `Source/`, `bin/`, `amcatnlo.tar.gz`, etc. — a normal compiled aMC@NLO process directory.
- Verified from job logs that the executed script (`magnus job logs 90094d080d1f05e6`) matches the
  current `MyAgent` repo's `scripts/run_madgraph_compile.py` exactly, including the `set ninja None`
  / `set OLP MadLoop` guard lines for `[QCD]`-tagged processes. No Ninja/OneLOop install was
  attempted; MG5 proceeded directly to model import, diagram generation ("Generated 9 subprocesses
  ... 11 born diagrams and 124 virtual diagrams" — matches attempt-5's diagram count), and `output`.
- **Root cause #1 (Ninja/OneLOop dead-URL) — CONFIRMED FIXED, no longer regressed.**
- **Root cause #2 (broken-symlink archiving crash) — not directly exercised as a failure this
  session (no crash occurred), consistent with the fix being present.**

## Step 2: Launch — FAILED (new issue, 3/3 attempts)

Command used (all 3 attempts identical except where noted):
```
magnus run madgraph-launch -- \
  --process events/pp_ttbar_nlo_13tev \
  --commands "done
set nevents 100
set ebeam1 6500
set ebeam2 6500
set pdlabel lhapdf
set lhaid 244800
set dynamical_scale_choice 3
set fixed_ren_scale False
set fixed_fac_scale False
set req_acc_FO -1
set param_card MASS 6 172.5
set param_card DECAY 6 Auto
done" \
  --output events/pp_ttbar_nlo_13tev
```

### Attempt 1 — Job ID `6d4a546671c9bba6`
- `success = false`
- MG5 log: `set nb_core 192` (auto-detected via `os.sched_getaffinity(0)` inside the container),
  then `launch process_output` proceeds through param setting, `compute_widths 6` (top width
  auto-computation succeeds), survey, `Combining Events`, `Compiling directories...`,
  `Compiling on 192 cores`, compiling `P0_gg_ttx`, `P0_uux_ttx`, `P0_uxu_ttx` in parallel.
- Failure: `A compilation Error occurs when trying to compile
  .../SubProcesses/P0_uxu_ttx`:
  ```
  gfortran -O -ffixed-line-length-132 -fno-automatic -c -I. -I.../lib/ handling_lhe_events.f
  handling_lhe_events.f:174: Error: Can't open included file './run_card.inc'
  make: *** [makefile:105: handling_lhe_events.o] Error 1
  ```

### Attempt 2 — Job ID `25585e62a2555da7`
- Added `set nb_core 8` as the first line of `--commands` (after the initial `done`), hypothesizing
  the failure is a parallel-compilation race exacerbated by the very high auto-detected core count
  (192) exceeding the blueprint's declared job `cpu_count=10`.
- **`set nb_core 8` was rejected**: `WARNING: invalid set command nb_core 8` — `nb_core` can only be
  set via the top-level `set nb_core N` line injected *before* `launch` is invoked (by
  `scripts/run_madgraph_launch.py`, which hardcodes `nb_core = len(os.sched_getaffinity(0))` with no
  override), not from within the post-`launch` interactive parameter-setting session used for
  `--commands`. The run therefore still compiled with 192 cores.
- Same failure signature, different victim: `SubProcesses/P0_uux_ttx` (not `P0_uxu_ttx`) failed with
  the identical `Can't open included file './run_card.inc'` error at the identical source line
  (`handling_lhe_events.f:174`).

### Attempt 3 — Job ID `702e64b65e1f337c`
- Plain retry (no `--commands` modification), to check whether the race is non-deterministic and
  might succeed on a bare retry.
- Same failure signature again, third different victim: `SubProcesses/P0_gg_ttx` failed with the
  identical `Can't open included file './run_card.inc'` error at the identical source line.

### Diagnosis

This is a **reproducible race condition** in MG5_aMC@NLO's parallel compilation of NLO subprocess
directories (`P0_gg_ttx`, `P0_uux_ttx`, `P0_uxu_ttx` — all 3 subprocesses for this process), NOT
either of the two previously-documented root causes (Ninja/OneLOop dead URL; broken-symlink
archiving). Evidence:

- 3/3 launch attempts failed at the identical point (`Compiling directories...` /
  `Compiling on 192 cores`) with the identical error (`handling_lhe_events.f:174: Can't open
  included file './run_card.inc'`), but a **different** one of the 3 subprocess directories was the
  victim each time (`P0_uxu_ttx`, `P0_uux_ttx`, `P0_gg_ttx` respectively) — consistent with a timing
  race rather than a deterministic bug tied to a specific subprocess.
- `run_card.inc` is a per-subprocess-directory generated include file (regenerated from the
  just-modified `run_card.dat` after the `set ...` commands and `compute_widths` step, right before
  `Compiling directories...`). With all 3 subprocess directories' `make` invocations launched
  simultaneously across 192 requested cores, it appears the generation/propagation of
  `run_card.inc` into each subprocess directory is not properly synchronized before `gfortran`
  attempts to compile `handling_lhe_events.f` (which `include`s it) in at least one directory.
- The blueprint job spec declares `cpu_count=10` (see `magnus blueprint get madgraph-launch`), but
  the container reports `os.sched_getaffinity(0) = 192` cores, i.e. `nb_core` is set far higher than
  the actual CPU quota allocated to the job. This mismatch (192-way parallel `make`/`gfortran`
  invocations contending for effectively ~10 real cores) plausibly extends I/O/scheduling latency
  enough to trigger the race, though this has not been proven as the exact mechanism.
- `nb_core` cannot be overridden from the `--commands` string passed to the `madgraph-launch`
  blueprint: the value is fixed by `scripts/run_madgraph_launch.py`'s
  `nb_core = len(os.sched_getaffinity(0))` (no CLI override), injected as `set nb_core N` *before*
  `launch` starts. A `set nb_core N` command placed inside `--commands` (i.e. during the post-launch
  interactive parameter session) is rejected as an "invalid set command" in that context.
- **This is not the same issue as root causes #1/#2.** It occurs strictly after a fully successful
  `output`/compile step, during MG5's own internal build of the downloaded process directory at
  `launch` time, and is unrelated to Ninja/OneLOop or symlink archiving.

### Secondary observation (not confirmed as causal, but worth flagging)

`magnus blueprint get madgraph-launch` shows the registry entry still points at
`namespace="HET-AGI"`, `repo_name="ColliderAgent"` (`updated_at: 2026-07-17T07:48:51.990320`) — the
same stale-repo pattern (and near-identical timestamp) previously found and fixed for
`madgraph-compile` (now correctly `PSereewat/MyAgent`, `updated_at: 2026-07-17T09:01:16`). The
`madgraph-launch` blueprint was apparently never corrected. However, comparing the job's own printed
script (`set nb_core 192\nlaunch process_output\ndone\n...`) against the local/`origin/main`
`MyAgent` repo's `scripts/run_madgraph_launch.py` shows **identical logic** — both hardcode
`nb_core = len(os.sched_getaffinity(0))` with no cap — so this stale pointer does **not** appear to
be the direct cause of the race condition observed here (the `MyAgent` version would behave the same
way). It is flagged here as a genuine inconsistency that should still be corrected for
maintainability/consistency, but is not believed to explain this specific failure.

### Not attempted (out of scope for this agent)

Per task scope (report new failure modes rather than apply further live infra/script changes), no
attempt was made to:
- Modify `scripts/run_madgraph_launch.py` to cap `nb_core` (e.g. to match the declared `cpu_count`),
  which would very plausibly fix this race.
- Re-save the `madgraph-launch` blueprint registry entry to point at `PSereewat/MyAgent` (even though
  this alone would likely not fix the race, per the analysis above).
- Manually patch the downloaded process directory / retry via `--interactive` mode with a smaller
  scope.

**Required remediation** (for whoever has script/infra access): cap `nb_core` in
`scripts/run_madgraph_launch.py` (e.g. `nb_core = min(len(os.sched_getaffinity(0)), <declared
cpu_count>)` or a fixed conservative value such as 8-10) to eliminate the 192-way over-subscription
that appears to trigger this `run_card.inc` race during NLO subprocess compilation. Also recommended
(lower priority, not confirmed causal): re-save the `madgraph-launch` blueprint registry to point at
`namespace="PSereewat"`, `repo_name="MyAgent"` for consistency with `madgraph-compile`.

## Cross Section

Not obtained (all 3 launch attempts failed during subprocess compilation, before any survey/event
generation with the final settings could run to completion — the `Combining Events` / `fail to reach
target 10000` / width-computation lines seen in the logs are from MG5's automatic
`compute_widths 6` sub-run, NOT the actual physics process cross-section).

## Events Generated

None. No LHE file exists at `events/pp_ttbar_nlo_13tev/Events/run_01/unweighted_events.lhe.gz` (or
any other run name) as of this session.

## Job IDs (prior session, earlier 2026-07-17)

| Step | Attempt | Job ID | Result |
|---|---|---|---|
| Compile | 1 (session attempt #6 overall) | `90094d080d1f05e6` | SUCCESS |
| Launch | 1 | `6d4a546671c9bba6` | FAILED (run_card.inc race, victim P0_uxu_ttx) |
| Launch | 2 (added invalid `set nb_core 8`) | `25585e62a2555da7` | FAILED (run_card.inc race, victim P0_uux_ttx) |
| Launch | 3 (plain retry) | `702e64b65e1f337c` | FAILED (run_card.inc race, victim P0_gg_ttx) |

## Job IDs (this later session — retry after nb_core fix pushed to origin/main)

| Step | Attempt | Job ID | Result |
|---|---|---|---|
| Launch | 4 (retry after fix confirmed on `origin/main` commit `1464c94`) | `26f11984255ee767` | FAILED (run_card.inc race, victim P0_gg_ttx) — job log proves the OLD unfixed script ran (`CPU cores (sched_getaffinity): 192`, not the new `..., capped): 10`), because the `madgraph-launch` blueprint registry still points to stale `HET-AGI/ColliderAgent`, not `PSereewat/MyAgent` |

**Conclusion: this is not a code bug that needs another fix — the existing fix is correct — it is a
blueprint-registry misconfiguration (wrong source repo pinned) that needs to be corrected by someone
with `magnus blueprint` write access before another launch retry can succeed.**

## Settings (intended, per paper doc / reference script — confirmed applied up to the point of
failure via job logs, i.e. all `set` commands for run_card/param_card were accepted by MG5 before
the compilation race occurred)

| Setting | Intended Value | Confirmed applied in logs? |
|---|---|---|
| Process | `p p > t t~ [QCD]` (NLO QCD) | Yes (compile + launch both show this) |
| Model | `loop_sm` | Yes |
| Collider | $pp$, $\sqrt{s} = 13$ TeV (`ebeam1 = ebeam2 = 6500` GeV) | Yes (`modify parameter ebeam1 ... to 6500.0`, same for ebeam2) |
| PDF set | `NNPDF23_nlo_as_0119_qed` (`pdlabel = lhapdf`, `lhaid = 244800`) | Yes (`modify parameter pdlabel ... to lhapdf`, `lhaid ... to [244800]`) |
| Renorm./fact. scale | Dynamic, $\mu_R = \mu_F = H_T/2$ | Yes (`dynamical_scale_choice ... to [3]`, `fixed_ren_scale ... to False`, `fixed_fac_scale ... to False`) |
| Fixed-order accuracy | `req_acc_FO = -1` | Yes (`modify parameter req_acc_fo ... to -1.0`) |
| Top mass | `MASS 6 = 172.5` GeV | Yes (`modify param_card information BLOCK mass with id (6,) set to 172.5`) |
| Top width | `DECAY 6 Auto` | Yes (`modify param_card information BLOCK decay with id (6,) set to Auto`; automatic width computation ran successfully, `compute_widths 6` completed with "Done") |
| Number of events requested | 100 | Yes (`modify parameter nevents ... to 100`) |
| Reduction library | Ninja disabled at compile time (`set ninja None`), `OLP MadLoop` | Confirmed at compile time; not directly re-verified at launch time (irrelevant to this failure, which occurs before matrix-element evaluation begins) |

None of these settings are believed to be the cause of the launch failure — the failure occurs
during MG5's generic Fortran build step (subprocess directory compilation), before any
physics-specific integration/evaluation begins.

## Output Directory Structure

`events/pp_ttbar_nlo_13tev/` exists locally (from the successful compile + partial launch
uploads), containing the standard aMC@NLO process directory layout (`Cards/`, `Events/`,
`SubProcesses/`, `Source/`, `bin/`, etc.) plus partial build artifacts from the 3 failed launch
attempts (e.g. debug logs `run_01_tag_1_debug.log`, `run_02_tag_1_debug.log`,
`run_03_tag_1_debug.log` inside the process directory, one per failed attempt). No `Events/run_*/`
subdirectory with actual generated events exists.

## Final LHE File Path

Not applicable — file does not exist.

## Negative-weight fraction

Not applicable — no events were generated.

## Warnings / Issues

- **Root causes #1 (Ninja/OneLOop dead URL) and #2 (broken-symlink archiving crash) are CONFIRMED
  FIXED** as of this session — compile succeeded cleanly, matching the expected script content.
- **New issue (root cause #3, this session): reproducible `run_card.inc` race condition** in MG5's
  parallel NLO subprocess compilation, occurring in 3/3 launch attempts, with a different victim
  subprocess directory each time. Blocked on this issue as of this session. See "Diagnosis" section
  above for full analysis and recommended remediation (cap `nb_core` in
  `scripts/run_madgraph_launch.py`).
- Secondary (non-causal, flagged for hygiene): `madgraph-launch` blueprint registry still points at
  stale `namespace="HET-AGI"`, `repo_name="ColliderAgent"` (unlike the already-corrected
  `madgraph-compile` registry entry). Recommended to re-save for consistency, though this does not
  appear to explain the observed failure.
- Run 1 (LO) remains unaffected and complete
  (`events/pp_ttbar_lo_13tev/Events/run_01/unweighted_events.lhe.gz`, 100 unweighted events,
  cross section 522.309 pb), since it uses the plain tree-level `sm` model (no MadLoop, no NLO
  subprocess parallel-compile path at all).

## Downstream Note

Run 2 (NLO) still has not completed. The paper's LO-vs-NLO $d\sigma/d\Delta\phi_{t\bar t}$ comparison
cannot currently proceed to the NLO half. The LO half (Run 1) remains valid and complete. Downstream
analysis agents should be informed that only the LO distribution is available until this step is
re-run successfully after `scripts/run_madgraph_launch.py`'s `nb_core` over-subscription issue is
fixed by someone with script/infra access (capping `nb_core` to a value consistent with the job's
actual CPU allocation, e.g. `cpu_count=10`, should eliminate the `run_card.inc` race observed in all
3 attempts this session).
