# Step 4: Numerical Analysis — Delta_phi(t,tbar) Distribution (LO + NLO)

## Status: SUCCESS (final — N=10000 per run, session 5)

## Overview

Implemented Section 4 ("Numerical Analysis") of `ttbar_production.md`: extracted the
top/antitop four-momenta from both the LO and NLO LHE files, computed
$\Delta\phi_{t\bar{t}} = |\phi_t - \phi_{\bar t}|$ (folded to $[0,\pi]$), filled a
20-bin weighted histogram over $[0,\pi]$ per run, normalized to $d\sigma/d\Delta\phi_{t\bar t}$
(pb/rad) with statistical error bars, and produced the combined plot per the spec's plot
settings (LO = green solid step line, NLO = blue solid step line, linear/linear axes,
$y \in [0, 1.1\,y_{max}]$).

**Session 5 (this version):** regenerated at **nevents=10000** per run (user request),
up from the task spec's `nevents=100`. Supersedes the N=100 version (session 4 results
preserved below in "N=100 run (superseded)" for reference/comparison — they were also
the first evidence that the small-N NLO discrepancy discussed there was genuine
statistical noise, since it disappears at higher N, confirmed here).

The NLO run (`pp > t t~ [QCD]`, `NNPDF23_nlo_as_0119_qed`) required infrastructure fixes
to `scripts/run_madgraph_launch.py` to work at all — see
`progress/ttbar_13tev_lo_nlo/step2_nlo_madgraph.md` for the full root-cause history
(compile-time Ninja/OneLOop and symlink-archiving fixes, blueprint-registry repointing,
and a background thread that actively syncs `run_card.inc` into every NLO subprocess
directory to close a gap in MG5's own internal file propagation).

## Script

`scripts/analyze_dphi_ttbar.py` — generic, re-runnable script; behavior unchanged from
session 4 (see prior description below). Re-run as:
```
python3 scripts/analyze_dphi_ttbar.py \
  --lo events/pp_ttbar_lo_13tev/Events/run_02/unweighted_events.lhe.gz \
  --nlo events/pp_ttbar_nlo_13tev/Events/run_12/events.lhe.gz \
  --outdir .
```

### LHE weight normalization convention (IDWTUP = -4)

Both LHE files report `IDWTUP = -4`. Under this convention, the raw per-event weight
`XWGTUP` satisfies $\sigma = \frac{1}{N_{\rm events}}\sum_i \mathrm{XWGTUP}_i$ (average,
not direct sum). The script uses the **normalized** per-event weight
$w_i = \mathrm{XWGTUP}_i / N_{\rm events}$ in
$d\sigma/d\Delta\phi\approx\sum_{\rm bin}w_i/\Delta\phi_{\rm bin}$, so that $\sum_i w_i$
over all events/bins reproduces the physical total cross section.

## Results (N=10000, final)

### LO run

- LHE file: `events/pp_ttbar_lo_13tev/Events/run_02/unweighted_events.lhe.gz`
- Events processed: 10000/10000.
- Generator-reported cross section: 520 ± 0.6095 pb.
- Raw sum of LHE weights: 5,199,560 pb; **normalized sum of weights / histogram
  integral: 519.956 pb** — matches the generator-reported value closely.
- Negative-weight fraction: **0%** (tree-level LO, all weights positive and identical).
- Distribution: all 10000 events give $\Delta\phi_{t\bar t} = \pi$ to floating-point
  precision, unchanged from the N=100 run — this is an exact fixed-order LO property
  (pure $2\to2$ back-to-back kinematics), not a statistical effect, so it does not
  change with $N$. Single spike in the last bin ($[2.9845,3.1416]$ rad) with all cross
  section concentrated there.

### NLO run

- LHE file: `events/pp_ttbar_nlo_13tev/Events/run_12/events.lhe.gz`
- Events processed: 10000/10000.
- Generator-reported cross section: 700.0 ± 4.2 pb.
- Raw sum of LHE weights: 6,938,997.42 pb; **normalized sum of weights: 693.90 pb** —
  now closely matches the quoted cross section (within ~1%), confirming the N=100 run's
  larger gap (804.99 pb vs. 699.96 pb quoted) was small-$N$ statistical noise, not a bug
  (see "N=100 run (superseded)" below for the full explanation, which predicted exactly
  this convergence).
- Negative-weight fraction: **19.83%** (1983/10000) — very close to the ~19.6% expected
  from the weight magnitude and quoted cross section, as predicted.
- Distribution: a smooth, well-resolved tail populates the full $[0,\pi]$ range (all 20
  bins nonzero, with tight statistical error bars — a much clearer picture than the
  sparse N=100 version, where 12/20 bins were empty). The dominant peak remains at
  $\Delta\phi_{t\bar t}=\pi$ (last bin, $3963.60 \pm 67.59$ pb/rad), with the real-emission
  recoil tail visible and well-populated (roughly flat around 15-25 pb/rad through most
  of $[0, 2]$ rad, rising smoothly toward $\pi$) — the expected physical signature of
  extra QCD radiation letting the $t\bar t$ pair recoil away from exact back-to-back
  topology.

### Binned data (full table)

Full tables in `output/data/dphi_ttbar_LO.csv` / `.json` and
`output/data/dphi_ttbar_NLO.csv` / `.json`. NLO:

| Bin range [rad] | $d\sigma/d\Delta\phi$ [pb/rad] | error [pb/rad] |
|---|---|---|
| $[0.000,\,0.157]$ | 22.70 | 4.33 |
| $[0.157,\,0.314]$ | 15.37 | 3.66 |
| $[0.314,\,0.471]$ | 13.91 | 3.35 |
| $[0.471,\,0.628]$ | 18.30 | 3.94 |
| $[0.628,\,0.785]$ | 10.98 | 3.19 |
| $[0.785,\,0.942]$ | 16.84 | 3.66 |
| $[0.942,\,1.100]$ | 17.57 | 3.73 |
| $[1.100,\,1.257]$ | 14.64 | 3.59 |
| $[1.257,\,1.414]$ | 20.50 | 4.01 |
| $[1.414,\,1.571]$ | 19.77 | 4.21 |
| $[1.571,\,1.728]$ | 24.16 | 4.80 |
| $[1.728,\,1.885]$ | 20.50 | 4.51 |
| $[1.885,\,2.042]$ | 24.89 | 5.07 |
| $[2.042,\,2.199]$ | 36.61 | 6.21 |
| $[2.199,\,2.356]$ | 35.87 | 6.26 |
| $[2.356,\,2.513]$ | 37.34 | 6.91 |
| $[2.513,\,2.670]$ | 30.75 | 8.72 |
| $[2.670,\,2.827]$ | 35.14 | 11.10 |
| $[2.827,\,2.985]$ | 38.07 | 15.94 |
| $[2.985,\,3.142]$ (last bin) | 3963.60 | 67.59 |

## Negative-weight fraction (final, N=10000)

- LO run: **0%** — all weights positive and identical, as expected for tree-level LO.
- NLO run: **19.83%** (1983/10000) — matches the ~19.6% expected from the weight
  magnitude/cross-section relationship (see above).

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
  on both files.
- No kinematic/detector-level cuts were applied — this is parton-level LHE truth
  information (undecayed top/antitop, status-1 in the LHE record), as specified by the
  task. No parton shower or detector simulation was run (task specifies parton-level LHE
  analysis only; MG5 itself warned "NLO events without showering are NOT physical" for
  physics use beyond this LHE-level kinematic comparison, which is expected/accepted
  here since the task's target observable is defined directly at the LHE/parton level).
- $N=10000$ was used per explicit user request, deviating from the task document's
  specified $N=100$; the underlying physics settings (process, PDF sets, scales, masses)
  are otherwise unchanged from the spec.

---

## N=100 run (superseded, session 4) — preserved for reference

The original run at the task spec's `nevents=100` gave the same qualitative physics
(LO delta-spike at $\pi$; NLO peak at $\pi$ plus real-emission smearing), but with much
sparser NLO statistics (only 8/20 bins nonzero) and a notable cross-section discrepancy
that this N=10000 rerun has now confirmed was pure sampling noise:

- LO: 100 events, cross section 522.309 ± 4.897 pb, normalized weight sum matched
  exactly (522.309 pb, 6 sig. figs — trivial since all weights are identical at LO).
- NLO: 100 events, cross section (quoted) 699.9608 ± 4.237205 pb, but **normalized
  weight sum was 804.988 pb** — a ~15% discrepancy. Explanation (now confirmed by the
  N=10000 result above): the NLO weights take only two discrete magnitudes
  ($\pm1149.983$ pb); the sample average reproduces the quoted cross section only if the
  realized negative-weight fraction matches the expected $\approx19.6\%$. At $N=100$,
  only 15% were realized negative (within $\sim$1.1σ of a binomial fluctuation,
  $\sigma_{\rm frac}\approx4\%$) — a plausible but non-trivial deviation purely from
  small-sample counting statistics on the weight sign. At $N=10000$, the realized
  fraction (19.83%) converges tightly to the expected value, confirming this diagnosis
  and validating both runs' underlying correctness.
- Negative-weight fraction at N=100: 15% (15/100).

Data/figures from the N=100 run were overwritten in place by the N=10000 rerun (same
output paths); the N=100 LHE files themselves remain on disk
(`events/pp_ttbar_lo_13tev/Events/run_01/`, `events/pp_ttbar_nlo_13tev/Events/run_11/`)
if needed for comparison.
