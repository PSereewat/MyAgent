---
name: pheno-analyzer
description: >
  Performs downstream phenomenological inference and visualization on
  collider-simulation output: profile-likelihood statistical analysis,
  95% CL / discovery-significance exclusion-limit extraction, 1D/2D
  parameter-space scans, and publication-style plotting. Trigger this
  skill whenever a task asks to (a) derive an exclusion contour or
  discovery-significance region in a BSM parameter plane, (b) compute a
  profile-likelihood fit against experimental data (HEPData tables, ATLAS/
  CMS binned distributions), (c) combine multiple channels/experiments
  into a joint limit, or (d) turn simulated event yields into a final
  kinematic-distribution or exclusion plot. This skill is the downstream
  consumer of collider-simulator / event-analyzer output (Delphes ROOT,
  LHCO, or MadAnalysis5 histograms) — invoke it after those stages, not
  in place of them.
---

# pheno-analyzer

## Purpose

This skill turns simulated signal yields plus experimental background/data
into a statistically defensible result: an exclusion contour, a discovery
significance, or a validated kinematic distribution. It exists because
generic LLM reasoning about statistics is unreliable in exactly the ways
that matter for physics results — see `references/normalization-conventions.md`
and the anti-fabrication rules below, which were written in direct response
to observed failure modes (silently wrong normalization, fabricated
fallback values when a run actually selected zero events).

Read `references/statistical-methods.md`, `references/data-formats.md`,
and `references/normalization-conventions.md` before starting any task.
Do not improvise a likelihood construction or a normalization scheme from
first principles — use the conventions documented here so results are
reproducible and comparable across runs.

## Expected inputs

- Observed data: either a HEPData table (YAML/JSON), a hard-coded binned
  table given in the prompt, or a reference to a specific arXiv paper's
  Table/Figure to be looked up.
- Background prediction per bin, with uncertainty (symmetric or asymmetric).
- Simulated signal events: Delphes ROOT file, LHCO file, or a MadAnalysis5
  histogram/cutflow output, plus the generator-level cross section and
  number of generated events (`N_gen`) needed to compute per-event weight.
- Integrated luminosity for each experiment/channel being combined.
- The coupling(s) whose limit is being derived, and how the signal scales
  with them (e.g. quadratic in a single coupling, quartic in a product of
  two couplings, or an arbitrary interference pattern that must be
  extracted by scanning, not assumed).
- Selection cuts already applied upstream (from the prompt or from the
  event-analyzer's progress record) — do not re-derive or guess cuts.
- Whether the sample is LO or NLO (i.e. whether events carry non-constant,
  possibly negative weights). Treat this as a claim to verify against the
  actual event weights, not a fact to trust blindly — see
  `references/normalization-conventions.md`.

## Expected outputs

- A plot (matplotlib, saved as PNG/PDF) matching the requested format:
  kinematic distribution, 1D limit vs. mass, or 2D exclusion contour with
  shading convention as specified (default: excluded region shaded,
  boundary as a solid line).
- The underlying numerical data backing the plot (contour points, fit
  results, best-fit value, test statistic) saved alongside the plot —
  never only the image.
- A short provenance log: which input files were read, which normalization
  convention was used, whether the fit converged, and any bins where
  signal yield was zero or the background prediction was used as-is
  without a signal contribution.

## Workflow

1. **Load and validate inputs.** Parse experimental data with
   `templates/parse_hepdata.py` conventions. Confirm units, binning, and
   that background + observed counts are internally consistent (e.g.
   `n_obs >= 0`, uncertainties are positive). Flag and stop if the data
   format doesn't match what's expected rather than guessing a schema.

2. **Compute signal yields with explicit normalization.** Use the
   unified weighting convention in
   `references/normalization-conventions.md`: `w_i = weight_i * L /
   N_gen` per event (which reduces to `sigma * L / N_gen` for constant-
   weight LO samples), or the shape-normalized equivalent if the target
   is a normalized distribution rather than an absolute yield. State
   which mode is being used before proceeding. If the sample is NLO
   (verified from actual event weights, not just assumed), use
   `templates/nlo_event_weights.py` to get per-bin yields, errors, and
   `Neff` with the correct general formula. If zero events survive the
   selection, report zero explicitly — do not substitute a literature
   value, an extrapolation, or a "typical" number.

3. **Determine coupling scaling.** If the signal scales analytically with
   the coupling(s) (e.g. `s_i(g) = g^n * s_i^(1)`), compute once at a
   reference coupling and scale algebraically for the scan. If the
   scaling is not a simple power law (interference with background,
   multiple contributing diagrams), regenerate signal at each scan point
   — do not assume a power law without justification.

4. **Build the likelihood** following
   `references/statistical-methods.md`: binned Poisson likelihood with
   Gaussian-constrained nuisance parameters for systematics, profiled
   numerically. Combine channels/experiments by summing log-likelihoods.
   Use `templates/profile_likelihood_fit.py` as the starting point rather
   than writing a fit from scratch.

5. **Extract the result.** For exclusion contours, scan the parameter
   grid and solve for the boundary where
   `-2*[lnL(g_excl) - lnL(g_hat)] = 4` (2 sigma, one-sided) or the
   appropriate discovery threshold. Use `templates/exclusion_contour_scan.py`.
   Record the best-fit point and check it lies in the physical region
   (e.g. non-negative signal strength) before reporting.

6. **Run the validation checklist** in
   `references/validation-checklist.md` before finalizing any plot or
   number.

7. **Plot** using `templates/plot_exclusion_contour.py` conventions
   (or the equivalent kinematic-distribution template) and save both the
   figure and its underlying data.

## Hard rules (anti-fabrication)

These are non-negotiable, not suggestions:

- Never hard-code a fallback array, a "typical" cross section, or a
  literature number in place of an actual computed result. If the
  pipeline produced nothing usable, say so and stop — do not paper over
  it with a plausible-looking substitute.
- Never report a yield, significance, or limit derived from a run that
  selected zero signal events without explicitly flagging that the
  result reflects zero events passing selection.
- Every number that ends up in a plot or a reported limit must be
  traceable to a specific input file and computation step. If asked,
  be able to show the chain from raw simulation output to final number.
- If the fit did not converge, or the minimizer hit a boundary, report
  that rather than presenting the boundary value as a converged best fit.
- Never drop or filter negative-weight events from an NLO sample, and
  never use the reduced closed-form `Neff = N*(1-2*f_minus)^2` as a
  general-purpose formula — it silently gives wrong (often drastically
  wrong) answers for realistic non-uniform-magnitude weight
  distributions. Always compute `Neff` with the general Kish formula and
  the bin error with `sqrt(sum(w_i**2))`; see
  `references/normalization-conventions.md` and
  `templates/nlo_event_weights.py`.

## Notes on scope

This skill covers standard simplified-model and EFT-style statistical
analysis (single or few-parameter profile likelihoods, CLs-style
exclusion). It does not (yet) cover full RooStats/combine-style
workspace construction for multi-hundred-nuisance-parameter analyses —
for that level of complexity, prefer calling out to `pyhf` directly
(see `references/statistical-methods.md`) rather than hand-rolling the
likelihood.
