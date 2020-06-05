from sqlalchemy.orm import Session

from nonbonded.backend.database import models
from nonbonded.library.models.results import OptimizationResult, BenchmarkResult
from nonbonded.tests.backend.api.utilities import BaseTestEndpoints
from nonbonded.tests.backend.crud.utilities.commit import (
    commit_optimization, commit_optimization_result, commit_benchmark,
    commit_benchmark_result,
)
from nonbonded.tests.backend.crud.utilities.comparison import (
    compare_optimization_results, compare_benchmark_results,
)
from nonbonded.tests.backend.crud.utilities.create import (
    create_optimization_result, create_benchmark_result, create_data_set,
)


class TestOptimizationResultEndpoints(BaseTestEndpoints):
    @classmethod
    def _rest_class(cls):
        return OptimizationResult

    @classmethod
    def _create_model(cls, db, create_dependencies=True):

        project_id = "project-1"
        study_id = "study-1"
        optimization_id = "optimization-1"

        if create_dependencies:

            project, study, optimization, _ = commit_optimization(db)

            project_id = project.id
            study_id = study.id
            optimization_id = optimization.id

        optimization_result = create_optimization_result(
            project_id,
            study_id,
            optimization_id
        )

        return (
            optimization_result,
            {
                "project_id": project_id,
                "study_id": study_id,
                "model_id": optimization_id,
            },
        )

    @classmethod
    def _perturb_model(cls, model):
        model.refit_force_field.inner_xml = "<root>Updated</root>"

    @classmethod
    def _commit_model(cls, db):
        project, study, optimization, _, optimization_result = commit_optimization_result(db)

        return (
            optimization_result,
            {
                "project_id": project.id,
                "study_id": study.id,
                "model_id": optimization.id,
            },
        )

    @classmethod
    def _comparison_function(cls):
        return compare_optimization_results

    @classmethod
    def _n_db_models(cls, db: Session) -> int:
        return db.query(models.OptimizationResult.id).count()


class TestBenchmarkResultEndpoints(BaseTestEndpoints):
    @classmethod
    def _rest_class(cls):
        return BenchmarkResult

    @classmethod
    def _create_model(cls, db, create_dependencies=True):

        project_id = "project-1"
        study_id = "study-1"
        benchmark_id = "benchmark-1"

        data_sets = create_data_set("data-set-1")

        for index, entry in enumerate(data_sets.entries):
            entry.id = index + 1

        if create_dependencies:

            project, study, benchmark, data_set, _, _ = commit_benchmark(db, False)

            project_id = project.id
            study_id = study.id
            benchmark_id = benchmark.id

            data_sets = data_set

        benchmark_result = create_benchmark_result(
            project_id,
            study_id,
            benchmark_id,
            data_sets,
        )

        return (
            benchmark_result,
            {
                "project_id": project_id,
                "study_id": study_id,
                "model_id": benchmark_id,
            },
        )

    @classmethod
    def _perturb_model(cls, model):
        model.analysed_result.statistic_entries = []

    @classmethod
    def _commit_model(cls, db):
        project, study, benchmark, benchmark_result, _, _, _ = commit_benchmark_result(db, False)

        return (
            benchmark_result,
            {
                "project_id": project.id,
                "study_id": study.id,
                "model_id": benchmark.id,
            },
        )

    @classmethod
    def _comparison_function(cls):
        return compare_benchmark_results

    @classmethod
    def _n_db_models(cls, db: Session) -> int:
        return db.query(models.BenchmarkResult.id).count()
