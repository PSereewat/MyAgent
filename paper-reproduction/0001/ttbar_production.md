# $t\bar{t}$ Production

**Author:** Just an alien who lost his way  
**Date:** July 2026

---

## 1. Target

Consider the $t\bar{t}$ production process described in this document. We aim to compute and compare the following observables at leading order (LO) and next-to-leading order (NLO) in QCD, at fixed top quark mass $m_t = 172.5~\mathrm{GeV}$ and center-of-mass energy $\sqrt{s} = 13~\mathrm{TeV}$:

1. **Azimuthal angle distribution** between the top quark and antitop quark:

$$\frac{d\sigma}{d\Delta\phi_{t\bar{t}}}$$

where $\Delta\phi_{t\bar{t}} = |\phi_t - \phi_{\bar{t}}|$ in the range $0 \leq \Delta\phi_{t\bar{t}} \leq \pi$.

---

## 2. Model

This is a pure Standard Model QCD process. No BSM model is required. The full QCD Lagrangian is:

$$\mathcal{L}_{\mathrm{QCD}} = -\frac{1}{4} G^a_{\mu\nu} G^{a\mu\nu} + \sum_{q} \bar{q}\left(i\gamma^\mu D_\mu - m_q\right)q$$

where the sum runs over all quark flavors $q = u, d, s, c, b, t$, and $m_q$ is the mass of each quark.

The gluon field strength tensor is:

$$G^a_{\mu\nu} = \partial_\mu G^a_\nu - \partial_\nu G^a_\mu + g_s f^{abc} G^b_\mu G^c_\nu$$

where $g_s$ is the strong coupling constant, $f^{abc}$ are the SU(3) structure constants, and $G^a_\mu$ is the gluon field.

The covariant derivative acting on quarks is:

$$D_\mu = \partial_\mu - ig_s T^a G^a_\mu$$

where $T^a = \lambda^a/2$ are the SU(3) color generators ($\lambda^a$ are the Gell-Mann matrices).

The Lagrangian contains three interaction vertices relevant to $t\bar{t}$ production:

$$\mathcal{L}_{\mathrm{QCD}} \supset \underbrace{g_s \sum_{q} \bar{q}\,\gamma^\mu T^a q\, G^a_\mu}_{\text{quark-gluon vertex}} \underbrace{-\, g_s f^{abc}(\partial_\mu G^a_\nu)\, G^{b\mu} G^{c\nu}}_{\text{3-gluon vertex}} \underbrace{-\, \frac{g_s^2}{4} f^{abc} f^{ade} G^b_\mu G^c_\nu G^{d\mu} G^{e\nu}}_{\text{4-gluon vertex}}$$

### Parameters

The only free parameter relevant to this study is the top quark mass:

- $m_t = 172.5~\mathrm{GeV}$ (fixed, world average)
- The strong coupling constant $\alpha_s$ depends on whether the process is LO or NLO. For LO, $\alpha_s$ is determined by the PDF set `NNPDF23_lo_as_0130_qed`. For NLO, the PDF set `NNPDF23_nlo_as_0119_qed` is used. In both cases, $\alpha_s$ is evaluated at the dynamic renormalisation scale, and the PDF is evaluated at the factorisation scale, with both set equal:

$$\mu_R = \mu_F = \frac{H_T}{2} = \frac{p_{T,t} + p_{T,\bar{t}}}{2}$$

which varies event by event.

---

## 3. Collider Process

### Process

The collider process considered in this study is:

$$pp \to t\bar{t}$$

### Collider Simulation Settings

The simulation is performed for proton-proton collisions at the LHC with:

$$\sqrt{s} = 13~\mathrm{TeV}$$

The top quark decay width is computed automatically (`set param_card DECAY 6 Auto`).

### Parameter Settings

Two simulation runs are performed, both at $\sqrt{s} = 13~\mathrm{TeV}$ with fixed top quark mass $m_t = 172.5~\mathrm{GeV}$:

| Run | Order | Process | PDF set |
|-----|-------|---------|---------|
| 1 | LO | $pp \to t\bar{t}$ | `NNPDF23_lo_as_0130_qed` |
| 2 | NLO | $pp \to t\bar{t}~[\mathrm{QCD}]$ | `NNPDF23_nlo_as_0119_qed` |

Both runs use the same kinematic settings:

- Number of events: $N = 10$
- Beam energy: $E_{\mathrm{beam}} = 6500~\mathrm{GeV}$ per beam
- Renormalisation and factorisation scale: $\mu_R = \mu_F = H_T/2$ (dynamic, per event)
- Top quark decay width: computed automatically

This gives a total of 2 simulation runs.

---

## 4. Numerical Analysis

### Procedure to Reproduce the Figure

The numerical analysis is performed in two main steps.

#### Step 1: Extract Events from LHE File

For each run (LO and NLO), the generated events are read from the `unweighted_events.lhe.gz` output file. For each event, the azimuthal angle difference is computed as:

$$\Delta\phi_{t\bar{t}} = |\phi_t - \phi_{\bar{t}}|$$

and a binned distribution is filled with event weight $w_i$ (which may be negative for NLO events).

#### Step 2: Normalize and Plot

Each bin is divided by its bin width $\Delta(\Delta\phi_{t\bar{t}})$ to obtain the differential cross section:

$$\frac{d\sigma}{d\Delta\phi_{t\bar{t}}} \approx \frac{\sum_{i \in \mathrm{bin}} w_i}{\Delta(\Delta\phi_{t\bar{t}})}$$

The LO and NLO distributions are plotted on the same figure.

### Plot Settings

The plot is produced using the following settings:

- **Binning**: 20 uniform bins over $[0, \pi]$, giving a bin width of $\Delta(\Delta\phi_{t\bar{t}}) = \pi/20 \approx 0.157$ rad.
- The $x$-axis represents $\Delta\phi_{t\bar{t}}$ in radians, shown on a **linear** scale in the range $0 \leq \Delta\phi_{t\bar{t}} \leq \pi$.
- The $y$-axis represents the differential cross section $d\sigma/d\Delta\phi_{t\bar{t}}$ in pb rad$^{-1}$, shown on a **linear** scale from $0$ to $1.1 \times \max(d\sigma/d\Delta\phi_{t\bar{t}})$.
- Two curves are plotted as step functions:
  - LO: **green** solid line
  - NLO: **blue** solid line
- **Error bars**: statistical uncertainty at each bin, computed as:

$$\delta\!\left(\frac{d\sigma}{d\Delta\phi_{t\bar{t}}}\right) = \frac{\sqrt{\sum_{i \in \mathrm{bin}} w_i^2}}{\Delta(\Delta\phi)}$$
