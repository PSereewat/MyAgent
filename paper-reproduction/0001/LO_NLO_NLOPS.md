# LO vs NLO vs NLO+PS QCD Comparison: $t\bar{t}$ Production at the LHC

*Just an alien who lost his way — July 2026*

---

## Target

The goal of this study is to **demonstrate the complete collider simulation capability of our MadGraph-based pipeline**, using Standard Model $t\bar{t}$ production at the LHC as the benchmark process.

The study compares three levels of simulation:

1. **LO fixed-order**
2. **NLO fixed-order QCD**
3. **NLO+PS simulation using MC@NLO matching with Pythia8**

The purpose is to validate the complete collider workflow:

$$pp \rightarrow t\bar{t}$$

from perturbative QCD calculation to realistic event generation including parton showering and hadronization.

All simulations use identical collider inputs:

$$m_t = 172.5~\mathrm{GeV}$$
$$\sqrt{s} = 13~\mathrm{TeV}$$
$$\mu_R = \mu_F = H_T/2$$

Differences between LO, NLO, and NLO+PS are attributed to higher-order QCD corrections and shower effects.

---

## Simulation Levels

### Level 1 — LO

Leading-order matrix element:

$$pp \rightarrow t\bar{t}$$

Features:

- Tree-level amplitudes
- No virtual corrections
- No real emission
- No parton shower

Output: `events.lhe.gz`

---

### Level 2 — NLO Fixed Order

Next-to-leading order QCD:

$$pp \rightarrow t\bar{t}~\mathrm{[QCD]}$$

Includes:

- Born contribution
- Virtual loop corrections
- Real emission
- FKS subtraction

Output: `events.lhe.gz`

This is a parton-level prediction.

---

### Level 3 — NLO+PS (MC@NLO + Pythia8)

The NLO calculation is matched with a parton shower:

$$\boxed{\mathrm{NLO + MC@NLO + Pythia8}}$$

Workflow:

$$pp \rightarrow t\bar{t} \;\downarrow\; \mathrm{NLO~matrix~element} \;\downarrow\; \mathrm{MC@NLO~matching} \;\downarrow\; \mathrm{Pythia8~parton~shower} \;\downarrow\; \mathrm{Hadronization}$$

Output: `events_PYTHIA8.hepmc.gz`

This represents the realistic collider event sample.

---

## Tier 1 — Rates and Uncertainties

### Total Cross Sections

Report:

$$\sigma_{\mathrm{LO}} \qquad \sigma_{\mathrm{NLO}} \qquad \sigma_{\mathrm{NLO+PS}}$$

The K-factor:

$$K = \frac{\sigma_{\mathrm{NLO}}}{\sigma_{\mathrm{LO}}}$$

---

### Scale Uncertainty

Perform the 7-point variation:

$$(\mu_R,\mu_F) = (1/2,1),\ (1,1/2),\ (1,1),\ (1,2),\ (2,1),\ (1/2,1/2),\ (2,2)$$

Report:

$$\sigma^{+\Delta^+}_{-\Delta^-}$$

Expected behavior:

$$\Delta_{\mathrm{NLO}} < \Delta_{\mathrm{LO}}$$

---

## Tier 2 — Differential Observables

Compare LO, NLO fixed-order, and NLO+PS for each observable below.

### 1. Transverse Momentum of the Pair

Observable:

$$p_T^{t\bar{t}} = |\vec{p}_{T,t} + \vec{p}_{T,\bar{t}}|$$

Physics check:

- At LO: $p_T^{t\bar{t}} = 0$ because the pair is produced back-to-back.
- At NLO: $p_T^{t\bar{t}} > 0$ from real emission.
- At NLO+PS: additional soft radiation modifies the distribution.

---

### 2. Azimuthal Separation

$$\Delta\phi_{t\bar{t}} = |\phi_t - \phi_{\bar{t}}|\quad\text{folded into}\quad[0,\pi]$$

- LO: $\Delta\phi_{t\bar{t}} = \pi$
- NLO: $\Delta\phi_{t\bar{t}} < \pi$
- NLO+PS: further decorrelation from shower radiation.

---

### 3. Top Transverse Momentum

Observable: $p_T^t$

Studies:

- Hard QCD corrections
- High-energy tails
- Shower effects

---

### 4. Invariant Mass

Observable: $m_{t\bar{t}}$

Sensitive to:

- Higher-order corrections
- Radiation effects

---

### 5. Top Rapidity

Observable: $y_t$

Used to study:

- PDF effects
- Acceptance

---

## Tier 3 — Technical Validation

### NLO Validation

Confirm virtual contribution. The MG5 log must contain:

```
MadLoop
Virtual
COLLIER
```

---

### Negative Weight Fraction

For MC@NLO:

$$f_{\mathrm{neg}} = \frac{N_{\mathrm{negative}}}{N_{\mathrm{total}}}$$

Expected: $f_{\mathrm{neg}} > 0$. Zero negative weights indicates MC@NLO was not activated.

---

### NLO+PS Validation

The MG5 log must contain:

```
Preparing MCatNLO run
Compiling MCatNLO for PYTHIA8
Showering events...
```

Final output: `events_PYTHIA8_0.hepmc.gz`

The HEPMC file must contain:

- Showered events
- Hadronized events

---

## Simulation Runs

| Run | Order | Shower | Output |
|---|---|---|---|
| Run 1 | LO | OFF | LHE |
| Run 2 | NLO | OFF | LHE |
| Run 3 | NLO | PYTHIA8 | HEPMC |

---

## Common Parameters

Collider: $\sqrt{s} = 13~\mathrm{TeV}$

Top mass: $m_t = 172.5~\mathrm{GeV}$

Scale: $\mu_R = \mu_F = H_T/2$

---

## PDF Choice

| Run | PDF |
|---|---|
| LO | NNPDF23_lo_as_0130_qed |
| NLO | NNPDF23_nlo_as_0119_qed |
| NLO+PS | NNPDF23_nlo_as_0119_qed |

---

## Final Summary Table

| | LO | NLO | NLO+PS |
|---|---|---|---|
| Cross section [pb] | 520.4 | 700.0 | 702.3 |
| MC integration error | ± 0.7669 pb | ± 4.2 pb | ± 4.5 pb |
| Scale uncertainty | **not available** (see note) | +10.4% / −10.9% (692.7 pb central, self-computed 7-point envelope from stored LHE reweight block; cross-checked against MG5's own 9-point envelope, 693.4 pb +10.4%/−10.9%) | not separately recomputed (fixed-order NLO ME unchanged by shower; use the NLO column) |
| K-factor | 1.0 (reference) | 1.345 (= 700.0/520.4) | 1.350 (= 702.3/520.4) |
| Negative weights | 0 (0.00%, confirmed) | 19.88% (1988/10000) — independently discovered in this analysis, not flagged upstream | 22.92% (2292/10000) — independently reproduced, matches task-supplied value |
| Shower | No | No | Pythia8 (MC@NLO) |
| Output | LHE | LHE | HEPMC |

Note on the missing LO scale uncertainty: the LO sample
(`run1_LO/pp_ttbar/Events/run_01/unweighted_events.lhe.gz`) was generated
with `use_syst=False`, so it carries no `<initrwgt>`/`<rwgt>` per-event
scale-reweighting information (confirmed by direct inspection — unlike
Runs 2/3, which store a full 9-point `(muR,muF)` reweight block per
event). This analysis could not derive it locally: (a) relaunching the
compiled `run1_LO/pp_ttbar` process directory with `use_syst=True` is
blocked because its `SubProcesses` binaries are Linux x86_64 ELF
executables (built for the cloud generation container) that cannot
execute on this local macOS/ARM64 analysis machine, and a direct
`./bin/generate_events` attempt also hit the previously-documented
"`lhapdf-config` not found" failure before even reaching that
incompatibility; (b) an independent PDF+alpha_s reweighting of the
existing events would need the `lhapdf` python package, which has no
installable distribution in this offline-ish environment. See the
detailed diagnostic in `analysis/tier1_summary.py`'s printed output and
the main report for full detail. This is reported as a genuine gap, not
approximated from a literature value or fabricated.

---

## Acceptance Criteria

The task is complete only if:

1. LO, NLO, and NLO+PS samples are generated successfully.
2. The NLO uncertainty band is smaller than LO.
3. The K-factor is physically reasonable: $1.3 \lesssim K \lesssim 1.6$.
4. Physics checks pass:
   - LO: $p_T^{t\bar{t}} = 0$, $\Delta\phi_{t\bar{t}} = \pi$
   - NLO: non-zero radiation tails
   - NLO+PS: showered and hadronized HEPMC events
5. The final pipeline produces:

$$\boxed{\mathrm{MadGraph} \rightarrow \mathrm{MC@NLO} \rightarrow \mathrm{Pythia8} \rightarrow \mathrm{HEPMC} \rightarrow \mathrm{Analysis}}$$

If any stage fails, it must be reported as:

```
BLOCKED
```

along with:

- Failing stage
- Full error message
- Diagnostic information

No partial success should be reported.
