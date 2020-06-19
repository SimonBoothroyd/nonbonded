import logging
import os
from glob import glob

import click

from nonbonded.library.models.datasets import DataSetCollection
from nonbonded.library.models.forcefield import ForceField
from nonbonded.library.models.projects import Optimization
from nonbonded.library.models.results import AnalysedResult, OptimizationResult
from nonbonded.library.statistics.statistics import StatisticType
from nonbonded.library.utilities.exceptions import ForceFieldNotFound
from nonbonded.library.utilities.logging import (
    get_log_levels,
    setup_timestamp_logging,
    string_to_log_level,
)
from nonbonded.library.utilities.migration import reindex_results

logger = logging.getLogger(__name__)


@click.command(help="Analyzes the output of an optimization.")
@click.option(
    "--reindex",
    is_flag=True,
    default=False,
    help="Attempt to determine matching reference and estimated data points based on "
    "the state at which the property was measured, rather than by its unique id. This "
    "option is only to allow backwards compatibility with optimizations ran not using "
    "this framework, and should not be used in general.",
)
@click.option(
    "--log-level",
    default="info",
    type=click.Choice(get_log_levels()),
    help="The verbosity of the server logger.",
    show_default=True,
)
def analyze(reindex, log_level):

    from forcebalance.nifty import lp_load
    from openff.evaluator.client import RequestResult
    from openforcefield.typing.engines.smirnoff import ForceField as OFFForceField

    # Set up logging if requested.
    logging_level = string_to_log_level(log_level)

    if logging_level is not None:
        setup_timestamp_logging(logging_level)

    # Load in the definition of the optimization to optimize.
    optimization = Optimization.parse_file("optimization.json")

    # Create a directory to store the results in
    output_directory = "analysis"
    os.makedirs(output_directory, exist_ok=True)

    # Load in the refit force field (if it exists)
    refit_force_field_path = os.path.join("result", "optimize", "force-field.offxml")

    if not os.path.isfile(refit_force_field_path):

        raise ForceFieldNotFound(
            f"A refit force field could not be found (expected "
            f"path={refit_force_field_path}. Make sure that the optimization completed "
            f"at least one iteration successfully."
        )

    refit_force_field_off = OFFForceField(
        refit_force_field_path, allow_cosmetic_attributes=True
    )
    refit_force_field = ForceField.from_openff(refit_force_field_off)

    # Load the reference data set
    reference_data_sets = DataSetCollection.parse_file(
        os.path.join(
            "targets",
            optimization.force_balance_input.evaluator_target_name,
            "training-set-collection.json",
        )
    )

    # Determine the number of optimization iterations.
    tmp_directory = os.path.join(
        "optimize.tmp", optimization.force_balance_input.evaluator_target_name
    )

    n_iterations = len(glob(os.path.join(tmp_directory, "iter_*", "results.json")))

    if n_iterations == 0:

        raise ValueError(
            "No iteration results could be found, even though a refit force field "
            "was. Make sure not to delete the `optimize.tmp` directory after the "
            "optimization has completed."
        )

    # Analyse the results of each iteration.
    objective_function = {}
    iteration_statistics = {}

    for iteration in range(n_iterations):

        logger.info(f"Analysing the results of iteration {iteration}")

        iteration_directory = os.path.join(
            tmp_directory, "iter_" + str(iteration).zfill(4)
        )
        iteration_results_path = os.path.join(iteration_directory, "results.json")

        if not os.path.isfile(iteration_results_path):

            logger.info(
                f"The results file could not be found for iteration {iteration}."
            )

            continue

        iteration_results = RequestResult.from_json(iteration_results_path)

        if reindex:
            iteration_results = reindex_results(iteration_results, reference_data_sets)

        estimated_data_set = iteration_results.estimated_properties

        # Generate statistics about each iteration.
        analyzed_results = AnalysedResult.from_evaluator(
            reference_data_set=reference_data_sets,
            estimated_data_set=estimated_data_set,
            analysis_environments=optimization.analysis_environments,
            statistic_types=[StatisticType.RMSE],
        )
        iteration_statistics[iteration] = analyzed_results.statistic_entries

        # Save the results
        with open(
            os.path.join(output_directory, f"iteration-{iteration}.json"), "w"
        ) as file:

            file.write(analyzed_results.json())

        # Extract the value of this iterations objective function
        objective_file_path = os.path.join(iteration_directory, "objective.p")
        objective_statistics = lp_load(objective_file_path)

        objective_function[iteration] = objective_statistics["X"]

    # Save the full results
    optimization_results = OptimizationResult(
        project_id=optimization.project_id,
        study_id=optimization.study_id,
        id=optimization.id,
        objective_function=objective_function,
        refit_force_field=refit_force_field,
        statistics=iteration_statistics,
    )

    with open(os.path.join(output_directory, "optimization-results.json"), "w") as file:
        file.write(optimization_results.json())
