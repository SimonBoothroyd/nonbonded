import logging
from typing import Optional

import pytest
from openff.evaluator.client import (
    EvaluatorClient,
    Request,
    RequestOptions,
    RequestResult,
)
from openff.evaluator.forcefield import ForceFieldSource, TLeapForceFieldSource
from openff.evaluator.utils.exceptions import EvaluatorException
from openff.toolkit.typing.engines.smirnoff import ForceField

from nonbonded.cli.projects.benchmark.run import (
    _load_force_field,
    _prepare_restart,
    _run_calculations,
    run_command,
)
from nonbonded.library.factories.inputs.evaluator import (
    ComputeResources,
    DaskLocalClusterConfig,
    EvaluatorServerConfig,
)
from nonbonded.library.models.datasets import DataSetCollection
from nonbonded.library.utilities import temporary_cd
from nonbonded.tests.utilities.comparison import does_not_raise
from nonbonded.tests.utilities.factory import create_data_set


def successful_result():
    result = RequestResult()
    result.estimated_properties = create_data_set("data-set-1", 1).to_evaluator()
    return result


def unsuccessful_result():

    result = RequestResult()
    result.unsuccessful_properties = create_data_set("data-set-1", 1).to_evaluator()
    return result


@pytest.mark.parametrize(
    "original_existing_results, restart, expected_message",
    [
        (None, False, None),
        (None, True, None),
        (successful_result(), False, "These results will be overwritten"),
        (successful_result(), True, "All properties were successfully estimated"),
        (unsuccessful_result(), False, "These results will be overwritten"),
        (
            unsuccessful_result(),
            True,
            "Attempting to re-estimate these unsuccessful data points",
        ),
    ],
)
def test_prepare_restart(
    original_existing_results: Optional[RequestResult],
    restart: bool,
    expected_message: Optional[str],
    caplog,
):

    with temporary_cd():

        # Create a mock data set
        original_data_set = DataSetCollection(
            data_sets=[create_data_set("data-set-1", 1)]
        )
        original_data_set.to_file("test-set-collection.json")

        if original_existing_results is not None:
            original_existing_results.json("results.json")

        with caplog.at_level(logging.INFO):
            data_set, existing_result = _prepare_restart(restart)

    if original_existing_results is not None and restart:
        assert existing_result.json() == original_existing_results.json()
    else:
        assert existing_result is None

    if expected_message is not None:
        assert expected_message in caplog.text
    else:
        assert caplog.text == ""

    expected_n_data_points = (
        1 if existing_result is None else len(existing_result.unsuccessful_properties)
    )

    assert len(data_set) == expected_n_data_points


@pytest.mark.parametrize(
    "force_fields, expected_raises, expected_error_message",
    [
        (
            [("force-field.offxml", ForceField("openff-1.0.0.offxml"))],
            does_not_raise(),
            None,
        ),
        ([("force-field.json", TLeapForceFieldSource())], does_not_raise(), None),
        (
            [
                ("force-field.offxml", ForceField("openff-1.0.0.offxml")),
                ("force-field.json", TLeapForceFieldSource()),
            ],
            pytest.raises(RuntimeError),
            "Two valid force fields were found",
        ),
        ([], pytest.raises(RuntimeError), "No valid force field could be found."),
    ],
)
def test_load_force_field(force_fields, expected_raises, expected_error_message):

    with temporary_cd():

        # Create any required force field files.
        for force_field_path, force_field in force_fields:

            if isinstance(force_field, ForceField):
                force_field.to_file(force_field_path)
            elif isinstance(force_field, ForceFieldSource):
                force_field.json(force_field_path)

        # Make sure the right error (if any is raised) on loading
        with expected_raises as error_info:
            _load_force_field()

        if expected_error_message is not None:
            assert expected_error_message in str(error_info.value)


@pytest.mark.parametrize(
    "request_error, results_error, expected_raises",
    [
        (None, None, does_not_raise()),
        (EvaluatorException("Request"), None, pytest.raises(EvaluatorException)),
        (None, EvaluatorException("Result"), pytest.raises(EvaluatorException)),
    ],
)
def test_run_calculations(request_error, results_error, expected_raises, monkeypatch):

    monkeypatch.setattr(
        EvaluatorServerConfig, "to_backend", lambda *_: does_not_raise()
    )
    monkeypatch.setattr(EvaluatorServerConfig, "to_server", lambda *_: does_not_raise())

    empty_request = Request()
    empty_result = RequestResult()

    monkeypatch.setattr(
        EvaluatorClient,
        "request_estimate",
        lambda *args, **kwargs: (empty_request, request_error),
    )
    monkeypatch.setattr(
        Request, "results", lambda *args, **kwargs: (empty_result, results_error)
    )

    server_config = EvaluatorServerConfig(
        backend_config=DaskLocalClusterConfig(resources_per_worker=ComputeResources())
    )

    with expected_raises as error_info:
        # noinspection PyTypeChecker
        _run_calculations(None, None, 1, None, server_config)

    error_value = None if error_info is None else error_info.value

    assert error_value == (
        request_error
        if request_error is not None
        else results_error
        if results_error is not None
        else None
    )


def test_run_command(runner, monkeypatch):

    from nonbonded.cli.projects.benchmark import run

    monkeypatch.setattr(
        run, "_prepare_restart", lambda *args: (None, successful_result())
    )
    monkeypatch.setattr(run, "_load_force_field", lambda *args: None)
    monkeypatch.setattr(run, "_run_calculations", lambda *args: RequestResult())

    # Save a copy of the result model.
    with temporary_cd():

        # Create mock inputs
        with open("server-config.json", "w") as file:

            file.write(
                EvaluatorServerConfig(
                    backend_config=DaskLocalClusterConfig(
                        resources_per_worker=ComputeResources()
                    )
                ).json()
            )

        RequestOptions().json("estimation-options.json")

        result = runner.invoke(run_command())

        with open("results.json") as file:
            assert successful_result().json() == file.read()

    if result.exit_code != 0:
        raise result.exception
