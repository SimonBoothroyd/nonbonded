from typing import TYPE_CHECKING

from pydantic import Field

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

    target_name: IdentifierStr = Field(
        "phys-prop", description="The name of the fitting target."
    )
