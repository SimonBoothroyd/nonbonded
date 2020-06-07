import sys

import pytest

from nonbonded.cli.optimization import optimization as optimization_cli
from nonbonded.library.models.forcefield import ForceField
from nonbonded.tests.backend.crud.utilities.create import (
    create_data_set,
    create_optimization,
    create_optimization_result,
)
from nonbonded.tests.cli.utilities import (
    mock_get_data_set,
    mock_get_optimization,
    mock_get_optimization_result,
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

    @pytest.mark.skipif(
        sys.platform.startswith("linux") and sys.version_info < (3, 7),
        reason="ForceBalance v1.7.2 is currently not built correctly on "
        "linux for python 3.6.",
    )
    def test_generate(self, requests_mock, runner):

        from openforcefield.typing.engines.smirnoff.forcefield import (
            ForceField as SMIRNOFFForceField,
        )

        optimization = create_optimization(
            "project-1", "study-1", "optimization-1", ["data-set-1"],
        )
        optimization.initial_force_field = ForceField.from_openff(
            SMIRNOFFForceField("openff-1.0.0.offxml")
        )

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
