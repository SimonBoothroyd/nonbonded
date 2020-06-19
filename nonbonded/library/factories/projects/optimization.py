import os
from collections import defaultdict
from typing import TYPE_CHECKING, List

from nonbonded.cli.options.evaluator import (
    ComputeResources,
    DaskHPCClusterConfig,
    DaskLocalClusterConfig,
    EvaluatorServerConfig,
    QueueWorkerResources,
)
from nonbonded.library.models.datasets import DataSet, DataSetCollection
from nonbonded.library.models.projects import Optimization
from nonbonded.library.models.results import OptimizationResult
from nonbonded.library.templates.forcebalance import ForceBalanceInput
from nonbonded.library.templates.submission import Submission, SubmissionTemplate
from nonbonded.library.utilities import temporary_cd

if TYPE_CHECKING:

    from openff.evaluator.client import RequestOptions
    from openff.evaluator.datasets import PhysicalPropertyDataSet


class OptimizationFactory:
    """An factory used to create the directory structure and
    inputs for a particular optimization.
    """

    @classmethod
    def generate_directory_structure(cls, optimization: Optimization):
        """Generates the directory for an optimization."""
        os.makedirs(optimization.id, exist_ok=True)

    @classmethod
    def retrieve_results(
        cls, optimization: Optimization,
    ):
        """Retrieves the full results for a optimization.

        Parameters
        ----------
        optimization
            The optimization to retrieve the results for.
        """

        results = OptimizationResult.from_rest(
            project_id=optimization.project_id,
            study_id=optimization.study_id,
            model_id=optimization.id,
        )

        cls.generate_directory_structure(optimization)

        with temporary_cd(optimization.id):

            output_directory = "analysis"
            os.makedirs(output_directory, exist_ok=True)

            with open(
                os.path.join(output_directory, "optimization-results.json"), "w"
            ) as file:
                file.write(results.json())

    @classmethod
    def _generate_evaluator_options(
        cls, optimization: Optimization, training_set: "PhysicalPropertyDataSet"
    ) -> "RequestOptions":
        """Generates the evaluator request options to use when estimating
        the training set.

        Parameters
        ----------
        optimization
            The optimization which will trigger the estimation requests.
        training_set
            The training set which will be estimated.

        Returns
        -------
            The request options.
        """

        import inspect

        from openff.evaluator.client import RequestOptions
        from openff.evaluator.layers import registered_calculation_schemas

        request_options = RequestOptions()
        force_balance_input = optimization.force_balance_input

        # Specify the calculation layers to use.
        request_options.calculation_layers = []

        if force_balance_input.allow_reweighting:
            request_options.calculation_layers.append("ReweightingLayer")
        if force_balance_input.allow_direct_simulation:
            request_options.calculation_layers.append("SimulationLayer")

        # Check if a non-default option has been specified.
        if (
            force_balance_input.n_molecules is None
            and force_balance_input.n_effective_samples is None
        ):
            return request_options

        # Generate estimation schemas for each of the properties if a non-default
        # option has been specified in the optimization options.
        property_types = training_set.property_types

        request_options.calculation_schemas = defaultdict(dict)

        for property_type in property_types:

            default_reweighting_schemas = registered_calculation_schemas.get(
                "ReweightingLayer", {}
            )

            if (
                force_balance_input.allow_reweighting
                and force_balance_input.n_effective_samples is not None
                and property_type in default_reweighting_schemas
                and callable(default_reweighting_schemas[property_type])
            ):

                default_schema = default_reweighting_schemas[property_type]

                if "n_effective_samples" in inspect.getfullargspec(default_schema).args:

                    default_schema = default_schema(
                        n_effective_samples=force_balance_input.n_effective_samples
                    )
                    request_options.calculation_schemas[property_type][
                        "ReweightingLayer"
                    ] = default_schema

            default_simulation_schemas = registered_calculation_schemas.get(
                "SimulationLayer", {}
            )

            if (
                force_balance_input.allow_direct_simulation
                and force_balance_input.n_molecules is not None
                and property_type in default_simulation_schemas
                and callable(default_simulation_schemas[property_type])
            ):

                default_schema = default_simulation_schemas[property_type]

                if "n_molecules" in inspect.getfullargspec(default_schema).args:

                    default_schema = default_schema(
                        n_molecules=force_balance_input.n_molecules
                    )
                    request_options.calculation_schemas[property_type][
                        "SimulationLayer"
                    ] = default_schema

        return request_options

    @classmethod
    def generate_inputs(
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

        cls.generate_directory_structure(optimization)

        with temporary_cd(optimization.id):

            # Save the optimization definition in the directory
            optimization_path = "optimization.json"

            with open(optimization_path, "w") as file:
                file.write(optimization.json())

            # Create the force field directory
            force_field_directory = "forcefield"
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

                    parameter_handler = off_force_field.get_parameter_handler(
                        handler_type
                    )

                    parameter = parameter_handler.parameters[smirks]
                    parameter.add_cosmetic_attribute("parameterize", attributes_string)

            force_field_path = os.path.join(force_field_directory, "force-field.offxml")
            off_force_field.to_file(
                force_field_path, io_format="offxml", discard_cosmetic_attributes=False
            )

            # Create the options.in file.
            optimize_in_path = "optimize.in"

            optimize_in_contents = ForceBalanceInput.generate(
                "force-field.offxml",
                optimization.force_balance_input.max_iterations,
                optimization.force_balance_input.convergence_step_criteria,
                optimization.force_balance_input.convergence_objective_criteria,
                optimization.force_balance_input.convergence_gradient_criteria,
                optimization.force_balance_input.n_criteria,
                optimization.force_balance_input.initial_trust_radius,
                optimization.force_balance_input.minimum_trust_radius,
                optimization.force_balance_input.evaluator_target_name,
                optimization.priors,
            )

            with open(optimize_in_path, "w") as file:
                file.write(optimize_in_contents)

            # Create the targets directory
            targets_directory = os.path.join(
                "targets", optimization.force_balance_input.evaluator_target_name
            )
            os.makedirs(targets_directory, exist_ok=True)

            # Store the data set in the targets directory
            training_sets: List[DataSet] = [
                DataSet.from_rest(data_set_id=x) for x in optimization.training_set_ids
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

            target_options.estimation_options = cls._generate_evaluator_options(
                optimization, evaluator_set
            )

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

            server_config = EvaluatorServerConfig(
                backend_config=backend_config, port=port
            )

            with open("server-config.json", "w") as file:
                file.write(server_config.json())

            # Create a job submission file
            submission_path = "submit.sh"

            submission = Submission(
                job_name="optim",
                wall_clock_limit=max_wall_clock,
                max_memory=max_memory,
                gpu=backend_name == "lilac-local",
                environment_name=environment_name,
                commands=[
                    (
                        "nonbonded optimization run --config server-config.json "
                        "--restart true"
                    ),
                    "nonbonded optimization analyze",
                ],
            )

            submission_content = SubmissionTemplate.generate(
                "submit_lilac.txt", submission
            )

            with open(submission_path, "w") as file:
                file.write(submission_content)
