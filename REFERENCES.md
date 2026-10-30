# References and source notes

1. M. E. Baran and F. F. Wu, “Network reconfiguration in distribution systems for loss reduction and load balancing,” *IEEE Transactions on Power Delivery*, vol. 4, no. 2, pp. 1401–1407, April 1989. [DOI: 10.1109/61.25627](https://doi.org/10.1109/61.25627). Original feeder attribution as identified in the distributed case data; this project does not reproduce or claim to independently review the full paper.
2. MATPOWER, [case33bw source data](https://github.com/MATPOWER/matpower/blob/master/data/case33bw.m). Source for topology, base loads, voltage and impedance conventions.
3. pandapower 3.3.1, [power system test cases](https://pandapower.readthedocs.io/en/v3.3.1/networks/power_system_test_cases.html). Documents `case33bw` and its MATPOWER origin.
4. pandapower 3.3.1, [balanced AC power flow](https://pandapower.readthedocs.io/en/v3.3.1/powerflow/ac.html). Solver options and convergence parameters.
5. pandapower 3.3.1, [storage](https://pandapower.readthedocs.io/en/v3.3.1/elements/storage.html). Storage sign convention and need for explicit time-dependent SOC management.
6. pandapower 3.3.1, [static generator](https://pandapower.readthedocs.io/en/v3.3.1/elements/sgen.html). Static injection representation and generation sign convention.

Documentation and case provenance were consulted during preparation on 30 October 2026. Versioned documentation and package pins are preferred for reproduction. The GitHub source link can change; the executed pandapower version and run evidence provide the implementation context.
