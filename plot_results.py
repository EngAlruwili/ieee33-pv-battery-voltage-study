"""Create presentation-quality figures from a completed run; no recomputation."""
import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

COLORS = {"baseline": "#687787", "pv_only": "#e6a23c", "pv_bess": "#087f8c"}
LABELS = {"baseline": "Baseline", "pv_only": "PV only", "pv_bess": "PV + BESS"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("results/run_01"))
    args = parser.parse_args()
    root = args.input
    if json.loads((root / "manifest.json").read_text())["status"] != "completed":
        raise ValueError("Plot only completed runs")
    h, v, s = [pd.read_csv(root / name) for name in ("hourly.csv", "bus_voltages.csv", "summary.csv")]
    profiles = pd.read_csv(root / "profiles_used.csv")
    config = json.loads((root / "config_used.json").read_text())
    plots = root / "figures"
    plots.mkdir(exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "axes.grid": True, "grid.alpha": .18, "figure.dpi": 130})

    def save(fig, name):
        fig.text(.5, -.035, "IEEE 33-bus case | Synthetic 24-hour study | Prepared for Abdullah Alruwaili",
                 ha="center", va="top", fontsize=8, color="#52606d")
        fig.savefig(plots / (name + ".png"), dpi=180, bbox_inches="tight")
        fig.savefig(plots / (name + ".svg"), bbox_inches="tight")
        plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 4), layout="constrained")
    ax.step(np.arange(25), np.r_[profiles.load_pu, profiles.load_pu.iloc[-1]],
            where="post", label="Load multiplier", color="#687787")
    ax.step(np.arange(25), np.r_[profiles.pv_pu, profiles.pv_pu.iloc[-1]],
            where="post", label="PV availability", color="#e6a23c")
    ax.set(xlabel="Hour (interval start)", ylabel="Per-unit multiplier", title="Explicit synthetic inputs")
    ax.legend(); save(fig, "01_inputs")

    fig, axes = plt.subplots(2, 1, figsize=(10, 7), sharex=True, layout="constrained")
    for name, d in h.groupby("scenario", sort=False):
        axes[0].plot(d.hour, d.v_min_pu, label=LABELS[name], color=COLORS[name], marker=".")
        axes[1].plot(d.hour, d.line_loss_mw * 1000, label=LABELS[name], color=COLORS[name], marker=".")
    axes[0].axhline(config["voltage_min_pu"], color="#b94141", linestyle="--", label="Lower study target")
    axes[0].set(ylabel="Minimum bus voltage (pu)", title="Daily voltage and feeder-loss comparison")
    axes[0].legend(ncol=2)
    axes[1].set(xlabel="Hour (interval start)", ylabel="Active line losses (kW)")
    save(fig, "02_daily_performance")

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), sharey=True, layout="constrained")
    for ax, hour in zip(axes, [12, 18]):
        for name, d in v[v.hour == hour].groupby("scenario", sort=False):
            ax.plot(d.bus, d.vm_pu, color=COLORS[name], label=LABELS[name], marker=".")
        ax.axhline(config["voltage_min_pu"], color="#b94141", linestyle="--")
        ax.axhline(config["voltage_max_pu"], color="#b94141", linestyle="--")
        ax.set(title=f"Hour {hour:02d}:00", xlabel="Physical bus number (not distance)")
    axes[0].set_ylabel("Voltage magnitude (pu)")
    axes[1].legend(); save(fig, "03_bus_voltage_profiles")

    fig, axes = plt.subplots(1, 3, figsize=(13, 5), sharey=True, layout="constrained")
    for ax, name in zip(axes, COLORS):
        matrix = v[v.scenario == name].pivot(index="bus", columns="hour", values="vm_pu")
        im = ax.imshow(matrix, origin="lower", aspect="auto", extent=[-.5, 23.5, .5, 33.5],
                       vmin=min(.90, v.vm_pu.min()), vmax=max(1.05, v.vm_pu.max()), cmap="viridis")
        ax.set(title=LABELS[name], xlabel="Hour"); ax.grid(False)
    axes[0].set_ylabel("Physical bus number")
    fig.colorbar(im, ax=axes, label="Voltage (pu)", shrink=.8)
    save(fig, "04_voltage_heatmaps")

    d = h[h.scenario == "pv_bess"]
    fig, axes = plt.subplots(2, 1, figsize=(10, 7), layout="constrained")
    axes[0].bar(d.hour, d.bess_p_mw, color=np.where(d.bess_p_mw >= 0, "#e6a23c", "#087f8c"))
    axes[0].axhline(0, color="#687787", linewidth=.8)
    axes[0].set(ylabel="Battery AC power (MW)", title="Positive = charging; negative = discharging", xlabel="Hour")
    # SOC is an interval-boundary state: 25 points from hour 0 through hour 24.
    axes[1].plot(np.arange(25), np.r_[d.soc_start.iloc[0], d.soc_end] * 100, color="#087f8c", marker=".")
    for value in (config["battery"]["soc_min"], config["battery"]["soc_max"]):
        axes[1].axhline(value * 100, linestyle="--", color="#b94141")
    axes[1].set(xlabel="Hour boundary", ylabel="State of charge (%)", ylim=(0, 100))
    save(fig, "05_battery_dispatch")

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), layout="constrained")
    x = np.arange(len(s)); labels = [LABELS[n] for n in s.scenario]
    axes[0].bar(x, s.line_loss_mwh, label="Feeder lines", color="#087f8c")
    axes[0].bar(x, s.battery_conversion_loss_mwh, bottom=s.line_loss_mwh,
                label="Battery conversion", color="#e6a23c")
    axes[0].set(xticks=x, xticklabels=labels, ylabel="Energy loss (MWh/day)", title="Loss accounting")
    axes[0].legend()
    axes[1].bar(x, s.voltage_violation_bus_hours, color=[COLORS[n] for n in s.scenario])
    axes[1].set(xticks=x, xticklabels=labels, ylabel="Bus-hours outside study band", title="Remaining voltage violations")
    save(fig, "06_loss_and_voltage_summary")

    fig, ax = plt.subplots(figsize=(10, 4.5), layout="constrained")
    for name, d in h.groupby("scenario", sort=False):
        ax.plot(d.hour, d.grid_p_mw, color=COLORS[name], label=LABELS[name])
    ax.axhline(0, color="#687787", linewidth=.8)
    ax.set(xlabel="Hour", ylabel="Grid active power (MW)", title="Positive = import; negative = export")
    ax.legend(); save(fig, "07_grid_exchange")
    provenance = {"plot_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  "matplotlib_version": matplotlib.__version__,
                  "input_sha256": {name: hashlib.sha256((root / name).read_bytes()).hexdigest()
                                   for name in ["hourly.csv", "bus_voltages.csv", "summary.csv",
                                                "profiles_used.csv", "config_used.json", "manifest.json"]}}
    (plots / "provenance.json").write_text(json.dumps(provenance, indent=2), encoding="utf-8")
    print(f"Created 7 PNG and 7 SVG figures in {plots}")


if __name__ == "__main__":
    main()
