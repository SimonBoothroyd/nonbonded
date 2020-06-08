from typing import List, Optional, Union

from nonbonded.library.models.authors import Author
from nonbonded.library.models.datasets import (
    Component,
    DataSet,
    DataSetCollection,
    DataSetEntry,
)
from nonbonded.library.models.forcebalance import ForceBalanceOptions
from nonbonded.library.models.forcefield import ForceField, Parameter
from nonbonded.library.models.projects import Benchmark, Optimization, Project, Study
from nonbonded.library.models.results import (
    AnalysedResult,
    BenchmarkResult,
    OptimizationResult,
    ResultsEntry,
    StatisticsEntry,
)
from nonbonded.library.statistics.statistics import StatisticType
from nonbonded.library.utilities.environments import ChemicalEnvironment


def create_force_field(inner_text="") -> ForceField:
    return ForceField(inner_xml=f"<root>{inner_text}</root>")


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


def create_data_set(data_set_id: str):
    """Creates a single author data set which contains a single
    density data entry. The entry contains two components, an
    aqueous solvent (x=1) and a methanol solute (n=1).

    Parameters
    ----------
    data_set_id: str
        The id to assign to the data set.

    Returns
    -------
    DataSet
    """

    author = create_author()

    data_entry = DataSetEntry(
        id=None,
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


def create_empty_project(project_id: str) -> Project:
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


def create_empty_study(project_id: str, study_id: str) -> Study:
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


def create_optimization(
    project_id: str, study_id: str, optimization_id: str, data_set_ids: List[str]
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
    data_set_ids
        The ids of the data sets which form the training set.
    """

    return Optimization(
        id=optimization_id,
        study_id=study_id,
        project_id=project_id,
        name=" ",
        description=" ",
        training_set_ids=data_set_ids,
        initial_force_field=create_force_field(),
        parameters_to_train=[
            Parameter(handler_type="vdW", smirks="[#6:1]", attribute_name="epsilon")
        ],
        force_balance_input=ForceBalanceOptions(),
        denominators={"Density": "1 * kg * m**-3"},
        priors={"vdW/Atom/epsilon": 0.1},
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


def create_statistic_entry(category: Optional[str] = "None"):

    return StatisticsEntry(
        statistics_type=StatisticType.RMSE,
        property_type="Density",
        n_components=2,
        category=category,
        value=1.0,
        lower_95_ci=0.95,
        upper_95_ci=1.05,
    )


def create_optimization_result(
    project_id: str, study_id: str, optimization_id: str
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
    """
    return OptimizationResult(
        id=optimization_id,
        study_id=study_id,
        project_id=project_id,
        objective_function={0: 1.0, 1: 0.5, 2: 0.1},
        statistics={
            0: [create_statistic_entry()],
            1: [create_statistic_entry()],
            2: [create_statistic_entry()],
        },
        refit_force_field=create_force_field("Refit"),
    )


def results_entries_from_data_sets(
    data_sets: Union[DataSet, List[DataSet], DataSetCollection]
) -> List[ResultsEntry]:

    if isinstance(data_sets, DataSetCollection):
        data_sets = data_sets.data_sets
    elif isinstance(data_sets, DataSet):
        data_sets = [data_sets]

    data_entries = [
        data_entry for data_set in data_sets for data_entry in data_set.entries
    ]

    results_entries = [
        ResultsEntry(
            reference_id=data_entry.id,
            estimated_value=data_entry.value,
            estimated_std_error=data_entry.std_error,
            category="Category",
        )
        for data_entry in data_entries
    ]

    return results_entries


def statistics_from_result_entries(
    result_entries: List[ResultsEntry],
) -> List[StatisticsEntry]:

    categories = list({None, *(x.category for x in result_entries)})
    return [create_statistic_entry(x) for x in categories]


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

    results_entries = results_entries_from_data_sets(data_sets)
    statistics_entries = statistics_from_result_entries(results_entries)

    return BenchmarkResult(
        id=benchmark_id,
        study_id=study_id,
        project_id=project_id,
        analysed_result=AnalysedResult(
            statistic_entries=statistics_entries, results_entries=results_entries
        ),
    )
