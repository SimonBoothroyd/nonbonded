from typing import TYPE_CHECKING, Optional

from pydantic import Field, root_validator

from nonbonded.library.models import BaseORM
from nonbonded.library.models.validators.string import IdentifierStr

if TYPE_CHECKING:
    PositiveFloat = float
    PositiveInt = int
else:
    from pydantic import PositiveFloat, PositiveInt


class ForceBalanceOptions(BaseORM):

    max_iterations: PositiveInt = Field(
        12, description="The maximum number of optimization iterations to perform."
    )

    convergence_step_criteria: PositiveFloat = Field(
        0.0001, description="The convergence criterion of the step size."
    )
    convergence_objective_criteria: PositiveFloat = Field(
        0.0001, description="The convergence criterion of the objective function."
    )
    convergence_gradient_criteria: PositiveFloat = Field(
        0.0001, description="The convergence criterion of the gradient norm."
    )
    n_criteria: PositiveInt = Field(
        3,
        description="The number of convergence criteria that must be met for the "
        "optimizer to be declared converged.",
    )

    initial_trust_radius: PositiveFloat = Field(
        0.25, description="The initial trust radius."
    )
    minimum_trust_radius: PositiveFloat = Field(
        0.05, description="The minimum trust radius."
    )

    evaluator_target_name: IdentifierStr = Field(
        "phys-prop", description="The name of the evaluator fitting target."
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
        "documentation for details) accept this option. If no value is provided the "
        "schema default will be used.",
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
        "details) accept this option. If no value is provided the schema default will "
        "be used.",
    )

    @root_validator
    def _validate_calculation_layers(cls, values):
        """Validates that at least one calculation approach has been specified."""
        allow_direct_simulation = values.get("allow_direct_simulation")
        allow_reweighting = values.get("allow_reweighting")

        assert allow_direct_simulation or allow_reweighting

        return values
