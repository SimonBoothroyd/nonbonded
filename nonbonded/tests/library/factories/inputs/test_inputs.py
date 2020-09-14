import os

import pytest

from nonbonded.library.factories.inputs import InputFactory
from nonbonded.library.factories.inputs.benchmark import BenchmarkInputFactory
from nonbonded.library.factories.inputs.evaluator import (
    DaskHPCClusterConfig,
    DaskLocalClusterConfig,
)
from nonbonded.library.factories.inputs.optimization import OptimizationInputFactory
from nonbonded.library.utilities import temporary_cd
from nonbonded.tests.utilities.factory import (
    create_benchmark,
    create_data_set,
    create_evaluator_target,
    create_force_field,
    create_optimization,
    create_project,
    create_study,
)
from nonbonded.tests.utilities.mock import (
    mock_get_data_set,
    mock_get_project,
    mock_get_study,
)


@pytest.mark.parametrize(
    "present, expected_class",
    [("lilac-local", DaskLocalClusterConfig), ("lilac-dask", DaskHPCClusterConfig)],
)
def test_generate_evaluator_config(present, expected_class):

    config = InputFactory._generate_evaluator_config(present, "env", 1, 8000)
    assert isinstance(config.backend_config, expected_class)


def test_project_no_children(requests_mock):

    project = create_project(project_id="project-1")
    mock_get_project(requests_mock, project)

    with temporary_cd():

        InputFactory.generate(
            project, "test-env", "12:34", "lilac-dask", 8000, 1, False
        )


def test_project_with_children(requests_mock):

    project = create_project(project_id="project-1")
    project.studies = [create_study(project.id, "study-1")]

    mock_get_project(requests_mock, project)
    mock_get_study(requests_mock, project.studies[0])

    with temporary_cd():

        InputFactory.generate(
            project, "test-env", "12:34", "lilac-dask", 8000, 1, False
        )

        assert os.path.isdir(project.id)
        assert os.path.isdir(os.path.join(project.id, "studies"))


def test_study_no_children(requests_mock):

    study = create_study("project-1", "study-1")
    mock_get_study(requests_mock, study)

    with temporary_cd():

        InputFactory.generate(study, "test-env", "12:34", "lilac-dask", 8000, 1, False)


def test_study_with_children(requests_mock, monkeypatch):

    # Overwrite the child factories so we don't need to provide
    # sensible children and wait for them to be buit.
    def mock_generate(model, **_):
        os.makedirs(model.id, exist_ok=True)

    monkeypatch.setattr(OptimizationInputFactory, "generate", mock_generate)
    monkeypatch.setattr(BenchmarkInputFactory, "generate", mock_generate)

    mock_get_data_set(requests_mock, create_data_set("data-set-1"))

    optimization = create_optimization(
        "project-1",
        "study-1",
        "optimization-1",
        targets=[create_evaluator_target("evaluator-target", ["data-set-1"])],
    )
    benchmark = create_benchmark(
        "project-1",
        "study-1",
        "benchmark-1",
        ["data-set-1"],
        None,
        create_force_field(),
    )

    study = create_study("project-1", "study-1")
    study.optimizations = [optimization]
    study.benchmarks = [benchmark]

    mock_get_study(requests_mock, study)

    with temporary_cd():

        InputFactory.generate(study, "test-env", "12:34", "lilac-dask", 8000, 1, False)

        assert os.path.isdir(study.id)
        assert os.path.isdir(os.path.join(study.id, "optimizations"))
        assert os.path.isdir(os.path.join(study.id, "benchmarks"))

        assert os.path.isdir(os.path.join(study.id, "optimizations", optimization.id))
        assert os.path.isdir(os.path.join(study.id, "benchmarks", benchmark.id))
