from sqlalchemy.orm import Session

from nonbonded.backend.database import models
from nonbonded.backend.database.crud.projects import BenchmarkCRUD, OptimizationCRUD
from nonbonded.backend.database.utilities.exceptions import (
    BenchmarkNotFoundError,
    BenchmarkResultExistsError,
    OptimizationNotFoundError,
    OptimizationResultExistsError,
)
from nonbonded.library.models import results


class ResultEntryCRUD:
    @staticmethod
    def create(results_entry: results.ResultsEntry) -> models.ResultsEntry:

        results_entry_dict = results_entry.dict()
        results_entry_dict["components"] = [
            models.ResultsComponent(**component.dict())
            for component in results_entry.components
        ]

        db_results_entry = models.ResultsEntry(**results_entry_dict)
        return db_results_entry

    @staticmethod
    def db_to_model(db_results_entry: models.ResultsEntry) -> results.ResultsEntry:

        # noinspection PyTypeChecker
        results_entry = models.ResultsEntry(
            property_type=db_results_entry.property_type,
            temperature=db_results_entry.temperature,
            pressure=db_results_entry.pressure,
            phase=db_results_entry.phase,
            unit=db_results_entry.unit,
            reference_value=db_results_entry.reference_value,
            reference_std_error=db_results_entry.reference_std_error,
            estimated_value=db_results_entry.estimated_value,
            estimated_std_error=db_results_entry.estimated_std_error,
            category=db_results_entry.category,
            components=db_results_entry.components,
        )

        return results_entry


class StatisticsEntryCRUD:
    @staticmethod
    def create(statistics_entry: results.StatisticsEntry) -> models.StatisticsEntry:
        # noinspection PyTypeChecker
        db_statistics_entry = models.StatisticsEntry(**statistics_entry.dict())

        return db_statistics_entry

    @staticmethod
    def db_to_model(
        db_statistics_entry: models.StatisticsEntry,
    ) -> results.StatisticsEntry:

        return db_statistics_entry


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
                StatisticsEntryCRUD.create(x)
                for x in benchmark_result.statistic_entries
            ],
            results_entries=[
                ResultEntryCRUD.create(x) for x in benchmark_result.results_entries
            ],
        )

        return db_benchmark_result

    @staticmethod
    def read_all(db: Session, skip: int = 0, limit: int = 100):

        benchmark_results = (
            db.query(models.BenchmarkResult).offset(skip).limit(limit).all()
        )
        return [BenchmarkResultCRUD.db_to_model(x) for x in benchmark_results]

    @staticmethod
    def read(db: Session, project_id: str, study_id: str, benchmark_id: str):

        db_benchmark = BenchmarkCRUD.query(db, project_id, study_id, benchmark_id)

        if not db_benchmark:
            raise BenchmarkNotFoundError(project_id, study_id, benchmark_id)

        return BenchmarkResultCRUD.db_to_model(db_benchmark.results)

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
        db_benchmark_result: models.BenchmarkResult,
    ) -> results.BenchmarkResult:

        benchmark_id = db_benchmark_result.parent.identifier
        study_id = db_benchmark_result.parent.parent.identifier
        project_id = db_benchmark_result.parent.parent.parent.identifier

        # noinspection PyTypeChecker
        benchmark_result = results.BenchmarkResult(
            project_id=project_id,
            study_id=study_id,
            id=benchmark_id,
            statistic_entries=[
                StatisticsEntryCRUD.db_to_model(x)
                for x in db_benchmark_result.statistic_entries
            ],
            results_entries=[
                ResultEntryCRUD.db_to_model(x)
                for x in db_benchmark_result.results_entries
            ],
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
                for i, x in enumerate(optimization_result.objective_function)
            ],
            refit_force_field=models.RefitForceField(
                inner_xml=optimization_result.refit_force_field.inner_xml
            ),
        )

        return db_optimization_result

    @staticmethod
    def read_all(db: Session, skip: int = 0, limit: int = 100):

        optimization_results = (
            db.query(models.OptimizationResult).offset(skip).limit(limit).all()
        )
        return [OptimizationResultCRUD.db_to_model(x) for x in optimization_results]

    @staticmethod
    def read(db: Session, project_id: str, study_id: str, optimization_id: str):

        db_optimization = OptimizationCRUD.query(
            db, project_id, study_id, optimization_id
        )

        if not db_optimization:
            raise OptimizationNotFoundError(project_id, study_id, optimization_id)

        return OptimizationResultCRUD.db_to_model(db_optimization.results)

    @staticmethod
    def delete(db: Session, project_id: str, study_id: str, optimization_id: str):

        db_optimization_result = OptimizationResultCRUD.query(
            db, project_id, study_id, optimization_id
        )

        if not db_optimization_result:
            raise OptimizationResultExistsError(project_id, study_id, optimization_id)

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

        optimization_result = results.OptimizationResult(
            project_id=project_id,
            study_id=study_id,
            id=optimization_id,
            objective_function=[
                db_objective_function[i] for i in range(len(db_objective_function))
            ],
            refit_force_field=db_optimization_result.refit_force_field,
        )

        return optimization_result
