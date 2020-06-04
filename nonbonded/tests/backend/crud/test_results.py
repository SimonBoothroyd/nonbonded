import functools

import pytest
from sqlalchemy.orm import Session

from nonbonded.backend.database import models
from nonbonded.backend.database.crud.results import OptimizationResultCRUD
from nonbonded.backend.database.utilities.exceptions import (
    OptimizationNotFoundError,
    OptimizationResultExistsError,
    OptimizationResultNotFoundError,
)
from nonbonded.library.models.results import OptimizationResult
from nonbonded.tests.backend.crud.utilities import create_and_compare_models
from nonbonded.tests.backend.crud.utilities.commit import commit_optimization
from nonbonded.tests.backend.crud.utilities.comparison import (
    compare_optimization_results,
)
from nonbonded.tests.backend.crud.utilities.creation import create_optimization_result


class TestOptimizationResultCRUD:
    @staticmethod
    def create(db: Session) -> OptimizationResult:
        """Creates a new optimization result and commits it the current session.

        Parameters
        ----------
        db
            The current data base session.
        """

        # Create the parent optimization
        project, study, optimization, training_set = commit_optimization(db)

        result = create_optimization_result(project.id, study.id, optimization.id)

        db_result = OptimizationResultCRUD.create(db, result)
        db.add(db_result)
        db.commit()

        return OptimizationResultCRUD.db_to_model(db_result)

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

    def test_not_found(self, db: Session):
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

    def test_delete(self, db: Session):
        """Test that an optimization result can be deleted successfully and also
        that it's children get successfully deleted.
        """

        results = self.create(db)

        assert db.query(models.OptimizationResult.id).count() == 1
        assert db.query(models.ObjectiveFunction.id).count() == 3
        assert db.query(models.OptimizationStatisticsEntry.id).count() == 3
        assert db.query(models.RefitForceField.id).count() == 1

        OptimizationResultCRUD.delete(
            db, results.project_id, results.study_id, results.id
        )

        db.commit()

        assert db.query(models.OptimizationResult.id).count() == 0
        assert db.query(models.ObjectiveFunction.id).count() == 0
        assert db.query(models.OptimizationStatisticsEntry.id).count() == 0
        assert db.query(models.RefitForceField.id).count() == 0

    def test_delete_not_found(self, db: Session):

        with pytest.raises(OptimizationResultNotFoundError):
            OptimizationResultCRUD.delete(db, " ", " ", " ")
