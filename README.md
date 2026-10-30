# Input provenance

`profiles.csv` is a manually specified, deterministic **synthetic educational day**. It is not a measured day, a typical meteorological year, a utility load trace, or a Saudi-specific forecast. There is no random seed because no random sampling is used.

| Column | Meaning | Units |
| --- | --- | --- |
| `hour` | Beginning of interval [hour, hour + 1), 0 through 23 | h |
| `load_pu` | Common multiplier applied to every original P and Q load | dimensionless |
| `pv_pu` | Common AC-output availability fraction for every PV unit | dimensionless |

Every interval lasts one hour. P and Q use the same multiplier, preserving each load's original power factor. Profiles intentionally include daytime PV and an evening demand peak. No particular season, timezone, latitude, temperature, or cloud pattern is represented.

Network data are loaded through `pandapower.networks.case33bw()`; the repository does not manually reconstruct line impedances. The source is the [MATPOWER case33bw data](https://github.com/MATPOWER/matpower/blob/master/data/case33bw.m), citing Baran and Wu (1989), [DOI 10.1109/61.25627](https://doi.org/10.1109/61.25627). Preserve source attribution if exporting or adapting the dataset.

All PV and battery ratings in `config/default.json` are **assumed design inputs**, not simulation results or vendor specifications. Replacing the profiles with measured data requires permission to use those data, unit/time alignment, missing-value treatment and documentation of any scaling.
