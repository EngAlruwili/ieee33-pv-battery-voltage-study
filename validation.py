"""Numerical checks, including a second solver on the nominal unmodified feeder."""
import numpy as np

from .network import build_network, solve


def benchmark(config):
    net = build_network(config, "baseline")
    # Reference checkpoint always uses nominal demand and a 1.0 pu source.
    net.ext_grid.loc[:, "vm_pu"] = 1.0
    solve(net, "bfsw")
    voltages = net.res_bus.vm_pu.copy()
    losses = float(net.res_line.pl_mw.sum())
    minimum = float(voltages.min())
    weakest = int(voltages.idxmin()) + 1
    solve(net, "nr")
    error = float(np.abs(net.res_bus.vm_pu - voltages).max())
    loss_error = abs(float(net.res_line.pl_mw.sum()) - losses)
    # Broad sanity bands, not targets that the solver is forced to reproduce.
    if not (0.90 < minimum < 0.93 and 0.19 < losses < 0.22 and weakest == 18):
        raise RuntimeError("Nominal benchmark outside expected sanity range; inspect input data")
    if error > 1e-6 or loss_error > 1e-6:
        raise RuntimeError("BFSW / Newton-Raphson disagreement exceeds tolerance")
    return {"nominal_min_voltage_pu": minimum, "nominal_weakest_bus": weakest,
            "nominal_line_loss_mw": losses, "solver_max_voltage_difference_pu": error,
            "solver_loss_difference_mw": loss_error,
            "note": "Same-library solver cross-check, not independent experimental validation"}


def check_day(hourly, config):
    for name, d in hourly.groupby("scenario"):
        if len(d) != 24 or not np.array_equal(d.hour, np.arange(24)):
            raise ValueError(f"Missing or reordered hours in {name}")
        if d.balance_residual_mw.abs().max() > 1e-6:
            raise ValueError("Power balance failed")
        if name != "pv_bess":
            continue
        b = config["battery"]
        p = d.bess_p_mw.to_numpy()
        start, end = d.energy_start_mwh.to_numpy(), d.energy_end_mwh.to_numpy()
        expected = np.maximum(p, 0) * b["eta_charge"] + np.minimum(p, 0) / b["eta_discharge"]
        if not np.allclose(end - start, expected, atol=1e-10, rtol=0):
            raise ValueError("Battery energy recursion failed")
        if not np.allclose(start[1:], end[:-1], atol=1e-10, rtol=0):
            raise ValueError("Battery energy is discontinuous")
        if abs(end[-1] - start[0]) > 1e-9 or np.abs(p).max() > b["p_max_mw"] + 1e-9:
            raise ValueError("Terminal energy or battery power limit failed")
        if min(start.min(), end.min()) < b["soc_min"] * b["e_nom_mwh"] - 1e-9:
            raise ValueError("Battery minimum SOC failed")
        if max(start.max(), end.max()) > b["soc_max"] * b["e_nom_mwh"] + 1e-9:
            raise ValueError("Battery maximum SOC failed")


def markdown_table(frame):
    """Small Markdown table without an optional tabulate dependency."""
    lines = ["| " + " | ".join(frame.columns) + " |", "| " + " | ".join(["---"] * len(frame.columns)) + " |"]
    for row in frame.itertuples(index=False, name=None):
        lines.append("| " + " | ".join(f"{v:.6g}" if isinstance(v, (float, np.floating)) else str(v) for v in row) + " |")
    return "\n".join(lines)
