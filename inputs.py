"""Read explicit, deterministic study inputs; reject unsupported configurations."""
import json
from pathlib import Path

import numpy as np
import pandas as pd


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_inputs(config_path, profile_path):
    config = json.loads(Path(config_path).read_text(encoding="utf-8"))
    profiles = pd.read_csv(profile_path)
    validate_inputs(config, profiles)
    return config, profiles


def validate_inputs(c, p):
    require(list(p.columns) == ["hour", "load_pu", "pv_pu"], "Unexpected profile columns")
    require(len(p) == 24 and np.array_equal(p.hour, np.arange(24)),
            "Use exactly 24 consecutive one-hour intervals, starting at hour 0")
    require(np.isfinite(p.to_numpy()).all(), "Profiles must be finite")
    require((p.load_pu > 0).all() and p.pv_pu.between(0, 1).all(), "Invalid profile values")
    require(0 < c["voltage_min_pu"] < c["slack_vm_pu"] < c["voltage_max_pu"],
            "Invalid voltage settings")
    require(len(c["pv_units"]) > 0, "Provide at least one PV unit")
    for u in c["pv_units"]:
        require(isinstance(u["bus"], int) and 2 <= u["bus"] <= 33, "PV bus must be 2..33")
        require(np.isfinite(u["p_rated_mw"]) and u["p_rated_mw"] >= 0, "Invalid PV rating")
    b = c["battery"]
    require(isinstance(b["bus"], int) and 2 <= b["bus"] <= 33, "Battery bus must be 2..33")
    require(np.isfinite(b["p_max_mw"]) and b["p_max_mw"] >= 0, "Invalid battery power")
    require(np.isfinite(b["e_nom_mwh"]) and b["e_nom_mwh"] > 0, "Invalid energy rating")
    require(0 <= b["soc_min"] <= b["soc_initial"] < b["soc_max"] <= 1, "Invalid SOC limits")
    require(0 < b["eta_charge"] <= 1 and 0 < b["eta_discharge"] <= 1, "Invalid efficiency")
    for key in ("charge_hours", "discharge_hours"):
        h = b[key]
        require(bool(h) and len(h) == len(set(h)) and
                all(isinstance(t, int) and 0 <= t < 24 for t in h), "Invalid dispatch hours")
    require(max(b["charge_hours"]) < min(b["discharge_hours"]),
            "This day-ahead schedule requires charging before discharging")
