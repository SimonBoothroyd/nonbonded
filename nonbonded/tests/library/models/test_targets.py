import pytest
from pydantic import ValidationError

from nonbonded.library.models.targets import EvaluatorTarget


def test_optimization_validation():
    """Test that evaluator targets must have at least on calculation
    layer set."""

    target = EvaluatorTarget(
        id="name",
        data_set_ids=["data-set-1"],
        denominators={"Density": "1.0 * g / mL"},
    )

    with pytest.raises(ValidationError):
        EvaluatorTarget(**{**target.dict(), "allow_direct_simulation": False})
