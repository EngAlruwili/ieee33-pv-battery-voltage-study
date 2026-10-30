"""Regression tests for physical invariants and independent solver formulations."""
from copy import deepcopy
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from study.dispatch import battery_schedule
from study.inputs import read_inputs, validate_inputs
from study.simulation import SCENARIOS, run_scenario, summarize
from study.validation import benchmark, check_day

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def inputs():
    return read_inputs(ROOT / "config/default.json", ROOT / "data/profiles.csv")


def test_original_feeder_and_solvers(inputs):
    c, _ = inputs
    assert benchmark(c)["solver_max_voltage_difference_pu"] < 1e-6


def test_battery_energy_and_efficiency(inputs):
    c, p = inputs
    d = battery_schedule(c, p)
    b = c["battery"]
    charge = d.bess_p_mw.clip(lower=0).sum()
    discharge = -d.bess_p_mw.clip(upper=0).sum()
    assert discharge / charge == pytest.approx(b["eta_charge"] * b["eta_discharge"])
    assert d.energy_end_mwh.iloc[-1] == pytest.approx(d.energy_start_mwh.iloc[0])
    assert d.soc_end.between(b["soc_min"] - 1e-10, b["soc_max"] + 1e-10).all()
    assert d.bess_p_mw.abs().max() <= b["p_max_mw"] + 1e-10


def test_no_sun_means_no_battery_throughput(inputs):
    c, p = inputs
    p.pv_pu = 0.0
    d = battery_schedule(c, p)
    assert np.allclose(d.bess_p_mw, 0)
    assert np.allclose(d.soc_end, c["battery"]["soc_initial"])


def test_no_colocated_pv_means_no_charging(inputs):
    c, p = inputs
    c["battery"]["bus"] = 25
    assert np.allclose(battery_schedule(c, p).bess_p_mw, 0)


def test_low_power_high_capacity_respects_terminal_target(inputs):
    c, p = inputs
    c["battery"]["p_max_mw"] = .01
    c["battery"]["e_nom_mwh"] = 100
    d = battery_schedule(c, p)
    assert d.energy_end_mwh.iloc[-1] == pytest.approx(d.energy_start_mwh.iloc[0])
    assert d.bess_p_mw.abs().max() <= .01 + 1e-12


def test_invalid_hours_rejected(inputs):
    c, p = inputs
    c["battery"]["discharge_hours"] = [11, 18]
    with pytest.raises(ValueError, match="charging before discharging"):
        validate_inputs(c, p)


def test_all_scenarios_daily_energy_balance(inputs):
    c, p = inputs
    h = pd.concat([run_scenario(c, p, s)[0] for s in SCENARIOS], ignore_index=True)
    check_day(h, c)
    s = summarize(h)
    # Terminal SOC equality allows AC energy conservation with conversion loss.
    residual = s.import_mwh - s.export_mwh + s.pv_energy_mwh - s.load_energy_mwh - s.combined_loss_mwh
    assert np.max(np.abs(residual)) < 24e-6
    assert (s.line_loss_mwh > 0).all()
    # Do not assert that the intervention improves every metric: that is a result.


def test_zero_der_reproduces_baseline(inputs):
    c, p = inputs
    c = deepcopy(c)
    for unit in c["pv_units"]:
        unit["p_rated_mw"] = 0.0
    base = run_scenario(c, p, "baseline")[0]
    improved = run_scenario(c, p, "pv_bess")[0]
    assert np.allclose(base.v_min_pu, improved.v_min_pu, atol=1e-10, rtol=0)
    assert np.allclose(base.line_loss_mw, improved.line_loss_mw, atol=1e-10, rtol=0)
