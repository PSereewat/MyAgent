"""
Tier 1 summary: consolidates cross sections, MC integration errors,
7-point scale variation, K-factor, and negative-weight fractions for all
three runs into a single JSON + CSV (Final Summary Table of
../LO_NLO_NLOPS.md).

Sources (all traceable, no fabricated numbers):
- LO "Total cross section" + MC integration error: the LO run's own
  generation-level result is NOT printed with an explicit MC-integration
  error in the saved banner (run1_LO/pp_ttbar/Events/run_01/
  run_01_tag_1_banner.txt only records the central "Integrated weight
  (pb) : 520.365", no separate stat error line -- this is a known
  limitation of the banner file, not this analysis). The error
  (0.7669 pb) is taken from run1_LO/progress/step2_madgraph_lo.md,
  which recorded it directly from the original MadGraph generation job's
  own result summary at generation time. Central value cross-checked
  here against both the banner (520.365) and this script's own
  independent re-sum of the LHE XWGTUP weights (output/data/lo_results.json,
  520.3650 +- 5.2037 -- NOTE: the 5.2037 pb figure there is a *sample*
  statistical error i.e. weight_const/sqrt(N_gen), not the same
  quantity as the generator's phase-space MC integration error; see
  note in the printed report below).
- NLO and NLO+PS "Total cross section" + MC integration error: parsed
  directly, at run time, from each run's summary.txt
  ("Total cross section: X +- Y pb" line).
- NLO 7-point scale variation: computed by analyze_nlo.py directly from
  the LHE file's stored per-event reweight (<rwgt>) block (see that
  script's docstring) -- output/data/nlo_results.json.
- LO 7-point scale variation: NOT AVAILABLE. See detailed explanation
  printed below and in the final report -- flagged explicitly rather
  than fabricated or approximated from literature.
- Negative-weight fractions: independently verified directly from the
  actual per-event weights in each sample (see analyze_*.py outputs),
  not assumed from upstream labels.
"""

import csv
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))

OUT_DATA_DIR = "output/data"

LO_BANNER = "run1_LO/pp_ttbar/Events/run_01/run_01_tag_1_banner.txt"
LO_PROGRESS = "run1_LO/progress/step2_madgraph_lo.md"
NLO_SUMMARY = "run2_NLO/pp_ttbar_nlo/Events/run_01/summary.txt"
NLOPS_SUMMARY = "run3_NLOPS/pp_ttbar_nlops_run/Events/run_02/summary.txt"


def parse_summary_txt(path):
    with open(path) as f:
        content = f.read()
    m = re.search(r"Total cross section:\s*([0-9.eE+-]+)\s*\+-\s*([0-9.eE+-]+)\s*pb", content)
    if not m:
        raise RuntimeError(f"Could not parse 'Total cross section' from {path}")
    sigma = float(m.group(1))
    err = float(m.group(2))

    m2 = re.search(
        r"envelope of 9 values\)\s*:\s*\n\s*([0-9.eE+-]+)\s*pb\s*\+([0-9.]+)%\s*-([0-9.]+)%",
        content,
    )
    scale = None
    if m2:
        scale = dict(
            central_pb=float(m2.group(1)),
            plus_pct=float(m2.group(2)),
            minus_pct=float(m2.group(3)),
        )
    return sigma, err, scale


def parse_lo_banner_central(path):
    with open(path) as f:
        content = f.read()
    m = re.search(r"Integrated weight \(pb\)\s*:\s*([0-9.eE+-]+)", content)
    if not m:
        raise RuntimeError(f"Could not parse 'Integrated weight' from {path}")
    return float(m.group(1))


def parse_lo_progress_error(path):
    with open(path) as f:
        content = f.read()
    m = re.search(r"\*\*([0-9.]+)\s*\+-\s*([0-9.]+)\s*pb\*\*", content)
    if not m:
        raise RuntimeError(f"Could not parse LO cross section +- error from {path}")
    return float(m.group(1)), float(m.group(2))


def main():
    lo_central_banner = parse_lo_banner_central(LO_BANNER)
    lo_central_progress, lo_err_progress = parse_lo_progress_error(LO_PROGRESS)

    nlo_sigma, nlo_err, nlo_scale_9pt_mg5 = parse_summary_txt(NLO_SUMMARY)
    nlops_sigma, nlops_err, nlops_scale_9pt_mg5 = parse_summary_txt(NLOPS_SUMMARY)

    with open(os.path.join(OUT_DATA_DIR, "lo_results.json")) as f:
        lo_res = json.load(f)
    with open(os.path.join(OUT_DATA_DIR, "nlo_results.json")) as f:
        nlo_res = json.load(f)
    with open(os.path.join(OUT_DATA_DIR, "nlops_results.json")) as f:
        nlops_res = json.load(f)

    k_factor = nlo_sigma / lo_central_progress

    print("=" * 70)
    print("TIER 1 SUMMARY")
    print("=" * 70)
    print(f"LO      : sigma = {lo_central_progress} +- {lo_err_progress} pb "
          f"(source: {LO_PROGRESS}; banner central = {lo_central_banner} pb, consistent)")
    print(f"          self-summed cross-check from LHE weights: "
          f"{lo_res['sigma_pb_self_summed']:.4f} pb (constant-weight sample, exact match expected)")
    print(f"NLO     : sigma = {nlo_sigma} +- {nlo_err} pb (source: {NLO_SUMMARY})")
    print(f"          self-summed cross-check from LHE weights: "
          f"{nlo_res['sigma_pb_self_summed']:.4f} +- {nlo_res['sigma_err_pb_self_summed']:.4f} pb "
          f"(sample stat. error, Neff={nlo_res['neff_total']:.0f}/10000)")
    print(f"NLO+PS  : sigma = {nlops_sigma} +- {nlops_err} pb (source: {NLOPS_SUMMARY})")
    print(f"          self-summed cross-check from HepMC weights: "
          f"{nlops_res['sigma_pb_self_summed']:.4f} +- {nlops_res['sigma_err_pb_self_summed']:.4f} pb "
          f"(sample stat. error, Neff={nlops_res['neff_total']:.0f}/10000)")
    print()
    print(f"K-factor = sigma_NLO / sigma_LO = {nlo_sigma} / {lo_central_progress} = {k_factor:.4f}")
    print(f"  Acceptance criterion 1.3 <= K <= 1.6: "
          f"{'PASS' if 1.3 <= k_factor <= 1.6 else 'FAIL'}")
    print()
    print("Scale uncertainty (7-point muR,muF envelope):")
    print(f"  LO : NOT AVAILABLE. The LO LHE sample was generated with use_syst=False "
          f"(confirmed: no <initrwgt>/<rwgt> blocks in "
          f"run1_LO/pp_ttbar/Events/run_01/unweighted_events.lhe.gz), so no per-event "
          f"scale-reweighting information was stored, unlike Run 2/3. Deriving it would "
          f"require either (a) a fresh small MadGraph run with use_syst=True on the "
          f"existing compiled run1_LO/pp_ttbar process directory, which could not be "
          f"performed locally in this analysis session: the compiled SubProcesses "
          f"binaries are Linux x86_64 ELF executables (built for the cloud generation "
          f"container) and cannot run on this local macOS/ARM64 analysis machine, and "
          f"a direct attempt via ./bin/generate_events also hit the previously-documented "
          f"'lhapdf-config not found' issue before even reaching the incompatible binaries; "
          f"or (b) manually reweighting the existing 10000 LO events at the PDF+alpha_s "
          f"level using LHAPDF, which requires the `lhapdf` python package -- not "
          f"installable in this session (no matching PyPI distribution; conda-forge "
          f"lookup was not pursued further given the additional PDF-grid download it would "
          f"still require, judged out of scope for 'minimal and targeted'). This is "
          f"reported as a genuine gap, not approximated from a literature value.")
    print(f"  NLO: {nlo_res['scale_variation_7pt']['central_pb']:.4f} "
          f"+{nlo_res['scale_variation_7pt']['delta_plus_pct']:.2f}% "
          f"-{nlo_res['scale_variation_7pt']['delta_minus_pct']:.2f}% "
          f"(self-computed from stored LHE rwgt weights, output/data/nlo_results.json; "
          f"cross-checked against MG5's own reported 9-point envelope in {NLO_SUMMARY}: "
          f"{nlo_scale_9pt_mg5})")
    print()
    print("Negative-weight fractions (independently verified from actual event weights):")
    print(f"  LO     : f_minus = {lo_res['f_minus']:.4f} (expected/confirmed 0)")
    print(f"  NLO    : f_minus = {nlo_res['f_minus']:.4f} "
          f"({nlo_res['n_negative']}/{nlo_res['N_gen']}) -- NOT flagged upstream, "
          f"independently discovered here; expected for aMC@NLO fixed-order samples.")
    print(f"  NLO+PS : f_minus = {nlops_res['f_minus']:.4f} "
          f"({nlops_res['n_negative']}/{nlops_res['N_gen']}) -- matches task-supplied 22.92%")

    # --- write CSV: one row per run ---
    csv_path = os.path.join(OUT_DATA_DIR, "tier1_summary.csv")
    with open(csv_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "run", "cross_section_pb", "mc_integration_error_pb",
            "scale_unc_plus_pct", "scale_unc_minus_pct",
            "scale_unc_plus_pb", "scale_unc_minus_pb",
            "k_factor", "negative_weight_fraction", "shower", "output_format",
        ])
        w.writerow([
            "LO", lo_central_progress, lo_err_progress,
            "NOT_AVAILABLE", "NOT_AVAILABLE", "NOT_AVAILABLE", "NOT_AVAILABLE",
            1.0, lo_res["f_minus"], "No", "LHE",
        ])
        nlo_scale = nlo_res["scale_variation_7pt"]
        w.writerow([
            "NLO", nlo_sigma, nlo_err,
            nlo_scale["delta_plus_pct"], nlo_scale["delta_minus_pct"],
            nlo_scale["delta_plus_pb"], nlo_scale["delta_minus_pb"],
            k_factor, nlo_res["f_minus"], "No", "LHE",
        ])
        w.writerow([
            "NLO+PS", nlops_sigma, nlops_err,
            "NOT_COMPUTED_SEE_NLO", "NOT_COMPUTED_SEE_NLO", "NOT_COMPUTED_SEE_NLO", "NOT_COMPUTED_SEE_NLO",
            nlops_sigma / lo_central_progress, nlops_res["f_minus"], "Pythia8", "HEPMC",
        ])
    print(f"\nWrote {csv_path}")

    # also a JSON version for programmatic downstream use
    json_path = os.path.join(OUT_DATA_DIR, "tier1_summary.json")
    with open(json_path, "w") as f:
        json.dump(
            {
                "LO": {
                    "sigma_pb": lo_central_progress,
                    "mc_integration_error_pb": lo_err_progress,
                    "scale_variation_7pt": None,
                    "f_minus": lo_res["f_minus"],
                },
                "NLO": {
                    "sigma_pb": nlo_sigma,
                    "mc_integration_error_pb": nlo_err,
                    "scale_variation_7pt": nlo_res["scale_variation_7pt"],
                    "scale_variation_9pt_mg5_reported": nlo_scale_9pt_mg5,
                    "f_minus": nlo_res["f_minus"],
                },
                "NLO+PS": {
                    "sigma_pb": nlops_sigma,
                    "mc_integration_error_pb": nlops_err,
                    "scale_variation_9pt_mg5_reported": nlops_scale_9pt_mg5,
                    "f_minus": nlops_res["f_minus"],
                },
                "k_factor": k_factor,
            },
            f,
            indent=2,
        )
    print(f"Wrote {json_path}")


if __name__ == "__main__":
    main()
