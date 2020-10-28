import abc
from typing import TYPE_CHECKING, Dict, Optional, Union

from openff.recharge.conformers import ConformerSettings
from openff.recharge.esp import ESPSettings
from pydantic import Field, conlist, root_validator
from typing_extensions import Literal

from nonbonded.library.models import BaseORM
from nonbonded.library.models.validators.string import IdentifierStr, NonEmptyStr

if TYPE_CHECKING:
    PositiveFloat = float
    PositiveInt = int

else:
    from pydantic import PositiveFloat, PositiveInt


class OptimizationTarget(BaseORM, abc.ABC):
    """The base class for schemas describing a particular fitting target, such as
    a target which fits to experimental data."""

    id: IdentifierStr = Field(..., description="The name of the fitting target.")

    weight: PositiveFloat = Field(
        1.0,
        description="The amount to weight this fitting targets contribution to the "
        "total objective function by.",
    )


class EvaluatorTarget(OptimizationTarget):
    """A fitting target which uses the ``openff-evaluator`` framework to train
    force field parameters against experimental physical property data."""

    model_version: Literal[0] = Field(
        0,
        description="The current version of this model. Models with different version "
        "numbers are incompatible.",
    )

    data_set_ids: conlist(IdentifierStr, min_items=1) = Field(
        ...,
        description="The unique identifiers of the physical property data sets to "
        "include in this optimization target.",
    )
    denominators: Dict[NonEmptyStr, NonEmptyStr] = Field(
        ...,
        description="The denominators to scale each class of properties "
        "contribution to the objective function by.",
    )

    allow_direct_simulation: bool = Field(
        True,
        description="This option controls whether the OpenFF Evaluator should be "
        "allowed to attempt to estimate the physical property training set using the "
        "direct simulation calculation layer.",
    )
    n_molecules: Optional[PositiveInt] = Field(
        None,
        description="This field controls the number of molecules to use in the "
        "simulations of physical properties. This value is only used when simulating "
        "properties whose default simulation schema (see the OpenFF Evaluator "
        "documentation for details) accept this option. If no value is provided, or "
        "the option is not supported by the schema, the schema default will be used "
        "instead.",
    )

    allow_reweighting: bool = Field(
        False,
        description="This option controls whether the OpenFF Evaluator should be "
        "allowed to attempt to estimate the physical property training set using the "
        "cached simulation data reweighting calculation layer.",
    )
    n_effective_samples: Optional[PositiveInt] = Field(
        None,
        description="This field controls the minimum number of effective samples which "
        "are required in order to estimate a physical property be reweighting cached "
        "simulation data. This value is only used when reweighting properties whose "
        "default reweighting schema (see the OpenFF Evaluator documentation for "
        "details) accept this option. If no value is provided, or the option is not "
        "supported by the schema the schema default will be used instead.",
    )

    @root_validator
    def _validate_calculation_layers(cls, values):
        """Validates that at least one calculation approach has been specified."""
        allow_direct_simulation = values.get("allow_direct_simulation")
        allow_reweighting = values.get("allow_reweighting")

        assert allow_direct_simulation or allow_reweighting

        return values


class RechargeTarget(OptimizationTarget):
    """A fitting target which uses the ``openff-recharge`` framework to train
    bond charge correction parameters against QM electrostatic potential data."""

    model_version: Literal[0] = Field(
        0,
        description="The current version of this model. Models with different version "
        "numbers are incompatible.",
    )

    molecule_set_ids: conlist(IdentifierStr, min_items=1) = Field(
        ...,
        description="The unique identifiers of the molecule sets to include in this "
        "optimization target.",
    )

    conformer_settings: "ConformerSettings" = Field(
        ...,
        description="The settings to use when generating conformers for each molecule "
        "in the training molecule sets.",
    )
    esp_settings: "ESPSettings" = Field(
        ...,
        description="The settings to use when generating the electrostatic data "
        "for each molecule in the training molecule sets.",
    )

    property: Literal["esp", "electric-field"] = Field(
        ..., description="The type of electrostatic property to train against."
    )


OptimizationTarget = Union[EvaluatorTarget, RechargeTarget]
