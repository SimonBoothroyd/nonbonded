from nonbonded.library.models.forcefield import ForceField


def test_to_from_openff_smirnoff():
    """Tests that a force field model can be created from a
    force field.
    """
    from openff.toolkit.typing.engines.smirnoff.forcefield import (
        ForceField as OFFForceField,
    )

    force_field = ForceField.from_openff(OFFForceField("openff-1.0.0.offxml"))
    assert isinstance(force_field.to_openff(), OFFForceField)


def test_to_from_openff_evaluator():
    """Tests that a force field model can be created from a
    force field.
    """
    from openff.evaluator.forcefield import TLeapForceFieldSource

    force_field = ForceField.from_openff(TLeapForceFieldSource())
    assert isinstance(force_field.to_openff(), TLeapForceFieldSource)
