# LO vs NLO QCD Comparison: $t\bar{t}$ Production at the LHC

*Just an alien who lost his way — July 2026*

## Target

The goal of this study is to **demonstrate the NLO QCD simulation capability** of our MadGraph-based pipeline, using Standard Model $t\bar{t}$ production at the LHC as the benchmark process.

All observables are computed at both LO and NLO with identical settings (same $\sqrt{s}$, $m_t$, scale choice), so that every difference between the two results is attributable to the NLO corrections themselves. No comparison with external or literature data is performed in this study; the comparison is strictly LO vs NLO, internally.

Fixed inputs: $m_t = 172.5~\text{GeV}$, $\sqrt{s} = 13~\text{TeV}$, $\mu_R = \mu_F = H_T/2$ (dynamic).

The deliverables are organized in three tiers:

### Tier 1 — Rates and uncertainties (the headline numbers)

1. Total cross sections $\sigma_{\text{LO}}$ and $\sigma_{\text{NLO}}$ (pb, with Monte Carlo integration errors).
2. The $K$-factor $K = \sigma_{\text{NLO}}/\sigma_{\text{LO}}$.
3. **Scale uncertainty** of each cross section from independent 7-point variation of $(\mu_R, \mu_F)$ by factors of $\{1/2, 1, 2\}$ around the central scale, excluding the two opposite-extreme combinations. Report as $\sigma^{+\Delta^+\%}_{-\Delta^-\%}$ at each order.

   *Key validation point: the NLO scale band must be substantially narrower than the LO band — this reduction of theoretical uncertainty is the principal reason NLO matters.*

### Tier 2 — Differential distributions (the physics plots)

All distributions are computed at parton level for both LO and NLO and overlaid on shared figures, each with a lower ratio panel NLO/LO (the differential $K$-factor):

1. $d\sigma/dp_T^{\,t\bar{t}}$ — transverse momentum of the $t\bar{t}$ **system**.

   *Validation point: at LO this is a delta function at $p_T^{\,t\bar{t}} = 0$ (back-to-back kinematics); the entire nonzero spectrum exists only because of NLO real emission. This is the single most direct visual proof that NLO is working.*

2. $d\sigma/d\Delta\phi_{t\bar{t}}$ — azimuthal separation of the pair, folded into $[0, \pi]$:

   $$
   \Delta\phi_{t\bar{t}} =
   \begin{cases}
       |\phi_t - \phi_{\bar{t}}| & \text{if } \leq \pi \\
       2\pi - |\phi_t - \phi_{\bar{t}}| & \text{otherwise}
   \end{cases}
   $$

   $\Delta\phi = \pi$ exactly at LO; NLO generates the tail below $\pi$.

3. $d\sigma/dp_T^{\,t}$ — top quark transverse momentum (shape-changing $K$-factor in the tail).
4. $d\sigma/dm_{t\bar{t}}$ — invariant mass of the pair.
5. $d\sigma/dy_t$ — top quark rapidity.

### Tier 3 — Technical evidence of a correct NLO calculation

1. The **fraction of negative-weight events** in the NLO sample (expected nonzero, typically $\mathcal{O}(10\%)$ for fixed-order $t\bar{t}$; exactly zero would indicate the run was not actually NLO).
2. The number of `<wgt>` variation entries per event in the NLO LHE header (proof that scale reweighting ran) and the list of their labels.
3. Confirmation that the virtual (loop) contribution was evaluated (e.g. from the MG5 run log: loop libraries loaded, `[QCD]` mode active).

## Model

Pure Standard Model QCD; no BSM model required. Use the built-in SM for the LO run and the NLO-capable loop model (`loop_sm` variant, pipeline default) for the NLO run.

### Parameters

- $m_t = 172.5~\text{GeV}$ (pole mass, fixed).
- Order-matched PDFs (do not mix): `NNPDF23_lo_as_0130_qed` for LO, `NNPDF23_nlo_as_0119_qed` for NLO. $\alpha_s$ is taken from the corresponding PDF set.
- Central scales, dynamic, event by event:

  $$
  \mu_R = \mu_F = \frac{H_T}{2}, \qquad H_T \equiv \sum_{i \in \text{final state}} \sqrt{m_i^2 + p_{T,i}^2}
  $$

  (MadGraph `dynamical_scale_choice = 3`).

## Collider Process

### Process

$$
pp \to t\bar{t}
$$

Top quarks are kept **stable** (undecayed); the analysis uses the $t$ and $\bar{t}$ momenta directly from the event record. No parton shower, hadronization, or detector simulation: this is a fixed-order, parton-level study.

### Simulation Runs

| Run | Order | Process syntax | PDF set | $N_{\text{events}}$ |
|---|---|---|---|---|
| 1 | LO | `p p > t t~` | `NNPDF23_lo_as_0130_qed` | 100,000 |
| 2 | NLO | `p p > t t~ [QCD]` | `NNPDF23_nlo_as_0119_qed` | 100,000 |

Common settings for both runs: $E_{\text{beam}} = 6500~\text{GeV}$ per beam; scale reweighting (systematics module) **enabled** in both runs so that the 7-point scale envelope of Tier 1 can be extracted from the stored per-event weights without re-running.

If compute time requires it, event counts may be reduced, but not below 10,000 per run; otherwise tails and error bars are meaningless.

## Numerical Analysis

### Event extraction

For each run, read the LHE output. Identify $t$ (PDG id 6) and $\bar{t}$ (PDG id $-6$); build all Tier-2 observables from their four-momenta. Histogram everything with the **signed** event weight $w_i$ (NLO weights may be negative).

### Cross sections and scale bands

Take $\sigma_{\text{LO}}$, $\sigma_{\text{NLO}}$ and their MC errors from the run summaries. Build the 7-point scale envelope at each order from the stored variation weights: the quoted uncertainty is the maximum upward and downward excursion of the total rate across the 7 scale combinations.

### Histograms

Differential cross sections per bin:

$$
\left.\frac{d\sigma}{dX}\right|_{\text{bin}} = \frac{\sum_{i \in \text{bin}} w_i}{\Delta X}, \qquad \delta = \frac{\sqrt{\sum_{i \in \text{bin}} w_i^2}}{\Delta X}
$$

Binning:

- $|p_T^{\,t\bar{t}}|$: 40 bins, $[0, 400]$ GeV, log $y$-axis. (Plot the LO delta at zero as a single first-bin entry and state its content in the caption.)
- $|\Delta\phi_{t\bar{t}}|$: 40 bins, $[0, \pi]$, log $y$-axis.
- $|p_T^{\,t}|$: 40 bins, $[0, 800]$ GeV, log $y$-axis.
- $m_{t\bar{t}}$: 40 bins, $[300, 1500]$ GeV, log $y$-axis.
- $y_t$: 40 bins, $[-3, 3]$, linear $y$-axis.

### Figures

One figure per observable, each with:

- Upper panel: LO (**green** step histogram) and NLO (**blue** step histogram) with statistical error bars; NLO additionally drawn with a **shaded scale-uncertainty band** from the 7-point envelope computed bin by bin.
- Lower panel: ratio NLO/LO (differential $K$-factor) with its uncertainty, horizontal reference line at 1. (For $p_T^{\,t\bar{t}}$ and $\Delta\phi_{t\bar{t}}$, where LO is a delta function, omit the ratio panel.)
- Label: $\sqrt{s}=13$ TeV, $m_t = 172.5$ GeV, $\mu_R=\mu_F=H_T/2$, PDF names.
- Saved as PDF and PNG with descriptive filenames.

### Summary table

Produce a single summary table:

| | LO | NLO |
|---|---|---|
| $\sigma$ [pb] $\pm$ MC err | … | … |
| Scale envelope [%] | $+\ldots/-\ldots$ | $+\ldots/-\ldots$ |
| $K$-factor | … *(one value, both orders)* | |
| Negative-weight fraction | 0 | … |
| `<wgt>` entries per event | … | … |

## Acceptance Criteria

The task is complete **only** if the final report contains all of the following, taken from the actual runs (not illustrative examples):

1. The completed summary table above, with real numbers.
2. $K$-factor in a physically sensible range (roughly 1.3–1.6 for these settings); flag and investigate otherwise.
3. NLO scale band **narrower** than the LO scale band.
4. All five figures, produced from the actual event samples.
5. Physics checks passed: LO events exactly at $p_T^{\,t\bar{t}}=0$ and $\Delta\phi_{t\bar{t}}=\pi$; nonvanishing NLO tails in both; nonzero negative-weight fraction at NLO.

If any run or analysis step fails, report the task as **BLOCKED** with the failing step and its full error; do not report success with partial or illustrative results.
