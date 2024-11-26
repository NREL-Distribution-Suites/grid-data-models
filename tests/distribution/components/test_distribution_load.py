import pytest
from uuid import uuid4

from gdm import (
    PhaseLoadEquipment,
    DistributionLoad,
    DistributionBus,
    LoadEquipment,
    ReactivePower,
    ActivePower,
)


def test_invalid_power_system_load():
    with pytest.raises(ValueError) as _:
        PhaseLoadEquipment(
            name="phase-1-load-equipment1",
            num_customers=1,
            real_power=ActivePower(2.5, "kilowatt"),
            reactive_power=ReactivePower(0.2, "kilovar"),
            z_real=1.0,
            z_imag=0.0,
            i_real=0.0,
            i_imag=0.0,
            p_real=0.0,
            p_imag=0.0,
        )
    with pytest.raises(ValueError) as _:
        PhaseLoadEquipment(
            name="phase-1-load-equipment2",
            num_customers=1,
            real_power=ActivePower(2.5, "kilowatt"),
            reactive_power=ReactivePower(0.2, "kilovar"),
            z_real=0.0,
            z_imag=1.0,
            i_real=0.0,
            i_imag=0.0,
            p_real=0.0,
            p_imag=0.0,
        )


def test_timeseries_load_aggregation():
    loads = [
        DistributionLoad.example().model_copy(
            update={
                "uuid": uuid4(),
                "name": f"load_{j}",
                "equipment": LoadEquipment.example().model_copy(
                    update={
                        "uuid": uuid4(),
                        "name": f"load_equipment_{j}",
                        "phase_loads": [
                            PhaseLoadEquipment.example().model_copy(
                                update={
                                    "uuid": uuid4(),
                                    "name": f"phase_load_{j}",
                                    "real_power": ActivePower(j + 1, "kilowatt"),
                                    "reactive_power": ReactivePower((j + 1) * 0.44, "kilovar"),
                                }
                            )
                        ]
                        * 3,
                    }
                ),
            }
        )
        for j in range(10)
    ]

    for load in loads:
        load.pprint()
        break

    aggregate_load = DistributionLoad.aggregate(loads, DistributionBus.example(), "total_load", {})
    aggregate_load.pprint()
