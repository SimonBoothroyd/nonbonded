import pytest
from openff.toolkit.typing.engines.smirnoff import ForceField as OFFForceField
from openff.toolkit.typing.engines.smirnoff import vdWHandler
from openff.toolkit.typing.engines.smirnoff.parameters import (
    ChargeIncrementModelHandler,
)

from nonbonded.library.models.forcefield import ForceField


@pytest.fixture()
def smirnoff_force_field() -> OFFForceField:
    from simtk import unit

    off_force_field = OFFForceField(
        '<SMIRNOFF version="0.3" aromaticity_model="OEAroModel_MDL"></SMIRNOFF>'
    )

    vdw_handler = vdWHandler(**{"version": "0.3"})
    vdw_handler.add_parameter(
        parameter_kwargs={
            "smirks": "[#6:1]",
            "epsilon": 1.0 * unit.kilojoules_per_mole,
            "sigma": 1.0 * unit.angstrom,
        }
    )
    off_force_field.register_parameter_handler(vdw_handler)

    charge_handler = ChargeIncrementModelHandler(**{"version": "0.3"})
    charge_handler.add_parameter(
        parameter_kwargs={
            "smirks": "[#6:1]-[#6:2]",
            "charge_increment1": 1.0 * unit.elementary_charge,
            "charge_increment2": -1.0 * unit.elementary_charge,
        }
    )
    off_force_field.register_parameter_handler(charge_handler)

    return off_force_field


@pytest.fixture()
def force_field(smirnoff_force_field: OFFForceField) -> ForceField:
    return ForceField.from_openff(smirnoff_force_field)
