import abc
from collections import defaultdict
from typing import Any, Dict, Type, Union

from sqlalchemy.orm import Session, object_session

from nonbonded.backend.database import models
from nonbonded.backend.database.crud.forcefield import ForceFieldCRUD
from nonbonded.backend.database.crud.projects import BenchmarkCRUD, OptimizationCRUD
from nonbonded.backend.database.crud.targets import (
    EvaluatorTargetResultCRUD,
    RechargeTargetResultCRUD,
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
    TargetNotFoundError,
    TargetResultNotFoundError,
    TargetResultTypeError,
    UnableToDeleteError,
    UnableToUpdateError,
)
from nonbonded.library.models import results


class ResultCRUD(abc.ABC):
    """A base class for optimization and benchmark CRUD methods."""

    @classmethod
    @abc.abstractmethod
    def parent_crud(cls) -> Type[Union[BenchmarkCRUD, OptimizationCRUD]]:
        """Returns the CRUD class associated with the parent of the results class."""

    @classmethod
    @abc.abstractmethod
    def orm_class(
        cls,
    ) -> Type[Union[models.BenchmarkResult, models.OptimizationResult]]:
        """Returns the ORM class associated with the CRUD."""

    @classmethod
    @abc.abstractmethod
    def rest_class(
        cls,
    ) -> Union[Type[results.BenchmarkResult], Type[results.OptimizationResult]]:
        """Returns the REST class associated with the CRUD."""

    @classmethod
    @abc.abstractmethod
    def exists_error(
        cls,
    ) -> Union[Type[BenchmarkResultExistsError], Type[OptimizationResultExistsError]]:
        """The error to raise when attempting to add an entry which already exists in
        the database."""

    @classmethod
    @abc.abstractmethod
    def parent_not_found_error(
        cls,
    ) -> Union[Type[BenchmarkNotFoundError], Type[OptimizationNotFoundError]]:
        """The error to raise when attempting to retrieve an entry which could not
        be found in the database."""

    @classmethod
    @abc.abstractmethod
    def not_found_error(
        cls,
    ) -> Union[
        Type[BenchmarkResultNotFoundError], Type[OptimizationResultNotFoundError]
    ]:
        """The error to raise when attempting to retrieve an entry which could not
        be found in the database."""

    @classmethod
    def query(cls, db: Session, project_id: str, study_id: str, sub_study_id: str):

        db_sub_study = cls.parent_crud().query(db, project_id, study_id, sub_study_id)

        if not db_sub_study:
            return None

        return db_sub_study.results

    @classmethod
    def _check_dependencies_exist(
        cls, db: Session, sub_study_result: results.SubStudyResult
    ) -> models.SubStudy:

        db_parent = cls.parent_crud().query(
            db,
            sub_study_result.project_id,
            sub_study_result.study_id,
            sub_study_result.id,
        )

        if db_parent is None:
            raise cls.parent_not_found_error()(
                sub_study_result.project_id,
                sub_study_result.study_id,
                sub_study_result.id,
            )

        return db_parent

    @classmethod
    @abc.abstractmethod
    def _check_has_dependants(
        cls,
        db: Session,
        db_sub_study_result: Union[models.BenchmarkResult, models.OptimizationResult],
        error_type: Type[Union[UnableToUpdateError, UnableToDeleteError]],
    ):
        """A method to check whether all of the required dependencies are present in the
        database and raise the correct exception if not."""

    @classmethod
    def create(
        cls, db: Session, sub_study_result: results.SubStudyResult
    ) -> Union[models.BenchmarkResult, models.OptimizationResult]:

        # Make sure the results have not already been uploaded.
        if (
            cls.query(
                db,
                sub_study_result.project_id,
                sub_study_result.study_id,
                sub_study_result.id,
            )
            is not None
        ):

            raise cls.exists_error()(
                sub_study_result.project_id,
                sub_study_result.study_id,
                sub_study_result.id,
            )

        # Make sure all of the required dependencies exist in the database.
        db_parent = cls._check_dependencies_exist(db, sub_study_result)

        # noinspection PyArgumentList
        db_model = cls.orm_class()(
            **cls._db_model_kwargs(
                sub_study_result=sub_study_result, db_parent=db_parent
            )
        )

        return db_model

    @classmethod
    def read(cls, db: Session, project_id: str, study_id: str, sub_study_id: str):

        db_parent = cls.parent_crud().query(db, project_id, study_id, sub_study_id)

        if not db_parent:
            raise cls.parent_not_found_error()(project_id, study_id, sub_study_id)

        if not db_parent.results:
            return None

        return cls.db_to_model(db_parent.results)

    @classmethod
    def delete(cls, db: Session, project_id: str, study_id: str, sub_study_id: str):

        db_model = cls.query(db, project_id, study_id, sub_study_id)

        if not db_model:
            raise cls.not_found_error()(project_id, study_id, sub_study_id)

        cls._check_has_dependants(db, db_model, UnableToDeleteError)
        db.delete(db_model)

    @classmethod
    @abc.abstractmethod
    def _model_kwargs(
        cls,
        db_sub_study_result: Union[models.BenchmarkResult, models.OptimizationResult],
    ) -> Dict[str, Any]:
        """Returns the kwargs to create a new model with."""

        db_parent = db_sub_study_result.parent

        db_parent_study = db_parent.parent
        db_parent_project = db_parent_study.parent

        return dict(
            id=db_parent.identifier,
            study_id=db_parent_study.identifier,
            project_id=db_parent_project.identifier,
        )

    @classmethod
    @abc.abstractmethod
    def _db_model_kwargs(
        cls,
        sub_study_result: results.SubStudyResult,
        db_parent: models.SubStudy,
    ) -> Dict[str, Any]:
        """Returns the kwargs to create a new database model with."""
        raise NotImplementedError()

    @classmethod
    def db_to_model(
        cls, db_sub_study: Union[models.BenchmarkResult, models.OptimizationResult]
    ) -> results.SubStudyResult:

        sub_study = cls.rest_class()(**cls._model_kwargs(db_sub_study))
        return sub_study


class BenchmarkResultCRUD(ResultCRUD):
    @classmethod
    def parent_crud(cls):
        return BenchmarkCRUD

    @classmethod
    def orm_class(cls):
        return models.BenchmarkResult

    @classmethod
    def rest_class(cls):
        return results.BenchmarkResult

    @classmethod
    def exists_error(cls):
        return BenchmarkResultExistsError

    @classmethod
    def parent_not_found_error(cls):
        return BenchmarkNotFoundError

    @classmethod
    @abc.abstractmethod
    def not_found_error(cls):
        return BenchmarkResultNotFoundError

    @classmethod
    def _check_dependencies_exist(
        cls, db: Session, sub_study_result: results.BenchmarkResult
    ) -> models.SubStudy:

        db_parent = super(BenchmarkResultCRUD, cls)._check_dependencies_exist(
            db, sub_study_result
        )

        # Make sure that all of the data set entries referenced by the results
        # exist.
        reference_ids = [
            x.reference_id for x in sub_study_result.data_set_result.result_entries
        ]

        found_ids = (
            db.query(models.DataSetEntry.id)
            .filter(models.DataSetEntry.id.in_(reference_ids))
            .all()
        )

        missing_ids = {*reference_ids} - {x for (x,) in found_ids}

        if len(missing_ids) > 0:
            missing_ids_string = ", ".join(map(str, missing_ids))

            raise DataSetEntryNotFound(
                f"The benchmark results contains results entries which reference "
                f"non-existent data set entries: {missing_ids_string}."
            )

        return db_parent

    @classmethod
    def _check_has_dependants(cls, db, db_sub_study_result, error_type):
        pass

    @classmethod
    def _model_kwargs(
        cls, db_sub_study_result: models.BenchmarkResult
    ) -> Dict[str, Any]:

        db = object_session(db_sub_study_result)

        db_results_entries = (
            db.query(models.DataSetResultEntry)
            .filter(
                models.DataSetResultEntry.parent_id
                == db_sub_study_result.data_set_result.id
            )
            .all()
        )
        db_statistic_entries = (
            db.query(models.DataSetStatistic)
            .filter(
                models.DataSetStatistic.parent_id
                == db_sub_study_result.data_set_result.id
            )
            .all()
        )

        result_kwargs = dict(
            **super(BenchmarkResultCRUD, cls)._model_kwargs(db_sub_study_result),
            data_set_result=results.DataSetResult(
                result_entries=db_results_entries,
                statistic_entries=db_statistic_entries,
            ),
        )

        return result_kwargs

    @classmethod
    def _db_model_kwargs(cls, sub_study_result, db_parent) -> Dict[str, Any]:

        # noinspection PyTypeChecker
        return dict(
            parent=db_parent,
            data_set_result=models.DataSetResult(
                statistic_entries=[
                    models.DataSetStatistic(
                        **{
                            **statistic.dict(),
                            "statistic_type": statistic.dict()["statistic_type"].value,
                        },
                    )
                    for statistic in sub_study_result.data_set_result.statistic_entries
                ],
                result_entries=[
                    models.DataSetResultEntry(**x.dict())
                    for x in sub_study_result.data_set_result.result_entries
                ],
            ),
        )


class OptimizationResultCRUD(ResultCRUD):
    @classmethod
    def parent_crud(cls):
        return OptimizationCRUD

    @classmethod
    def orm_class(cls):
        return models.OptimizationResult

    @classmethod
    def rest_class(cls):
        return results.OptimizationResult

    @classmethod
    def exists_error(cls):
        return OptimizationResultExistsError

    @classmethod
    def parent_not_found_error(cls):
        return OptimizationNotFoundError

    @classmethod
    @abc.abstractmethod
    def not_found_error(cls):
        return OptimizationResultNotFoundError

    @classmethod
    def _check_dependencies_exist(
        cls, db: Session, sub_study_result: results.OptimizationResult
    ) -> models.SubStudy:

        # noinspection PyTypeChecker
        db_parent: models.Optimization = super(
            OptimizationResultCRUD, cls
        )._check_dependencies_exist(db, sub_study_result)

        # Make sure the refit force field does not yet exist
        # in the database. This should not be possible.
        if (
            db.query(models.ForceField.inner_content)
            .filter(
                models.ForceField.inner_content
                == sub_study_result.refit_force_field.inner_content
            )
            .count()
            > 0
        ):
            raise ForceFieldExistsError(
                sub_study_result.project_id,
                sub_study_result.study_id,
                sub_study_result.id,
            )

        # Make sure the results of all targets have been provided.
        expected_target_results = {
            **{
                db_target.identifier: results.EvaluatorTargetResult
                for db_target in db_parent.evaluator_targets
            },
            **{
                db_target.identifier: results.RechargeTargetResult
                for db_target in db_parent.recharge_targets
            },
        }
        found_target_results = {
            target_id: type(target)
            for target_id, target in next(
                iter(sub_study_result.target_results.values())
            ).items()
        }

        missing_target_ids = {*expected_target_results} - {*found_target_results}
        extra_target_result_ids = {*found_target_results} - {*expected_target_results}

        if len(missing_target_ids) > 0:
            raise TargetResultNotFoundError(
                sub_study_result.project_id,
                sub_study_result.study_id,
                sub_study_result.id,
                missing_target_ids,
            )
        if len(extra_target_result_ids) > 0:
            raise TargetNotFoundError(
                sub_study_result.project_id,
                sub_study_result.study_id,
                sub_study_result.id,
                extra_target_result_ids,
            )

        for target_id in expected_target_results:

            if expected_target_results[target_id] != found_target_results[target_id]:

                raise TargetResultTypeError(
                    sub_study_result.project_id,
                    sub_study_result.study_id,
                    sub_study_result.id,
                    target_id,
                    found_target_results[target_id],
                    expected_target_results[target_id],
                )

        return db_parent

    @classmethod
    def _check_has_dependants(
        cls, db, db_sub_study_result: models.OptimizationResult, error_type
    ):

        OptimizationCRUD.check_has_children(db_sub_study_result.parent, error_type)

    @classmethod
    def delete(cls, db: Session, project_id: str, study_id: str, sub_study_id: str):

        db_optimization_result = OptimizationResultCRUD.query(
            db, project_id, study_id, sub_study_id
        )

        # Make sure to delete the refit force field if uploaded.
        if db_optimization_result is not None:

            refit_force_field = db_optimization_result.refit_force_field
            db_optimization_result.refit_force_field = None

            ForceFieldCRUD.delete(db, refit_force_field)

        super(OptimizationResultCRUD, cls).delete(
            db, project_id, study_id, sub_study_id
        )

    @classmethod
    def _db_model_kwargs(
        cls,
        sub_study_result: results.OptimizationResult,
        db_parent: models.Optimization,
    ) -> Dict[str, Any]:

        db = object_session(db_parent)

        # noinspection PyTypeChecker
        return dict(
            parent=db_parent,
            evaluator_target_results=[
                EvaluatorTargetResultCRUD.model_to_db(
                    sub_study_result.target_results[iteration][db_target.identifier],
                    iteration,
                    db_target,
                )
                for db_target in db_parent.evaluator_targets
                for iteration in sub_study_result.target_results
            ],
            recharge_target_results=[
                RechargeTargetResultCRUD.model_to_db(
                    sub_study_result.target_results[iteration][db_target.identifier],
                    iteration,
                    db_target,
                )
                for db_target in db_parent.recharge_targets
                for iteration in sub_study_result.target_results
            ],
            refit_force_field=models.ForceField.unique(
                db,
                models.ForceField(
                    inner_content=sub_study_result.refit_force_field.inner_content
                ),
            ),
        )

    @classmethod
    def _model_kwargs(
        cls, db_sub_study_result: models.OptimizationResult
    ) -> Dict[str, Any]:

        target_results = defaultdict(dict)

        # noinspection PyTypeChecker
        for db_target_result in db_sub_study_result.recharge_target_results:

            target_results[db_target_result.iteration][
                db_target_result.target.identifier
            ] = RechargeTargetResultCRUD.db_to_model(db_target_result)

        # noinspection PyTypeChecker
        for db_target_result in db_sub_study_result.evaluator_target_results:

            target_results[db_target_result.iteration][
                db_target_result.target.identifier
            ] = EvaluatorTargetResultCRUD.db_to_model(db_target_result)

        return dict(
            **super(OptimizationResultCRUD, cls)._model_kwargs(db_sub_study_result),
            target_results=target_results,
            refit_force_field=db_sub_study_result.refit_force_field,
        )
