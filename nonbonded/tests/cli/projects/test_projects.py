import os

import pytest

from nonbonded.cli.projects.analysis import analyze_command
from nonbonded.cli.projects.plots import plot_command
from nonbonded.cli.projects.retrieve import retrieve_command
from nonbonded.cli.projects.upload import upload_command
from nonbonded.cli.projects.utilities import extract_identifiers
from nonbonded.library.factories.analysis import AnalysisFactory
from nonbonded.library.factories.inputs import InputFactory
from nonbonded.library.factories.plots import PlotFactory
from nonbonded.library.models.projects import Benchmark, Optimization, Project, Study
from nonbonded.library.utilities import temporary_cd
from nonbonded.tests.utilities.factory import (
    create_benchmark_result,
    create_data_set,
    create_optimization_result,
)


def empty_function(*args, **kwargs):
    pass


@pytest.mark.parametrize(
    "model_type, identifier_kwargs",
    [
        (Project, {"project_id": "project-1"}),
        (Study, {"project_id": "project-1", "study_id": "study-1"}),
        (
            Optimization,
            {
                "project_id": "project-1",
                "study_id": "study-1",
                "optimization_id": "optimization-1",
            },
        ),
        (
            Benchmark,
            {
                "project_id": "project-1",
                "study_id": "study-1",
                "benchmark_id": "benchmark-1",
            },
        ),
    ],
)
def test_retrieve(model_type, identifier_kwargs, runner, monkeypatch):

    model_factory = InputFactory.model_type_to_factory(model_type)

    monkeypatch.setattr(model_factory, "generate", empty_function)
    monkeypatch.setattr(model_type, "from_rest", empty_function)

    arguments = [
        (f"--{argument_name.replace('_', '-')}", argument_value)
        for argument_name, argument_value in extract_identifiers(
            model_type, {**identifier_kwargs}
        ).items()
    ]
    arguments = [argument for argument_pair in arguments for argument in argument_pair]

    result = runner.invoke(retrieve_command(model_type), arguments)

    if result.exit_code != 0:
        raise result.exception


@pytest.mark.parametrize("model_type", [Optimization, Benchmark])
def test_analyze(model_type, runner, monkeypatch):

    model_factory = AnalysisFactory.model_type_to_factory(model_type)
    monkeypatch.setattr(model_factory, "analyze", empty_function)

    result = runner.invoke(analyze_command(model_type))

    if result.exit_code != 0:
        raise result.exception


@pytest.mark.parametrize("model_type", [Optimization, Benchmark])
def test_plot(model_type, runner, monkeypatch):

    model_factory = PlotFactory.model_type_to_factory(model_type)
    monkeypatch.setattr(model_factory, "plot", empty_function)

    result = runner.invoke(plot_command(model_type))

    if result.exit_code != 0:
        raise result.exception


@pytest.mark.parametrize(
    "model_type, result_model",
    [
        (
            Optimization,
            create_optimization_result(
                "project-1", "study-1", "optimization-1", ["target-1"], []
            ),
        ),
        (
            Benchmark,
            create_benchmark_result(
                "project-1",
                "study-1",
                "optimization-1",
                create_data_set("data-set-1", 0),
            ),
        ),
    ],
)
@pytest.mark.usefixtures("change_api_url")
def test_upload(model_type, result_model, runner, monkeypatch, requests_mock):

    model_name = model_type.__name__.lower()

    # Mock the upload endpoint.
    requests_mock.post(
        result_model._post_endpoint(),
        text=result_model.json(),
    )

    # Save a copy of the result model.
    with temporary_cd():

        os.makedirs("analysis", exist_ok=True)

        with open(os.path.join("analysis", f"{model_name}-results.json"), "w") as file:
            file.write(result_model.json())

        result = runner.invoke(upload_command(model_type))

    if result.exit_code != 0:
        raise result.exception


# def test_list(self, requests_mock, runner):
#
#     projects = ProjectCollection(projects=[create_project("project-1")])
#     mock_get_projects(requests_mock, projects)
#
#     result = runner.invoke(project_cli, ["list"])
#
#     if result.exit_code != 0:
#         raise result.exception
#
#     assert projects.projects[0].id in result.output
