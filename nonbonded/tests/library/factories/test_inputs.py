import os

import pytest
from openforcefield.typing.engines.smirnoff import ForceField as OFFForceField
from openforcefield.typing.engines.smirnoff import vdWHandler

from nonbonded.library.factories.inputs import InputFactory
from nonbonded.library.factories.inputs.benchmark import BenchmarkFactory
from nonbonded.library.factories.inputs.optimization import OptimizationFactory
from nonbonded.library.models.forcefield import ForceField
from nonbonded.library.models.targets import EvaluatorTarget, RechargeTarget
from nonbonded.library.utilities import temporary_cd
from nonbonded.tests.utilities.factory import (
    create_benchmark,
    create_benchmark_result,
    create_data_set,
    create_evaluator_target,
    create_force_field,
    create_molecule_set,
    create_optimization,
    create_optimization_result,
    create_project,
    create_recharge_target,
    create_study,
)
from nonbonded.tests.utilities.mock import (
    mock_get_benchmark,
    mock_get_benchmark_result,
    mock_get_data_set,
    mock_get_molecule_set,
    mock_get_optimization,
    mock_get_optimization_result,
    mock_get_project,
    mock_get_study,
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

    monkeypatch.setattr(OptimizationFactory, "generate", mock_generate)
    monkeypatch.setattr(BenchmarkFactory, "generate", mock_generate)

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


@pytest.mark.usefixtures("change_api_url")
def test_optimization(requests_mock, monkeypatch):

    from simtk import unit

    data_set = create_data_set("data-set-1")
    mock_get_data_set(requests_mock, data_set)
    molecule_set = create_molecule_set("molecule-set-1")
    mock_get_molecule_set(requests_mock, molecule_set)

    mock_get_optimization_result(
        requests_mock,
        create_optimization_result(
            "project-1",
            "study-1",
            "benchmark-1",
            ["evaluator-target"],
            ["recharge-target"],
        ),
    )

    off_force_field = OFFForceField(
        '<SMIRNOFF version="0.3" aromaticity_model="OEAroModel_MDL"></SMIRNOFF>'
    )

    vdw_handler = vdWHandler(**{"version": "0.3"})
    vdw_handler.add_parameter(
        parameter_kwargs={
            "smirks": "[#6:1]",
            "epsilon": 1.0 * unit.kilojoules_per_mole,
            "sigma": 1.0 * unit.angstrom,
        }
    )

    off_force_field.register_parameter_handler(vdw_handler)

    optimization = create_optimization(
        "project-1",
        "study-1",
        "optimization-1",
        targets=[
            create_evaluator_target("evaluator-target", ["data-set-1"]),
            create_recharge_target("recharge-target", ["molecule-set-1"]),
        ],
    )
    optimization.force_field = ForceField.from_openff(off_force_field)

    mock_get_optimization(requests_mock, optimization)

    with temporary_cd():

        OptimizationFactory.generate(
            optimization, "test-env", "12:34", "lilac-dask", 8000, 1, False
        )

        assert os.path.isdir(optimization.id)

        with temporary_cd(optimization.id):

            assert all(
                os.path.isfile(expected_file_name)
                for expected_file_name in [
                    "optimization.json",
                    "optimize.in",
                    "server-config.json",
                    "submit.sh",
                ]
            )

            # Validate the force filed
            assert os.path.isdir("forcefield")

            off_force_field = OFFForceField(
                os.path.join("forcefield", "force-field.offxml"),
                allow_cosmetic_attributes=True,
            )
            vdw_handler: vdWHandler = off_force_field.get_parameter_handler("vdW")

            assert len(vdw_handler.parameters) == 1
            assert vdw_handler.parameters[0]._parameterize == "epsilon, sigma"

            for target in optimization.targets:

                target_directory = os.path.join("targets", target.id)
                assert os.path.isdir(target_directory)

                with temporary_cd(target_directory):

                    assert os.path.isfile("training-set.json")

                    if isinstance(target, EvaluatorTarget):
                        assert os.path.isfile("options.json")

                    elif isinstance(target, RechargeTarget):
                        assert os.path.isfile("conformer-settings.json")
                        assert os.path.isfile("esp-settings.json")


@pytest.mark.usefixtures("change_api_url")
def test_generate(requests_mock, monkeypatch):

    data_set = create_data_set("data-set-1")
    data_set.entries[0].id = 1

    mock_get_data_set(requests_mock, data_set)

    mock_get_benchmark_result(
        requests_mock,
        create_benchmark_result("project-1", "study-1", "benchmark-1", data_set),
    )

    benchmark = create_benchmark(
        "project-1",
        "study-1",
        "benchmark-1",
        ["data-set-1"],
        None,
        ForceField(
            inner_content=(
                '<SMIRNOFF version="0.3" '
                'aromaticity_model="OEAroModel_MDL"></SMIRNOFF>'
            )
        ),
    )

    mock_get_benchmark(requests_mock, benchmark)

    with temporary_cd():

        BenchmarkFactory.generate(
            benchmark, "test-env", "12:34", "lilac-dask", 8000, 1, False
        )

        assert os.path.isdir(benchmark.id)

        with temporary_cd(benchmark.id):

            assert all(
                os.path.isfile(expected_file_name)
                for expected_file_name in [
                    "benchmark.json",
                    "estimation-options.json",
                    "server-config.json",
                    "submit.sh",
                    "test-set.json",
                    "test-set-collection.json",
                ]
            )

            with open("force-field.offxml") as file:
                assert benchmark.force_field.inner_content in file.read()
