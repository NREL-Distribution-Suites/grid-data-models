import pytest
from gdm import PhaseLoadEquipment, ActivePower, ReactivePower


def test_invalid_power_system_load():
    with pytest.raises(ValueError) as _:
        PhaseLoadEquipment(
            name="phase-1-load-equipment1",
            num_customers=1,
            real_power=ActivePower(2.5, "kilowatt"),
            reactive_power=ReactivePower(0, "kilovar"),
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
            reactive_power=ReactivePower(0, "kilovar"),
            z_real=0.0,
            z_imag=1.0,
            i_real=0.0,
            i_imag=0.0,
            p_real=0.0,
            p_imag=0.0,
        )
