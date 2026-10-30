"""Run identical hourly demand and solar profiles for three fair comparisons."""
import numpy as np
import pandas as pd

from .dispatch import battery_schedule
from .network import build_network, solve

SCENARIOS = ("baseline", "pv_only", "pv_bess")


def run_scenario(config, profiles, scenario, algorithm="bfsw"):
    net = build_network(config, scenario)
    base_p, base_q = net.load.p_mw.copy(), net.load.q_mvar.copy()
    schedule = battery_schedule(config, profiles) if scenario == "pv_bess" else None
    hours, buses, lines = [], [], []
    for t, profile in profiles.iterrows():
        net.load.loc[:, "p_mw"] = base_p * profile.load_pu
        net.load.loc[:, "q_mvar"] = base_q * profile.load_pu
        if scenario != "baseline":
            net.sgen.loc[:, "p_mw"] = [u["p_rated_mw"] * profile.pv_pu for u in config["pv_units"]]
        if schedule is not None:
            net.storage.loc[:, "p_mw"] = schedule.bess_p_mw.iloc[t]
            net.storage.loc[:, "soc_percent"] = 100 * schedule.soc_start.iloc[t]
        try:
            solve(net, algorithm)
        except Exception as exc:
            raise RuntimeError(f"{scenario}, hour {int(profile.hour)}: {exc}") from exc
        v = net.res_bus.vm_pu
        loss = float(net.res_line.pl_mw.sum())
        grid = float(net.res_ext_grid.p_mw.sum())
        load = float(net.res_load.p_mw.sum())
        pv = float(net.res_sgen.p_mw.sum())
        battery = float(net.res_storage.p_mw.sum())
        residual = grid + pv - load - battery - loss
        q_residual = float(net.res_ext_grid.q_mvar.sum() + net.res_sgen.q_mvar.sum()
                           - net.res_load.q_mvar.sum() - net.res_storage.q_mvar.sum()
                           - net.res_line.ql_mvar.sum())
        if abs(residual) > 1e-6 or abs(q_residual) > 1e-6 or loss < -1e-9:
            raise RuntimeError("Active/reactive balance or nonnegative-loss check failed")
        row = dict(scenario=scenario, hour=int(profile.hour), load_mw=load, pv_mw=pv,
                   bess_p_mw=battery, grid_p_mw=grid, grid_q_mvar=float(net.res_ext_grid.q_mvar.sum()),
                   line_loss_mw=loss, v_min_pu=float(v.min()), v_max_pu=float(v.max()),
                   mean_abs_voltage_deviation_pu=float(np.abs(v - 1).mean()),
                   violating_buses=int(((v < config["voltage_min_pu"]) |
                                        (v > config["voltage_max_pu"])).sum()),
                   balance_residual_mw=residual, q_balance_residual_mvar=q_residual)
        for col in ("energy_start_mwh", "energy_end_mwh", "soc_start", "soc_end"):
            row[col] = float(schedule[col].iloc[t]) if schedule is not None else np.nan
        hours.append(row)
        for bus, value in v.items():
            buses.append(dict(scenario=scenario, hour=int(profile.hour), bus=int(bus) + 1, vm_pu=float(value)))
        for idx in net.line.index[net.line.in_service]:
            lines.append(dict(scenario=scenario, hour=int(profile.hour), line_index=int(idx),
                              from_bus=int(net.line.at[idx, "from_bus"]) + 1,
                              to_bus=int(net.line.at[idx, "to_bus"]) + 1,
                              loss_mw=float(net.res_line.at[idx, "pl_mw"]),
                              current_ka=float(net.res_line.at[idx, "i_ka"])))
    return pd.DataFrame(hours), pd.DataFrame(buses), pd.DataFrame(lines)


def summarize(hourly):
    rows = []
    for scenario, d in hourly.groupby("scenario", sort=False):
        charge = d.bess_p_mw.clip(lower=0).sum()  # MW * 1 h = MWh
        discharge = -d.bess_p_mw.clip(upper=0).sum()
        delta_energy = (d.energy_end_mwh.iloc[-1] - d.energy_start_mwh.iloc[0]
                        if scenario == "pv_bess" else 0.0)
        conversion_loss = charge - discharge - delta_energy
        rows.append(dict(scenario=scenario, line_loss_mwh=d.line_loss_mw.sum(),
                         battery_conversion_loss_mwh=conversion_loss,
                         combined_loss_mwh=d.line_loss_mw.sum() + conversion_loss,
                         load_energy_mwh=d.load_mw.sum(), pv_energy_mwh=d.pv_mw.sum(),
                         import_mwh=d.grid_p_mw.clip(lower=0).sum(),
                         export_mwh=-d.grid_p_mw.clip(upper=0).sum(),
                         peak_import_mw=max(0.0, d.grid_p_mw.max()),
                         min_voltage_pu=d.v_min_pu.min(), max_voltage_pu=d.v_max_pu.max(),
                         mean_abs_voltage_deviation_pu=d.mean_abs_voltage_deviation_pu.mean(),
                         voltage_violation_bus_hours=d.violating_buses.sum(),
                         hours_any_violation=int((d.violating_buses > 0).sum()),
                         battery_charge_mwh=charge, battery_discharge_mwh=discharge,
                         terminal_energy_change_mwh=delta_energy,
                         max_balance_residual_mw=d.balance_residual_mw.abs().max()))
    out = pd.DataFrame(rows)
    base = out.loc[out.scenario == "baseline"].iloc[0]
    for column in ("line_loss_mwh", "combined_loss_mwh"):
        out[column.replace("_mwh", "_reduction_percent")] = 100 * (base[column] - out[column]) / base[column]
    return out
