---
name: pheno-pipeline-orchestrator
description: >
  Orchestrate the full particle physics analysis pipeline using subagents.
  Triggers when the user asks to "execute an analysis", "run the full pipeline",
  "execute <filename>.md", or references an analysis prompt/plan .md file to
  execute end-to-end.
  Also triggers when the user's request spans multiple pipeline stages simultaneously,
  such as event generation (simulate, generate events, pp ->, LHC, TeV) combined with
  event analysis (plot, distribution, invariant mass, cut-flow) and/or post-processing
  (reproduction guide, summarize, exclusion limit, fit), or when the user describes
  a complete physics study (e.g. "complete study of...", "full analysis of...",
  "investigate ... and produce ...").
  ALSO triggers for incremental or follow-up requests that modify a previous run and
  propagate changes through downstream stages, such as "add more events and update
  the plot", "re-run with different parameters", "increase statistics and re-analyze",
  "change cuts and update figures", or any request that combines a modification to an
  upstream stage with updating downstream results. These are multi-stage tasks and
  MUST go through the orchestrator to maintain run labeling, progress tracking, and
  script generation consistency.
  Do NOT trigger for single-stage requests that only involve one of: model building,
  event generation, event analysis, or plotting — UNLESS the request is a follow-up
  modification to a previous run tracked in progress/run_manifest.yaml (e.g. "update
  only the plot style" on an existing run), in which case it must still go through
  the orchestrator so run labeling and progress tracking stay consistent.
---
# Analysis Pipeline Orchestrator
You are the orchestrator for a particle physics analysis pipeline. When the user provides a task description (typically a .md file), you break it down and delegate each step to a specialized subagent.
# Standard Directory Layout (reference)
Each subagent's skill defines its own output paths. The combined layout is
```
<working_dir>/
├── models/          # Step 1 (model-generator)
├── scripts/         # Steps 2/3/4/5 (all executable scripts)
├── events_lo/       # Step 2 (collider-lo-simulator)
├── events_nlo/      # Step 3 (collider-nlo-simulator)
├── analysis/        # Step 4 (event-analyzer)
├── output/          # Step 5 (pheno-analyzer)
│   ├── lo/
│   │    ├── figures/
│   │    └── data/
│   └── nlo/
│        ├── figures/
│        └── data/
├── progress/        # Orchestrator tracking
│   ├── run_manifest.yaml   # Index of all runs
│   └── <run_label>/        # Per-run progress files
├── reproduction/    # Step 6 (reproduction-guide-generator)
└── execution_summary.md
```
Note: If the user does not include [QCD] or explicitly request an NLO calculation, use LO by default and skip Step 3. If the user requests both LO and NLO calculations, complete the full LO workflow first. Then return to the event-generation stage, run Step 3 for NLO while skipping Step 2, and repeat the downstream analysis and output steps using the NLO events.
## Run Initialization
Before executing any pipeline step:
1. Generate a short, descriptive **run label** from the task content (e.g., `dy_14tev_50k`, `heavyN_scan_7TeV`).
2. Read `progress/run_manifest.yaml` if it exists; otherwise create it.
3. If the manifest already contains a run with the same label, append a short timestamp to disambiguate (e.g., `dy_14tev_50k_1432`).
4. Create the directory `progress/<run_label>/`.
5. Add a new run entry to the manifest:
   ```yaml
   - label: <run_label>
     timestamp: "<ISO 8601>"
     task: "<one-line task description>"
     steps: {}
   ```
## Incremental Runs
When the user's request modifies or extends a **previous run** (e.g., "add more events", "re-run with different cuts" ,"increase statistics and update the plot"), this is an **incremental run**. The orchestrator must still manage run labels, scripts, and progress — the same structure as a fresh run, but reusing upstream artifacts.
### Detection
An incremental run is identified when:
- The conversation already contains results from a prior run, OR
- `progress/run_manifest.yaml` contains completed runs for the same process
- AND the user requests a modification + downstream update (not a fresh start)
### Run Labeling
Create a **new run label** that references the parent run, e.g.:
- Parent: `dy_ll_14tev` → Incremental: `dy_ll_14tev_add10k` or `dy_ll_14tev_100k`
- This ensures full traceability; never silently overwrite a previous run's progress files.
## Artifact Reuse
Read the parent run's progress files to identify reusable artifacts:
- **Compiled process directory** — if the physics process is unchanged, reuse it (skip `madgraph-compile`; only run `madgraph-launch` for additional events)
- **UFO model** — if the Lagrangian is unchanged, skip Step 1 entirely
- **Analysis scripts** — if only statistics changed, the MA5/plotting scripts may need only path updates
### Script Generation
Even for incremental runs, the collider-simulator subagent **must generate a new script file** (e.g., `scripts/mg5_dy_14tev_run02.mg5`). This ensures:
1. The exact parameters of the incremental run are recorded
2. The reproduction package can replay this specific run
3. Parameter overrides (e.g., `nevents 10000`) are explicitly written, not inherited from a previous run_card
When passing instructions to the collider-simulator subagent for an incremental launch, explicitly state:
- That a compiled process directory already exists (give the path)
- That a NEW script must still be generated with the incremental parameters
- The exact `nevents` and any changed parameters — do NOT rely on the existing run_card defaults
### Pipeline Execution
Execute only the **affected steps and all downstream steps**:
| User Request | Steps to Execute |
|---|---|
| Add more LO events and update the plot | Step 2 (launch only) → Step 4 → Step 5 |
| Add more NLO events and update the plot | Step 3 (launch only) → Step 4 → Step 5 |
| Change analysis cuts and update the plot | Step 4 → Step 5 |
| Rerun at a different mass using LO | Step 2 → Step 4 → Step 5 |
| Rerun at a different mass using NLO | Step 3 → Step 4 → Step 5 |
| Update only the plot style | Step 5 only |
For each executed step, write progress files under `progress/<new_run_label>/` and update the manifest.
### Manifest Entry
Add a `parent` field to link incremental runs to their origin:
```yaml
- label: dy_ll_14tev_add10k
  parent: dy_ll_14tev
  timestamp: "<ISO 8601>"
  task: "Add 10k events to Drell-Yan run and update figure"
  steps: {}
```
## Pipeline
Execute the following steps **sequentially**, using the specified subagent for each. Pass intermediate results via the `progress/` directory.
### Step 1: Model Building → `model-generator` subagent
- Input: the Lagrangian and particle content from the user's task description
- If NLO is requested, pass `nlo: true` to the model-generator subagent
- The subagent generates .fr model → validates → produces UFO model (NLO-capable if requested)
- Output: `progress/<run_label>/step1_feynrules.md`
- Extract from return: UFO path, model file path, particle names, PDG codes, parameter block/code info
### Step 2: LO Event Generation → `collider-simulator` subagent
- Run this step by default unless the user requests NLO only.
- Use the `collider-simulator` subagent to perform the LO calculation.
- Input: the UFO model path and particle information from Step 1, together with the collider settings from the task description.
- The subagent compiles the LO process and generates Monte Carlo events.
- Output: `progress/<run_label>/step2_madgraph_lo.md`
- Extract from the returned result:
  - executable script paths
  - compiled process directories
  - event directories
  - run-name-to-parameter mappings
- **Do not extract or interpret physics results.** Leave that work to the downstream analysis subagents.
### Step 3: NLO Event Generation → `collider-nlo-simulator` subagent
- Run this step only when the user explicitly requests NLO, includes `[QCD]` in the process, or specifies `nlo: true`.
- Skip this step for LO-only tasks.
- If the user requests both LO and NLO, complete the LO workflow first. Then run this step and repeat the downstream analysis using the NLO events.
- Use the `collider-nlo-simulator` subagent to perform the NLO calculation.
- Input: the UFO model path and particle information from Step 1, together with the collider settings from the task description.
- The subagent compiles the NLO process and generates Monte Carlo events.
- Output: `progress/<run_label>/step3_madgraph_nlo.md`
- Extract from the returned result:
  - executable script paths
  - compiled process directories
  - event directories
  - run-name-to-parameter mappings
- **Do not extract or interpret physics results.** Leave that work to the downstream analysis subagents.
### Step 4: Event Analysis → `event-analyzer` subagent (if needed)
- Input: event file paths from step 2, analysis specifications from the task description
- The subagent runs MadAnalysis5 for kinematic distributions and cut-flow
- When both LO and NLO are requested, analyze them separately and preserve an explicit perturbative-order label for every result.
- Output: LO: `progress/<run_label>/step4_madanalysis_lo.md`
         NLO: `progress/<run_label>/step4_madanalysis_nlo.md`
- Extract from return: script path (e.g. `scripts/ma5_dilepton.ma5`), analysis dir (e.g. `analysis/dilepton_mass`), histogram path
- Skip this step if the task does not require MA5 analysis
### Step 5: Post-Processing → `pheno-analyzer` subagent
- Input: Step 4 output when event analysis was performed; otherwise, step 2 output for LO or Step 3 output for NLO, run-name-to-parameter mappings, the post-processing requirements from the task description
- For combined LO and NLO tasks, keep the two datasets distinct and clearly label their perturbative orders. Compare them only when the user requests a comparison.
- The subagent reads simulation/analysis output files directly, extracts the physics results it needs (cross sections, kinematic distributions, etc.), performs analysis, and produces plots
- Output: LO: `progress/<run_label>/step5_postprocessing_lo.md`,
         NLO: `progress/<run_label>/step5_postprocessing_nlo.md`
- Extract from return: script path (e.g. `scripts/plot_xsec_vs_mass.py`), figure files (e.g. `output/figures/figure_3.pdf`), data files (if any)
### Step 6: Reproduction Guide → `reproduction-guide-generator` subagent (if requested)
- Run this step only when the task description asks for a reproduction guide/package, or when producing `execution_summary.md` for a complete end-to-end study.
- Input: all script paths, compiled process directories, event/analysis directories, and run-name-to-parameter mappings collected from Steps 1–5.
- The subagent assembles a step-by-step guide (and any packaging scripts) that lets someone else replay the run from scratch.
- Output: `progress/<run_label>/step6_reproduction.md`
- Extract from return: reproduction guide path (e.g. `reproduction/README.md`), any packaged script/archive paths
- Skip this step if the task does not require a reproduction guide.
## Rules
1. **Read the task file first** — understand the full scope before starting any step.
2. **Run steps sequentially** — each step depends on the previous step's output.
3. **Pass precise information** — when invoking each subagent, include all relevant details from the task description AND the previous step's return summary. Tell the subagent the progress file path to write to (e.g., `progress/<run_label>/step2_madgraph_lo.md`). The subagent has no access to the task file or conversation history.
4. **If a subagent's return summary is insufficient**, read the corresponding `progress/<run_label>/stepN_*.md` file for complete details before proceeding.
5. **Skip steps that are not needed** — Not every task requires all six steps. For example, skip Step 1 when the user supplies a valid UFO model, skip Step 2 for NLO-only tasks, skip Step 3 for LO-only tasks, skip Step 4 when no MadAnalysis5 analysis is required, and skip Step 6 unless a reproduction guide is requested.
6. **Generate execution summary** — after all steps complete, invoke the `execution-summarizer` subagent to produce a detailed `execution_summary.md` with prompt-to-code mapping tables and key results.
7. **Update manifest after each step** — after a subagent completes, update the run's entry in `progress/run_manifest.yaml` with the step's status (success/failed).
## Separation of Concerns
The orchestrator manages **paths and scheduling**, not physics results:
- **Step 1 → Step 2 or 3**: Pass the UFO path, particle names, PDG codes, parameter blocks, and other structural model information.
- **Step 2 → Step 4 or 5**: Pass LO event directories, script paths, compiled-process directories, and run-name-to-parameter mappings.
- **Step 3 → Step 4 or 5**: Pass NLO event directories, script paths, compiled-process directories, and run-name-to-parameter mappings.
- **Step 4 → Step 5**: Pass analysis directories, histogram paths, cut-flow paths, and run mappings.
- **Steps 1–5 → Step 6**: Pass all script, directory, and run-mapping information needed to replay the run; do not summarize physics results yourself.
- **Physics results**: Do not parse event-generator logs for cross sections or other physics results. The analysis and post-processing subagents must read the relevant output files directly.
## Local Execution
Local execution is triggered in two cases:
### Case 1: User requests local execution
If the user explicitly asks to run locally (e.g., "run locally", "use local MadGraph", "don't use Magnus"), skip Magnus entirely and use local tools directly. Do not attempt Magnus calls.
### Case 2: Magnus is unavailable
If the Magnus server is unreachable:
1. **Retry up to 2 times** with a 20-second interval (`sleep 20`) before falling back to local execution. Each failed Magnus call returns a large HTML error page, so limit retries to avoid wasting context.
2. **Check for local tools** (wolframscript, MadGraph5) and fall back to local execution.
### Local execution guidelines
When running locally:
- **Check for local tools** — verify `wolframscript` and MadGraph5 (`mg5_aMC` or `MG5_aMC_v*`) are available before proceeding.
- **When running MadGraph locally via `Bash(run_in_background=true)`**:
   - Wait for the `task-notification` to confirm completion. Do NOT use `TaskOutput(block=true)` — it pulls the entire verbose MadGraph log into context.
   - After the notification, use `Grep` on the task output file to extract only the specific lines needed (e.g., run names, output paths).
   - Let downstream subagents read the MadGraph output directories directly for physics results.
