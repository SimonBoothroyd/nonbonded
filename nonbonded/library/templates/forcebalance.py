import os
from typing import Dict, List, Union

from jinja2 import Template

from nonbonded.library.models.targets import EvaluatorTarget, RechargeTarget
from nonbonded.library.templates import BaseTemplate
from nonbonded.library.utilities import get_data_file_path


class ForceBalanceInput(BaseTemplate):
    @classmethod
    def generate(
        cls,
        force_field_file_name: str,
        max_iterations: int,
        convergence_step_criteria: float,
        convergence_objective_criteria: float,
        convergence_gradient_criteria: float,
        n_criteria: int,
        initial_trust_radius: float,
        minimum_trust_radius: float,
        targets: List[Union[EvaluatorTarget, RechargeTarget]],
        priors: Dict[str, float],
        **options
    ):

        cls._check_unrecognised_options(**options)

        template_file_name = get_data_file_path(os.path.join("jinja", "optimize.txt"))

        with open(template_file_name) as file:
            template = Template(file.read())

        evaluator_targets = [
            target for target in targets if isinstance(target, EvaluatorTarget)
        ]
        recharge_targets = [
            target for target in targets if isinstance(target, RechargeTarget)
        ]

        rendered_template = template.render(
            force_field_file_name=force_field_file_name,
            max_iterations=max_iterations,
            convergence_step_criteria=convergence_step_criteria,
            convergence_objective_criteria=convergence_objective_criteria,
            convergence_gradient_criteria=convergence_gradient_criteria,
            n_criteria=n_criteria,
            initial_trust_radius=initial_trust_radius,
            minimum_trust_radius=minimum_trust_radius,
            evaluator_targets=evaluator_targets,
            recharge_targets=recharge_targets,
            priors=priors,
        )
        return rendered_template
