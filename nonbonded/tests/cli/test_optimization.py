import os

import pytest

from nonbonded.cli.optimization import optimization as optimization_cli
from nonbonded.library.models.forcefield import ForceField
from nonbonded.tests.backend.crud.utilities.create import (
    create_data_set,
    create_empty_study,
    create_optimization,
    create_optimization_result,
)
from nonbonded.tests.cli.utilities import (
    mock_get_data_set,
    mock_get_optimization,
    mock_get_optimization_result,
    mock_get_study,
)


@pytest.mark.usefixtures("change_api_url")
class TestOptimizationCLI:
    def test_retrieve(self, requests_mock, runner):

        optimization = create_optimization(
            "project-1", "study-1", "optimization-1", ["data-set-1"]
        )
        mock_get_optimization(requests_mock, optimization)

        arguments = [
            "retrieve",
            "--project-id",
            optimization.project_id,
            "--study-id",
            optimization.study_id,
            "--optimization-id",
            optimization.id,
        ]

        result = runner.invoke(optimization_cli, arguments)

        if result.exit_code != 0:
            raise result.exception

        assert result.output.replace("\n", "") == optimization.json()

    def test_generate(self, requests_mock, runner):

        from forcebalance.evaluator_io import Evaluator_SMIRNOFF
        from openforcefield.typing.engines.smirnoff.forcefield import (
            ForceField as SMIRNOFFForceField,
        )

        optimization = create_optimization(
            "project-1", "study-1", "optimization-1", ["data-set-1"],
        )
        optimization.initial_force_field = ForceField.from_openff(
            SMIRNOFFForceField("openff-1.0.0.offxml")
        )

        optimization.force_balance_input.allow_direct_simulation = True
        optimization.force_balance_input.n_molecules = 512

        optimization.force_balance_input.allow_reweighting = True
        optimization.force_balance_input.n_effective_samples = 25

        mock_get_optimization(requests_mock, optimization)
        mock_get_data_set(requests_mock, create_data_set("data-set-1"))

        arguments = [
            "generate",
            "--project-id",
            optimization.project_id,
            "--study-id",
            optimization.study_id,
            "--optimization-id",
            optimization.id,
            "--max-workers",
            1,
        ]

        result = runner.invoke(optimization_cli, arguments)

        if result.exit_code != 0:
            raise result.exception

        with open(
            os.path.join(
                optimization.id,
                "targets",
                optimization.force_balance_input.evaluator_target_name,
                "options.json",
            ),
        ) as file:

            target_options = Evaluator_SMIRNOFF.OptionsFile.from_json(file)

        assert target_options.estimation_options.calculation_layers == [
            "ReweightingLayer",
            "SimulationLayer",
        ]

        assert "Density" in target_options.estimation_options.calculation_schemas
        density_schemas = target_options.estimation_options.calculation_schemas[
            "Density"
        ]

        assert "ReweightingLayer" in density_schemas
        assert density_schemas["ReweightingLayer"] is not None

        assert "SimulationLayer" in density_schemas
        assert density_schemas["SimulationLayer"] is not None

    def test_results(self, requests_mock, runner):

        optimization = create_optimization(
            "project-1", "study-1", "optimization-1", ["data-set-1"]
        )
        data_set = create_data_set("data-set-1")
        optimization_result = create_optimization_result(
            "project-1", "study-1", "optimization-1",
        )

        mock_get_data_set(requests_mock, data_set)
        mock_get_optimization(requests_mock, optimization)
        mock_get_optimization_result(requests_mock, optimization_result)

        arguments = [
            "results",
            "--project-id",
            optimization.project_id,
            "--study-id",
            optimization.study_id,
            "--optimization-id",
            optimization.id,
        ]

        result = runner.invoke(optimization_cli, arguments)

        if result.exit_code != 0:
            raise result.exception

    def test_list(self, requests_mock, runner):

        study = create_empty_study("project-1", "study-1")
        study.optimizations = [
            create_optimization("project-1", "study-1", "optimization-1", ["a"])
        ]
        mock_get_study(requests_mock, study)

        result = runner.invoke(
            optimization_cli,
            ["list", "--project-id", "project-1", "--study-id", "study-1"],
        )

        if result.exit_code != 0:
            raise result.exception

        assert study.optimizations[0].id in result.output
