import os
from collections import defaultdict

import click

from nonbonded.cli.options.evaluator import (
    ComputeResources,
    DaskHPCClusterConfig,
    DaskLocalClusterConfig,
    EvaluatorServerConfig,
    QueueWorkerResources,
)
from nonbonded.library.models.datasets import DataSet
from nonbonded.library.models.projects import Optimization
from nonbonded.library.templates.forcebalance import ForceBalanceInput
from nonbonded.library.templates.submission import Submission, SubmissionTemplate
from nonbonded.library.utilities.logging import (
    get_log_levels,
    setup_timestamp_logging,
    string_to_log_level,
)


@click.command(help="Generates the input files for a specified optimization.")
@click.option(
    "--project-id",
    type=click.STRING,
    help="The id of the project which the optimization to is part of.",
)
@click.option(
    "--study-id",
    type=click.STRING,
    help="The id of the study which the optimization is part of.",
)
@click.option(
    "--optimization-id", type=click.STRING, help="The id of the optimization.",
)
@click.option(
    "--backend",
    "backend_name",
    default="lilac-dask",
    type=click.Choice(["lilac-dask", "lilac-local"], case_sensitive=True),
    help="The name of the backend to perform the optimization using.",
    show_default=True,
)
@click.option(
    "--environment",
    "environment_name",
    default="forcebalance",
    type=click.STRING,
    help="The name of the conda environment to run using.",
    show_default=True,
)
@click.option(
    "--port",
    default=8000,
    type=click.INT,
    help="The port to run the evaluator server on.",
    show_default=True,
)
@click.option(
    "--max-workers",
    required=True,
    type=click.INT,
    help="The maximum number of workers to spawn. This option is only used with dask-"
    "jobqueue based backends",
    show_default=True,
)
@click.option(
    "--max-wallclock",
    "max_wall_clock",
    default="168:00",
    type=click.STRING,
    help="The maximum wall-clock time to run for.",
    show_default=True,
)
@click.option(
    "--max-memory",
    default=8,
    type=click.INT,
    help="The maximum memory (GB) to request for the main job.",
    show_default=True,
)
@click.option(
    "--log-level",
    default="info",
    type=click.Choice(get_log_levels()),
    help="The verbosity of the server logger.",
    show_default=True,
)
def generate(
    project_id,
    study_id,
    optimization_id,
    backend_name,
    environment_name,
    port,
    max_workers,
    max_wall_clock,
    max_memory,
    log_level,
):

    from forcebalance.evaluator_io import Evaluator_SMIRNOFF
    from openff.evaluator import unit
    from openforcefield.typing.engines.smirnoff import ForceField

    # Set up logging if requested.
    logging_level = string_to_log_level(log_level)

    if logging_level is not None:
        setup_timestamp_logging(logging_level)

    # Retrieve the optimization
    optimization: Optimization = Optimization.from_rest(
        project_id, study_id, optimization_id
    )

    root_directory = optimization_id
    os.makedirs(root_directory, exist_ok=True)

    # Save the optimization definition in the directory
    optimization_path = os.path.join(root_directory, "optimization.json")

    with open(optimization_path, "w") as file:
        file.write(optimization.json())

    # Create the force field directory
    force_field_directory = os.path.join(root_directory, "forcefield")
    os.makedirs(force_field_directory, exist_ok=True)

    force_field = ForceField(optimization.initial_force_field)

    # Add the required cosmetic attributes to the force field.
    parameters_to_train = defaultdict(lambda: defaultdict(list))

    for parameter_to_train in optimization.parameters_to_train:

        parameters_to_train[parameter_to_train.handler_type][
            parameter_to_train.smirks
        ].append(parameter_to_train.attribute_name)

    for handler_type in parameters_to_train:
        for smirks in parameters_to_train[handler_type]:

            attributes = parameters_to_train[handler_type][smirks]
            attributes_string = ", ".join(attributes)

            parameter_handler = force_field.get_parameter_handler(handler_type)

            parameter = parameter_handler.parameters[smirks]
            parameter.add_cosmetic_attribute("parameterize", attributes_string)

    force_field_path = os.path.join(
        force_field_directory, optimization.initial_force_field
    )
    force_field.to_file(
        force_field_path, io_format="offxml", discard_cosmetic_attributes=False
    )

    # Create the options.in file.
    optimize_in_path = os.path.join(root_directory, "optimize.in")

    optimize_in_contents = ForceBalanceInput.generate(
        optimization.initial_force_field,
        optimization.force_balance_input.max_iterations,
        optimization.force_balance_input.convergence_step_criteria,
        optimization.force_balance_input.convergence_objective_criteria,
        optimization.force_balance_input.convergence_gradient_criteria,
        optimization.force_balance_input.n_criteria,
        optimization.force_balance_input.target_name,
        optimization.priors,
    )

    with open(optimize_in_path, "w") as file:
        file.write(optimize_in_contents)

    # Create the targets directory
    targets_directory = os.path.join(
        root_directory, "targets", optimization.force_balance_input.target_name
    )
    os.makedirs(targets_directory, exist_ok=True)

    # Store the data set in the targets directory
    training_set: DataSet = DataSet.from_rest(optimization.training_set_id)

    with open(
        os.path.join(targets_directory, "training-set-definition.json"), "w"
    ) as file:
        file.write(training_set.json())

    evaluator_set = training_set.to_evaluator()
    evaluator_set.json(os.path.join(targets_directory, "training-set.json"))

    # Create the target options
    target_options = Evaluator_SMIRNOFF.OptionsFile()
    target_options.connection_options.server_port = port
    target_options.estimation_options.calculation_layers = ["SimulationLayer"]

    target_options.data_set_path = "training-set.json"

    target_options.weights = {
        property_type: 1.0 for property_type in evaluator_set.property_types
    }
    target_options.denominators = {
        property_type: unit.Quantity(value)
        for property_type, value in optimization.denominators.items()
    }
    target_options.polling_interval = 600

    with open(os.path.join(targets_directory, "options.json"), "w") as file:
        file.write(target_options.to_json())

    # Generate a server configuration
    if backend_name == "lilac-local":

        backend_config = DaskLocalClusterConfig(resources_per_worker=ComputeResources())

    elif backend_name == "lilac-dask":

        backend_config = DaskHPCClusterConfig(
            maximum_workers=max_workers,
            resources_per_worker=QueueWorkerResources(),
            queue_name="gpuqueue",
            setup_script_commands=[
                f"conda activate {environment_name}",
                "module load cuda/10.1",
            ],
        )

    else:
        raise NotImplementedError()

    server_config = EvaluatorServerConfig(backend_config=backend_config, port=port)

    with open(os.path.join(root_directory, "server-config.json"), "w") as file:
        file.write(server_config.json())

    # Create a job submission file
    submission_path = os.path.join(root_directory, "submit.sh")

    submission = Submission(
        job_name="optim",
        wall_clock_limit=max_wall_clock,
        max_memory=max_memory,
        gpu=backend_name == "lilac-local",
        environment_name=environment_name,
        commands=[
            "nonbonded optimization run --config server-config.json",
            "nonbonded optimization analyze",
        ],
    )

    submission_content = SubmissionTemplate.generate("submit_lilac.txt", submission)

    with open(submission_path, "w") as file:
        file.write(submission_content)
