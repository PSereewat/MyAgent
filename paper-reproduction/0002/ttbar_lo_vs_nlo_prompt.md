# LO vs NLO QCD Comparison: t tbar Production at the LHC

## 1. Target

The goal of this study is to **demonstrate the NLO QCD simulation capability** of our MadGraph-based pipeline, using Standard Model t tbar production at the LHC as the benchmark process. All observables are computed at both LO and NLO with identical settings (same sqrt(s), m_t, scale choice), so that every difference between the two results is attributable to the NLO corrections themselves. No comparison with external or literature data is performed in this study; the comparison is strictly LO vs NLO, internally.

Fixed inputs: m_t = 172.5 GeV, sqrt(s) = 13 TeV, mu_R = mu_F = H_T/2 (dynamic).

The deliverables are organized in three tiers:

### Tier 1 — Rates and uncertainties (the headline numbers)

1. Total cross sections sigma_LO and sigma_NLO (pb, with Monte Carlo integration errors).
2. The K-factor: K = sigma_NLO / sigma_LO.
3. **Scale uncertainty** of each cross section from independent 7-point variation of (mu_R, mu_F) by factors of {1/2, 1, 2} around the central scale, excluding the two opposite-extreme combinations. Report as sigma +X% / -Y% at each order.
   *Key validation point: the NLO scale band must be substantially narrower than the LO band — this reduction of theoretical uncertainty is the principal reason NLO matters.*

### Tier 2 — Differential distributions (the physics plots)

All distributions are computed at parton level for both LO and NLO and overlaid on shared figures, each with a lower ratio panel NLO/LO (the differential K-factor):

1. **d(sigma)/d(pT of the t-tbar system)** — transverse momentum of the t tbar **system**.
   *Validation point: at LO this is a delta function at pT(ttbar) = 0 (back-to-back kinematics); the entire nonzero spectrum exists only because of NLO real emission. This is the single most direct visual proof that NLO is working.*
2. **d(sigma)/d(Delta-phi of the pair)** — azimuthal separation, folded into [0, pi]:
   - Delta-phi = |phi_t − phi_tbar| if that is ≤ pi
   - Delta-phi = 2*pi − |phi_t − phi_tbar| otherwise
   Delta-phi = pi exactly at LO; NLO generates the tail below pi.
3. **d(sigma)/d(pT of the top quark)** — shape-changing K-factor in the tail.
4. **d(sigma)/d(m of the t-tbar pair)** — invariant mass of the pair.
5. **d(sigma)/d(y of the top quark)** — top quark rapidity.

### Tier 3 — Technical evidence of a correct NLO calculation

1. The **fraction of negative-weight events** in the NLO sample (expected nonzero, typically O(10%) for fixed-order t tbar; exactly zero would indicate the run was not actually NLO).
2. The number of `<wgt>` variation entries per event in the NLO LHE header (proof that scale reweighting ran) and the list of their labels.
3. Confirmation that the virtual (loop) contribution was evaluated (e.g. from the MG5 run log: loop libraries loaded, `[QCD]` mode active).

---

## 2. Model

Pure Standard Model QCD; no BSM model required. Use the built-in SM for the LO run and the NLO-capable loop model (`loop_sm` variant, pipeline default) for the NLO run.

### Parameters

- m_t = 172.5 GeV (pole mass, fixed).
- Order-matched PDFs (do not mix):
  - LO: `NNPDF23_lo_as_0130_qed`
  - NLO: `NNPDF23_nlo_as_0119_qed`
  - alpha_s is taken from the corresponding PDF set.
- Central scales, dynamic, event by event:

  mu_R = mu_F = H_T / 2, where H_T = sum over final-state particles of sqrt(m_i^2 + pT_i^2)

  (half the sum of transverse masses; MadGraph `dynamical_scale_choice = 3`).

---

## 3. Collider Process

### Process

    p p > t t~

Top quarks are kept **stable** (undecayed); the analysis uses the t and tbar momenta directly from the event record. No parton shower, hadronization, or detector simulation: this is a fixed-order, parton-level study.

### Simulation Runs

| Run | Order | Process syntax | PDF set | N_events |
|---|---|---|---|---|
| 1 | LO | `p p > t t~` | `NNPDF23_lo_as_0130_qed` | 100000 |
| 2 | NLO | `p p > t t~ [QCD]` | `NNPDF23_nlo_as_0119_qed` | 100000 |

Common settings for both runs:

- Beam energy: 6500 GeV per beam (sqrt(s) = 13 TeV).
- Scale reweighting (systematics module) **enabled** in both runs, so the 7-point scale envelope of Tier 1 can be extracted from the stored per-event weights without re-running.
- If compute time requires it, event counts may be reduced, but not below 10000 per run; otherwise tails and error bars are meaningless.

---

## 4. Numerical Analysis

### Step 1: Event extraction

For each run, read the LHE output. Identify t (PDG id 6) and tbar (PDG id −6); build all Tier-2 observables from their four-momenta. Histogram everything with the **signed** event weight w_i (NLO weights may be negative).

### Step 2: Cross sections and scale bands

Take sigma_LO, sigma_NLO and their MC errors from the run summaries. Build the 7-point scale envelope at each order from the stored variation weights: the quoted uncertainty is the maximum upward and downward excursion of the total rate across the 7 scale combinations.

### Step 3: Histograms

Differential cross section per bin:

    dsigma/dX |_bin = (sum of w_i in bin) / (bin width)

Statistical uncertainty per bin:

    delta = sqrt(sum of w_i^2 in bin) / (bin width)

Binning:

| Observable | Bins | Range | y-axis |
|---|---|---|---|
| pT(ttbar system) | 40 | [0, 400] GeV | log |
| Delta-phi(ttbar) | 40 | [0, pi] | log |
| pT(t) | 40 | [0, 800] GeV | log |
| m(ttbar) | 40 | [300, 1500] GeV | log |
| y(t) | 40 | [−3, 3] | linear |

For pT(ttbar): plot the LO delta at zero as a single first-bin entry and state its content in the caption.

### Step 4: Figures

One figure per observable, each with:

- **Upper panel:** LO (green solid step histogram, RGB 0,120,0) and NLO (blue solid step histogram, RGB 0,0,200) with statistical error bars; NLO additionally drawn with a **shaded scale-uncertainty band** from the 7-point envelope computed bin by bin.
- **Lower panel:** ratio NLO/LO (differential K-factor) with its uncertainty, horizontal reference line at 1. (For pT(ttbar) and Delta-phi, where LO is a delta function, omit the ratio panel.)
- Label on each figure: sqrt(s) = 13 TeV, m_t = 172.5 GeV, mu_R = mu_F = H_T/2, PDF names.
- Save each figure as PDF and PNG with descriptive filenames.

### Step 5: Summary table

Produce a single summary table:

| | LO | NLO |
|---|---|---|
| sigma [pb] ± MC err | ... | ... |
| Scale envelope [%] | +... / −... | +... / −... |
| K-factor | (one value) | |
| Negative-weight fraction | 0 | ... |
| `<wgt>` entries per event | ... | ... |

---

## 5. Acceptance Criteria

The task is complete **only** if the final report contains all of the following, taken from the actual runs (not illustrative examples):

1. The completed summary table above, with real numbers.
2. K-factor in a physically sensible range (roughly 1.3–1.6 for these settings); flag and investigate otherwise.
3. NLO scale band **narrower** than the LO scale band.
4. All five figures, produced from the actual event samples.
5. Physics checks passed: LO events exactly at pT(ttbar) = 0 and Delta-phi = pi; nonvanishing NLO tails in both; nonzero negative-weight fraction at NLO.

If any run or analysis step fails, report the task as **BLOCKED** with the failing step and its full error; do not report success with partial or illustrative results.
