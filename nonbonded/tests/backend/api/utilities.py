import abc
import copy
from typing import Dict, Optional, Tuple, Type, TypeVar

import pytest
from fastapi.testclient import TestClient
from requests import HTTPError
from sqlalchemy.orm import Session

from nonbonded.backend.database.crud.datasets import DataSetCRUD, QCDataSetCRUD
from nonbonded.backend.database.crud.projects import BenchmarkCRUD, ProjectCRUD
from nonbonded.backend.database.crud.results import (
    BenchmarkResultCRUD,
    OptimizationResultCRUD,
)
from nonbonded.library.models import BaseREST
from nonbonded.library.models.datasets import (
    DataSet,
    DataSetCollection,
    QCDataSet,
    QCDataSetCollection,
)
from nonbonded.library.models.projects import Benchmark, Optimization, Project, Study
from nonbonded.library.models.results import BenchmarkResult, OptimizationResult
from nonbonded.library.models.targets import EvaluatorTarget, RechargeTarget
from nonbonded.library.utilities.exceptions import UnsupportedEndpointError
from nonbonded.tests.utilities.comparison import compare_pydantic_models
from nonbonded.tests.utilities.factory import (
    create_benchmark,
    create_benchmark_result,
    create_data_set,
    create_evaluator_target,
    create_force_field,
    create_optimization,
    create_optimization_result,
    create_project,
    create_qc_data_set,
    create_recharge_target,
    create_study,
)

T = TypeVar("T", bound="BaseREST")


def commit_data_set(db: Session, unique_id: str = "data-set-1") -> DataSet:
    """Creates a new data set and commits it the current session.

    Parameters
    ----------
    db
        The current data base session.
    unique_id
        The id to assign to the data set.
    """
    db_data_set = DataSetCRUD.create(db, create_data_set(unique_id))

    db.add(db_data_set)
    db.commit()

    return DataSetCRUD.db_to_model(db_data_set)


def commit_data_set_collection(db: Session) -> DataSetCollection:
    """Commits two data sets to the current session and returns
    them in a collection object.

    Parameters
    ----------
    db
        The current database session.
    """

    # Create the training set.
    data_set_ids = ["data-set-1", "data-set-2"]

    data_sets = [commit_data_set(db, x) for x in data_set_ids]
    data_set_collection = DataSetCollection(data_sets=data_sets)

    return data_set_collection


def commit_qc_data_set(db: Session, unique_id: str = "qc-data-set-1") -> QCDataSet:
    """Creates a new QC data set and commits it the current session.

    Parameters
    ----------
    db
        The current data base session.
    unique_id
        The id to assign to the QC data set.
    """
    db_qc_data_set = QCDataSetCRUD.create(db, create_qc_data_set(unique_id))

    db.add(db_qc_data_set)
    db.commit()

    return QCDataSetCRUD.db_to_model(db_qc_data_set)


def commit_qc_data_set_collection(db: Session) -> QCDataSetCollection:
    """Commits two QC data sets to the current session and returns
    them in a collection object.

    Parameters
    ----------
    db
        The current database session.
    """

    # Create the training set.
    qc_data_set_ids = ["qc-data-set-1", "qc-data-set-2"]

    qc_data_sets = [commit_qc_data_set(db, x) for x in qc_data_set_ids]
    qc_data_set_collection = QCDataSetCollection(data_sets=qc_data_sets)

    return qc_data_set_collection


def commit_project(db: Session) -> Project:
    """Creates a new project and commits it the current session.

    Parameters
    ----------
    db
        The current data base session.
    """
    db_project = ProjectCRUD.create(db, create_project("project-1"))

    db.add(db_project)
    db.commit()

    return ProjectCRUD.db_to_model(db_project)


def commit_study(db: Session) -> Tuple[Project, Study]:
    """Commits a new project to the current session and appends an empty
    study onto it.

    Parameters
    ----------
    db
        The current data base session.
    """
    project = create_project("project-1")
    project.studies = [create_study(project.id, "study-1")]

    db_project = ProjectCRUD.create(db, project)
    db.add(db_project)
    db.commit()

    project = ProjectCRUD.db_to_model(db_project)
    return project, project.studies[0]


def commit_optimization(
    db: Session,
) -> Tuple[Project, Study, Optimization, DataSetCollection, QCDataSetCollection]:
    """Commits a new project and study to the current session and appends an
    empty optimization onto it. Additionally, this function commits two data sets
    to the session to use as the training set.

    Parameters
    ----------
    db
        The current data base session.
    """

    training_set = commit_data_set_collection(db)
    training_set_ids = [x.id for x in training_set.data_sets]

    qc_data_set = commit_qc_data_set_collection(db)
    qc_data_set_ids = [x.id for x in qc_data_set.data_sets]

    study = create_study("project-1", "study-1")
    study.optimizations = [
        create_optimization(
            "project-1",
            "study-1",
            "optimization-1",
            [
                create_evaluator_target("evaluator-target-1", training_set_ids),
                create_recharge_target("recharge-target-1", qc_data_set_ids),
            ],
        )
    ]

    project = create_project(study.project_id)
    project.studies = [study]

    db_project = ProjectCRUD.create(db, project)
    db.add(db_project)
    db.commit()

    project = ProjectCRUD.db_to_model(db_project)
    return project, study, study.optimizations[0], training_set, qc_data_set


def commit_optimization_result(
    db: Session,
) -> Tuple[
    Project,
    Study,
    Optimization,
    DataSetCollection,
    QCDataSetCollection,
    OptimizationResult,
]:
    """Creates a new optimization result and commits it the current session.

    Parameters
    ----------
    db
        The current data base session.
    """

    # Create the parent optimization
    project, study, optimization, data_set, qc_data_set = commit_optimization(db)

    result = create_optimization_result(
        project.id,
        study.id,
        optimization.id,
        [
            target.id
            for target in optimization.targets
            if isinstance(target, EvaluatorTarget)
        ],
        [
            target.id
            for target in optimization.targets
            if isinstance(target, RechargeTarget)
        ],
    )

    db_result = OptimizationResultCRUD.create(db, result)
    db.add(db_result)
    db.commit()

    result = OptimizationResultCRUD.db_to_model(db_result)
    return project, study, optimization, data_set, qc_data_set, result


def commit_benchmark(
    db: Session, target_optimization: bool
) -> Tuple[
    Project,
    Study,
    Benchmark,
    DataSetCollection,
    Optional[Optimization],
    Optional[OptimizationResult],
]:
    """Commits a new project and study to the current session and appends an
    empty benchmark onto it. Additionally, this function commits two data sets
    to the session to use as the training set.

    Parameters
    ----------
    db
        The current data base session.
    target_optimization
        Whether the benchmark should target an optimization. This will be
        created along with a set of optimization results if true.
    """

    optimization_id = None
    optimization_result = None

    force_field = None

    if not target_optimization:

        data_set = commit_data_set_collection(db)
        data_set_ids = [x.id for x in data_set.data_sets]

        force_field = create_force_field()

        project, study = commit_study(db)

    else:

        (
            project,
            study,
            optimization,
            data_set,
            _,
            optimization_result,
        ) = commit_optimization_result(db)
        data_set_ids = [x.id for x in data_set.data_sets]

        optimization_id = optimization.id

    benchmark = create_benchmark(
        project.id,
        study.id,
        "benchmark-1",
        data_set_ids,
        optimization_id,
        force_field,
    )

    db_benchmark = BenchmarkCRUD.create(db, benchmark)
    db.add(db_benchmark)
    db.commit()

    project = ProjectCRUD.read(db, project.id)

    optimization = (
        None if optimization_id is None else project.studies[0].optimizations[0]
    )

    return (
        project,
        project.studies[0],
        project.studies[0].benchmarks[0],
        data_set,
        optimization,
        optimization_result,
    )


def commit_benchmark_result(
    db: Session, for_optimization: bool
) -> Tuple[
    Project,
    Study,
    Benchmark,
    BenchmarkResult,
    DataSetCollection,
    Optional[Optimization],
    Optional[OptimizationResult],
]:
    """Creates a new benchmark result (and all of the required parents such as
    a parent project, study etc.).

    Parameters
    ----------
    db
        The current data base session.
    for_optimization
        Whether the results should be generated for a benchmark against an
        optimization.
    """

    # Create the parent optimization
    (
        project,
        study,
        benchmark,
        data_sets,
        optimization,
        optimization_result,
    ) = commit_benchmark(db, for_optimization)

    result = create_benchmark_result(project.id, study.id, benchmark.id, data_sets)

    db_result = BenchmarkResultCRUD.create(db, result)
    db.add(db_result)
    db.commit()

    # noinspection PyTypeChecker
    result = BenchmarkResultCRUD.db_to_model(db_result)

    return (
        project,
        study,
        benchmark,
        result,
        data_sets,
        optimization,
        optimization_result,
    )


class BaseTestEndpoints(abc.ABC):
    @classmethod
    @abc.abstractmethod
    def _rest_class(cls) -> Type[BaseREST]:
        """The model class associated with the endpoints to test."""
        raise NotImplementedError()

    @classmethod
    @abc.abstractmethod
    def _create_model(
        cls, db: Session, create_dependencies: bool = True
    ) -> Tuple[T, Dict[str, str]]:
        """Creates an instance of the model represented by the endpoints
        being tested but does not commit it to the database. Optionally,
        this function can also commit any parents / dependencies to the database
        which would be required to store the created model.

        Parameters
        ----------
        db
            The current database session.
        create_dependencies
            Whether to commit any of the associated parents / dependencies
            to the database while creating this model.

        Returns
        -------
            The created model.

            The keys which uniquely identify the model.
        """
        raise NotImplementedError()

    @classmethod
    @abc.abstractmethod
    def _perturb_model(cls, model: T):
        """Perturbs a specified model in such a way so as to
        constitute an 'updated' model.

        Parameters
        ----------
        model
            The model to perturb.
        """
        raise NotImplementedError()

    @classmethod
    @abc.abstractmethod
    def _commit_model(cls, db: Session) -> Tuple[T, Dict[str, str]]:
        """Commit the model represented by the endpoints
        being tested to the database, so that it can be
        read, updated or deleted.

        Parameters
        ----------
        db
            The current database session.

        Returns
        -------
            The model which has been committed to the database.

            The keys which uniquely identify the model in the database.
        """
        raise NotImplementedError()

    @classmethod
    @abc.abstractmethod
    def _n_db_models(cls, db: Session) -> int:
        """Returns the number of models of the type represented
        by this endpoint which are stored in the database.

        Parameters
        ----------
        db
            The current database session.
        """
        raise NotImplementedError()

    def test_get(self, rest_client: TestClient, db: Session):

        model, model_keys = self._commit_model(db)

        rest_model = self._rest_class().from_rest(
            **model_keys, requests_class=rest_client
        )

        compare_pydantic_models(model, rest_model)

    def test_post(self, rest_client: TestClient, db: Session):

        model, _ = self._create_model(db)
        rest_model = self._rest_class().upload(model, rest_client)

        compare_pydantic_models(model, rest_model)

    def test_put(self, rest_client: TestClient, db: Session):

        original_model, _ = self._commit_model(db)

        updated_model = copy.deepcopy(original_model)
        self._perturb_model(updated_model)

        try:
            rest_model = self._rest_class().update(updated_model, rest_client)

            with pytest.raises(AssertionError):
                compare_pydantic_models(original_model, rest_model)

        except UnsupportedEndpointError:
            pytest.skip("Unsupported endpoint.")
            raise
        except Exception:
            raise

        compare_pydantic_models(updated_model, rest_model)

    def test_delete(self, rest_client: TestClient, db: Session):

        model, _ = self._commit_model(db)
        assert self._n_db_models(db) == 1

        self._rest_class().delete(model, requests_class=rest_client)
        assert self._n_db_models(db) == 0

    def test_not_found(self, rest_client: TestClient, db: Session):

        model, model_keys = self._create_model(db, False)

        with pytest.raises(HTTPError) as error_info:
            self._rest_class().from_rest(**model_keys, requests_class=rest_client)

        assert error_info.value.response.status_code == 404

        with pytest.raises(HTTPError) as error_info:
            self._rest_class().delete(model, requests_class=rest_client)

        assert error_info.value.response.status_code == 404

        try:
            with pytest.raises(HTTPError) as error_info:
                self._rest_class().update(model, rest_client)

            assert error_info.value.response.status_code == 404

        except UnsupportedEndpointError:
            pass
        except Exception:
            raise
