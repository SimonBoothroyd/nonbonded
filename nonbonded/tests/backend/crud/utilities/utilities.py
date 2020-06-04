from functools import partial
from typing import Callable, List, Optional, TypeVar, Union

from sqlalchemy.orm import Session
from typing_extensions import Protocol

S = TypeVar("S", bound="BaseORM")
T = TypeVar("T", bound="Base")


class PaginationCallable(Protocol):
    def __call__(self, db: Session, skip: int = 0, limit: int = 100) -> List[S]:
        ...


ReadAllCallable = Union[
    PaginationCallable, Callable[[Session], List[S]], partial,
]


def create_and_compare_models(
    db: Session,
    model: S,
    create_function: Callable[[Session, S], T],
    read_all_function: Optional[ReadAllCallable],
    read_function: Union[Callable[[Session], T], partial],
    compare_function: Callable[[Union[S, T], Union[S, T]], None],
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
    compare_function
        A static function which should compare to models
        of the type to create for exact equality.
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
    compare_function(model, db_model)

    db.add(db_model)
    db.commit()

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
        compare_function(model, db_retrieved_model)

    db_retrieved_model = read_function(db)
    assert isinstance(db_retrieved_model, type(model))
    compare_function(model, db_retrieved_model)


def paginate_models(
    db: Session,
    models_to_create: List[S],
    create_function: Callable[[Session, S], T],
    read_all_function: Callable[[Session, int, int], T],
    compare_function: Callable[[Union[S, T], Union[S, T]], None],
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
    compare_function
        A static function which should compare two models
        for exact equality.

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

        compare_function(models_to_create[model_index], retrieved_models[0])


def update_and_compare_model(
    db: Session,
    model_to_update: S,
    update_function: Callable[[Session, S], T],
    read_function: Union[Callable[[Session], T], partial],
    compare_function: Callable[[Union[S, T], Union[S, T]], None],
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
    compare_function
        A static function which should compare two models
        for exact equality.
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
    compare_function(expected_model, db_updated_model)

    db.commit()

    db_updated_model = read_function(db)
    compare_function(expected_model, db_updated_model)
