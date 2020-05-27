import os
from collections import defaultdict
from typing import List

from nonbonded.cli.options.evaluator import (
    ComputeResources,
    DaskHPCClusterConfig,
    DaskLocalClusterConfig,
    EvaluatorServerConfig,
    QueueWorkerResources,
)
from nonbonded.library.models.datasets import DataSet, DataSetCollection
from nonbonded.library.models.projects import Optimization
from nonbonded.library.templates.forcebalance import ForceBalanceInput
from nonbonded.library.templates.submission import Submission, SubmissionTemplate


class OptimizationFactory:
    """An factory used to create the directory structure and
    inputs for a particular optimization.
    """

    @classmethod
    def generate(
        cls,
        optimization: Optimization,
        backend_name: str,
        environment_name: str,
        port: int,
        max_workers: int,
        max_wall_clock: str,
        max_memory: int,
    ):

        from forcebalance.evaluator_io import Evaluator_SMIRNOFF
        from openff.evaluator import unit

        root_directory = optimization.id
        os.makedirs(root_directory, exist_ok=True)

        # Save the optimization definition in the directory
        optimization_path = os.path.join(root_directory, "optimization.json")

        with open(optimization_path, "w") as file:
            file.write(optimization.json())

        # Create the force field directory
        force_field_directory = os.path.join(root_directory, "forcefield")
        os.makedirs(force_field_directory, exist_ok=True)

        off_force_field = optimization.initial_force_field.to_openff()

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

                parameter_handler = off_force_field.get_parameter_handler(handler_type)

                parameter = parameter_handler.parameters[smirks]
                parameter.add_cosmetic_attribute("parameterize", attributes_string)

        force_field_path = os.path.join(force_field_directory, "force-field.offxml")
        off_force_field.to_file(
            force_field_path, io_format="offxml", discard_cosmetic_attributes=False
        )

        # Create the options.in file.
        optimize_in_path = os.path.join(root_directory, "optimize.in")

        optimize_in_contents = ForceBalanceInput.generate(
            "force-field.offxml",
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
        training_sets: List[DataSet] = [
            DataSet.from_rest(x) for x in optimization.training_set_ids
        ]
        training_set_collection = DataSetCollection(data_sets=training_sets)

        with open(
            os.path.join(targets_directory, "training-set-collection.json"), "w"
        ) as file:
            file.write(training_set_collection.json())

        evaluator_set = training_set_collection.to_evaluator()
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

            backend_config = DaskLocalClusterConfig(
                resources_per_worker=ComputeResources()
            )

        elif backend_name == "lilac-dask":

            # noinspection PyTypeChecker
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
