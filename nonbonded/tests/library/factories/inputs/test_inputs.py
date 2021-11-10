import os

import pytest
from requests_mock import NoMockAddress

from nonbonded.library.factories.inputs import InputFactory
from nonbonded.library.factories.inputs.benchmark import BenchmarkInputFactory
from nonbonded.library.factories.inputs.evaluator import (
    DaskHPCClusterConfig,
    DaskLocalClusterConfig,
)
from nonbonded.library.factories.inputs.optimization import OptimizationInputFactory
from nonbonded.library.models.datasets import DataSet, QCDataSet
from nonbonded.library.utilities import temporary_cd
from nonbonded.tests.utilities.comparison import does_not_raise
from nonbonded.tests.utilities.factory import (
    create_benchmark,
    create_data_set,
    create_evaluator_target,
    create_force_field,
    create_optimization,
    create_optimization_result,
    create_project,
    create_qc_data_set,
    create_study,
)
from nonbonded.tests.utilities.mock import (
    mock_get_data_set,
    mock_get_project,
    mock_get_qc_data_set,
    mock_get_study,
)


@pytest.mark.usefixtures("change_api_url")
@pytest.mark.parametrize(
    "data_set_ids, data_set_type, expected_data_set_ids, expected_raises",
    [
        (["data-set-2"], DataSet, [2], does_not_raise()),
        (["data-set-3"], DataSet, [4], does_not_raise()),
        (["data-set-2", "data-set-3"], DataSet, [2, 4], does_not_raise()),
        (
            ["data-set-4"],
            DataSet,
            [],
            pytest.raises(NoMockAddress, match="phys-prop/data-set-4"),
        ),
        (["data-set-1"], QCDataSet, [], does_not_raise()),
        (["data-set-2"], QCDataSet, [], does_not_raise()),
        (["data-set-1", "data-set-2"], QCDataSet, [], does_not_raise()),
        (
            ["data-set-4"],
            QCDataSet,
            [],
            pytest.raises(NoMockAddress, match="qc/data-set-4"),
        ),
    ],
)
def test_find_or_retrieve_data_sets(
    requests_mock, data_set_ids, data_set_type, expected_data_set_ids, expected_raises
):

    local_data_sets = [
        create_data_set("data-set-1", 1),
        create_qc_data_set("data-set-1"),
        create_data_set("data-set-2", 2),
    ]

    remote_data_sets = [
        create_qc_data_set("data-set-2"),
        create_data_set("data-set-2", 3),
        create_data_set("data-set-3", 4),
    ]

    for remote_data_set in remote_data_sets:

        if isinstance(remote_data_set, DataSet):
            mock_get_data_set(requests_mock, remote_data_set)
        else:
            mock_get_qc_data_set(requests_mock, remote_data_set)

    with expected_raises:

        found_data_sets = InputFactory._find_or_retrieve_data_sets(
            data_set_ids, data_set_type, local_data_sets
        )

        assert sorted(data_set_ids) == sorted(
            data_set.id for data_set in found_data_sets
        )
        assert all(isinstance(data_set, data_set_type) for data_set in found_data_sets)

        found_entry_ids = [
            entry.id
            for data_set in found_data_sets
            if isinstance(data_set, DataSet)
            for entry in data_set.entries
        ]
        assert found_entry_ids == expected_data_set_ids


@pytest.mark.parametrize(
    "present, expected_class",
    [("lilac-local", DaskLocalClusterConfig), ("lilac-dask", DaskHPCClusterConfig)],
)
def test_generate_evaluator_config(present, expected_class):

    config = InputFactory._generate_evaluator_config(present, "env", 1, 8000)
    assert isinstance(config.backend_config, expected_class)


@pytest.mark.parametrize(
    "model, optimization_result, expected_raises",
    [
        (
            create_optimization(
                "mock-project-1",
                "mock-study-1",
                "mock-optimization-2",
                targets=[create_evaluator_target("phys-prop-1", ["data-set-1"])],
                optimization_result_id="mock-optimization-1",
            ),
            create_optimization_result(
                "mock-project-1",
                "mock-study-1",
                "mock-optimization-1",
                ["phys-prop-1"],
                [],
            ),
            does_not_raise(),
        ),
        (
            create_optimization(
                "mock-project-1",
                "mock-study-1",
                "mock-optimization-2",
                targets=[create_evaluator_target("phys-prop-1", ["data-set-1"])],
                optimization_result_id=None,
            ),
            None,
            does_not_raise(),
        ),
        (
            create_optimization(
                "mock-project-1",
                "mock-study-1",
                "mock-optimization-2",
                targets=[create_evaluator_target("phys-prop-1", ["data-set-1"])],
                optimization_result_id="mock-optimization-1",
            ),
            None,
            does_not_raise(),
        ),
        (
            create_optimization(
                "mock-project-1",
                "mock-study-1",
                "mock-optimization-2",
                targets=[create_evaluator_target("phys-prop-1", ["data-set-1"])],
                optimization_result_id="mock-optimization-1",
            ),
            create_optimization_result(
                "mock-project-2",
                "mock-study-1",
                "mock-optimization-1",
                ["phys-prop-1"],
                [],
            ),
            pytest.raises(
                AssertionError,
                match="the provided optimization result does not match the one",
            ),
        ),
    ],
)
def test_generate_validate_result(model, optimization_result, expected_raises):

    with temporary_cd():

        with expected_raises:

            InputFactory._generate(
                model,
                "mock-env",
                "01:00",
                "lilac-dask",
                8000,
                1,
                False,
                None,
                optimization_result,
            )


@pytest.mark.parametrize(
    "reference_data_sets, expected_raises",
    [
        (
            [create_data_set("data-set-1"), create_qc_data_set("data-set-1")],
            does_not_raise(),
        ),
        (
            [
                create_data_set("data-set-1"),
                create_data_set("data-set-1"),
                create_qc_data_set("data-set-1"),
            ],
            pytest.raises(AssertionError, match="multiple reference data sets of"),
        ),
        (
            [
                create_data_set("data-set-1"),
                create_qc_data_set("data-set-1"),
                create_qc_data_set("data-set-1"),
            ],
            pytest.raises(AssertionError, match="multiple reference data sets of"),
        ),
    ],
)
def test_generate_validate_data_sets(reference_data_sets, expected_raises):

    model = create_optimization(
        "mock-project-1",
        "mock-study-1",
        "mock-optimization-1",
        targets=[create_evaluator_target("phys-prop-1", ["data-set-1"])],
    )

    with temporary_cd():

        with expected_raises:

            InputFactory._generate(
                model,
                "mock-env",
                "01:00",
                "lilac-dask",
                8000,
                1,
                False,
                reference_data_sets,
                None,
            )


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
