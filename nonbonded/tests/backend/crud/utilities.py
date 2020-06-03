from functools import partial
from typing import Callable, Optional, TypeVar, Union, List
from typing_extensions import Protocol

import numpy
from sqlalchemy.orm import Session

from nonbonded.backend.database import models
from nonbonded.library.models.authors import Author
from nonbonded.library.models.datasets import Component, DataSet, DataSetEntry
from nonbonded.library.models.projects import Project
from nonbonded.library.models.projects import Study, Optimization, Benchmark

S = TypeVar("S", bound="BaseORM")
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
    compare_function: Callable[[Union[S, T], Union[S, T]], None],
    n_expected_models: int = 1
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

        if len(read_all_signature.parameters) == 3:
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


def create_author():
    """Creates an author objects with

        * name="Fake Name"
        * email="fake@email.com"
        * institute="None"

    Returns
    -------
    Author
        The created author
    """
    return Author(name="Fake Name", email="fake@email.com", institute="None")


def compare_authors(
    author_1: Union[Author, models.Author], author_2: Union[Author, models.Author],
):
    """Compares two author models.

    Parameters
    ----------
    author_1
        The first author to compare.
    author_2
        The second author to compare.

    Raises
    -------
    AssertionError
    """
    assert author_2.name == author_1.name
    assert author_2.email == author_1.email
    assert author_2.institute == author_1.institute


def create_data_set(data_set_id: str):
    """Creates a single author data set which contains a single
    density data entry. The entry contains two components, an
    aqueous solvent (x=1) and a methanol solute (n=1).

    Parameters
    ----------
    data_set_id: str
        The id to assign to the data set.

    Returns
    -------
    DataSet
    """

    author = create_author()

    data_entry = DataSetEntry(
        id=None,
        property_type="Density",
        temperature=298.15,
        pressure=101.325,
        value=1.0,
        std_error=0.1,
        doi=" ",
        components=[
            Component(smiles="O", mole_fraction=1.0, exact_amount=0, role="Solvent"),
            Component(smiles="CO", mole_fraction=0.0, exact_amount=1, role="Solute"),
        ],
    )

    data_set = DataSet(
        id=data_set_id, description=" ", authors=[author], entries=[data_entry]
    )

    return data_set


def compare_data_sets(
    data_set_1: Union[DataSet, models.DataSet],
    data_set_2: Union[DataSet, models.DataSet],
):
    """Compares two data set models.

    Parameters
    ----------
    data_set_1
        The first data set to compare.
    data_set_2
        The second data set to compare.

    Raises
    -------
    AssertionError
    """
    assert data_set_2.id == data_set_1.id
    assert data_set_2.description == data_set_1.description

    assert len(data_set_2.authors) == 1
    compare_authors(data_set_1.authors[0], data_set_2.authors[0])

    assert len(data_set_2.entries) == 1
    original_entry = data_set_1.entries[0]
    retrieved_entry = data_set_2.entries[0]

    assert numpy.isclose(retrieved_entry.temperature, original_entry.temperature)
    assert numpy.isclose(retrieved_entry.pressure, original_entry.pressure)

    assert retrieved_entry.phase == original_entry.phase

    assert numpy.isclose(retrieved_entry.value, original_entry.value)
    assert numpy.isclose(retrieved_entry.std_error, original_entry.std_error)

    assert retrieved_entry.doi == original_entry.doi

    assert len(retrieved_entry.components) == len(original_entry.components)

    matched_components = []

    for component in original_entry.components:

        matched_component = next(
            (x for x in retrieved_entry.components if x.smiles == component.smiles),
            None,
        )

        assert matched_component is not None

        matched_components.append((component, matched_component))

    for original_component, retrieved_component in matched_components:
        assert retrieved_component.smiles == original_component.smiles
        assert retrieved_component.mole_fraction == original_component.mole_fraction
        assert retrieved_component.exact_amount == original_component.exact_amount
        assert retrieved_component.role == original_component.role


def create_empty_project(project_id: str) -> Project:
    """Creates an empty projects with a single author and no studies
    with a specified id.

    Parameters
    ----------
    project_id
        The id to assign to the project.
    """
    return Project(
        id=project_id, name=project_id, description=" ", authors=[create_author()]
    )


def compare_projects(
    project_1: Union[Project, models.Project], project_2: Union[Project, models.Project]
):
    """Compare if two project models are equivalent.

    Parameters
    ----------
    project_1
        The first project to compare.
    project_2
        The second project to compare.

    Raises
    ------
    AssertionError
    """

    id_1 = project_1.id if isinstance(project_1, Project) else project_1.identifier
    id_2 = project_2.id if isinstance(project_2, Project) else project_2.identifier

    assert id_1 == id_2

    assert project_1.name == project_2.name
    assert project_1.description == project_2.description

    assert len(project_1.authors) == len(project_2.authors)

    authors_1 = {x.email: x for x in project_1.authors}
    authors_2 = {x.email: x for x in project_2.authors}

    assert {*authors_1} == {*authors_2}

    for email in authors_1:
        compare_authors(authors_1[email], authors_2[email])

    assert len(project_1.studies) == len(project_2.studies)

    studies_1 = {
        x.id if isinstance(x, Study) else x.identifier: x
        for x in project_1.studies
    }
    studies_2 = {
        x.id if isinstance(x, Study) else x.identifier: x
        for x in project_1.studies
    }

    assert {*studies_1} == {*studies_2}

    for study_id in studies_1:
        compare_studies(studies_1[study_id], studies_2[study_id])


def create_empty_study(project_id: str, study_id: str) -> Study:
    """Creates a study with a specified id and no optimizations or
    benchmarks.

    Parameters
    ----------
    project_id
        The id of the parent project.
    study_id
        The id to assign to the study.
    """
    return Study(id=study_id, project_id=project_id, name=" ", description=" ")


def compare_studies(
    study_1: Union[Study, models.Study], study_2: Union[Study, models.Study]
):
    """Compare if two study models are equivalent.

    Parameters
    ----------
    study_1
        The first study to compare.
    study_2
        The second study to compare.

    Raises
    ------
    AssertionError
    """

    id_1 = study_1.id if isinstance(study_1, Study) else study_1.identifier
    id_2 = study_2.id if isinstance(study_2, Study) else study_2.identifier

    assert id_1 == id_2

    assert study_1.name == study_2.name
    assert study_1.description == study_2.description

    # TODO: Compare optimizations
    assert len(study_1.optimizations) == len(study_2.optimizations)

    optimizations_1 = {
        x.id if isinstance(x, Optimization) else x.identifier: x
        for x in study_1.optimizations
    }
    optimizations_2 = {
        x.id if isinstance(x, Optimization) else x.identifier: x
        for x in study_1.optimizations
    }

    assert {*optimizations_1} == {*optimizations_2}

    # TODO: Compare benchmarks
    assert len(study_1.benchmarks) == len(study_2.benchmarks)

    benchmarks_1 = {
        x.id if isinstance(x, Benchmark) else x.identifier: x
        for x in study_1.benchmarks
    }
    benchmarks_2 = {
        x.id if isinstance(x, Benchmark) else x.identifier: x
        for x in study_1.benchmarks
    }

    assert {*benchmarks_1} == {*benchmarks_2}
