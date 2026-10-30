# Technical project guide

**Voltage Regulation and Energy Loss Reduction in a Distribution Network Using Solar PV and Battery Storage**  
Author: Abdullah Alruwaili · University of Jeddah · Electrical and Electronics Engineering · Power Engineering

Prepared for study, verification and adaptation. The author must review the supplied implementation and evidence before presenting the work as his own completed project.

## 1. Problem and objectives

Distribution feeders have impedance along the path from the substation to customers. Active and reactive demand cause voltage drop and resistive losses. Downstream generation can reduce upstream current, but the outcome depends on location, time, rating and reverse power flow. Solar output often falls before evening demand. A battery can shift energy to that period, but charging increases local demand and conversion losses consume energy.

This project asks whether selected PV and storage installations improve the feeder's voltage profile and reduce daily losses under a consistent set of assumptions. It develops four practical skills: constructing a reproducible AC load-flow model, managing time-dependent storage states, evaluating competing performance metrics, and communicating engineering limitations.

Deliverables are a validated network setup, three comparable scenarios, a 24-hour simulation, a nine-case sensitivity study, auditable CSV outputs and figures. No hardware, power-electronics switching model, commercial solver or proprietary utility dataset is required. The project is a study of a published benchmark, not a design for an actual University of Jeddah or Saudi distribution circuit.

## 2. Feeder and scope

Use `pandapower.networks.case33bw()` with the original radial configuration. The [pandapower test-case documentation](https://pandapower.readthedocs.io/en/v3.3.1/networks/power_system_test_cases.html) identifies the case's MATPOWER provenance. The [source data](https://github.com/MATPOWER/matpower/blob/master/data/case33bw.m) specify a 12.66 kV feeder with 33 buses, 3.715 MW and 2.300 MVAr nominal total load, 32 energized branches and five open ties. The MATPOWER system base is 10 MVA. Use the library's converted data; do not convert line ohms to per-unit a second time.

The upstream grid is an ideal slack at physical bus 1, fixed at 1.0 pu. All buses are energized; ties remain open throughout. Original bus number = pandapower index + 1 for this checked dataset. Native names are not used to infer numbering.

The model is balanced, positive sequence, quasi-static and constant PQ. Each hour is an independent AC operating point linked only by battery energy. The slack supplies the required active and reactive mismatch. The study has no explicit substation transformer, tap controller, capacitor bank, regulator, load growth or feeder reconfiguration.

The engineering target of 0.95–1.05 pu is an **assumed study band**. It is not a claim of compliance with a specific electricity code. The raw case may contain different voltage-bound fields; normal load flow does not enforce those fields. This code compares calculated voltages against the separately configured study band.

Thermal limits are not assessed: original branch ratings are not adequate evidence of physical ampacity. Report actual calculated currents, but do not interpret placeholder `loading_percent` values as validated thermal margins.

## 3. Scenarios and device selection

| Scenario | Devices | Question |
| --- | --- | --- |
| Baseline | Original feeder | Where and when is performance weakest? |
| PV only | 0.9 MW at bus 18; 1.2 MW at bus 33 | What changes during solar production? |
| PV + BESS | Same PV; 0.6 MW / 2.4 MWh battery at bus 33 | What is the incremental effect of shifting energy? |

Buses 18 and 33 are downstream ends of two substantial feeder paths. Bus 18 is checked as the weakest nominal-voltage bus; bus 33 provides a second downstream location. The battery is co-located with PV at bus 33 to make the charging policy easy to explain. These placements are a heuristic starting point, not a search result. The ratings are deliberately editable, moderate-scale assumptions; no economic or globally optimal sizing claim is made.

The 0.6 MW / 2.4 MWh label implies four hours at rated power only at nominal energy before SOC restrictions and conversion losses. Usable internal energy from 20% to 90% SOC is 1.68 MWh. This is an input-derived capacity calculation, not a simulated performance result.

Use the same profiles, voltage source, topology and solver settings in all three cases. Compare PV against baseline; then compare PV + BESS against **both** baseline and PV only. The latter comparison isolates the storage contribution.

## 4. Load flow and photovoltaic representation

For each one-hour interval, scale every original load using the same multiplier:

$$
P_{L,i,t}=\alpha_t P_{L,i,0},\qquad Q_{L,i,t}=\alpha_t Q_{L,i,0}.
$$

The solver enforces AC nodal power balance. With net injections positive into the network:

$$
P_i=V_i\sum_j V_j\left[G_{ij}\cos(\theta_i-\theta_j)+B_{ij}\sin(\theta_i-\theta_j)\right],
$$
$$
Q_i=V_i\sum_j V_j\left[G_{ij}\sin(\theta_i-\theta_j)-B_{ij}\cos(\theta_i-\theta_j)\right].
$$

Here $Y=G+jB$ is the nodal admittance matrix. Voltages are per-unit and power uses consistent system-base quantities within the solver. Pandapower inputs/outputs use MW and MVAr.

Backward/forward sweep (`bfsw`) is selected for the radial feeder, with flat initialization, 100 maximum iterations and $10^{-9}$ MVA convergence tolerance. A nominal-case Newton–Raphson (`nr`) cross-check tests agreement to $10^{-6}$ pu in voltage and $10^{-6}$ MW in loss. Both algorithms are documented in [pandapower's AC power-flow reference](https://pandapower.readthedocs.io/en/v3.3.1/powerflow/ac.html). This is a numerical cross-check within one library, not independent field validation.

PV is an AC-side static generator:

$$
P_{PV,k,t}=P_{PV,k}^{rated}g_t,\qquad Q_{PV,k,t}=0,\qquad 0\le g_t\le 1.
$$

The rating is AC active power, not DC module nameplate power. `sgen.p_mw` is positive for generation. “PV” here means photovoltaic; it does **not** mean a voltage-controlled PV bus. The generator is modeled as a fixed-PQ injection, using the [static generator convention](https://pandapower.readthedocs.io/en/v3.3.1/elements/sgen.html). There is no Volt–VAR control, curtailment, inverter overloading or separate PV conversion loss. The availability factor already represents assumed AC output.

The approximate radial voltage-drop relationship

$$
\Delta V\approx\frac{RP+XQ}{V}
$$

helps explain why local generation can support voltage, using consistently based quantities. It is an interpretation aid; the reported results come from the full AC solver. Reducing P alone cannot eliminate voltage drop caused by Q or every branch's loading.

## 5. Battery representation and dispatch

Pandapower storage uses the consumer sign convention: positive power charges and negative power discharges. The [storage documentation](https://pandapower.readthedocs.io/en/v3.3.1/elements/storage.html) states that ordinary power flow does not evolve SOC or enforce energy capacity. The Python dispatcher performs these tasks explicitly.

Let $p_t$ be AC terminal battery power, positive for charging. Define nonnegative powers $P_{ch,t}=\max(p_t,0)$ and $P_{dis,t}=\max(-p_t,0)$. Then:

$$
E_{t+1}=E_t+\eta_{ch}P_{ch,t}\Delta t-\frac{P_{dis,t}\Delta t}{\eta_{dis}},\qquad SOC_t=\frac{E_t}{E_{nom}}.
$$
$$
SOC_{min}E_{nom}\le E_t\le SOC_{max}E_{nom},\quad |p_t|\le P_{max},\quad E_{24}=E_0.
$$

Default values are $\Delta t=1$ h, $\eta_{ch}=\eta_{dis}=0.95$, 20% minimum and initial SOC, and 90% maximum SOC. The corresponding modeled AC round-trip efficiency is $0.95^2=90.25\%$. This is an assumption, not a measured device efficiency. All device Q is zero, so the selected active-power limit also bounds apparent power at unity power factor.

The schedule uses a known day-ahead synthetic forecast:

1. Permit charging in intervals beginning 10:00–15:00. At each permitted hour, cap charging by the lesser of battery power rating and co-located PV output.
2. Permit discharging in intervals beginning 17:00–21:00. Cap discharge by the battery power rating.
3. Limit the total internal energy gain by SOC headroom, available charging energy and the amount that can be discharged before the day ends.
4. Allocate charging in proportion to solar availability and discharging in proportion to the evening load multiplier, iteratively redistributing power when an interval reaches its cap.
5. Update energy and verify every boundary state, including return to initial SOC.

Writing $C_t$ and $D_t$ for the charging and discharging AC power caps:

$$
\Delta E_{cycle}=\min\left[E_{max}-E_0,\;\eta_{ch}\Delta t\sum_t C_t,\;\frac{\Delta t}{\eta_{dis}}\sum_t D_t\right].
$$

Allocate total AC charge $\Delta E_{cycle}/\eta_{ch}$ and total AC discharge $\eta_{dis}\Delta E_{cycle}$. All charging precedes discharge, so this construction guarantees an attainable daily energy trajectory. Zero sunshine produces zero throughput. The implementation rejects interleaved charge/discharge windows because the present construction does not support them.

The policy is a transparent load-shifting heuristic, not optimal power flow, voltage feedback or an online energy-management system. Charging is limited by local PV output, but grid-connected AC flows do not prove exclusive solar sourcing. Network voltage limits are evaluated after dispatch, not enforced by the scheduler. The controller may worsen midday voltage or fail to solve an evening violation; those are legitimate findings.

## 6. Evaluation equations and output definitions

Let $N=33$ include the slack bus, $T=24$, and $\mathcal L$ contain energized lines. Including the slack slightly reduces the reported average deviation; the convention is identical in all cases.

**Voltage profile and extrema:** store every $V_{i,t}$, and calculate $\min_{i,t}V_{i,t}$ and $\max_{i,t}V_{i,t}$. Compare noon and evening profiles and the entire bus/hour heatmap.

**Mean absolute voltage deviation:**

$$
MAVD_t=\frac{1}{N}\sum_{i=1}^N|V_{i,t}-1|,\qquad
MAVD=\frac{1}{T}\sum_{t=1}^T MAVD_t.
$$

This is in pu; $100\,MAVD$ expresses the mean absolute deviation as a percentage of nominal voltage. It is not the signed average voltage error.

**Voltage violation exposure:**

$$
H_V=\sum_t\sum_i\mathbf{1}\{V_{i,t}<V_{min}\;\lor\;V_{i,t}>V_{max}\}\Delta t.
$$

Units are bus-hours. Also report hours with at least one violation. Limits are inclusive: a voltage exactly at a bound is not a violation. One hour with five violating buses contributes five bus-hours, not five hours of system-wide outage.

**Instantaneous active line losses:**

$$
P_{loss,t}=\sum_{\ell\in\mathcal L}\left(P_{from,\ell,t}+P_{to,\ell,t}\right).
$$

Use `res_line.pl_mw`; at both ends pandapower defines branch power into the line. Resistive loss is equivalently $3I_{phase}^2R_{phase}$ per balanced physical branch when units are consistent. Currents are available in `line_results.csv`.

**Daily line-loss energy and percentage reduction:**

$$
E_{line}=\sum_t P_{loss,t}\Delta t,\qquad
R_{line}=100\frac{E_{line,base}-E_{line,case}}{E_{line,base}}.
$$

MW multiplied by hours gives MWh. A positive reduction is an improvement; a negative value is deterioration. The implemented summary also computes a corresponding reduction in combined losses.

**Battery conversion and combined modeled loss:**

$$
E_{conv}=\sum_t(P_{ch,t}-P_{dis,t})\Delta t-(E_T-E_0),\qquad
E_{combined}=E_{line}+E_{conv}.
$$

Equivalently, $E_{conv}=\sum_t[(1-\eta_{ch})P_{ch,t}+(1/\eta_{dis}-1)P_{dis,t}]\Delta t$. The subtraction of stored-energy change matters for any non-cyclic extension. This model's combined loss excludes PV inverter, transformer, auxiliary and upstream-grid losses. Do not call it total real-world lifecycle loss.

**Grid exchange and peak:** with slack active power $P_{grid,t}$ positive for import,

$$
E_{import}=\sum_t\max(P_{grid,t},0)\Delta t,\quad
E_{export}=\sum_t\max(-P_{grid,t},0)\Delta t,\quad
P_{peak}=\max\{0,\max_t P_{grid,t}\}.
$$

PV energy is $\sum_t P_{PV,t}\Delta t$ and served demand is $\sum_t P_{L,t}\Delta t$. Lower imports can come from PV generation even when loss performance worsens.

**Conservation checks:**

$$
r_{P,t}=P_{grid,t}+P_{PV,t}-P_{L,t}-p_t-P_{loss,t}\approx0.
$$

An analogous reactive-power balance includes grid Q, generator Q, load Q, storage Q and line reactive consumption. With $E_T=E_0$, the daily identity is:

$$
E_{import}-E_{export}+E_{PV}=E_{load}+E_{line}+E_{conv}.
$$

Each hourly active/reactive residual must be within $10^{-6}$ MW/MVAr. The test allows $24\times10^{-6}$ MWh for accumulated daily residual. These are numerical tolerances, not instrument accuracies.

## 7. Reproducible results workflow

1. Install the pinned environment and run `python -m pip check` and `python -m pytest -q`.
2. Run the default study into a new directory. Inspect `validation.json` and verify `manifest.json` says `completed`.
3. Examine the full `summary.csv`; do not select only favorable metrics. Check peak-demand hour and identify the minimum-voltage bus from `bus_voltages.csv`.
4. Generate all figures from that same directory. The plot script reads its saved config and profiles, avoiding disagreement with later input edits.
5. Compare line and combined losses separately and state whether the battery improves on PV alone.
6. Run sensitivity cases and use `docs/RESULTS_TEMPLATE.md` to interpret them. Keep each run's versions, inputs and hashes with its outputs.

The nine sensitivity cases comprise the reference plus two alternatives each for PV scale (0.5 and 1.5), demand scale (0.8 and 1.2), battery power (0.3 and 0.9 MW) and battery energy (1.2 and 4.8 MWh). Only one factor changes at a time. Each case uses its own baseline with matching demand. All 27 scenario rows are saved, along with case-level inputs and hourly evidence. The completion marker is written only after all 648 power flows finish. This is a local sensitivity experiment, not a full uncertainty analysis or proof of optimality.

The default study's manuscript-style table and figures are generated from actual calculations, not handwritten sample results. Inputs and expected sanity ranges must never be described as achieved results. The package's preparation runs, if present, are identified separately in `docs/VERIFICATION.md`.

## 8. Validation plan

| Check | Purpose | Acceptance / action |
| --- | --- | --- |
| Topology and load inventory | Catch wrong case, ties or units | 33 buses, 32 energized lines, five open ties, connected tree; nominal totals as documented |
| Nominal full-load run | Catch gross modeling mistakes | Broad diagnostic ranges: 0.90–0.93 pu minimum, 0.19–0.22 MW losses; weakest bus 18 |
| Second solver | Check numerical formulation consistency | Maximum voltage and loss differences below stated tolerances |
| All-bus finite results | Catch disconnected or failed solutions | Stop on failure; never substitute last-hour voltages |
| P and Q conservation | Check signs and accounting | Residuals within tolerance every hour |
| Battery state recursion | Catch energy creation and sign errors | Bounds, power limit, continuity, efficiencies and terminal equality pass |
| No-sun and no-local-PV tests | Verify dispatch edge cases | Battery throughput equals zero |
| Zero-device equivalence | Check scenario construction | PV + BESS with zero PV reproduces baseline |
| Daily energy identity | Check aggregation | Input/output energy plus losses balances |

The broad nominal ranges are diagnostic expectations, not fabricated observations, fitted targets or substitutes for source verification. Before claiming independent validation, compare the same data and settings with a separate implementation such as MATPOWER and document the result. That external comparison is not included here.

## 9. Limitations and extensions

- A single synthetic day cannot establish annual energy savings, financial return or performance in Jeddah. Use seasonally representative measured profiles or a documented solar model for that extension.
- Balanced steady-state load flow omits unbalance, neutral effects, harmonics, switching, frequency dynamics, protection and fault duty.
- Constant-PQ loads and a fixed slack omit voltage-sensitive demand and upstream voltage variations. Test those assumptions before a field application.
- A common profile at every bus hides load diversity and geographic solar variation. A spatially diverse dataset may change device value and location.
- Unity-power-factor PV and battery operation leave reactive demand unsupported. Add a constrained Volt–VAR law with $P^2+Q^2\le S_{rated}^2$, consistent sign conventions and tested controller convergence.
- Fixed conversion efficiencies omit temperature, rate dependence, standby consumption, self-discharge, degradation and cycle economics.
- Perfect day-ahead information, restricted windows and fixed siting are not a deployable controller. Add forecast errors, multi-day energy continuity or an optimization model with explicit voltage and energy constraints.
- High PV penetration can increase voltage and reverse flows; storage charging can add losses. Do not assume monotonic benefit from increasing ratings.
- No validated ampacities, cost inputs or utility interconnection requirements are provided. This project makes no thermal, economic or regulatory compliance claim.

Recommended next work: first reproduce and explain the default case; then test siting with equal device ratings and a predeclared objective; then add realistic input data; finally compare active-only dispatch with reactive support. Keep an unmodified baseline and document each extension separately.
