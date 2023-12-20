
from infra_sys.system import System
from powersystem_data_models.node import Node
from powersystem_data_models.units import Voltage


def test_node():
    
    sys = System()
    node = Node(name='voltage1', nominal_voltage=Voltage(3, 'volt'), phases=[])

    sys.add_component(node)
    sys.to_json("test.json", overwrite=True)
    sys = System.from_json("test.json")
    node = sys.get_component(Node, 'voltage1')
    print(node)
