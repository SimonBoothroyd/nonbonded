from typing import List, Tuple

import pytest

from nonbonded.library.models.datasets import DataSet
from nonbonded.library.models.forcefield import ForceField
from nonbonded.library.models.projects import Benchmark, Optimization
from nonbonded.library.models.results import BenchmarkResult, OptimizationResult
from nonbonded.tests.utilities.factory import (
    create_benchmark,
    create_benchmark_result,
    create_data_set,
    create_evaluator_target,
    create_optimization,
    create_optimization_result,
    create_recharge_target,
)


@pytest.fixture()
def optimizations_and_results(
    smirnoff_force_field,
) -> Tuple[List[Optimization], List[OptimizationResult]]:

    optimization_1 = create_optimization(
        "project-1",
        "study-1",
        "optimization-1",
        [
            create_evaluator_target("evaluator-target-1", ["data-set-1"]),
            create_recharge_target("recharge-target-1", ["molecule-set-1"]),
        ],
    )
    optimization_1.name = "Optimization 1"
    optimization_1.force_field = ForceField.from_openff(smirnoff_force_field)
    optimization_2 = create_optimization(
        "project-1",
        "study-1",
        "optimization-2",
        [
            create_evaluator_target("evaluator-target-1", ["data-set-1"]),
            create_recharge_target("recharge-target-1", ["molecule-set-1"]),
        ],
    )
    optimization_2.force_field = ForceField.from_openff(smirnoff_force_field)
    optimization_2.name = "Optimization 2"

    smirnoff_force_field.get_parameter_handler("vdW").parameters["[#6:1]"].epsilon *= 2
    smirnoff_force_field.get_parameter_handler("vdW").parameters["[#6:1]"].sigma *= 3

    optimization_result_1 = create_optimization_result(
        "project-1",
        "study-1",
        "optimization-1",
        ["evaluator-target-1"],
        ["recharge-target-1"],
    )
    optimization_result_1.refit_force_field = ForceField.from_openff(
        smirnoff_force_field
    )

    smirnoff_force_field.get_parameter_handler("vdW").parameters["[#6:1]"].epsilon /= 4
    smirnoff_force_field.get_parameter_handler("vdW").parameters["[#6:1]"].sigma /= 6

    optimization_result_2 = create_optimization_result(
        "project-1",
        "study-1",
        "optimization-2",
        ["evaluator-target-1"],
        ["recharge-target-1"],
    )
    optimization_result_2.refit_force_field = ForceField.from_openff(
        smirnoff_force_field
    )

    return (
        [optimization_1, optimization_2],
        [optimization_result_1, optimization_result_2],
    )


@pytest.fixture()
def benchmarks_and_results(
    force_field: ForceField,
) -> Tuple[List[Benchmark], List[BenchmarkResult], List[DataSet]]:

    benchmarks = []
    benchmark_results = []
    data_sets = [create_data_set("data-set-1", 1)]

    for index in range(2):

        benchmark = create_benchmark(
            "project-1",
            "study-1",
            f"benchmark-{index + 1}",
            ["data-set-1"],
            None,
            force_field,
        )
        benchmark.name = f"Benchmark {index + 1}"
        benchmarks.append(benchmark)

        benchmark_result = create_benchmark_result(
            "project-1", "study-1", "benchmark-1", data_sets
        )

        for statistic_entry in benchmark_result.data_set_result.statistic_entries:
            statistic_entry.value /= index + 1
            statistic_entry.lower_95_ci /= index + 1
            statistic_entry.upper_95_ci /= index + 1

        benchmark_results.append(benchmark_result)

    # benchmarks = [
    #     Benchmark.from_rest(
    #         project_id="binary-mixture",
    #         study_id="expanded",
    #         sub_study_id="openff-1-0-0",
    #     ),
    #     Benchmark.from_rest(
    #         project_id="binary-mixture",
    #         study_id="expanded",
    #         sub_study_id="h-mix-rho-x-rho",
    #     ),
    #     Benchmark.from_rest(
    #         project_id="binary-mixture", study_id="expanded", sub_study_id="h-mix-rho-x"
    #     ),
    # ]
    # benchmark_results = [
    #     BenchmarkResult.from_rest(
    #         project_id="binary-mixture", study_id="expanded", model_id="openff-1-0-0"
    #     ),
    #     BenchmarkResult.from_rest(
    #         project_id="binary-mixture", study_id="expanded", model_id="h-mix-rho-x-rho"
    #     ),
    #     BenchmarkResult.from_rest(
    #         project_id="binary-mixture", study_id="expanded", model_id="h-mix-rho-x"
    #     ),
    # ]
    #
    # data_set_ids = {
    #     test_set_id
    #     for benchmark in benchmarks
    #     for test_set_id in benchmark.test_set_ids
    # }
    # data_sets = [
    #     DataSet.from_rest(data_set_id=data_set_id) for data_set_id in data_set_ids
    # ]

    return benchmarks, benchmark_results, data_sets
