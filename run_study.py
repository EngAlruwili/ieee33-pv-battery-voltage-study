"""Run from repository root: python run_study.py --output results/run_01."""
import argparse
import hashlib
import importlib.metadata
import json
from datetime import datetime, timezone
from pathlib import Path
import platform
import sys

import pandas as pd

from study.inputs import read_inputs
from study.simulation import SCENARIOS, run_scenario, summarize
from study.validation import benchmark, check_day, markdown_table


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("config/default.json"))
    parser.add_argument("--profiles", type=Path, default=Path("data/profiles.csv"))
    parser.add_argument("--output", type=Path, default=Path("results/run_01"))
    args = parser.parse_args()
    config, profiles = read_inputs(args.config, args.profiles)
    if args.output.exists() and any(args.output.iterdir()):
        parser.error("Output folder is not empty. Choose a new folder to preserve earlier evidence.")
    args.output.mkdir(parents=True, exist_ok=True)
    # A missing manifest means the run was interrupted or failed; do not cite it.
    checks = benchmark(config)
    hourly, bus, line = [], [], []
    for scenario in SCENARIOS:
        h, v, l = run_scenario(config, profiles, scenario)
        hourly.append(h); bus.append(v); line.append(l)
        print(f"Completed {scenario}: {len(h)} converged hourly power flows")
    h = pd.concat(hourly, ignore_index=True)
    check_day(h, config)
    summary = summarize(h)
    h.to_csv(args.output / "hourly.csv", index=False)
    pd.concat(bus, ignore_index=True).to_csv(args.output / "bus_voltages.csv", index=False)
    pd.concat(line, ignore_index=True).to_csv(args.output / "line_results.csv", index=False)
    summary.to_csv(args.output / "summary.csv", index=False)
    profiles.to_csv(args.output / "profiles_used.csv", index=False)
    (args.output / "config_used.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    (args.output / "validation.json").write_text(json.dumps(checks, indent=2), encoding="utf-8")
    selected = summary[["scenario", "line_loss_mwh", "battery_conversion_loss_mwh", "combined_loss_mwh",
                        "min_voltage_pu", "voltage_violation_bus_hours"]]
    report = ("# Generated simulation summary\n\nAuthor: Abdullah Alruwaili (prepared project; review pending).\n\n"
              "These values were calculated by this run, using synthetic profiles. They are not field measurements. "
              "A completed run does not establish that the author personally reviewed or performed it.\n\n" +
              markdown_table(selected) + "\n\nCompare PV + BESS against PV alone as well as against baseline. "
              "Lower line losses need not mean lower combined losses. Remaining voltage violations must be reported. "
              "The 0.95–1.05 pu default is a study target, not a regulatory compliance claim.\n\n"
              "See summary.csv for all metrics, validation.json for the nominal check, and manifest.json for provenance.\n")
    (args.output / "RESULTS.md").write_text(report, encoding="utf-8")
    root = Path(__file__).resolve().parent
    sources = sorted(list(root.glob("*.py")) + list((root / "study").glob("*.py")))
    source_hashes = {str(p.relative_to(root)).replace("\\", "/"): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
    input_hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in [args.config, args.profiles]}
    versions = {p: importlib.metadata.version(p) for p in
                ["pandapower", "numpy", "pandas", "scipy", "matplotlib", "networkx", "pytest"]}
    manifest = {"status": "completed", "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "python": sys.version, "platform": platform.platform(), "packages": versions,
                "input_sha256": input_hashes, "source_sha256": source_hashes,
                "scenario_power_flows": 72, "benchmark_power_flows": 2,
                "time_step_hours": 1.0, "profiles": "Synthetic educational day; no location or weather validation",
                "executed_by": "Record the human reviewer separately; this file only records a software run"}
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(summary.to_string(index=False))
    print(f"Saved completed run to {args.output}")


if __name__ == "__main__":
    main()
