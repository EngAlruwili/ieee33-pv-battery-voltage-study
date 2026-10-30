# Review and presentation guide

Prepared for Abdullah Alruwaili. A credible portfolio demonstrates understanding of choices and limitations as well as working code.

## A manageable learning sequence

| Stage | Work to perform | Evidence to keep |
| --- | --- | --- |
| 1. Understand the feeder | Read the case provenance; trace paths 1–18 and 1–6–26–33; identify the slack and open ties | Annotated feeder sketch and nominal load totals |
| 2. Reproduce the baseline | Install Python; run checks; inspect nominal voltages and losses | Environment versions and validation output |
| 3. Understand distributed PV | Compare baseline and PV at noon and after sunset | Bus profiles and explanation of changed power flows |
| 4. Audit storage | Hand-calculate one charging and one discharging energy update | A checked SOC calculation and terminal-energy equality |
| 5. Interpret the full day | Compare line losses, conversion losses, voltage exposure and import | Results worksheet with both benefits and drawbacks |
| 6. Adapt one assumption | Change one rating, bus or input profile; rerun | Clearly labeled second run and reasoned comparison |
| 7. Prepare the portfolio | Review attribution, summarize limitations and select figures | A short report, repository and accurately worded post |

This can be spread over approximately three to four weeks of part-time study; it is a planning suggestion, not a claim that this time has already been spent.

## Questions to answer in a project discussion

**Why the 33-bus feeder?** It is small enough to inspect and widely used as a published radial benchmark. It supports reproducibility but does not represent a particular local utility circuit.

**Why buses 18 and 33?** They provide downstream injection on two feeder paths; the nominal check identifies bus 18 as weak. The choice is heuristic. A candidate-bus sweep would be required to claim best placement under a defined objective.

**Why can solar lower losses?** It can reduce the upstream current serving downstream loads. Resistive loss scales with current squared. Excess injection and reverse flow can change that trend.

**Why might the minimum voltage remain low?** PV output is small in the evening, reactive demand remains, and a battery at bus 33 does not directly supply every remote branch. The controller also does not enforce voltage constraints.

**Why use `sgen` for PV?** AC output is specified as P and Q. The project does not model a voltage-regulating synchronous generator or a voltage-controlled PV bus.

**What prevents free battery energy?** The code enforces SOC bounds, efficiency, power limits and return to initial energy. It checks the daily energy balance as well.

**Does positive storage power mean discharge?** No. It means charging in pandapower. Read `dispatch.py` and verify the sign with one hand calculation.

**Is the battery only charged by solar?** Its charging setpoint is capped by co-located PV output. AC network flows are shared, so that cap is not proof of physical energy provenance.

**Why compare PV + BESS against PV only?** That isolates the incremental storage effect. A comparison against baseline alone can conceal a battery that worsens an otherwise beneficial PV case.

**Why report combined losses?** A battery may lower feeder losses while losing more energy during charge and discharge. The project separates those effects.

**Did you optimize the system?** The supplied implementation uses a deterministic schedule and one-factor sensitivity cases. Do not call it optimization unless an explicit optimization extension has been implemented and evaluated.

**What does a solver cross-check prove?** Agreement provides numerical confidence in the supplied model. It does not validate synthetic profiles, equipment suitability or real-world behavior.

## Hand-calculation exercise (hypothetical inputs, not study results)

For an assumed one-hour charging interval at 0.20 MW, 95% charging efficiency adds 0.19 MWh internally. Discharging 0.20 MW for one hour removes approximately 0.210526 MWh at 95% discharge efficiency. These example powers are educational and are not asserted to occur in the default schedule.

## Before public presentation

- Reproduce the run locally and record what you changed and what you checked.
- Explain every axis, unit, sign and scenario in the selected plots.
- Distinguish assumed ratings and synthetic data from calculated outputs.
- State whether voltage violations remain and whether storage improves on PV alone.
- Describe the AI assistance and the review work you personally performed accurately.
- Select a repository license, preserve third-party citations, and replace any worksheet placeholders.
- Make no statement of novelty, field deployment, university endorsement or professional certification without evidence.
