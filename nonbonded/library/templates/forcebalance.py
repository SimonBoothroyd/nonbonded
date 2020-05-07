import os
from typing import Dict

from jinja2 import Template

from nonbonded.library.templates import BaseTemplate
from nonbonded.library.utilities import get_data_filename


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
        target_name: str,
        priors: Dict[str, float],
        **options
    ):

        cls._check_unrecognised_options(**options)

        template_file_name = get_data_filename(os.path.join("jinja", "optimize.txt"))

        with open(template_file_name) as file:
            template = Template(file.read())

        rendered_template = template.render(
            force_field_file_name=force_field_file_name,
            max_iterations=max_iterations,
            convergence_step_criteria=convergence_step_criteria,
            convergence_objective_criteria=convergence_objective_criteria,
            convergence_gradient_criteria=convergence_gradient_criteria,
            n_criteria=n_criteria,
            target_name=target_name,
            priors=priors,
        )
        return rendered_template
