from collections import defaultdict
from typing import List, Union

from sqlalchemy.orm import Session

from nonbonded.backend.database import models
from nonbonded.backend.database.crud.projects import BenchmarkCRUD, OptimizationCRUD
from nonbonded.backend.database.utilities.exceptions import (
    BenchmarkNotFoundError,
    BenchmarkResultExistsError,
    OptimizationNotFoundError,
    OptimizationResultExistsError,
    OptimizationResultNotFoundError,
    UnableToDeleteError,
)
from nonbonded.library.models import results


class BenchmarkResultCRUD:
    @staticmethod
    def query(db: Session, project_id: str, study_id: str, benchmark_id: str):

        db_benchmark = BenchmarkCRUD.query(db, project_id, study_id, benchmark_id)

        if not db_benchmark:
            return None

        return db_benchmark.results

    @staticmethod
    def create(
        db: Session, benchmark_result: results.BenchmarkResult
    ) -> models.BenchmarkResult:

        db_benchmark = BenchmarkCRUD.query(
            db,
            benchmark_result.project_id,
            benchmark_result.study_id,
            benchmark_result.id,
        )

        if not db_benchmark:

            raise BenchmarkNotFoundError(
                benchmark_result.project_id,
                benchmark_result.study_id,
                benchmark_result.id,
            )

        if (
            BenchmarkResultCRUD.query(
                db,
                benchmark_result.project_id,
                benchmark_result.study_id,
                benchmark_result.id,
            )
            is not None
        ):

            raise BenchmarkResultExistsError(
                benchmark_result.project_id,
                benchmark_result.study_id,
                benchmark_result.id,
            )

        # noinspection PyTypeChecker
        db_benchmark_result = models.BenchmarkResult(
            parent=db_benchmark,
            statistic_entries=[
                models.BenchmarkStatisticsEntry(**x.dict())
                for x in benchmark_result.analysed_result.statistic_entries
            ],
            results_entries=[
                models.BenchmarkResultsEntry(**x.dict())
                for x in benchmark_result.analysed_result.results_entries
            ],
        )

        return db_benchmark_result

    @staticmethod
    def read(db: Session, project_id: str, study_id: str, benchmark_id: str):

        db_benchmark = BenchmarkCRUD.query(db, project_id, study_id, benchmark_id)

        if not db_benchmark:
            raise BenchmarkNotFoundError(project_id, study_id, benchmark_id)

        if not db_benchmark.results:
            return None

        db_results_entries = (
            db.query(models.BenchmarkResultsEntry)
            .filter(models.BenchmarkResultsEntry.parent_id == db_benchmark.id)
            .all()
        )
        db_statistic_entries = (
            db.query(models.BenchmarkStatisticsEntry)
            .filter(models.BenchmarkStatisticsEntry.parent_id == db_benchmark.id)
            .all()
        )

        return BenchmarkResultCRUD.db_to_model(
            db_benchmark, db_results_entries, db_statistic_entries
        )

    @staticmethod
    def delete(db: Session, project_id: str, study_id: str, benchmark_id: str):

        db_benchmark_result = BenchmarkResultCRUD.query(
            db, project_id, study_id, benchmark_id
        )

        if not db_benchmark_result:
            raise BenchmarkResultExistsError(project_id, study_id, benchmark_id)

        db.delete(db_benchmark_result)

    @staticmethod
    def db_to_model(
        db_benchmark: Union[models.Benchmark, models.BenchmarkResult],
        db_results_entries: List[models.BenchmarkResultsEntry],
        db_statistic_entries: List[models.BenchmarkStatisticsEntry],
    ) -> results.BenchmarkResult:

        if isinstance(db_benchmark, models.BenchmarkResult):
            db_benchmark = db_benchmark.parent

        benchmark_id = db_benchmark.identifier
        study_id = db_benchmark.parent.identifier
        project_id = db_benchmark.parent.parent.identifier

        # noinspection PyTypeChecker
        analysed_result = results.AnalysedResult(
            statistic_entries=[x for x in db_statistic_entries],
            results_entries=[x for x in db_results_entries],
        )

        benchmark_result = results.BenchmarkResult(
            project_id=project_id,
            study_id=study_id,
            id=benchmark_id,
            analysed_result=analysed_result,
        )

        return benchmark_result


class OptimizationResultCRUD:
    @staticmethod
    def query(db: Session, project_id: str, study_id: str, optimization_id: str):

        db_optimization = OptimizationCRUD.query(
            db, project_id, study_id, optimization_id
        )

        if not db_optimization:
            return None

        return db_optimization.results

    @staticmethod
    def create(
        db: Session, optimization_result: results.OptimizationResult
    ) -> models.OptimizationResult:

        db_optimization = OptimizationCRUD.query(
            db,
            optimization_result.project_id,
            optimization_result.study_id,
            optimization_result.id,
        )

        if not db_optimization:

            raise OptimizationNotFoundError(
                optimization_result.project_id,
                optimization_result.study_id,
                optimization_result.id,
            )

        if (
            OptimizationResultCRUD.query(
                db,
                optimization_result.project_id,
                optimization_result.study_id,
                optimization_result.id,
            )
            is not None
        ):

            raise OptimizationResultExistsError(
                optimization_result.project_id,
                optimization_result.study_id,
                optimization_result.id,
            )

        # noinspection PyTypeChecker
        db_optimization_result = models.OptimizationResult(
            parent=db_optimization,
            objective_function=[
                models.ObjectiveFunction(iteration=i, value=x)
                for i, x in optimization_result.objective_function.items()
            ],
            refit_force_field=models.RefitForceField(
                inner_xml=optimization_result.refit_force_field.inner_xml
            ),
            statistics=[
                models.OptimizationStatisticsEntry(
                    **{
                        "iteration": iteration,
                        **{
                            **statistic.dict(),
                            "statistics_type": statistic.dict()[
                                "statistics_type"
                            ].value,
                        },
                    }
                )
                for iteration, statistics in optimization_result.statistics.items()
                for statistic in statistics
            ],
        )

        return db_optimization_result

    @staticmethod
    def read(db: Session, project_id: str, study_id: str, optimization_id: str):

        db_optimization = OptimizationCRUD.query(
            db, project_id, study_id, optimization_id
        )

        if not db_optimization:
            raise OptimizationNotFoundError(project_id, study_id, optimization_id)

        if not db_optimization.results:
            return None

        return OptimizationResultCRUD.db_to_model(db_optimization.results)

    @staticmethod
    def delete(db: Session, project_id: str, study_id: str, optimization_id: str):

        db_optimization_result = OptimizationResultCRUD.query(
            db, project_id, study_id, optimization_id
        )

        if not db_optimization_result:
            raise OptimizationResultNotFoundError(project_id, study_id, optimization_id)

        if (
            db_optimization_result.parent.benchmarks is not None
            and len(db_optimization_result.parent.benchmarks) > 0
        ):

            benchmark_ids = [
                ", ".join(
                    x.identifier for x in db_optimization_result.parent.benchmarks
                )
            ]

            raise UnableToDeleteError(
                f"The optimization (project_id={project_id}, "
                f"study_id={study_id}, optimization_id={optimization_id}) to which "
                f"this result belongs has benchmarks (with ids={benchmark_ids}) "
                f"associated with it and so cannot be deleted. Delete the benchmarks "
                f"first and then try again."
            )

        db.delete(db_optimization_result)

    @staticmethod
    def db_to_model(
        db_optimization_result: models.OptimizationResult,
    ) -> results.OptimizationResult:

        optimization_id = db_optimization_result.parent.identifier
        study_id = db_optimization_result.parent.parent.identifier
        project_id = db_optimization_result.parent.parent.parent.identifier

        # noinspection PyTypeChecker
        db_objective_function = {
            x.iteration: x.value for x in db_optimization_result.objective_function
        }

        statistics = defaultdict(list)

        # noinspection PyTypeChecker
        for db_statistic in db_optimization_result.statistics:
            statistics[db_statistic.iteration].append(db_statistic)

        # noinspection PyTypeChecker
        optimization_result = results.OptimizationResult(
            project_id=project_id,
            study_id=study_id,
            id=optimization_id,
            objective_function=db_objective_function,
            refit_force_field=db_optimization_result.refit_force_field,
            statistics=statistics,
        )

        return optimization_result
