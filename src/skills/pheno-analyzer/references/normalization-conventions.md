# Normalization conventions

This document exists because of a documented, recurring failure mode:
agents reconstruct a histogram's *shape* correctly but fail to propagate
the computed rate into the final normalization, or silently mix
normalization conventions between the simulation stage and the plotting
stage (see Collider-Bench, arXiv:2605.13950 — "fail to propagate the
computed rate into the final histogram" / "mix normalization
conventions" was identified as the dominant quantitative failure mode
across agents, more common than shape errors).

## The two normalization modes — never mix them

**Absolute yield mode** (events per bin per unit luminosity, or absolute
event counts at a fixed luminosity):

```
w_event = sigma * L / N_gen
yield_in_bin = sum(w_event for events in bin)
```

Use this when the target is: "events per bin per 100 fb^-1", an absolute
event count to compare against `n_obs`, or any input to a likelihood fit
(the likelihood in `statistical-methods.md` requires absolute yields, not
shape-normalized ones).

**Shape-normalized mode** (probability density / fraction of events):

```
yield_in_bin = count_in_bin / total_event_count
```

Use this only when the target explicitly says "normalized events",
"normalized distribution", "shape comparison", or similar — and the
resulting values should sum (or integrate, if bin widths vary) to 1.

**Before writing a single number to a histogram, state out loud (in the
provenance log) which of these two modes is being used and why**, based
on what the task actually asked for. If unsure which mode the target
paper used, check the y-axis label/units in the reference figure — "a.u."
or "normalized" implies shape mode; an explicit units label
(`events / bin / lumi`) implies absolute mode.

## Cross-section and luminosity bookkeeping

- `sigma` should be the cross section MadGraph reports for the exact
  process/cuts used to generate the sample — not a value looked up from
  a different generation-level cut configuration.
- `N_gen` is the number of generated events in that same sample (before
  any selection), not the number surviving cuts.
- `L` (luminosity) must match the experiment being compared to (e.g.
  36.1 fb^-1 for the ATLAS dataset, 35.9 fb^-1 for CMS, in the U1
  mono-tau example) — using the wrong experiment's luminosity when
  combining channels is an easy, silent error.
- When the signal is scanned over a coupling (see
  `statistical-methods.md`), the per-event weight at the reference
  coupling `g=1` is what gets scaled by `g^n`, not the already-scaled
  yield at a different reference point — rescale from a single fixed
  reference, don't chain rescalings.

## NLO events and negative weights

NLO samples (e.g. from MadGraph5_aMC@NLO) generally do not have unit
event weights — each event carries its own `weight_i`, which can be
negative, and the physical cross section is `sigma = sum(weight_i) /
N_gen` over the full generated sample. This is not a separate
normalization scheme from the LO case above — it is the same formula
generalized:

```
w_i = weight_i * L / N_gen
yield_in_bin = sum(w_i for events in bin)
```

For a plain LO sample with unit-weight events, `weight_i` is constant and
equal to `sigma`, which reduces exactly to `w_event = sigma * L / N_gen`
above. Treat LO as the constant-weight special case of this formula
rather than maintaining two separate mental models.

**Never filter out or drop negative-weight events.** Doing so biases the
result — the negative weights are physically meaningful (they arise from
subtraction terms in the NLO calculation) and must be summed along with
the positive ones.

**Do not assume a sample is LO just because the upstream agent says so
(or vice versa).** Read a sample of actual per-event weights from the
file and check directly for negative values before choosing a
normalization path. If the observed data disagrees with what was
reported upstream, flag the discrepancy explicitly.

### Statistical error and effective sample size (Neff)

The correct per-bin statistical error, valid regardless of the weight
distribution, is:

```
error_in_bin = sqrt(sum(w_i**2) for events in bin)
```

Effective sample size (a useful diagnostic for how much real statistical
power a weighted sample actually has, since positive and negative
weights partially cancel) should be computed with the general
(Kish) formula, directly from the actual weights:

```
Neff = (sum(w_i))**2 / sum(w_i**2)
```

**Do not use the reduced closed form `Neff = N * (1 - 2*f_minus)^2` as a
general-purpose formula.** It is only exactly equal to the general
formula above when every event has the same weight magnitude (pure
`+w0`/`-w0`). Real merged or reweighted NLO samples routinely have
negative-weight events with different magnitudes than positive ones, and
in that regime the reduced formula can be wrong by a large factor — for
example, weights `[10, -1]` give `Neff = 0` from the reduced formula but
`Neff ≈ 0.80` from the general formula. Use the reduced form only as a
quick cross-check when weight magnitudes visibly look uniform, and always
report the general-formula value as the actual result. See
`templates/nlo_event_weights.py` for a working implementation of both,
with a built-in check that warns when they disagree.

Report `f_minus` (fraction of negative-weight events), `Neff`, and the
per-bin error together for any NLO result — `f_minus` alone is not
sufficient, since it doesn't capture how unevenly weight magnitudes are
distributed.

## Zero-event bins

If a bin (or an entire selection) has zero simulated events, the correct
per-event-weight-based yield estimate is `0`, with a note that this may
reflect either genuinely negligible signal or insufficient generated
statistics (i.e. the true yield could be nonzero but below what `N_gen`
events can resolve). Report which of these it is if determinable (e.g.
by checking the generation-level cross section — a nonzero generation
cross section with zero events surviving selection cutting is a
statistics/binning issue, not a physical zero). Never replace a zero
with an interpolated or "expected" nonzero value.

## Pre-plot self-check

Before finalizing any plot, recompute one bin's yield by hand from raw
inputs (`sigma`, `L`, `N_gen`, raw count in that bin) and confirm it
matches the pipeline's output for that bin. This is a cheap, high-value
check that catches unit errors, off-by-`N_gen` errors, and mode-mixing
errors before they reach the final figure.
