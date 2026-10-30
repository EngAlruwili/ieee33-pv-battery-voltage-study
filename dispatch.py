"""Transparent day-ahead schedule with AC-side power and internal stored energy."""
import numpy as np
import pandas as pd


def _allocate(total, capacities, weights):
    """Weighted allocation with saturation. Its sum equals total within tolerance."""
    out = np.zeros_like(capacities, dtype=float)
    remaining = float(total)
    for _ in range(len(out) + 2):
        active = (capacities - out > 1e-12) & (weights > 0)
        if remaining < 1e-12 or not active.any():
            break
        addition = np.minimum(capacities[active] - out[active],
                              remaining * weights[active] / weights[active].sum())
        out[active] += addition
        remaining -= addition.sum()
    if remaining > 1e-9:
        raise ValueError("Requested energy cannot be allocated in dispatch windows")
    return out


def battery_schedule(config, profiles):
    """Positive p_mw charges; negative p_mw discharges (pandapower convention).

    Charge is capped by co-located PV output, but AC power is fungible: this
    does not prove that every charging electron came from the PV plant.
    A one-day perfect-forecast schedule is used; this is not real-time control.
    """
    b = config["battery"]
    dt = 1.0  # hours; validated input uses exactly 24 hourly intervals
    ch, dis = np.zeros(24), np.zeros(24)
    pv_local = sum(u["p_rated_mw"] for u in config["pv_units"] if u["bus"] == b["bus"])
    for t in b["charge_hours"]:
        ch[t] = min(b["p_max_mw"], pv_local * profiles.pv_pu.iloc[t])
    for t in b["discharge_hours"]:
        dis[t] = b["p_max_mw"]
    initial = b["soc_initial"] * b["e_nom_mwh"]
    # Limit throughput by room in the battery AND ability to empty it by day's end.
    internal_gain = min((b["soc_max"] * b["e_nom_mwh"] - initial),
                        ch.sum() * dt * b["eta_charge"],
                        dis.sum() * dt / b["eta_discharge"])
    charge = _allocate(internal_gain / b["eta_charge"] / dt, ch, profiles.pv_pu.to_numpy())
    discharge = _allocate(internal_gain * b["eta_discharge"] / dt, dis,
                          profiles.load_pu.to_numpy())
    power = charge - discharge
    delta = (charge * b["eta_charge"] - discharge / b["eta_discharge"]) * dt
    energy = np.r_[initial, initial + np.cumsum(delta)]
    if not (energy.min() >= b["soc_min"] * b["e_nom_mwh"] - 1e-9 and
            energy.max() <= b["soc_max"] * b["e_nom_mwh"] + 1e-9 and
            abs(energy[-1] - initial) < 1e-9):
        raise ValueError("Battery energy or terminal SOC constraint failed")
    return pd.DataFrame({"hour": profiles.hour, "bess_p_mw": power,
                         "energy_start_mwh": energy[:-1], "energy_end_mwh": energy[1:],
                         "soc_start": energy[:-1] / b["e_nom_mwh"],
                         "soc_end": energy[1:] / b["e_nom_mwh"]})
