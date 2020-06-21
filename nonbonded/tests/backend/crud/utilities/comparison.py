from typing import Dict, List, Tuple, Union

import numpy

from nonbonded.backend.database import models
from nonbonded.library.models.authors import Author
from nonbonded.library.models.datasets import DataSet
from nonbonded.library.models.projects import Benchmark, Optimization, Project, Study
from nonbonded.library.models.results import (
    BenchmarkResult,
    OptimizationResult,
    ResultsEntry,
    StatisticsEntry,
)
from nonbonded.library.statistics.statistics import StatisticType
from nonbonded.library.utilities.environments import ChemicalEnvironment


def compare_authors(
    author_1: Union[Author, models.Author], author_2: Union[Author, models.Author],
):
    """Compares two author models.

    Parameters
    ----------
    author_1
        The first author to compare.
    author_2
        The second author to compare.

    Raises
    -------
    AssertionError
    """
    assert author_2.name == author_1.name
    assert author_2.email == author_1.email
    assert author_2.institute == author_1.institute


def compare_data_sets(
    data_set_1: Union[DataSet, models.DataSet],
    data_set_2: Union[DataSet, models.DataSet],
):
    """Compares two data set models.

    Parameters
    ----------
    data_set_1
        The first data set to compare.
    data_set_2
        The second data set to compare.

    Raises
    -------
    AssertionError
    """
    assert data_set_2.id == data_set_1.id
    assert data_set_2.description == data_set_1.description

    assert len(data_set_2.authors) == 1
    compare_authors(data_set_1.authors[0], data_set_2.authors[0])

    assert len(data_set_2.entries) == 1
    original_entry = data_set_1.entries[0]
    retrieved_entry = data_set_2.entries[0]

    assert numpy.isclose(retrieved_entry.temperature, original_entry.temperature)
    assert numpy.isclose(retrieved_entry.pressure, original_entry.pressure)

    assert retrieved_entry.phase == original_entry.phase

    assert numpy.isclose(retrieved_entry.value, original_entry.value)
    assert numpy.isclose(retrieved_entry.std_error, original_entry.std_error)

    assert retrieved_entry.doi == original_entry.doi

    assert len(retrieved_entry.components) == len(original_entry.components)

    matched_components = []

    for component in original_entry.components:

        matched_component = next(
            (x for x in retrieved_entry.components if x.smiles == component.smiles),
            None,
        )

        assert matched_component is not None

        matched_components.append((component, matched_component))

    for original_component, retrieved_component in matched_components:
        assert retrieved_component.smiles == original_component.smiles
        assert retrieved_component.mole_fraction == original_component.mole_fraction
        assert retrieved_component.exact_amount == original_component.exact_amount
        assert retrieved_component.role == original_component.role


def compare_projects(
    project_1: Union[Project, models.Project], project_2: Union[Project, models.Project]
):
    """Compare if two project models are equivalent.

    Parameters
    ----------
    project_1
        The first project to compare.
    project_2
        The second project to compare.

    Raises
    ------
    AssertionError
    """

    id_1 = project_1.id if isinstance(project_1, Project) else project_1.identifier
    id_2 = project_2.id if isinstance(project_2, Project) else project_2.identifier

    assert id_1 == id_2

    assert project_1.name == project_2.name
    assert project_1.description == project_2.description

    assert len(project_1.authors) == len(project_2.authors)

    authors_1 = {x.email: x for x in project_1.authors}
    authors_2 = {x.email: x for x in project_2.authors}

    assert {*authors_1} == {*authors_2}

    for email in authors_1:
        compare_authors(authors_1[email], authors_2[email])

    assert len(project_1.studies) == len(project_2.studies)

    studies_1 = {
        x.id if isinstance(x, Study) else x.identifier: x for x in project_1.studies
    }
    studies_2 = {
        x.id if isinstance(x, Study) else x.identifier: x for x in project_1.studies
    }

    assert {*studies_1} == {*studies_2}

    for study_id in studies_1:
        compare_studies(studies_1[study_id], studies_2[study_id])


def compare_studies(
    study_1: Union[Study, models.Study], study_2: Union[Study, models.Study]
):
    """Compare if two study models are equivalent.

    Parameters
    ----------
    study_1
        The first study to compare.
    study_2
        The second study to compare.

    Raises
    ------
    AssertionError
    """

    id_1 = study_1.id if isinstance(study_1, Study) else study_1.identifier
    id_2 = study_2.id if isinstance(study_2, Study) else study_2.identifier

    assert id_1 == id_2

    assert study_1.name == study_2.name
    assert study_1.description == study_2.description

    assert len(study_1.optimizations) == len(study_2.optimizations)

    optimizations_1 = {
        x.id if isinstance(x, Optimization) else x.identifier: x
        for x in study_1.optimizations
    }
    optimizations_2 = {
        x.id if isinstance(x, Optimization) else x.identifier: x
        for x in study_1.optimizations
    }

    assert {*optimizations_1} == {*optimizations_2}

    for unique_id in optimizations_1:
        compare_optimizations(optimizations_1[unique_id], optimizations_2[unique_id])

    assert len(study_1.benchmarks) == len(study_2.benchmarks)

    benchmarks_1 = {
        x.id if isinstance(x, Benchmark) else x.identifier: x
        for x in study_1.benchmarks
    }
    benchmarks_2 = {
        x.id if isinstance(x, Benchmark) else x.identifier: x
        for x in study_1.benchmarks
    }

    assert {*benchmarks_1} == {*benchmarks_2}

    for unique_id in benchmarks_1:
        compare_benchmarks(benchmarks_1[unique_id], benchmarks_2[unique_id])


def compare_optimizations(
    optimization_1: Union[Optimization, models.Optimization],
    optimization_2: Union[Optimization, models.Optimization],
):
    """Compare if two optimization models are equivalent.

    Parameters
    ----------
    optimization_1
        The first optimization to compare.
    optimization_2
        The second optimization to compare.

    Raises
    ------
    AssertionError
    """

    def _id(optimization: Union[Optimization, models.Optimization]):
        return (
            optimization.id
            if isinstance(optimization, Optimization)
            else optimization.identifier
        )

    def _training_ids(optimization: Union[Optimization, models.Optimization]):
        if isinstance(optimization, Optimization):
            training_ids = {*optimization.training_set_ids}
        else:
            training_ids = {x.id for x in optimization.training_sets}

        return training_ids

    def _denominators(optimization: Union[Optimization, models.Optimization]):
        if isinstance(optimization, Optimization):
            denominators = optimization.denominators
        else:
            denominators = {x.property_type: x.value for x in optimization.denominators}
        return denominators

    def _priors(optimization: Union[Optimization, models.Optimization]):
        if isinstance(optimization, Optimization):
            priors = optimization.priors
        else:
            priors = {x.parameter_type: x.value for x in optimization.priors}
        return priors

    id_1 = _id(optimization_1)
    id_2 = _id(optimization_1)

    assert id_1 == id_2

    assert optimization_1.name == optimization_2.name
    assert optimization_1.description == optimization_2.description

    # Check that both optimizations are targeting the same data sets.
    training_ids_1 = _training_ids(optimization_1)
    training_ids_2 = _training_ids(optimization_2)

    assert {*training_ids_1} == {*training_ids_2}

    # Check that both optimizations start from the same force field.
    assert (
        optimization_1.initial_force_field.inner_content
        == optimization_2.initial_force_field.inner_content
    )

    # Check that both optimizations are training the same parameters.
    parameters_1 = {
        (x.handler_type, x.smirks, x.attribute_name)
        for x in optimization_1.parameters_to_train
    }
    parameters_2 = {
        (x.handler_type, x.smirks, x.attribute_name)
        for x in optimization_2.parameters_to_train
    }

    assert parameters_1 == parameters_2

    # Make sure both optimizations are using the same force balance inputs.
    assert (
        optimization_1.force_balance_input.max_iterations
        == optimization_2.force_balance_input.max_iterations
    )
    assert numpy.isclose(
        optimization_1.force_balance_input.convergence_step_criteria,
        optimization_2.force_balance_input.convergence_step_criteria,
    )
    assert numpy.isclose(
        optimization_1.force_balance_input.convergence_objective_criteria,
        optimization_2.force_balance_input.convergence_objective_criteria,
    )
    assert numpy.isclose(
        optimization_1.force_balance_input.convergence_gradient_criteria,
        optimization_2.force_balance_input.convergence_gradient_criteria,
    )
    assert (
        optimization_1.force_balance_input.n_criteria
        == optimization_2.force_balance_input.n_criteria
    )
    assert numpy.isclose(
        optimization_1.force_balance_input.initial_trust_radius,
        optimization_2.force_balance_input.initial_trust_radius,
    )
    assert numpy.isclose(
        optimization_1.force_balance_input.minimum_trust_radius,
        optimization_2.force_balance_input.minimum_trust_radius,
    )
    assert (
        optimization_1.force_balance_input.evaluator_target_name
        == optimization_2.force_balance_input.evaluator_target_name
    )
    assert (
        optimization_1.force_balance_input.allow_direct_simulation
        == optimization_2.force_balance_input.allow_direct_simulation
    )
    assert (
        optimization_1.force_balance_input.n_molecules
        == optimization_2.force_balance_input.n_molecules
    )
    assert (
        optimization_1.force_balance_input.allow_reweighting
        == optimization_2.force_balance_input.allow_reweighting
    )
    assert (
        optimization_1.force_balance_input.n_effective_samples
        == optimization_2.force_balance_input.n_effective_samples
    )

    # Make sure the same denominators are being used.
    denominators_1 = _denominators(optimization_1)
    denominators_2 = _denominators(optimization_2)

    assert {*denominators_1} == {*denominators_2}
    assert all(denominators_1[x] == denominators_2[x] for x in denominators_1)

    # Make sure the same priors are being used.
    priors_1 = _priors(optimization_1)
    priors_2 = _priors(optimization_2)

    assert {*priors_1} == {*priors_2}
    assert all(priors_1[x] == priors_2[x] for x in priors_1)

    # Make sure both optimizations are analyzing the same environments
    assert len(optimization_1.analysis_environments) == len(
        optimization_2.analysis_environments
    )

    environments_1 = {
        x if isinstance(x, ChemicalEnvironment) else ChemicalEnvironment(x.id)
        for x in optimization_1.analysis_environments
    }
    environments_2 = {
        x if isinstance(x, ChemicalEnvironment) else ChemicalEnvironment(x.id)
        for x in optimization_2.analysis_environments
    }

    assert environments_1 == environments_2


def compare_optimization_results(
    optimization_result_1: Union[OptimizationResult, models.OptimizationResult],
    optimization_result_2: Union[OptimizationResult, models.OptimizationResult],
):
    """Compare if two optimization result models are equivalent.

    Parameters
    ----------
    optimization_result_1
        The first optimization result to compare.
    optimization_result_2
        The second optimization result to compare.

    Raises
    ------
    AssertionError
    """

    def _ids(
        optimization_result: Union[OptimizationResult, models.OptimizationResult]
    ) -> Tuple[str, str, str]:

        if isinstance(optimization_result, OptimizationResult):

            return (
                optimization_result.project_id,
                optimization_result.study_id,
                optimization_result.id,
            )

        optimization = optimization_result.parent
        study = optimization.parent
        project = study.parent

        return project.identifier, study.identifier, optimization.identifier

    def _objective_function(
        optimization_result: Union[OptimizationResult, models.OptimizationResult]
    ) -> Dict[int, float]:

        if isinstance(optimization_result, OptimizationResult):
            return optimization_result.objective_function

        return {x.iteration: x.value for x in optimization_result.objective_function}

    def _statistics(
        optimization_result: Union[OptimizationResult, models.OptimizationResult]
    ) -> Dict[int, List[StatisticsEntry]]:

        if isinstance(optimization_result, OptimizationResult):
            return optimization_result.statistics

        return {x.iteration: x for x in optimization_result.statistics}

    ids_1 = _ids(optimization_result_1)
    ids_2 = _ids(optimization_result_2)

    assert ids_1 == ids_2

    objective_function_1 = _objective_function(optimization_result_1)
    objective_function_2 = _objective_function(optimization_result_2)

    assert len(objective_function_1) == len(objective_function_2)
    assert {*objective_function_1} == {*objective_function_2}

    assert all(
        numpy.isclose(objective_function_1[x], objective_function_2[x])
        for x in objective_function_1
    )

    statistics_1 = _statistics(optimization_result_1)
    statistics_2 = _statistics(optimization_result_2)

    assert len(statistics_1) == len(statistics_2)
    assert {*statistics_1} == {*statistics_2}

    for iteration in statistics_1:

        expected_attributes = StatisticsEntry.__fields__

        if isinstance(statistics_1[iteration], models.OptimizationStatisticsEntry):
            statistic_1 = statistics_1[iteration]
        else:
            assert len(statistics_1[iteration]) == 1
            statistic_1 = statistics_1[iteration][0]

        if isinstance(statistics_2[iteration], models.OptimizationStatisticsEntry):
            statistic_2 = statistics_2[iteration]
        else:
            assert len(statistics_2[iteration]) == 1
            statistic_2 = statistics_2[iteration][0]

        for expected_attribute in expected_attributes:

            field_1 = getattr(statistic_1, expected_attribute)
            field_2 = getattr(statistic_2, expected_attribute)

            if isinstance(field_1, float):

                assert numpy.isclose(field_1, field_2)
                continue

            elif expected_attribute == "statistics_type":

                field_1 = StatisticType(field_1)
                field_2 = StatisticType(field_2)

            assert field_1 == field_2

    assert (
        optimization_result_1.refit_force_field.inner_content
        == optimization_result_2.refit_force_field.inner_content
    )


def compare_benchmarks(
    benchmark_1: Union[Benchmark, models.Benchmark],
    benchmark_2: Union[Benchmark, models.Benchmark],
):
    """Compare if two benchmark models are equivalent.

    Parameters
    ----------
    benchmark_1
        The first benchmark to compare.
    benchmark_2
        The second benchmark to compare.

    Raises
    ------
    AssertionError
    """

    def _id(benchmark: Union[Benchmark, models.Benchmark]):
        return (
            benchmark.id if isinstance(benchmark, Benchmark) else benchmark.identifier
        )

    def _test_ids(benchmark: Union[Benchmark, models.Benchmark]):
        if isinstance(benchmark, Benchmark):
            test_ids = {*benchmark.test_set_ids}
        else:
            test_ids = {x.id for x in benchmark.test_sets}

        return test_ids

    id_1 = _id(benchmark_1)
    id_2 = _id(benchmark_1)

    assert id_1 == id_2

    assert benchmark_1.name == benchmark_2.name
    assert benchmark_1.description == benchmark_2.description

    # Check that both benchmarks are targeting the same data sets.
    test_ids_1 = _test_ids(benchmark_1)
    test_ids_2 = _test_ids(benchmark_2)

    assert {*test_ids_1} == {*test_ids_2}

    # Make the benchmarks are against the same targets.
    if (
        isinstance(benchmark_1, models.Benchmark)
        and benchmark_1.optimization is not None
    ):
        optimization_id_1 = benchmark_1.optimization.identifier
    else:
        optimization_id_1 = benchmark_1.optimization_id
    if (
        isinstance(benchmark_2, models.Benchmark)
        and benchmark_2.optimization is not None
    ):
        optimization_id_2 = benchmark_2.optimization.identifier
    else:
        optimization_id_2 = benchmark_2.optimization_id

    assert optimization_id_1 == optimization_id_2

    if benchmark_1.force_field is None:
        assert benchmark_1.force_field == benchmark_2.force_field
    else:
        assert (
            benchmark_1.force_field.inner_content
            == benchmark_2.force_field.inner_content
        )

    # Make sure both benchmarks are analyzing the same environments
    assert len(benchmark_1.analysis_environments) == len(
        benchmark_2.analysis_environments
    )

    environments_1 = {
        x if isinstance(x, ChemicalEnvironment) else ChemicalEnvironment(x.id)
        for x in benchmark_1.analysis_environments
    }
    environments_2 = {
        x if isinstance(x, ChemicalEnvironment) else ChemicalEnvironment(x.id)
        for x in benchmark_2.analysis_environments
    }

    assert environments_1 == environments_2


def compare_statistic_entries(
    statistic_1: Union[
        StatisticsEntry,
        models.OptimizationStatisticsEntry,
        models.BenchmarkStatisticsEntry,
    ],
    statistic_2: Union[
        StatisticsEntry,
        models.OptimizationStatisticsEntry,
        models.BenchmarkStatisticsEntry,
    ],
):
    """Compare if two statistic entry models are equivalent.

    Parameters
    ----------
    statistic_1
        The first statistic entry to compare.
    statistic_2
        The second statistic entry to compare.

    Raises
    ------
    AssertionError
    """

    expected_attributes = StatisticsEntry.__fields__

    for expected_attribute in expected_attributes:

        field_1 = getattr(statistic_1, expected_attribute)
        field_2 = getattr(statistic_2, expected_attribute)

        if isinstance(field_1, float):

            assert numpy.isclose(field_1, field_2)
            continue

        elif expected_attribute == "statistics_type":

            field_1 = StatisticType(field_1)
            field_2 = StatisticType(field_2)

        assert field_1 == field_2


def compare_result_entries(
    result_1: Union[ResultsEntry, models.BenchmarkResultsEntry],
    result_2: Union[ResultsEntry, models.BenchmarkResultsEntry],
):
    """Compare if two result entry models are equivalent.

    Parameters
    ----------
    result_1
        The first results entry to compare.
    result_2
        The second results entry to compare.

    Raises
    ------
    AssertionError
    """

    expected_attributes = ResultsEntry.__fields__

    for expected_attribute in expected_attributes:

        field_1 = getattr(result_1, expected_attribute)
        field_2 = getattr(result_2, expected_attribute)

        if isinstance(field_1, float):

            assert numpy.isclose(field_1, field_2)
            continue

        assert field_1 == field_2


def compare_benchmark_results(
    benchmark_result_1: Union[BenchmarkResult, models.BenchmarkResult],
    benchmark_result_2: Union[BenchmarkResult, models.BenchmarkResult],
):
    """Compare if two benchmark result models are equivalent.

    Parameters
    ----------
    benchmark_result_1
        The first benchmark result to compare.
    benchmark_result_2
        The second benchmark result to compare.

    Raises
    ------
    AssertionError
    """

    def _ids(
        benchmark_result: Union[BenchmarkResult, models.BenchmarkResult]
    ) -> Tuple[str, str, str]:

        if isinstance(benchmark_result, BenchmarkResult):

            return (
                benchmark_result.project_id,
                benchmark_result.study_id,
                benchmark_result.id,
            )

        benchmark = benchmark_result.parent
        study = benchmark.parent
        project = study.parent

        return project.identifier, study.identifier, benchmark.identifier

    def _results(
        benchmark_result: Union[BenchmarkResult, models.BenchmarkResult]
    ) -> Dict[int, ResultsEntry]:

        if isinstance(benchmark_result, BenchmarkResult):
            results_entries = benchmark_result.analysed_result.results_entries
        else:
            results_entries = benchmark_result.results_entries

        return {x.reference_id: x for x in results_entries}

    def _statistics(
        benchmark_result: Union[BenchmarkResult, models.BenchmarkResult]
    ) -> Dict[Tuple[StatisticType, str, int], StatisticsEntry]:

        if isinstance(benchmark_result, BenchmarkResult):
            statistic_entries = benchmark_result.analysed_result.statistic_entries
        else:
            statistic_entries = benchmark_result.statistic_entries

        return {
            (StatisticType(x.statistics_type), x.property_type, x.n_components): x
            for x in statistic_entries
        }

    ids_1 = _ids(benchmark_result_1)
    ids_2 = _ids(benchmark_result_2)

    assert ids_1 == ids_2

    statistics_1 = _statistics(benchmark_result_1)
    statistics_2 = _statistics(benchmark_result_2)

    assert len(statistics_1) == len(statistics_2)
    assert {*statistics_1} == {*statistics_2}

    for statistic_key in statistics_1:

        compare_statistic_entries(
            statistics_1[statistic_key], statistics_2[statistic_key]
        )

    results_1 = _results(benchmark_result_1)
    results_2 = _results(benchmark_result_2)

    assert len(results_1) == len(results_2)
    assert {*results_1} == {*results_2}

    for result_key in results_1:
        compare_result_entries(results_1[result_key], results_2[result_key])
