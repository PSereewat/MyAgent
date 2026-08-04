# Statistical methods reference

## A note on weighted (NLO) signal inputs

Everything below assumes `s_i(g)` is already the correct absolute signal
yield in bin `i` — computed per
`references/normalization-conventions.md`, including the NLO weighting
section if the sample has negative weights. If the signal sample is NLO,
`s_i` is a weighted sum (`sum(w_i)` in that bin, not a raw event count),
and its own statistical uncertainty (from finite Monte Carlo statistics,
separate from the systematic `delta_i` below) should be tracked using
`sqrt(sum(w_i**2))` and, ideally, folded in as an additional nuisance
parameter or at minimum reported alongside the fit result — a low-`Neff`
signal bin can dominate the uncertainty on an exclusion limit even when
its nominal yield looks precise.

## Binned profile likelihood

For a set of bins `i` with observed counts `n_i`, expected background
`b_i` with uncertainty `delta_i`, and signal prediction `s_i(g)` as a
function of coupling(s) `g`:

```
mu_i(g, theta_i) = b_i * (1 + theta_i) + s_i(g)

-ln L_i(g, theta_i) = -[ n_i * ln(mu_i) - mu_i ] + theta_i^2 / (2 * (delta_i/b_i)^2)
```

`theta_i` is a nuisance parameter with a Gaussian constraint encoding the
fractional background uncertainty `delta_i/b_i`. Sum `-ln L_i` over bins
to get the total negative log-likelihood for one channel.

This is the same construction used in the ColliderAgent U1-leptoquark
mono-tau benchmark (arXiv:2603.14553, supplemental material, sec. 3.3) —
treat that as the canonical reference implementation, not an example to
deviate from without reason.

## Signal scaling with coupling

If the signal arises from a single diagram/vertex with a clean power-law
dependence on a coupling `g`, it's usually safe and much cheaper to
generate once at a reference coupling `g=1` and rescale:

```
s_i(g) = g^n * s_i^(g=1)
```

where `n` is the power of `g` appearing in the relevant matrix element
squared (e.g. `n=4` for a process with the coupling appearing twice in
amplitude, i.e. `|M|^2 ~ g^4`, as in the U1 mono-tau case with couplings
`g_c, g_b` where `s_i(g) = g_c^2 * g_b^2 * s_i^(1)` type scaling).

**Do not assume a power law when there is interference between signal
and background, or between multiple signal diagrams with independent
couplings** — in that case the cross section is not a pure power of any
single coupling, and each grid point in the scan needs its own generation
(or an explicit polynomial fit in the couplings, validated against a few
directly-generated points).

## Combining channels / experiments

Combine independent channels or experiments by summing log-likelihoods:

```
ln L_comb = ln L_channel_1 + ln L_channel_2 + ...
```

This assumes the channels are statistically independent (no shared
systematic nuisance parameters). If a systematic (e.g. luminosity,
detector calibration) is genuinely shared across channels, it should be
represented by a single shared nuisance parameter rather than independent
ones per channel — flag this explicitly rather than silently treating
correlated uncertainties as uncorrelated.

## Profiling and test statistic

1. For a given hypothesized coupling value `g`, profile out the nuisance
   parameters: minimize `-ln L(g, theta)` over `theta` with `mu_i >= 0`
   enforced as a constraint. Record `theta_hat(g)`.
2. Find the global best fit `g_hat` by minimizing `-ln L(g, theta)` over
   both `g` and `theta` jointly, subject to the physical constraint
   (usually `g >= 0` for a coupling-squared-type signal).
3. The profile-likelihood test statistic for a hypothesized `g`:

```
q(g) = -2 * [ ln L(g, theta_hat(g)) - ln L(g_hat, theta_hat(g_hat)) ]
```

4. **95% CL exclusion** (asymptotic, one-sided): solve for `g_excl` such
   that `q(g_excl) = 3.84` (chi-square with 1 dof, one-sided convention;
   note some analyses use `q = 4` as an approximation — confirm which
   convention the target paper used before matching it exactly).
5. **5-sigma discovery**: solve for the significance
   `Z = sqrt(q(g=0))` evaluated at the null hypothesis, require `Z >= 5`.

For anything beyond a single-parameter profile likelihood, or when the
target paper explicitly used the CLs method (common in ATLAS/CMS SUSY
searches) rather than a pure profile-likelihood ratio, use `pyhf`
(https://pyhf.readthedocs.io) instead of a hand-rolled implementation —
it is the field-standard, tested tool for exactly this and will avoid
subtle sign/convention errors in a from-scratch implementation.

## Reference implementations to cite/follow

- Cowan, Cranmer, Gross, Vitells, "Asymptotic formulae for likelihood-based
  tests of new physics" (arXiv:1007.1727) — the standard reference for
  the profile-likelihood asymptotics used above.
- Read, "Presentation of search results: the CLs technique" (2002) —
  for the CLs modification when the observed limit could otherwise
  exclude signal to which the analysis has no sensitivity.
- `pyhf` documentation and tutorials for a validated, standard
  implementation when the analysis complexity exceeds a simple 1D/2D
  profile likelihood.
