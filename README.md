# Voltage Regulation and Energy Loss Reduction in a Distribution Network Using Solar PV and Battery Storage

**Project author: Abdullah Alruwaili**  
Electrical and Electronics Engineering student, University of Jeddah  
Specialization: Power Engineering

An undergraduate simulation project using Python and pandapower to investigate how distributed solar PV and battery storage affect the IEEE 33-bus distribution feeder. No physical hardware is required.

**Status:** prepared with AI assistance for Abdullah to review, understand, reproduce, and adapt. Repository authorship does not imply that Abdullah has already performed the included runs or endorsed the conclusions. See [verification status](docs/VERIFICATION.md) for the checks actually performed during preparation. The project title describes an engineering objective; improvement in every metric is not assumed.

## Engineering question

Can downstream PV reduce daytime voltage drop and feeder losses, and can a constrained battery shift some energy to evening demand without hiding battery losses or using unaccounted initial energy?

Compare three cases with identical loads and source voltage:

| Case | PV | Battery | Purpose |
| --- | --- | --- | --- |
| Baseline | None | None | Original radial feeder |
| PV only | 0.9 MW at bus 18; 1.2 MW at bus 33 | None | Isolate the PV contribution |
| PV + BESS | Same PV | 0.6 MW / 2.4 MWh at bus 33 | Evaluate daytime charging and evening support |

These are transparent study design choices, not optimized equipment ratings or measured installations. All reporting uses original physical bus numbers 1–33; pandapower indices are 0–32. PV operates at unity power factor; the battery provides active power only. The 24-hour load and PV profiles are explicitly synthetic, not Jeddah utility or weather data.

## Quick start

Use **Python 3.12**. Open a terminal in the extracted repository folder. The full dependency snapshot is in `requirements-lock.txt`; `requirements.txt` pins direct dependencies. Internet access is required for the initial installation, but the feeder and profiles are local after installation.

Windows PowerShell (activation is unnecessary):

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe run_study.py --output results/run_01
.\.venv\Scripts\python.exe plot_results.py --input results/run_01
.\.venv\Scripts\python.exe run_sensitivity.py --output results/sensitivity_01
```

macOS/Linux:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-lock.txt
.venv/bin/python -m pip check
.venv/bin/python -m pytest -q
.venv/bin/python run_study.py --output results/run_01
.venv/bin/python plot_results.py --input results/run_01
.venv/bin/python run_sensitivity.py --output results/sensitivity_01
```

The packaged environment was verified only on the platform listed in `docs/VERIFICATION.md`. Other platforms need a local verification run. If a locked package has no compatible wheel, use `requirements.txt` in a fresh environment, record `python -m pip freeze`, and rerun all checks. Do not silently substitute dependency versions in a published result.

The main study solves 72 hourly cases plus two nominal benchmark power flows. The sensitivity study solves another 648 hourly cases. Execution time depends on the computer. Scripts refuse to overwrite a nonempty study output folder; choose `run_02` for another run. A failed run must not be treated as complete. Only a main run with `manifest.json` marked `completed` should be plotted or cited.

## Repository map

```text
voltage-regulation-pv-bess/
├── README.md
├── requirements.txt                  # Direct dependency pins
├── requirements-lock.txt             # Full preparation-environment snapshot
├── CITATION.cff
├── CONTRIBUTING.md
├── config/default.json               # PV, battery and voltage settings
├── data/profiles.csv                 # Synthetic hourly demand and sunshine
├── data/README.md                    # Input provenance and units
├── study/
│   ├── __init__.py
│   ├── inputs.py                     # Input validation
│   ├── network.py                    # case33bw, device placement, solver
│   ├── dispatch.py                   # Battery schedule and energy recursion
│   ├── simulation.py                 # Scenarios, records and metrics
│   └── validation.py                 # Benchmark and conservation checks
├── run_study.py
├── plot_results.py
├── run_sensitivity.py
├── tests/test_engineering.py
├── docs/
│   ├── PROJECT_GUIDE.md              # Method, equations, validation and limitations
│   ├── MENTOR_GUIDE.md                # Learning sequence and presentation questions
│   ├── PUBLICATION_KIT.md            # GitHub description, tags and LinkedIn draft
│   ├── RESULTS_TEMPLATE.md           # Human interpretation worksheet
│   ├── REFERENCES.md
│   └── VERIFICATION.md
├── evidence/                         # Preparation-run evidence; not Abdullah's own run
└── results/                          # New local runs; ignored by Git
```

## Outputs and interpretation

| Output | What it contains |
| --- | --- |
| `hourly.csv` | Grid power, loss, voltage extrema, violations, battery state and balance residuals |
| `bus_voltages.csv` | All 33 bus voltages at every hour in each scenario |
| `line_results.csv` | Active-branch losses and currents; no invented ampacity ratings |
| `summary.csv` | Daily line and conversion losses, imports, exports, peak import and voltage indicators |
| `validation.json` | Nominal feeder and two-solver comparison |
| `manifest.json` | Run completion, versions, UTC timestamp, input and source hashes |
| `RESULTS.md` | Automatically calculated summary for review |
| `figures/` | Seven figure sets in PNG and editable SVG formats |
| `sensitivity.csv` | Nine one-factor-at-a-time cases with all three scenarios |

The figures cover inputs, daily voltage and losses, noon/evening bus profiles, voltage heatmaps, battery dispatch and SOC, loss accounting, and grid exchange. The included evidence is generated output; the input profiles and device ratings are assumptions. No numerical claim should be copied into a CV or post without understanding the inputs and reproducing the run.

Read **[the project guide](docs/PROJECT_GUIDE.md)** for equations and model assumptions. Use **[the mentor guide](docs/MENTOR_GUIDE.md)** to prepare an explanation and **[the results worksheet](docs/RESULTS_TEMPLATE.md)** to write a conclusion. Report both improvements and remaining problems. A lower import is not itself a lower energy loss; PV supplies part of the load.

## Adapt the project

Copy `config/default.json`, change one parameter, and run:

```bash
python run_study.py --config config/my_case.json --profiles data/profiles.csv --output results/my_case
python plot_results.py --input results/my_case
```

The present dispatcher requires a full 24-hour day and all charging hours before all discharge hours. Moving the battery away from every PV unit gives zero charging under the co-located-PV policy. Different control logic, time steps, multi-day operation, or reactive-power support require code changes and new checks. A power-flow solver does not enforce voltage targets or battery energy limits automatically.

## Attribution and reuse

The feeder is the Baran–Wu 33-bus case supplied by pandapower from MATPOWER, commonly called the IEEE 33-bus system. Cite the original dataset and tools as well as this project; see [references](docs/REFERENCES.md) and `CITATION.cff`. This is an educational application, with no unsupported novelty claim or implied university endorsement. No project software license is selected in this preparation package; Abdullah should choose one before offering reuse rights. Third-party tools retain their own licenses.
