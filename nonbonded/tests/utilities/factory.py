from typing import List, Optional, Union

from openff.recharge.grids import GridSettings

from nonbonded.library.models.authors import Author
from nonbonded.library.models.datasets import (
    Component,
    DataSet,
    DataSetCollection,
    DataSetEntry,
    QCDataSet,
)
from nonbonded.library.models.engines import ForceBalance
from nonbonded.library.models.forcefield import ForceField, Parameter
from nonbonded.library.models.projects import Benchmark, Optimization, Project, Study
from nonbonded.library.models.results import (
    BenchmarkResult,
    DataSetResult,
    DataSetResultEntry,
    DataSetStatistic,
    EvaluatorTargetResult,
    OptimizationResult,
    RechargeTargetResult,
    Statistic,
)
from nonbonded.library.models.targets import EvaluatorTarget, RechargeTarget
from nonbonded.library.statistics.statistics import StatisticType
from nonbonded.library.utilities.environments import ChemicalEnvironment


def create_force_field(inner_text="") -> ForceField:
    return ForceField(inner_content=f"<root>{inner_text}</root>")


def create_author():
    """Creates an author objects with

        * name="Fake Name"
        * email="fake@email.com"
        * institute="None"

    Returns
    -------
    Author
        The created author
    """
    return Author(name="Fake Name", email="fake@email.com", institute="None")


def create_data_set(data_set_id: str, entry_id: Optional[int] = None):
    """Creates a single author data set which contains a single
    density data entry. The entry contains two components, an
    aqueous solvent (x=1) and a methanol solute (n=1).

    Parameters
    ----------
    data_set_id: str
        The id to assign to the data set.
    entry_id
        The id to assign to the one data entry.

    Returns
    -------
    DataSet
    """

    author = create_author()

    data_entry = DataSetEntry(
        id=entry_id,
        property_type="Density",
        temperature=298.15,
        pressure=101.325,
        value=1.0,
        std_error=0.1,
        doi=" ",
        components=[
            Component(smiles="O", mole_fraction=1.0, exact_amount=0, role="Solvent"),
            Component(smiles="CO", mole_fraction=0.0, exact_amount=1, role="Solute"),
        ],
    )

    data_set = DataSet(
        id=data_set_id, description=" ", authors=[author], entries=[data_entry]
    )

    return data_set


def create_qc_data_set(qc_data_set_id: str):
    """Creates a single author QC data set which contains a single methane entry.

    Parameters
    ----------
    qc_data_set_id: str
        The id to assign to the QC data set.

    Returns
    -------
    QCDataSet
    """

    author = create_author()

    qc_data_set = QCDataSet(
        id=qc_data_set_id,
        description=" ",
        authors=[author],
        entries=["1"],
    )

    return qc_data_set


def create_project(project_id: str) -> Project:
    """Creates an empty projects with a single author and no studies
    with a specified id.

    Parameters
    ----------
    project_id
        The id to assign to the project.
    """
    return Project(
        id=project_id, name=project_id, description=" ", authors=[create_author()]
    )


def create_study(project_id: str, study_id: str) -> Study:
    """Creates a study with a specified id and no optimizations or
    benchmarks.

    Parameters
    ----------
    project_id
        The id of the parent project.
    study_id
        The id to assign to the study.
    """
    return Study(id=study_id, project_id=project_id, name=" ", description=" ")


def create_evaluator_target(name: str, data_set_ids: List[str]) -> EvaluatorTarget:
    """Creates an evaluator optimization target.

    Parameters
    ----------
    name
        The name of the target.
    data_set_ids
        The ids of the data sets which form the training set.
    """
    return EvaluatorTarget(
        id=name,
        data_set_ids=data_set_ids,
        denominators={"Density": "1 * kg * m**-3"},
    )


def create_recharge_target(name: str, qc_data_set_ids: List[str]) -> RechargeTarget:
    """Creates a recharge optimization target.

    Parameters
    ----------
    name
        The name of the target.
    qc_data_set_ids
        The ids of the QC data sets which form the training set.
    """
    return RechargeTarget(
        id=name,
        qc_data_set_ids=qc_data_set_ids,
        grid_settings=GridSettings(),
        property="esp",
    )


def create_optimization(
    project_id: str,
    study_id: str,
    optimization_id: str,
    targets: List[Union[EvaluatorTarget, RechargeTarget]],
) -> Optimization:

    """Creates an optimization with a specified id which target the specified
    training sets.

    Parameters
    ----------
    project_id
        The id of the parent project.
    study_id
        The id of the parent study.
    optimization_id
        The id to assign to the optimization.
    targets
        The optimization targets.
    """

    return Optimization(
        id=optimization_id,
        study_id=study_id,
        project_id=project_id,
        name="op",
        description=" ",
        targets=targets,
        force_field=create_force_field(),
        parameters_to_train=[
            Parameter(handler_type="vdW", smirks="[#6:1]", attribute_name="epsilon"),
            Parameter(handler_type="vdW", smirks="[#6:1]", attribute_name="sigma"),
        ],
        max_iterations=10,
        engine=ForceBalance(priors={"vdW/Atom/epsilon": 0.1, "vdW/Atom/sigma": 1.0}),
        analysis_environments=[ChemicalEnvironment.Alkane, ChemicalEnvironment.Alcohol],
    )


def create_benchmark(
    project_id: str,
    study_id: str,
    benchmark_id: str,
    data_set_ids: List[str],
    optimization_id: Optional[str],
    force_field: Optional[ForceField],
) -> Benchmark:

    """Creates an benchmark with a specified id which target the specified
    test sets.

    Parameters
    ----------
    project_id
        The id of the parent project.
    study_id
        The id of the parent study.
    benchmark_id
        The id to assign to the benchmark.
    data_set_ids
        The ids of the data sets which form the test set.
    optimization_id
        The id of the optimization being benchmarked.
    force_field
        The force field being benchmarked.
    """

    assert optimization_id is None or force_field is None
    assert optimization_id is not None or force_field is not None

    return Benchmark(
        id=benchmark_id,
        study_id=study_id,
        project_id=project_id,
        name=" ",
        description=" ",
        test_set_ids=data_set_ids,
        optimization_id=optimization_id,
        force_field=force_field,
        analysis_environments=[ChemicalEnvironment.Alkane, ChemicalEnvironment.Alcohol],
    )


def create_statistic(category: Optional[str] = "None"):

    return Statistic(
        statistic_type=StatisticType.RMSE,
        value=1.0,
        lower_95_ci=0.95,
        upper_95_ci=1.05,
        category=category,
    )


def create_data_set_statistic(category: Optional[str] = "None"):

    return DataSetStatistic(
        **create_statistic(category).dict(),
        property_type="Density",
        n_components=2,
    )


def create_data_set_result_entry(category: str = "None"):

    return DataSetResultEntry(
        reference_id=1,
        estimated_value=1.0,
        estimated_std_error=2.0,
        categories=[category],
    )


def create_data_set_result():

    return DataSetResult(
        result_entries=[create_data_set_result_entry()],
        statistic_entries=[create_data_set_statistic()],
    )


def _results_entries_from_data_sets(
    data_sets: Union[DataSet, List[DataSet], DataSetCollection]
) -> List[DataSetResultEntry]:

    if isinstance(data_sets, DataSetCollection):
        data_sets = data_sets.data_sets
    elif isinstance(data_sets, DataSet):
        data_sets = [data_sets]

    data_entries = [
        data_entry for data_set in data_sets for data_entry in data_set.entries
    ]

    results_entries = [
        DataSetResultEntry(
            reference_id=data_entry.id,
            estimated_value=data_entry.value,
            estimated_std_error=data_entry.std_error,
            categories=["Category"],
        )
        for data_entry in data_entries
    ]

    return results_entries


def _statistics_from_result_entries(
    result_entries: List[DataSetResultEntry],
) -> List[DataSetStatistic]:

    categories = list({None, *(x for y in result_entries for x in y.categories)})
    return [create_data_set_statistic(x) for x in categories]


def create_benchmark_result(
    project_id: str,
    study_id: str,
    benchmark_id: str,
    data_sets: Union[DataSet, List[DataSet], DataSetCollection],
) -> BenchmarkResult:
    """Creates a benchmark result.

    Parameters
    ----------
    project_id
        The id of the parent project.
    study_id
        The id of the parent study.
    benchmark_id
        The id of the benchmark which the result belongs to.
    data_sets
        The data sets the benchmark is targeting.
    """

    results_entries = _results_entries_from_data_sets(data_sets)
    statistics_entries = _statistics_from_result_entries(results_entries)

    return BenchmarkResult(
        id=benchmark_id,
        study_id=study_id,
        project_id=project_id,
        calculation_environment={"openff-evaluator": "1.0.0"},
        analysis_environment={"nonbonded": "0.0.01a5"},
        data_set_result=DataSetResult(
            statistic_entries=statistics_entries, result_entries=results_entries
        ),
    )


def create_optimization_result(
    project_id: str,
    study_id: str,
    optimization_id: str,
    evaluator_target_ids: List[str],
    recharge_target_ids: List[str],
) -> OptimizationResult:
    """Creates an optimization result.

    Parameters
    ----------
    project_id
        The id of the parent project.
    study_id
        The id of the parent study.
    optimization_id
        The id of the optimization which the results to belong to.
    evaluator_target_ids
        The ids of any evaluator targets which yielded a number of the results.
    recharge_target_ids
        The ids of any recharge targets which yielded a number of the results.
    """
    return OptimizationResult(
        id=optimization_id,
        study_id=study_id,
        project_id=project_id,
        calculation_environment={"forcebalance": "1.0.0"},
        analysis_environment={"nonbonded": "0.0.01a5"},
        target_results={
            0: {
                **{
                    evaluator_target_id: EvaluatorTargetResult(
                        objective_function=1.0,
                        statistic_entries=[create_data_set_statistic()],
                    )
                    for evaluator_target_id in evaluator_target_ids
                },
                **{
                    recharge_target_id: RechargeTargetResult(
                        objective_function=0.5, statistic_entries=[create_statistic()]
                    )
                    for recharge_target_id in recharge_target_ids
                },
            },
            1: {
                **{
                    evaluator_target_id: EvaluatorTargetResult(
                        objective_function=1.0,
                        statistic_entries=[create_data_set_statistic()],
                    )
                    for evaluator_target_id in evaluator_target_ids
                },
                **{
                    recharge_target_id: RechargeTargetResult(
                        objective_function=0.5, statistic_entries=[create_statistic()]
                    )
                    for recharge_target_id in recharge_target_ids
                },
            },
        },
        refit_force_field=create_force_field("refit"),
    )
