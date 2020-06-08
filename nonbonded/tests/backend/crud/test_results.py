import functools

import pytest
from sqlalchemy.orm import Session

from nonbonded.backend.database import models
from nonbonded.backend.database.crud.projects import BenchmarkCRUD, OptimizationCRUD
from nonbonded.backend.database.crud.results import (
    BenchmarkResultCRUD,
    OptimizationResultCRUD,
)
from nonbonded.backend.database.utilities.exceptions import (
    BenchmarkNotFoundError,
    BenchmarkResultExistsError,
    BenchmarkResultNotFoundError,
    DataSetEntryNotFound,
    ForceFieldExistsError,
    OptimizationNotFoundError,
    OptimizationResultExistsError,
    OptimizationResultNotFoundError,
    UnableToDeleteError,
)
from nonbonded.tests.backend.crud.utilities import create_and_compare_models
from nonbonded.tests.backend.crud.utilities.commit import (
    commit_benchmark,
    commit_benchmark_result,
    commit_data_set,
    commit_optimization,
    commit_optimization_result,
    commit_study,
)
from nonbonded.tests.backend.crud.utilities.comparison import (
    compare_benchmark_results,
    compare_optimization_results,
)
from nonbonded.tests.backend.crud.utilities.create import (
    create_benchmark_result,
    create_force_field,
    create_optimization,
    create_optimization_result,
)


class TestOptimizationResultCRUD:
    def test_create_read(self, db: Session):
        """Test that an empty project (i.e. one without studies) can be created, and then
        read back out again while maintaining the integrity of the data.
        """

        project, study, optimization, _ = commit_optimization(db)
        result = create_optimization_result(project.id, study.id, optimization.id)

        create_and_compare_models(
            db,
            result,
            OptimizationResultCRUD.create,
            None,
            functools.partial(
                OptimizationResultCRUD.read,
                project_id=project.id,
                study_id=study.id,
                optimization_id=optimization.id,
            ),
            compare_optimization_results,
        )

        # Make sure results with duplicate parents cannot be added.
        with pytest.raises(OptimizationResultExistsError):
            OptimizationResultCRUD.create(db, result)

    def test_missing_parent(self, db: Session):
        """Test that an exception is raised when an optimization result is added
        but the parent optimization cannot be found.
        """

        optimization_result = create_optimization_result(
            "project-1", "study-1", "optimization-1"
        )

        with pytest.raises(OptimizationNotFoundError):

            create_and_compare_models(
                db,
                optimization_result,
                OptimizationResultCRUD.create,
                None,
                OptimizationResultCRUD.read,
                compare_optimization_results,
            )

    def test_read_not_found(self, db: Session):
        """Test that an exception is raised when the parent optimization
        of a result is not found, or None when no results have been submitted yet.
        """

        with pytest.raises(OptimizationNotFoundError):
            OptimizationResultCRUD.read(db, " ", " ", " ")

        project, study, optimization, _ = commit_optimization(db)

        assert (
            OptimizationResultCRUD.read(db, project.id, study.id, optimization.id)
            is None
        )

    def test_duplicate_refit_force_field(self, db: Session):
        """Test that an exception is raised when uploading a refit
        force field when that force field already is present.
        """

        data_set = commit_data_set(db)
        project, study = commit_study(db)

        optimization = create_optimization(
            project.id, study.id, "optimization-1", [data_set.id]
        )
        optimization.initial_force_field = create_force_field("Refit")

        db.add(OptimizationCRUD.create(db, optimization))
        db.commit()

        result = create_optimization_result(project.id, study.id, optimization.id)
        result.refit_force_field = create_force_field("Refit")

        # Make sure results with duplicate parents cannot be added.
        with pytest.raises(ForceFieldExistsError):
            OptimizationResultCRUD.create(db, result)

    def test_delete(self, db: Session):
        """Test that an optimization result can be deleted successfully and also
        that it's children get successfully deleted.
        """

        _, _, _, _, results = commit_optimization_result(db)

        assert db.query(models.OptimizationResult.id).count() == 1
        assert db.query(models.ObjectiveFunction.id).count() == 3
        assert db.query(models.OptimizationStatisticsEntry.id).count() == 3
        assert db.query(models.ForceField.id).count() == 2

        OptimizationResultCRUD.delete(
            db, results.project_id, results.study_id, results.id
        )

        db.commit()

        assert db.query(models.OptimizationResult.id).count() == 0
        assert db.query(models.ObjectiveFunction.id).count() == 0
        assert db.query(models.OptimizationStatisticsEntry.id).count() == 0
        assert db.query(models.ForceField.id).count() == 1

        # Make sure the right force field as deleted
        remaining_force_field = db.query(models.ForceField.inner_xml).first()
        assert "Refit" not in remaining_force_field

    def test_delete_not_found(self, db: Session):

        with pytest.raises(OptimizationResultNotFoundError):
            OptimizationResultCRUD.delete(db, " ", " ", " ")

    def test_delete_with_benchmark(self, db: Session):
        """Test that optimization results which are being targeted by a benchmark
        can only be deleted once the benchmark has been deleted.
        """

        (
            project,
            study,
            benchmark,
            data_set,
            optimization,
            optimization_result,
        ) = commit_benchmark(db, True)

        with pytest.raises(UnableToDeleteError) as error_info:
            OptimizationResultCRUD.delete(db, project.id, study.id, optimization.id)

        assert "benchmark" in str(error_info.value)

        # Delete the benchmark and results and try again.
        BenchmarkCRUD.delete(db, project.id, study.id, benchmark.id)
        db.commit()

        OptimizationResultCRUD.delete(db, project.id, study.id, optimization.id)
        db.commit()


class TestBenchmarkResultCRUD:
    def test_create_read_target_force_field(self, db: Session):
        """Test that a set of benchmark results can be generated for
        a benchmark which targets a force field directly.
        """

        project, study, benchmark, data_set, _, _ = commit_benchmark(db, False)
        result = create_benchmark_result(project.id, study.id, benchmark.id, data_set)

        create_and_compare_models(
            db,
            result,
            BenchmarkResultCRUD.create,
            None,
            functools.partial(
                BenchmarkResultCRUD.read,
                project_id=project.id,
                study_id=study.id,
                benchmark_id=benchmark.id,
            ),
            compare_benchmark_results,
        )

        # Make sure results with duplicate parents cannot be added.
        with pytest.raises(BenchmarkResultExistsError):
            BenchmarkResultCRUD.create(db, result)

    def test_create_target_optimization(self, db: Session):
        """Test that a set of benchmark results can be generated for
        a benchmark which targets a force field directly.
        """

        project, study, benchmark, data_set, _, _ = commit_benchmark(db, True)
        result = create_benchmark_result(project.id, study.id, benchmark.id, data_set)

        create_and_compare_models(
            db,
            result,
            BenchmarkResultCRUD.create,
            None,
            functools.partial(
                BenchmarkResultCRUD.read,
                project_id=project.id,
                study_id=study.id,
                benchmark_id=benchmark.id,
            ),
            compare_benchmark_results,
        )

    def test_create_bad_reference_id(self, db: Session):
        """Test that a set of benchmark results can be generated for
        a benchmark which targets a force field directly.
        """

        project, study, benchmark, data_set, _, _ = commit_benchmark(db, True)
        result = create_benchmark_result(project.id, study.id, benchmark.id, data_set)

        for results_entry in result.analysed_result.results_entries:
            results_entry.reference_id = -1

        with pytest.raises(DataSetEntryNotFound):
            BenchmarkResultCRUD.create(db, result)

    def test_missing_parent(self, db: Session):
        """Test that an exception is raised when a benchmark result is added
        but the parent benchmark cannot be found.
        """

        benchmark_result = create_benchmark_result(
            "project-1", "study-1", "benchmark-1", commit_data_set(db)
        )

        with pytest.raises(BenchmarkNotFoundError):
            BenchmarkResultCRUD.create(db, benchmark_result)

    def test_read_not_found(self, db: Session):
        """Test that an exception is raised when the parent benchmark
        of a result is not found, or None when no results have been submitted yet.
        """

        with pytest.raises(BenchmarkNotFoundError):
            BenchmarkResultCRUD.read(db, " ", " ", " ")

        project, study, benchmark, _, _, _ = commit_benchmark(db, False)

        assert BenchmarkResultCRUD.read(db, project.id, study.id, benchmark.id) is None

    def test_delete(self, db: Session):
        """Test that a benchmark result can be deleted successfully and also
        that it's children get successfully deleted.
        """

        _, _, _, results, _, _, _ = commit_benchmark_result(db, False)

        assert db.query(models.BenchmarkResult.id).count() == 1
        assert db.query(models.BenchmarkResultsEntry.id).count() == 2
        assert db.query(models.BenchmarkStatisticsEntry.id).count() == 2

        BenchmarkResultCRUD.delete(db, results.project_id, results.study_id, results.id)

        db.commit()

        assert db.query(models.BenchmarkResult.id).count() == 0
        assert db.query(models.BenchmarkResultsEntry.id).count() == 0
        assert db.query(models.BenchmarkStatisticsEntry.id).count() == 0

    def test_delete_not_found(self, db: Session):

        with pytest.raises(BenchmarkResultNotFoundError):
            BenchmarkResultCRUD.delete(db, " ", " ", " ")
