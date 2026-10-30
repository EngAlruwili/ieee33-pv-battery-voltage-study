# Verification and preparation-run results

**Prepared for Abdullah Alruwaili.** The checks below were executed by the assistant during package preparation on **30 October 2026**, not by Abdullah. They do not establish his personal review or completion. These are genuine software outputs from the supplied model; the profiles and device ratings remain synthetic assumptions.

## What was run

| Check | Observed outcome |
| --- | --- |
| Environment | Python 3.12.14, Windows 11; pandapower 3.3.1 |
| Dependency consistency | `pip check`: no broken requirements |
| Engineering tests | Eight tests passed; see `evidence/tests.txt` |
| Default study | All 72 hourly scenario power flows and two nominal benchmark solves completed |
| Sensitivity study | Nine cases × three scenarios × 24 hours = 648 hourly power flows completed |
| Figures | Seven PNG and seven SVG plots generated; figures visually reviewed |
| Input and source provenance | SHA-256 hashes and package versions saved with each completed study |

The full environment snapshot is `requirements-lock.txt`. Main-run metadata and numerical checks are in `evidence/default_run/manifest.json` and `validation.json`. Sensitivity evidence is in `evidence/sensitivity_run/`. Plot input and script hashes are in `evidence/default_run/figures/provenance.json`. Numerical results were regenerated after final plotting/provenance changes; all reported model values remained unchanged.

The local application initially produced a Matplotlib cache permission warning. Final run and plot commands used a writable workspace cache directory. This was an environment configuration issue; it did not alter the model. On an ordinary local installation the default user cache should work. If a restricted environment gives the same warning, set `MPLCONFIGDIR` to a writable folder before starting Python.

## Nominal feeder check

At unscaled original demand and a 1.0 pu slack, the calculated minimum voltage was **0.913090481 pu at bus 18**, and active line loss was **0.202677121 MW**. The maximum BFSW versus Newton–Raphson voltage difference was approximately **1.32 × 10⁻⁹ pu**; the loss difference was **5.51 × 10⁻⁹ MW**. These are actual preparation-run calculations, not values inserted into the result tables.

The two algorithms share the same library and case data. No comparison against an independently executed MATPOWER model, real feeder measurement or hardware experiment has been performed.

## Default synthetic-day results

Rounded values below are taken from `evidence/default_run/summary.csv`; use that CSV for full precision.

| Metric | Baseline | PV only | PV + BESS |
| --- | ---: | ---: | ---: |
| Daily line loss (MWh) | 2.872559 | 2.244832 | 2.079993 |
| Battery conversion loss (MWh) | 0 | 0 | 0.172421 |
| Combined modeled loss (MWh) | 2.872559 | 2.244832 | 2.252414 |
| Line-loss reduction vs baseline (%) | 0 | 21.8525 | 27.5909 |
| Combined-loss reduction vs baseline (%) | 0 | 21.8525 | 21.5886 |
| Minimum voltage (pu) | 0.913090 | 0.914919 | 0.920269 |
| Maximum voltage (pu) | 1.000000 | 1.008015 | 1.003551 |
| Mean absolute voltage deviation (pu) | 0.038764 | 0.029024 | 0.028950 |
| Voltage violation exposure (bus-hours) | 284 | 129 | 118 |
| Hours with any voltage violation | 18 | 9 | 9 |
| Peak grid import (MW) | 3.917677 | 3.870079 | 3.497158 |

![Loss accounting and remaining voltage violations](../evidence/default_run/figures/06_loss_and_voltage_summary.png)

The PV + BESS case reduces line losses by about **27.6%** relative to baseline. Its battery, however, adds **0.172421 MWh** of conversion loss while saving about **0.164839 MWh** of line loss relative to PV only. Consequently, combined modeled loss is about **0.007582 MWh (7.58 kWh) higher** than PV only. The default battery improves some voltage and peak-import metrics but does not improve combined energy loss over PV alone.

Voltage violation exposure decreases, but **118 bus-hours remain outside the assumed band** in the PV + BESS case. The project therefore demonstrates voltage support and feeder-loss reduction under these assumptions, not elimination of voltage violations or universally beneficial battery sizing.

The battery charges with approximately 1.768421 MWh AC and discharges 1.596000 MWh AC. Its starting and ending stored energy are equal. All scenarios serve the same 68.133100 MWh demand; both PV scenarios generate 13.881000 MWh. The largest default hourly active-power balance residual is below 3.4 × 10⁻⁸ MW.

## What Abdullah still needs to do

Reproduce the project in his own environment, review the code and input assumptions, hand-check battery accounting, examine the sensitivity table, and write his own interpretation. Before broader claims, use representative data, evaluate alternative placements and controls, and perform an independent model comparison. No macOS/Linux verification, annual study, economic assessment, thermal assessment or regulatory approval has been performed.
