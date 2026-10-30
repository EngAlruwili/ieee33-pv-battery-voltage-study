# Results interpretation worksheet

Author: Abdullah Alruwaili  
Status: **unfilled review worksheet — not a completed results report**

Run directory: [enter]  
Run timestamp / software versions: [copy from manifest]  
Reviewer and review date: [enter after reviewing]  
Changes from default configuration: [list, or state none]

## Calculated comparison

Copy these values from one completed `summary.csv`; do not mix runs.

| Metric | Baseline | PV only | PV + BESS |
| --- | --- | --- | --- |
| Line-loss energy (MWh/day) | [value] | [value] | [value] |
| Battery conversion loss (MWh/day) | [value] | [value] | [value] |
| Combined modeled loss (MWh/day) | [value] | [value] | [value] |
| Minimum / maximum voltage (pu) | [values] | [values] | [values] |
| Mean absolute voltage deviation (pu) | [value] | [value] | [value] |
| Voltage violation exposure (bus-hours) | [value] | [value] | [value] |
| Peak import (MW) | [value] | [value] | [value] |
| Import / export energy (MWh/day) | [values] | [values] | [values] |

Use `bus_voltages.csv` to identify the hour and physical bus of each minimum. If several values tie, say so.

## Interpretation to write after reviewing

1. What changed with PV during daylight? Which branches and hours benefit?
2. What happened during battery charging and evening discharge?
3. Does storage improve line loss relative to PV alone? Does it also improve combined modeled loss? Calculate both absolute and percentage changes using PV only as that comparison's denominator.
4. Were all voltages within the study band? If not, report remaining violations and avoid claiming complete voltage regulation.
5. Does the daily energy balance pass, and does battery energy return to its initial value?
6. Which sensitivity assumption most changes the conclusion? Do higher ratings always help?
7. Which conclusion depends most strongly on the synthetic profiles, selected buses or fixed efficiency?

Suggested conclusion structure: “For the stated synthetic day and device configuration, [observed change]. Compared with PV only, storage [observed incremental effects]. [Remaining violations or tradeoffs]. These findings are limited to [key assumptions]; [specific next validation step] is needed before broader conclusions.”

## Figure selection

Use the daily voltage/loss figure, noon/evening bus profiles, battery SOC figure and stacked loss comparison. Captions should identify the run, synthetic profiles, units and scenarios. Include the full CSVs and manifest alongside any rounded report values.
