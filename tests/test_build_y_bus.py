from pathlib import Path

from scipy.sparse import csc_matrix
import opendssdirect as dss
import pandas as pd

from gdm.distribution import DistributionSystem
from gdm.distribution.y_bus import YBus

BASE_PATH = Path(__file__).parent


def test_y_bus():
    system = DistributionSystem.from_json(BASE_PATH / "dataset" / "ieee13" / "ieee_13_node.json")
    ybus = YBus(system)
    y, bus_phase_index = ybus.build_ybus_sparse()
    bus_index = [f"{bus}__{phase.name}" for bus, phase in bus_phase_index]
    ybus_dense = pd.DataFrame(y.todense(), index=bus_index, columns=bus_index)
    coo = y.tocoo()

    swapped_dict = {value: key for key, value in bus_phase_index.items()}

    rr = [f"{swapped_dict[r][0]}__{swapped_dict[r][1].name}" for r in coo.row]
    cc = [f"{swapped_dict[c][0]}__{swapped_dict[c][1].name}" for c in coo.col]

    df = pd.DataFrame({"row": rr, "col": cc, "value": coo.data})
    # df = df.groupby(['row', 'col'], as_index=False)['value'].sum()
    df.to_csv("sparse_calc.csv", index=False)
    ybus_dense.to_csv("dense_calc.csv", index=True)

    model = BASE_PATH / "dataset" / "ieee13_dss" / "IEEE13Nodeckt.dss"

    dss.run_command(f"redirect {model}")
    dss.Solution.Solve()
    a = dss.YMatrix.getYsparse()
    b = csc_matrix(a)
    nodes = dss.Circuit.AllNodeNames()
    nodes = [n.replace(".1", "__A").replace(".2", "__B").replace(".3", "__C") for n in nodes]
    ybus_dense = pd.DataFrame(y.todense(), index=nodes, columns=nodes)
    ybus_dense = ybus_dense[bus_index]
    ybus_dense = ybus_dense.T[bus_index]
    ybus_dense.T.to_csv("dense_act.csv", index=True)

    coo = b.tocoo()

    rr = [nodes[r].replace(".1", "__A").replace(".2", "__B").replace(".3", "__B") for r in coo.row]
    cc = [nodes[c].replace(".1", "__A").replace(".2", "__B").replace(".3", "__B") for c in coo.col]

    df = pd.DataFrame({"row": rr, "col": cc, "value": coo.data})
    df.to_csv("sparse_act.csv", index=False)
