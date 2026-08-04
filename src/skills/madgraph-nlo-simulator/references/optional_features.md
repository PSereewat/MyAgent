# Optional Features

This document describes optional features that can be applied between `madgraph-compile` (Step 1) and `madgraph-launch` (Step 2). Only apply these when the user explicitly requests them.

---

## Enable LHCO Output

**When to use**: The user requests LHCO-format event files.

**Prerequisite**: `detector=Delphes` must be set in the launch commands. LHCO output is a Delphes feature.

**What to do**: After `madgraph-compile` downloads the compiled process directory, uncomment the `root2lhco` section (lines 48–58) in `<process_dir>/bin/internal/run_delphes3`. This section is commented out by default; uncommenting it tells Delphes to convert the ROOT output to LHCO format during event generation.

```bash
# Use sed to uncomment lines 48-58 in run_delphes3
sed -i '' '48,58 s/^#//' path/to/pp_ttbar/bin/internal/run_delphes3
```

**Output**: The launch step will produce `tag_1_delphes_events.lhco.gz` in `Events/run_XX/` alongside the ROOT file.

---

## Enable MadSpin Decays

**When to use**: The user wants spin-correlated decays of unstable resonances (top, W, Z, BSM particles) applied **after** the hard event is generated, without baking the decay chain into the `generate` line at compile time. MadSpin preserves angular correlations that a flat narrow-width treatment would lose, and lets you swap or rerun decay topologies without recompiling the process.

Prefer MadSpin over decay-chain syntax in `--process` when:
- You expect to vary or scan the decay final state (e.g. dileptonic vs. semileptonic top decays) on top of one compiled process.
- Spin correlations matter for the analysis (e.g. top polarization, anomalous couplings).
- The decay width is small enough that the narrow-width approximation is reasonable (`onshell` / `none` modes) or you explicitly want off-shell effects via `full`.

**How to enable**: this is configured entirely through `--commands`; no file edits are needed.

1. In **State 1** (before the first `done`), add the switch:
   ```
   madspin=ON
   ```
   This is mandatory. Without it, any `set spinmode` / `decay` lines in State 2 are dispatched to a card that MadSpin never reads, and MadSpin is silently skipped.
2. In **State 2** (between the two `done`s), specify the spin-correlation mode and one `decay` line per unstable particle:
   ```
   set spinmode onshell
   decay t > b l+ vl
   decay t~ > b~ l- vl~
   ```

**Multi-step / cascade decays**: chain them inside a single `decay` line with commas, the same syntax as MG5 process decay chains. For example:
```
decay t > b w+, w+ > l+ vl
decay t~ > b~ w-, w- > l- vl~
```
Each `decay` line targets one mother particle (by PDG label, e.g. `t`, `t~`, `w+`, `z`, `h`); cascades go inside that line.

**`spinmode` options**:

| `spinmode` value | Meaning |
|------------------|---------|
| `none` | No spin correlations. Fastest; equivalent to flat isotropic decay in the rest frame. Use only when correlations are known to be irrelevant. |
| `onshell` | Spin-correlated decays in the narrow-width approximation (resonances strictly on-shell). Default and recommended for narrow resonances like top, W, Z. |
| `full` | Spin-correlated decays including off-shell / finite-width effects. Slower and statistically less efficient; use when off-shell tails matter. |

**CRITICAL: silent failure modes.** MadSpin has two ways to be silently skipped while the job still reports `success=true`:
- **Forgot `madspin=ON` in State 1**: the State 2 `set spinmode` / `decay` lines look syntactically valid and are accepted by the run-card editor, but no MadSpin step runs. You will get the original undecayed `unweighted_events.lhe.gz` only — no `run_XX_decayed_1/` directory.
- **Put `decay` lines after the second `done`**: MG5 has already launched; the `decay` lines fall through to the master prompt and are swallowed as unknown commands. Same symptom: no `run_XX_decayed_1/` directory.

Always verify after the run that `Events/run_XX_decayed_1/` exists. If it does not, MadSpin did not run.

**Output**: when MadSpin runs successfully, decayed events are written to a sibling directory next to the original run:
- `Events/run_XX_decayed_1/unweighted_events.lhe.gz` — MadSpin-decayed LHE events (the file Pythia8 and Delphes consume downstream).
- `Events/run_XX_decayed_1/tag_1_pythia8_events.hepmc.gz` — if Pythia8 is enabled.
- `Events/run_XX_decayed_1/tag_1_delphes_events.root` — if Delphes is enabled.

The original undecayed events remain at `Events/run_XX/unweighted_events.lhe.gz` for reference.

---

## Enable Scale/PDF Uncertainty (Systematics)

**When to use**: The user wants an estimate of the renormalization/factorization scale (μ_R/μ_F) uncertainty and/or PDF uncertainty on the cross section, computed from a **single** run — no separate rerun at shifted scales or with alternate PDF sets is needed. aMC@NLO reweights every generated event to the requested scale/PDF variations internally and writes the extra weights into the LHE file.

Verified against this pipeline's actual installed MG5 version (v3.7.0): the real run_card keys are `reweight_scale` / `rw_rscale` / `rw_fscale` for scale variation and `reweight_PDF` for PDF variation — **not** `systematics_program`/`systematics_arguments` (that key does not exist in this version's NLO `run_card.dat`; it belongs to the LO `madevent` systematics module, a different mechanism).

**How to enable**: this is configured entirely through `--commands` (State 2, between the two `done`s); no State-1 switch and no file edits are needed.

```
set reweight_scale True
set rw_rscale 1.0, 2.0, 0.5
set rw_fscale 1.0, 2.0, 0.5
set reweight_PDF True
set lhaid 244800
set store_rwgt_info True
```

- `reweight_scale` is actually `True` **by default** in the run_card template, with `rw_rscale`/`rw_fscale` defaulting to `1.0, 2.0, 0.5` — scale variation is effectively always on unless explicitly disabled. Set it explicitly anyway for clarity.
- `reweight_PDF` is `False` by default. Turning it on reweights every event against the other members of the PDF set named by `lhaid` (an NNPDF-style set with replicas/eigenvectors, e.g. `244800` = NNPDF23_nlo_as_0119_qed, 101 members) to get the PDF envelope. No separate `--pdf` install is needed if the set is already pre-installed (see `lhaid` note in the main workflow section).
- `store_rwgt_info` stores the underlying reweight info in the LHE file for later off-line reweighting; not required for the scale/PDF envelope itself but harmless to enable alongside it.

**CRITICAL: the printed envelope summary requires `nevents >= 10000`.** MG5 gates the human-readable "Scale variation" / "PDF variation" summary block in `summary.txt` on `self.run_card['nevents'] >= 10000` (fixed-order mode is exempt from this gate). Below that threshold:
- The reweighting still runs and every event's LHE `<rwgt>` block still carries the full set of scale/PDF weights (confirmed: 128 `<wgt>` entries/event at `nevents=100` — 27 for scale, 101 for PDF — identical structure to a `nevents=10000` run).
- But `summary.txt` prints only the plain cross section, with **no** "Scale variation" / "PDF variation" lines — the job still reports `success=true`, so this looks like the feature silently did nothing when it actually just isn't being summarized yet.

If you need the human-readable envelope (not just the raw per-event weights), request `nevents >= 10000`. If nevents must stay low (e.g. a quick smoke test), read the weights directly from the LHE `<rwgt>`/`<initrwgt>` blocks instead of relying on `summary.txt`.

**Output**:
- `Events/run_XX/summary.txt` (also `.full_summary.txt`) — when `nevents >= 10000`, contains lines of the form:
  ```
  Scale variation (computed from LHE events):
      Dynamical_scale_choice <N> (envelope of 9 values):
          <central> pb  +<hi>% -<lo>%
  PDF variation (computed from LHE events):
      <PDF set name> (<n> members; using replicas method):
          <central> pb  +<hi>% -<lo>%
  ```
- `Events/run_XX/events.lhe.gz` (or `unweighted_events.lhe.gz`) — `<initrwgt>` header lists one `weightgroup` per scale choice (`combine='envelope'`) plus one `weightgroup` for the PDF set (`combine='unknown'`); each `<event>`'s `<rwgt>` block carries one `<wgt id='...'>` per weight (27 scale + 101 PDF = 128 total for the `rw_rscale`/`rw_fscale` defaults with a 101-member PDF set).
