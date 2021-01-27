import abc
import functools
import inspect
from functools import partial
from typing import Callable, Dict, List, Optional, TypeVar, Union

import pytest
from sqlalchemy.orm import Session
from typing_extensions import Protocol

from nonbonded.backend.database.crud.datasets import DataSetCRUD, QCDataSetCRUD
from nonbonded.backend.database.crud.projects import ProjectCRUD
from nonbonded.backend.database.utilities.exceptions import UnableToDeleteError
from nonbonded.tests.utilities.comparison import compare_pydantic_models
from nonbonded.tests.utilities.factory import (
    create_benchmark,
    create_data_set,
    create_evaluator_target,
    create_force_field,
    create_optimization,
    create_project,
    create_qc_data_set,
    create_recharge_target,
    create_study,
)

# noinspection PyTypeChecker
S = TypeVar("S", bound="BaseORM")
# noinspection PyTypeChecker
T = TypeVar("T", bound="Base")


class PaginationCallable(Protocol):
    def __call__(self, db: Session, skip: int = 0, limit: int = 100) -> List[S]:
        ...


ReadAllCallable = Union[
    PaginationCallable,
    Callable[[Session], List[S]],
    partial,
]


def create_and_compare_models(
    db: Session,
    model: S,
    create_function: Callable[[Session, S], T],
    read_all_function: Optional[ReadAllCallable],
    read_function: Union[Callable[[Session], T], partial],
    db_model_to_model: Callable[[S], T],
    n_expected_models: int = 1,
):
    """A generic utility for making sure that a particular
    set of CRUD functions, namely creating and then retrieving
    the created model, work as expected.

    Parameters
    ----------
    db
        The current database session.
    model
        The model to create.
    create_function
        The static function which will create a database
        version of the model (but not add or commit
        it to the current session).
    read_all_function
        A static function which should read all instances
        of the type of created model from the database.
    read_function
        A static function which should read the exact
        model which is to be created from the database.
    db_model_to_model
        A static function which should map a database model
        into a pydantic model.
    n_expected_models
        The number of models expected to be returned by
        the `read_all_function`. It will be assumed that
        the last model in the returned list is the created
        one.

    Raises
    ------
    AssertionError
    """
    from inspect import signature

    db_model = create_function(db, model)
    db.add(db_model)
    db.commit()

    compare_pydantic_models(model, db_model_to_model(db_model))

    if read_all_function is not None:

        read_all_signature = signature(read_all_function)

        if (
            "skip" in read_all_signature.parameters
            and "limit" in read_all_signature.parameters
        ):
            retrieved_models = read_all_function(db, 0, 1000)
        else:
            retrieved_models = read_all_function(db)

        assert len(retrieved_models) == n_expected_models

        db_retrieved_model = retrieved_models[-1]
        assert isinstance(db_retrieved_model, type(model))
        compare_pydantic_models(model, db_retrieved_model)

    db_retrieved_model = read_function(db)
    assert isinstance(db_retrieved_model, type(model))
    compare_pydantic_models(model, db_retrieved_model)


def paginate_models(
    db: Session,
    models_to_create: List[S],
    create_function: Callable[[Session, S], T],
    read_all_function: Callable[[Session, int, int], T],
):
    """A generic utility that ensures that the `read_all` function
    of a particular CRUD can correctly paginate.

    Parameters
    ----------
    db
        The current database session.
    models_to_create
        The models to create and which will be paginated.
    create_function
        The static function which will create a database
        version of a model (but not add or commit
        it to the current session).
    read_all_function
        A static function which should read all instances
        of the type of created model from the database.

    Raises
    ------
    AssertionError
    """

    assert len(models_to_create) > 1

    for model_to_create in models_to_create:
        db.add(create_function(db, model_to_create))

    db.commit()

    for model_index in range(len(models_to_create)):
        retrieved_models = read_all_function(db, model_index, 1)
        assert len(retrieved_models) == 1

        compare_pydantic_models(models_to_create[model_index], retrieved_models[0])


def update_and_compare_model(
    db: Session,
    model_to_update: S,
    update_function: Callable[[Session, S], T],
    read_function: Union[Callable[[Session], T], partial],
    db_model_to_model: Callable[[S], T],
    expected_model: Optional[S] = None,
):
    """Attempts to performs a CRUD update and then ensures that the updated
    model stored in the database matches the expected model.

    Parameters
    ----------
    db
        The current database session.
    model_to_update
        The model to update in the database.
    update_function
        The function to use to update the current database session.
        This function should not commit the update transaction.
    read_function
        The function to use to retrieve the updated model
        from the database.
    db_model_to_model
        A static function which should map a database model
        into a pydantic model.
    expected_model
        The expected state of the model in the database after the
        update. If none is specified, it will be assumed that the
        database model state should match exactly the `model_to_update`.

    Raises
    -------
    AssertionError
    """

    if expected_model is None:
        expected_model = model_to_update

    db_updated_model = update_function(db, model_to_update)
    db.flush()

    compare_pydantic_models(expected_model, db_model_to_model(db_updated_model))

    db.commit()

    db_updated_model = read_function(db)
    compare_pydantic_models(expected_model, db_updated_model)


def create_dependencies(db: Session, dependencies: List[str]):
    """Create any dependencies such as parent studies, projects, or data sets and
    commit them to the database.

    Parameters
    ----------
    db
        The current database session.
    dependencies
        The required dependencies.
    """

    project = None
    data_set_ids = []
    qc_data_set_ids = []

    if "data-set" in dependencies:
        data_set_ids.append("data-set-1")
    if "qc-data-set" in dependencies:
        qc_data_set_ids.append("qc-data-set-1")

    for data_set_id in data_set_ids:
        data_set = create_data_set(data_set_id)
        db_data_set = DataSetCRUD.create(db, data_set)
        db.add(db_data_set)

    for qc_data_set_id in qc_data_set_ids:
        qc_data_set = create_qc_data_set(qc_data_set_id)
        db_qc_data_set = QCDataSetCRUD.create(db, qc_data_set)
        db.add(db_qc_data_set)

    db.commit()

    if (
        "project" in dependencies
        or "study" in dependencies
        or "evaluator-target" in dependencies
        or "recharge-target" in dependencies
        or "benchmark" in dependencies
    ):
        project = create_project("project-1")

    if (
        "study" in dependencies
        or "evaluator-target" in dependencies
        or "recharge-target" in dependencies
        or "benchmark" in dependencies
    ):
        project.studies = [create_study(project.id, "study-1")]

    if "evaluator-target" in dependencies or "recharge-target" in dependencies:

        targets = []

        if "evaluator-target" in dependencies:
            targets.append(
                create_evaluator_target("evaluator-target-1", ["data-set-1"])
            )
        if "recharge-target" in dependencies:
            targets.append(
                create_recharge_target("recharge-target-1", ["qc-data-set-1"])
            )

        optimization = create_optimization(
            project.id, project.studies[0].id, "optimization-1", targets
        )

        project.studies[0].optimizations = [optimization]

    if "benchmark" in dependencies:
        benchmark = create_benchmark(
            project.id,
            project.studies[0].id,
            "benchmark-1",
            ["data-set-1"],
            None,
            create_force_field(),
        )

        project.studies[0].benchmarks = [benchmark]

    if project is not None:
        db_project = ProjectCRUD.create(db, project)
        db.add(db_project)
        db.commit()


class BaseCRUDTest(abc.ABC):
    @classmethod
    @abc.abstractmethod
    def crud_class(cls):
        """The CRUD class being tested."""

    @classmethod
    @abc.abstractmethod
    def dependencies(cls) -> List[str]:
        """The names of the dependencies which will be
        created by ``create_dependencies``."""

    @classmethod
    @abc.abstractmethod
    def create_model(cls, include_children: bool = False, index: int = 1):
        """Creates an instance of the model represented by the CRUD class."""

    @classmethod
    @abc.abstractmethod
    def model_to_read_kwargs(cls, model: S) -> Dict[str, str]:
        """Retrieves the kwargs which identify a particular model."""

    @classmethod
    @abc.abstractmethod
    def model_to_read_all_kwargs(cls, model: S) -> Dict[str, str]:
        """Retrieves the kwargs which identify a particular model."""

    @classmethod
    @abc.abstractmethod
    def not_found_error(cls):
        """Returns the expected error to be raised when a model cannot be found
        with the specified ids.
        """

    @classmethod
    @abc.abstractmethod
    def already_exists_error(cls):
        """Returns the expected error to be raised when a model already exists."""

    @classmethod
    @abc.abstractmethod
    def check_has_deleted(cls, db: Session):
        """Checks that a model created with dependants has been deleted."""

    @pytest.mark.parametrize("include_children", [True, False])
    def test_create_read(
        self, db: Session, include_children: bool, model=None, db_to_model=None
    ):
        """Test that an empty model (i.e. one without any dependants) can be created
        and then read back out again while maintaining the integrity of the data.
        """

        if model is None:

            create_dependencies(db, self.dependencies())
            model = self.create_model(include_children)

        if db_to_model is None:
            db_to_model = self.crud_class().db_to_model

        create_and_compare_models(
            db,
            model,
            self.crud_class().create,
            (
                None
                if not hasattr(self.crud_class(), "read_all")
                else functools.partial(
                    self.crud_class().read_all, **self.model_to_read_all_kwargs(model)
                )
            ),
            functools.partial(
                self.crud_class().read, **self.model_to_read_kwargs(model)
            ),
            db_to_model,
        )

        # Make sure projects with duplicate ids cannot be added.
        with pytest.raises(self.already_exists_error()):
            self.crud_class().create(db, model)

    def test_pagination(self, db: Session):
        """Test that the limit and skip options to read_all have been
        implemented correctly.
        """

        read_all_arguments, *_ = inspect.getfullargspec(self.crud_class().read_all)

        if "skip" not in read_all_arguments and "limit" not in read_all_arguments:

            pytest.skip(
                f"The {self.crud_class().__name__} does not support pagination."
            )

        create_dependencies(db, self.dependencies())

        models_to_create = [self.create_model(index=index + 1) for index in range(3)]

        paginate_models(
            db=db,
            models_to_create=models_to_create,
            create_function=self.crud_class().create,
            read_all_function=self.crud_class().read_all,
        )

    @abc.abstractmethod
    def test_update(self, db: Session, perturbation, database_checks, expected_raise):

        create_dependencies(db, self.dependencies())
        model = self.create_model(True)

        db_model = self.crud_class().create(db, model)
        db.add(db_model)
        db.commit()

        # Perturb the model.
        for key, value in perturbation.items():
            setattr(model, key, value)

        # Attempt to update the model in the database and check
        # the update was successful.
        with expected_raise:

            update_and_compare_model(
                db,
                model,
                self.crud_class().update,
                functools.partial(
                    self.crud_class().read, **self.model_to_read_kwargs(model)
                ),
                self.crud_class().db_to_model,
            )

        # Perform checks of the databases integrity after the update.
        # This mainly includes check to ensure that orphaned objects are
        # properly removed.
        assert all(check for check in database_checks(db))

    def test_update_not_found(self, db: Session):

        model = self.create_model()

        with pytest.raises(self.not_found_error()):
            self.crud_class().update(db, model)

    def test_delete(self, db: Session):

        create_dependencies(db, self.dependencies())
        model = self.create_model(True)

        db_model = self.crud_class().create(db, model)
        db.add(db_model)
        db.commit()

        self.crud_class().delete(db, **self.model_to_read_kwargs(model))
        db.commit()

        self.check_has_deleted(db)

    def test_delete_not_found(self, db: Session):

        model = self.create_model()

        with pytest.raises(self.not_found_error()):
            self.crud_class().delete(db, **self.model_to_read_kwargs(model))

    @abc.abstractmethod
    def test_delete_with_dependent(
        self, db: Session, create_dependant, delete_dependant
    ):
        """Tests that trying to delete a data set which is referenced by a
        dependant yields the correct error.
        """

        # Create the set to delete.
        model = self.create_model()
        db.add(self.crud_class().create(db, model))
        db.commit()

        # Create the dependant.
        create_dependant(db)

        with pytest.raises(UnableToDeleteError):
            self.crud_class().delete(db, model.id)

        # After deleting the dependant the set should be deletable.
        delete_dependant(db)
        db.commit()
        self.crud_class().delete(db, model.id)
        db.commit()

        self.check_has_deleted(db)

    @abc.abstractmethod
    def test_missing_dependencies(
        self, db: Session, dependencies: List[str], expected_error
    ):
        """Tests that the correct error is raised when a required dependency is
        missing."""

        dependencies = [
            dependency
            for dependency in self.dependencies()
            if dependency not in dependencies
        ]

        create_dependencies(db, dependencies)
        model = self.create_model(True)

        with pytest.raises(expected_error):
            self.crud_class().create(db, model)
