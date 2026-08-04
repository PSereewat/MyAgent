# Pre-output validation checklist

Run through this list before presenting any plot, limit, or significance
as a finished result. Treat a "no" on any item as a stop condition, not
a caveat to mention in passing.

1. **Event counts are sane.** Total generated events, events surviving
   each cut, and final bin counts are all non-negative integers (before
   weighting) and consistent with the cutflow table if one exists
   upstream.

2. **Normalization mode is stated and consistent.** Absolute-yield vs.
   shape-normalized (see `normalization-conventions.md`) was chosen
   deliberately for this task and applied uniformly — not shape mode in
   one part of the analysis and absolute mode in another.

3. **Units match.** GeV vs. TeV, fb vs. pb vs. nb, and bin-edge units in
   the experimental data table all match what the simulation is
   producing. A factor-of-1000 error here is common and easy to miss
   visually if the plot is on a log scale.

4. **No fabricated values.** Every number in the final output traces to
   an actual file and computation this run performed. No hard-coded
   fallback arrays, no "typical" literature values substituted for a
   failed or empty computation, no yields reported from a run that
   actually selected zero events without saying so explicitly.

5. **Fit convergence checked.** The likelihood minimizer reports a
   successful convergence flag (not just "didn't crash"). If the
   best-fit point sits exactly on a boundary (e.g. `g_hat = 0` when
   `g >= 0` is enforced), that's noted rather than silently accepted.

6. **Sanity cross-check against one hand-computed point.** At least one
   bin's yield, or the overall cross section, has been recomputed
   independently from raw inputs (per the pre-plot self-check in
   `normalization-conventions.md`) and matches the pipeline output.

7. **Result is physically sensible.** Exclusion contours are in the
   physical region (no excluding a coupling to be less than zero unless
   that's meaningful for the model), significance is not negative or
   above the value implied by the maximum possible test statistic for
   the observed data, and comparison to the target/reference curve (if
   reproducing a known result) is at least qualitatively consistent —
   if it isn't, that discrepancy is surfaced, not smoothed over.

8. **Provenance log is written.** Which input files, which normalization
   mode, which statistical method, and any zero-yield or non-convergence
   flags are recorded alongside the output, not just in this session's
   reasoning trace.

9. **NLO/negative-weight status was verified, not assumed.** For any
   sample, actual per-event weights (not just an upstream claim) were
   checked for negative values. If negative weights are present: no
   events were dropped, the per-bin error used `sqrt(sum(w_i**2))`, and
   `Neff` was computed with the general Kish formula
   `(sum(w_i))**2 / sum(w_i**2)` rather than the reduced
   `N*(1-2*f_minus)^2` form (see
   `normalization-conventions.md`). `f_minus` and `Neff` are reported
   together with the error, not `f_minus` alone.
