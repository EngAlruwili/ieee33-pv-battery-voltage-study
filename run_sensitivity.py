"""One-factor-at-a-time robustness study; no claim of optimal siting or sizing."""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path

import pandas as pd

from study.inputs import read_inputs, validate_inputs
from study.simulation import SCENARIOS, run_scenario, summarize
from study.validation import check_day


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("config/default.json"))
    parser.add_argument("--profiles", type=Path, default=Path("data/profiles.csv"))
    parser.add_argument("--output", type=Path, default=Path("results/sensitivity_01"))
    args = parser.parse_args()
    if args.output.exists() and any(args.output.iterdir()):
        parser.error("Choose a new, empty output folder")
    args.output.mkdir(parents=True, exist_ok=True)
    base, profiles = read_inputs(args.config, args.profiles)
    cases = [("reference", 1.0)] + [(factor, value) for factor, values in
             [("pv_scale", [0.5, 1.5]), ("load_scale", [0.8, 1.2]),
              ("battery_power_mw", [0.3, 0.9]), ("battery_energy_mwh", [1.2, 4.8])]
             for value in values]
    results = []
    for number, (factor, value) in enumerate(cases):
        c, p = deepcopy(base), profiles.copy()
        if factor == "pv_scale":
            for unit in c["pv_units"]:
                unit["p_rated_mw"] *= value
        elif factor == "load_scale":
            p.load_pu *= value
        elif factor == "battery_power_mw":
            c["battery"]["p_max_mw"] = value
        elif factor == "battery_energy_mwh":
            c["battery"]["e_nom_mwh"] = value
        validate_inputs(c, p)
        h = pd.concat([run_scenario(c, p, s)[0] for s in SCENARIOS], ignore_index=True)
        check_day(h, c)
        summary = summarize(h)
        summary.insert(0, "factor", factor); summary.insert(1, "value", value)
        results.append(summary)
        case_dir = args.output / f"case_{number:02d}"
        case_dir.mkdir()
        h.to_csv(case_dir / "hourly.csv", index=False)
        p.to_csv(case_dir / "profiles_used.csv", index=False)
        (case_dir / "config_used.json").write_text(json.dumps(c, indent=2), encoding="utf-8")
        print(f"Completed {factor} = {value}")
    pd.concat(results, ignore_index=True).to_csv(args.output / "sensitivity.csv", index=False)
    root = Path(__file__).resolve().parent
    sources = sorted(list(root.glob("*.py")) + list((root / "study").glob("*.py")))
    metadata = {"status": "completed", "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "hourly_power_flows": 648,
                "packages": {name: importlib.metadata.version(name) for name in
                             ["pandapower", "numpy", "pandas", "scipy", "networkx"]},
                "source_sha256": {str(p.relative_to(root)).replace("\\", "/"):
                                  hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
                "input_sha256": {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in [args.config, args.profiles]}}
    (args.output / "manifest.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    (args.output / "COMPLETED.txt").write_text("9 cases, 3 scenarios each, 648 hourly power flows.\n", encoding="utf-8")


if __name__ == "__main__":
    main()
