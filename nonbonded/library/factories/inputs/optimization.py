import json
import os
from collections import defaultdict
from typing import TYPE_CHECKING, List, Union

from nonbonded.library.factories.inputs import InputFactory
from nonbonded.library.models.datasets import DataSet, DataSetCollection, QCDataSet
from nonbonded.library.models.projects import Optimization
from nonbonded.library.models.results import OptimizationResult, logger
from nonbonded.library.models.targets import EvaluatorTarget, RechargeTarget
from nonbonded.library.templates.forcebalance import ForceBalanceInput
from nonbonded.library.utilities import temporary_cd

if TYPE_CHECKING:

    from openff.evaluator.client import RequestOptions
    from openff.evaluator.datasets import PhysicalPropertyDataSet


class OptimizationInputFactory(InputFactory):
    """A factory used to create the directory structure and
    inputs for a particular optimization.
    """

    @classmethod
    def _prepare_force_field(cls, optimization: Optimization):
        """Adds the required ForceBalance cosmetic attributes and stores the force field
        to refit it in the correct ``forcefield`` directory.
        """

        force_field_directory = "forcefield"
        os.makedirs(force_field_directory, exist_ok=True)

        off_force_field = optimization.force_field.to_openff()

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

                if handler_type == "ChargeIncrementModel":

                    parameter.add_cosmetic_attribute(
                        "parameter_eval",
                        "charge_increment2="
                        "-PRM['ChargeIncrementModel/ChargeIncrement/charge_increment1/"
                        f"{parameter.smirks}']",
                    )

        force_field_path = os.path.join(force_field_directory, "force-field.offxml")
        off_force_field.to_file(
            force_field_path, io_format="offxml", discard_cosmetic_attributes=False
        )

    @classmethod
    def _generate_force_balance_input(cls, optimization: Optimization):
        """Creates the required ``options.in`` file."""

        with open("optimize.in", "w") as file:

            file.write(
                ForceBalanceInput.generate(
                    "force-field.offxml",
                    optimization.max_iterations,
                    optimization.engine.convergence_step_criteria,
                    optimization.engine.convergence_objective_criteria,
                    optimization.engine.convergence_gradient_criteria,
                    optimization.engine.n_criteria,
                    optimization.engine.initial_trust_radius,
                    optimization.engine.minimum_trust_radius,
                    optimization.targets,
                    optimization.engine.priors,
                )
            )

    @classmethod
    def _generate_request_options(
        cls, target: EvaluatorTarget, training_set: "PhysicalPropertyDataSet"
    ) -> "RequestOptions":
        """Generates the request options to use when estimating an evaluator
        optimization targets.

        Parameters
        ----------
        target
            The evaluator target which will spawn the request.
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

        # Specify the calculation layers to use.
        request_options.calculation_layers = []

        if target.allow_reweighting:
            request_options.calculation_layers.append("ReweightingLayer")
        if target.allow_direct_simulation:
            request_options.calculation_layers.append("SimulationLayer")

        # Check if a non-default option has been specified.
        if target.n_molecules is None and target.n_effective_samples is None:
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
                target.allow_reweighting
                and target.n_effective_samples is not None
                and property_type in default_reweighting_schemas
                and callable(default_reweighting_schemas[property_type])
            ):

                default_schema = default_reweighting_schemas[property_type]

                if "n_effective_samples" in inspect.getfullargspec(default_schema).args:

                    default_schema = default_schema(
                        n_effective_samples=target.n_effective_samples
                    )
                    request_options.calculation_schemas[property_type][
                        "ReweightingLayer"
                    ] = default_schema

            default_simulation_schemas = registered_calculation_schemas.get(
                "SimulationLayer", {}
            )

            if (
                target.allow_direct_simulation
                and target.n_molecules is not None
                and property_type in default_simulation_schemas
                and callable(default_simulation_schemas[property_type])
            ):

                default_schema = default_simulation_schemas[property_type]

                if "n_molecules" in inspect.getfullargspec(default_schema).args:

                    default_schema = default_schema(n_molecules=target.n_molecules)
                    request_options.calculation_schemas[property_type][
                        "SimulationLayer"
                    ] = default_schema

        return request_options

    @classmethod
    def _generate_evaluator_target(cls, target: EvaluatorTarget, port: int):
        """Generates the input files for an evaluator target."""

        from forcebalance.evaluator_io import Evaluator_SMIRNOFF
        from openff.evaluator import unit

        # Store the data set in the targets directory
        training_sets: List[DataSet] = [
            DataSet.from_rest(data_set_id=x) for x in target.data_set_ids
        ]
        training_set_collection = DataSetCollection(data_sets=training_sets)

        evaluator_set = training_set_collection.to_evaluator()
        evaluator_set.json("training-set.json")

        # Create the target options
        target_options = Evaluator_SMIRNOFF.OptionsFile()
        target_options.connection_options.server_port = port

        target_options.estimation_options = cls._generate_request_options(
            target, evaluator_set
        )

        target_options.data_set_path = "training-set.json"

        target_options.weights = {
            property_type: 1.0 for property_type in evaluator_set.property_types
        }
        target_options.denominators = {
            property_type: unit.Quantity(value)
            for property_type, value in target.denominators.items()
        }
        target_options.polling_interval = 600

        with open("options.json", "w") as file:
            file.write(target_options.to_json())

    @classmethod
    def _generate_recharge_target(cls, target: RechargeTarget):
        """Generates the input files for an evaluator target."""

        training_sets: List[QCDataSet] = [
            QCDataSet.from_rest(qc_data_set_id=x) for x in target.qc_data_set_ids
        ]

        # Save the list of QCA compute record ids. The user will need to
        # reconstruct the full ESP and EF from these ids + the ESP settings
        # using the openff-recharge CLI.
        target_records = [
            *{
                record_id
                for training_set in training_sets
                for record_id in training_set.entries
            }
        ]

        with open("training-set.json", "w") as file:
            json.dump(target_records, file)

        # Save the ESP and conformer generation settings
        with open("grid-settings.json", "w") as file:
            file.write(target.grid_settings.json())

    @classmethod
    def _generate_target(
        cls,
        target: Union[EvaluatorTarget, RechargeTarget],
        evaluator_port: int,
    ):
        """Generates a directory for a particular optimization target
        and populates it with the required target inputs."""

        target_directory = os.path.join("targets", target.id)
        os.makedirs(target_directory, exist_ok=True)

        with temporary_cd(target_directory):

            if isinstance(target, EvaluatorTarget):
                cls._generate_evaluator_target(target, evaluator_port)
            elif isinstance(target, RechargeTarget):
                cls._generate_recharge_target(target)
            else:
                raise NotImplementedError()

    @classmethod
    def _retrieve_results(cls, optimization: Optimization):
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

        output_directory = "analysis"
        os.makedirs(output_directory, exist_ok=True)

        with open(
            os.path.join(output_directory, "optimization-results.json"), "w"
        ) as file:
            file.write(results.json())

    @classmethod
    def _generate(
        cls,
        model,
        conda_environment,
        max_time,
        evaluator_preset,
        evaluator_port,
        n_evaluator_workers,
        include_results,
    ):

        super(OptimizationInputFactory, cls)._generate(
            model=model,
            conda_environment=conda_environment,
            max_time=max_time,
            evaluator_preset=evaluator_preset,
            evaluator_port=evaluator_port,
            n_evaluator_workers=n_evaluator_workers,
            include_results=include_results,
        )

        # Save the optimization definition in the directory
        optimization_path = "optimization.json"

        with open(optimization_path, "w") as file:
            file.write(model.json())

        # Retrieve the force field.
        cls._prepare_force_field(model)

        # Create the options.in file.
        cls._generate_force_balance_input(model)

        # Create targets directory
        for target in model.targets:
            cls._generate_target(target, evaluator_port)

        # Give a warning that currently the user will need to reconstruct the
        # ESP and EF data used by any recharge targets manually.
        recharge_targets = [
            target for target in model.targets if isinstance(target, RechargeTarget)
        ]

        if len(recharge_targets) > 0:

            directories = "\n".join(
                [
                    f'    {os.path.join("targets", target.id, "training-set.json")}'
                    for target in recharge_targets
                ]
            )

            logger.info(
                f"The inputs to openff-recharge targets must currently be setup "
                f"manually. Reconstructing the ESP and electric field from a set of "
                f"QCArchive results can take some time, and is better handled "
                f"separately by the user."
                f"\n\n"
                f"The setup be performed by running the"
                f"\n\n"
                f"    recharge reconstruct --record-ids training-set.json "
                f"--grid-settings grid-settings.json"
                f"\n\n"
                f"command in the"
                f"\n\n"
                f"{directories}"
                f"\n\n"
                f"directories."
            )

        # Generate an Evaluator server configuration if needed.
        if any(isinstance(target, EvaluatorTarget) for target in model.targets):

            evaluator_configuration = cls._generate_evaluator_config(
                preset_name=evaluator_preset,
                conda_environment=conda_environment,
                n_workers=n_evaluator_workers,
                port=evaluator_port,
            )

            with open("server-config.json", "w") as file:
                file.write(evaluator_configuration.json())

        # Create a job submission file
        cls._generate_submission_script(
            "optim",
            conda_environment,
            evaluator_preset,
            max_time,
            [
                "nonbonded optimization run --restart true",
                "nonbonded optimization analyze",
            ],
        )

        # Optionally retrieve any previously generated results.
        if include_results:
            cls._retrieve_results(model)
