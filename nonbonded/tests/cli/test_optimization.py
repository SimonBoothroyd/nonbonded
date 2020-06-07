import sys

import pytest

from nonbonded.cli.optimization import optimization as optimization_cli
from nonbonded.library.models.datasets import DataSet
from nonbonded.library.models.forcefield import ForceField
from nonbonded.library.models.projects import Optimization
from nonbonded.tests.backend.crud.utilities.create import (
    create_data_set,
    create_optimization,
)


@pytest.mark.usefixtures("change_api_url")
class TestOptimizationCLI:
    @classmethod
    def _mock_get_optimization(cls, requests_mock, optimization: Optimization):
        requests_mock.get(
            Optimization._get_endpoint(
                project_id=optimization.project_id,
                study_id=optimization.study_id,
                optimization_id=optimization.id,
            ),
            text=optimization.json(),
        )

    @classmethod
    def _mock_get_data_set(cls, requests_mock, data_set: DataSet):
        requests_mock.get(
            DataSet._get_endpoint(data_set_id=data_set.id), text=data_set.json(),
        )

    @pytest.mark.parametrize("output_to_file", [True, False])
    def test_retrieve(self, output_to_file, requests_mock, runner):

        optimization = create_optimization(
            "project-1", "study-1", "optimization-1", ["data-set-1"]
        )
        self._mock_get_optimization(requests_mock, optimization)

        arguments = [
            "retrieve",
            "--project-id",
            optimization.project_id,
            "--study-id",
            optimization.study_id,
            "--optimization-id",
            optimization.id,
        ]

        if output_to_file:
            arguments.extend(["--output", "optimization.json"])

        result = runner.invoke(optimization_cli, arguments)

        if result.exit_code != 0:
            raise result.exception

        if output_to_file:
            with open("optimization.json") as file:
                assert file.read().replace("\n", "") == optimization.json()
        else:
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

        self._mock_get_optimization(requests_mock, optimization)
        self._mock_get_data_set(requests_mock, create_data_set("data-set-1"))

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
