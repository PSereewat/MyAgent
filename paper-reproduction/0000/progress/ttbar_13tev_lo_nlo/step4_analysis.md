# Step 4: Numerical Analysis — Delta_phi(t,tbar) Distribution (LO + NLO)

## Status: SUCCESS (final — both LO and NLO curves produced)

## Overview

Implemented Section 4 ("Numerical Analysis") of `ttbar_production.md`: extracted the
top/antitop four-momenta from both the LO and NLO LHE files, computed
$\Delta\phi_{t\bar{t}} = |\phi_t - \phi_{\bar t}|$ (folded to $[0,\pi]$), filled a
20-bin weighted histogram over $[0,\pi]$ per run, normalized to $d\sigma/d\Delta\phi_{t\bar t}$
(pb/rad) with statistical error bars, and produced the combined plot per the spec's plot
settings (LO = green solid step line, NLO = blue solid step line, linear/linear axes,
$y \in [0, 1.1\,y_{max}]$).

This supersedes the earlier LO-only version of this file (session 3 and prior): the
companion NLO run (`pp > t t~ [QCD]`, `NNPDF23_nlo_as_0119_qed`) completed successfully
in session 4 after three infrastructure fixes to `scripts/run_madgraph_launch.py` — see
`progress/ttbar_13tev_lo_nlo/step2_nlo_madgraph.md` for the full root-cause history
(compile-time Ninja/OneLOop and symlink-archiving fixes, blueprint-registry repointing,
and finally a background thread that actively syncs `run_card.inc` into every NLO
subprocess directory to close a gap in MG5's own internal file propagation).

## Script

`scripts/analyze_dphi_ttbar.py` — generic, re-runnable script that:
- Accepts `--lo <path>` and/or `--nlo <path>` LHE file paths (plain `.lhe` or `.lhe.gz`)
  plus `--outdir` (defaults to `.`).
- Parses each `<event>` block, extracts the final-state (status 1) PDG +6 (top) and
  PDG -6 (antitop) four-momenta, computes $\phi_t=\mathrm{atan2}(p_y,p_x)$,
  $\phi_{\bar t}=\mathrm{atan2}(p_y,p_x)$, and
  $\Delta\phi_{t\bar t}=|\phi_t-\phi_{\bar t}|$, folded into $[0,\pi]$ (if $>\pi$,
  replace with $2\pi - \Delta\phi$).
- Fills a 20-bin histogram over $[0,\pi]$ (bin width $\pi/20\approx0.1571$ rad) with
  each event's LHE weight, divides by bin width to get $d\sigma/d\Delta\phi$ (pb/rad),
  and computes the per-bin statistical error as $\sqrt{\sum w_i^2}/\Delta\phi_{\rm bin}$.
- Writes CSV + JSON per run to `output/data/` and a combined PNG+PDF figure to
  `output/figures/`.
- Negative LHE weights (NLO) are summed as-is per bin, not filtered — this is
  physically correct for MC@NLO-style samples.

### LHE weight normalization convention (IDWTUP = -4)

Both LHE files report `IDWTUP = -4`. Under this convention, the raw per-event weight
`XWGTUP` satisfies $\sigma = \frac{1}{N_{\rm events}}\sum_i \mathrm{XWGTUP}_i$ (average,
not direct sum). The script uses the **normalized** per-event weight
$w_i = \mathrm{XWGTUP}_i / N_{\rm events}$ in
$d\sigma/d\Delta\phi\approx\sum_{\rm bin}w_i/\Delta\phi_{\rm bin}$, so that $\sum_i w_i$
over all events/bins reproduces the physical total cross section.

## Results

### LO run

- LHE file: `events/pp_ttbar_lo_13tev/Events/run_01/unweighted_events.lhe.gz`
- Events processed: 100/100.
- Generator-reported cross section (`<init>` XSECUP): 522.309 ± 4.897 pb.
- Raw sum of LHE weights: 52230.9 pb (100× XSECUP, as expected under IDWTUP=-4 — all
  100 weights identical, $w_i=522.309$ pb each).
- **Normalized sum of weights / histogram integral: 522.309 pb** — reproduces XSECUP to
  6 significant figures.
- Negative-weight fraction: **0%** (tree-level LO, all weights positive and identical).
- Distribution: all 100 events give $\Delta\phi_{t\bar t} = \pi$ to floating-point
  precision. Expected fixed-order LO behavior — a pure $2\to2$ matrix element with no
  extra QCD radiation gives exact back-to-back recoil ($p_{x,t}=-p_{x,\bar t}$,
  $p_{y,t}=-p_{y,\bar t}$), so the histogram is a single spike in the last bin
  ($[19\pi/20,\pi]$, i.e. $[2.9845,3.1416]$ rad) with all cross section (522.309 pb)
  concentrated there, zero everywhere else.

### NLO run

- LHE file: `events/pp_ttbar_nlo_13tev/Events/run_11/events.lhe.gz`
- Events processed: 100/100.
- Generator-reported cross section (`<init>` XSECUP, MG5's multi-channel integration):
  699.9608 ± 4.237205 pb.
- Raw sum of LHE weights: 80498.81 pb; **normalized sum of weights: 804.988 pb.**
- Negative-weight fraction: **15%** (15/100 events).

**Note on the 699.96 pb vs. 804.99 pb discrepancy (not a bug):** this NLO sample's raw
weights take only two discrete magnitudes, $\pm 1149.983$ pb (matches the LHE `<init>`
block's "Total abs(cross section): 1.150e+03 pb" from the launch log). The *expected*
value averages to 699.96 pb only if the fraction of negative-weight events is
$\approx 19.6\%$ of $N$; the realized sample has 15%, which is within $\sim$1.1σ of a
binomial fluctuation for $N=100$ ($\sigma_{\rm frac}\approx\sqrt{p(1-p)/N}\approx4\%$).
This is a well-known small-$N$ effect for MC@NLO-style unweighted samples with signed
weights: at only 100 events, the realized sample average can differ visibly from the
quoted (much more precisely integrated) generator cross section, purely from counting
statistics on the sign of the weight. The histogram/analysis script itself is correct —
it faithfully sums the file's actual per-event weights; it is not expected to reproduce
XSECUP exactly at this small $N$ (unlike the LO case, where all weights are identical
and the match is exact by construction).

- Distribution: unlike LO's delta-function spike, the NLO histogram shows the dominant
  peak still near $\Delta\phi_{t\bar t}=\pi$ (last bin, $4612.24 \pm 682.86$ pb/rad) but
  with real events populating several lower-$\Delta\phi$ bins down to
  $\Delta\phi_{t\bar t}\approx0.5$ rad — the expected physical signature of the NLO
  real-emission correction: an extra radiated parton lets the $t\bar t$ pair recoil away
  from exact back-to-back topology. One bin (`[2.042, 2.199]` rad) shows a negative
  entry ($-73.21$ pb/rad), directly reflecting a single negative-weight event landing
  there — summed as-is, not filtered, per the task's instructions.

### Binned data

Full tables in `output/data/dphi_ttbar_LO.csv` / `.json` and
`output/data/dphi_ttbar_NLO.csv` / `.json`. NLO highlights:

| Bin range [rad] | $d\sigma/d\Delta\phi$ [pb/rad] | error [pb/rad] |
|---|---|---|
| $[0.471,\,0.628]$ | 73.21 | 73.21 |
| $[1.885,\,2.042]$ | 73.21 | 73.21 |
| $[2.042,\,2.199]$ | -73.21 | 73.21 |
| $[2.199,\,2.356]$ | 73.21 | 73.21 |
| $[2.356,\,2.513]$ | 73.21 | 73.21 |
| $[2.513,\,2.670]$ | 73.21 | 73.21 |
| $[2.670,\,2.827]$ | 219.63 | 126.80 |
| $[2.827,\,2.985]$ | 0.0 | 146.42 |
| $[2.985,\,3.142]$ (last bin) | 4612.24 | 682.86 |
| all other bins | 0.0 | 0.0 |

## Negative-weight fraction

- LO run: **0%** — all 100 weights positive and identical, as expected for tree-level LO.
- NLO run: **15%** (15/100 events) — as expected for NLO QCD with MadLoop virtual
  corrections.

## Outputs

- Data: `output/data/dphi_ttbar_LO.csv`, `output/data/dphi_ttbar_LO.json`,
  `output/data/dphi_ttbar_NLO.csv`, `output/data/dphi_ttbar_NLO.json`
- Figure: `output/figures/dphi_ttbar_lo_nlo.png`, `output/figures/dphi_ttbar_lo_nlo.pdf`
  (combined LO green + NLO blue step curves with error bars, per the spec's plot
  settings — linear/linear axes, $y \in [0, 1.1\,y_{max}]$, 20 uniform bins over
  $[0,\pi]$).

## Issues / Assumptions

- Assumed the LHE per-event weight normalization convention described above
  (`IDWTUP=-4`: $\sigma=\frac{1}{N}\sum w_i$) applies uniformly to both the LO and NLO
  runs, since both are generated by the same MadGraph5_aMC@NLO tool. Verified directly
  on both files (LO: exact match to XSECUP; NLO: consistent with XSECUP within expected
  small-$N$ statistical noise, explained above).
- No kinematic/detector-level cuts were applied — this is parton-level LHE truth
  information (undecayed top/antitop, status-1 in the LHE record), as specified by the
  task. No parton shower or detector simulation was run (task specifies parton-level LHE
  analysis only; MG5 itself warned "NLO events without showering are NOT physical" for
  physics use beyond this LHE-level kinematic comparison, which is expected/accepted
  here since the task's target observable is defined directly at the LHE/parton level).
- $N=100$ events per run (as specified by the task) is small for an NLO signed-weight
  sample; the resulting per-bin statistical uncertainties on the NLO curve are large
  (see error bars above), and the true expectation value of the NLO distribution would
  be much better resolved with a larger event sample. This is inherent to the task's
  specified $N=100$, not a limitation of the analysis method.
