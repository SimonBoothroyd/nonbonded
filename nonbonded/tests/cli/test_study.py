import pytest

from nonbonded.cli.study import study as study_cli
from nonbonded.tests.backend.crud.utilities.create import (
    create_benchmark,
    create_data_set,
    create_empty_study,
)
from nonbonded.tests.cli.utilities import mock_get_data_set, mock_get_study


@pytest.mark.usefixtures("change_api_url")
class TestStudyCLI:
    def test_retrieve(self, requests_mock, runner):

        study = create_empty_study("project-1", "study-1")
        mock_get_study(requests_mock, study)

        arguments = [
            "retrieve",
            "--project-id",
            study.project_id,
            "--study-id",
            study.id,
        ]

        result = runner.invoke(study_cli, arguments)

        if result.exit_code != 0:
            raise result.exception

        assert result.output.replace("\n", "") == study.json()

    def test_generate(self, requests_mock, runner):

        study = create_empty_study("project-1", "study-1")
        study.benchmarks = [
            create_benchmark(
                "project-1",
                "study-1",
                "benchmark-1",
                ["data-set-1"],
                None,
                "openff-1.0.0.offxml",
            )
        ]

        mock_get_study(requests_mock, study)
        mock_get_data_set(requests_mock, create_data_set("data-set-1"))

        arguments = [
            "generate",
            "--project-id",
            study.project_id,
            "--study-id",
            study.id,
            "--max-workers",
            1,
        ]

        result = runner.invoke(study_cli, arguments)

        if result.exit_code != 0:
            raise result.exception
