from pydantic import BaseModel, Field


class ForceBalanceOptions(BaseModel):

    max_iterations: int = Field(
        12, description="The maximum number of optimization iterations to perform."
    )

    convergence_step_criteria: float = Field(
        0.0001, description="The convergence criterion of the step size."
    )
    convergence_objective_criteria: float = Field(
        0.0001, description="The convergence criterion of the objective function."
    )
    convergence_gradient_criteria: float = Field(
        0.0001, description="The convergence criterion of the gradient norm."
    )
    n_criteria: int = Field(
        3,
        description="The number of convergence criteria that must be met for the "
        "optimizer to be declared converged.",
    )

    target_name: str = Field("phys-prop", description="The name of the fitting target.")
