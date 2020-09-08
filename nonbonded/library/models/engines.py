from typing import TYPE_CHECKING, Dict

from pydantic import Field
from typing_extensions import Literal

from nonbonded.library.models import BaseORM
from nonbonded.library.models.validators.string import NonEmptyStr

if TYPE_CHECKING:
    PositiveFloat = float
    PositiveInt = int
else:
    from pydantic import PositiveFloat, PositiveInt


class ForceBalance(BaseORM):

    type: Literal["ForceBalance"] = "ForceBalance"

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

    priors: Dict[NonEmptyStr, PositiveFloat] = Field(
        ..., description="The priors to place on each class of parameter."
    )
