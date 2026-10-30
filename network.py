"""The original radial case33bw network, with explicit physical bus numbering."""
import networkx as nx
import numpy as np
import pandapower as pp
import pandapower.networks as pn
import pandapower.topology as top


def build_network(config, scenario):
    if scenario not in ("baseline", "pv_only", "pv_bess"):
        raise ValueError(f"Unknown scenario: {scenario}")
    net = pn.case33bw()
    # pandapower case indices are 0..32; report original feeder buses as 1..33.
    if list(net.bus.index) != list(range(33)):
        raise ValueError("Unexpected case33bw indexing; review library conversion")
    if not np.isclose(net.load.p_mw.sum(), 3.715) or not np.isclose(net.load.q_mvar.sum(), 2.3):
        raise ValueError("Unexpected case33bw base load")
    if not np.allclose(net.bus.vn_kv, 12.66):
        raise ValueError("Unexpected nominal voltage")
    if int(net.line.in_service.sum()) != 32 or len(net.line) != 37:
        raise ValueError("Expected 32 energized branches and five open ties")
    if not nx.is_tree(top.create_nxgraph(net, multi=False)):
        raise ValueError("Feeder must be connected and radial")
    if len(net.ext_grid) != 1 or int(net.ext_grid.bus.iloc[0]) != 0:
        raise ValueError("Expected one slack at physical bus 1")
    net.ext_grid.loc[:, "vm_pu"] = config["slack_vm_pu"]
    if scenario != "baseline":
        for unit in config["pv_units"]:
            pp.create_sgen(net, bus=unit["bus"] - 1, p_mw=0, q_mvar=0,
                           sn_mva=unit["p_rated_mw"], name=f"PV_bus_{unit['bus']}")
    if scenario == "pv_bess":
        b = config["battery"]
        pp.create_storage(net, bus=b["bus"] - 1, p_mw=0, q_mvar=0,
                          max_e_mwh=b["e_nom_mwh"], min_e_mwh=b["soc_min"] * b["e_nom_mwh"],
                          soc_percent=100 * b["soc_initial"], sn_mva=b["p_max_mw"],
                          name="BESS")
    return net


def solve(net, algorithm="bfsw"):
    # Flat starts avoid dependence on previous-hour solver states.
    pp.runpp(net, algorithm=algorithm, init="flat", max_iteration=100,
             tolerance_mva=1e-9, numba=False, lightsim2grid=False,
             voltage_depend_loads=False, calculate_voltage_angles=True)
    if not net.converged or not np.isfinite(net.res_bus.vm_pu).all():
        raise RuntimeError("Power flow did not provide finite voltages for all buses")
