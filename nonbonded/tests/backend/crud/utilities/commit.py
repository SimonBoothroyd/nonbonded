from typing import Tuple

from sqlalchemy.orm import Session

from nonbonded.backend.database.crud.datasets import DataSetCRUD
from nonbonded.backend.database.crud.projects import ProjectCRUD
from nonbonded.library.models.datasets import DataSet, DataSetCollection
from nonbonded.library.models.projects import Optimization, Project, Study
from nonbonded.tests.backend.crud.utilities.creation import (
    create_data_set,
    create_empty_project,
    create_empty_study,
    create_optimization,
)


def commit_data_set(db: Session, unique_id: str = "data_set-1") -> DataSet:
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


def commit_project(db: Session) -> Project:
    """Creates a new project and commits it the current session.

    Parameters
    ----------
    db
        The current data base session.
    """
    db_project = ProjectCRUD.create(db, create_empty_project("project-1"))

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
    project = create_empty_project("project-1")
    project.studies = [create_empty_study(project.id, "study-1")]

    db_project = ProjectCRUD.create(db, project)
    db.add(db_project)
    db.commit()

    project = ProjectCRUD.db_to_model(db_project)
    return project, project.studies[0]


def commit_optimization(
    db: Session,
) -> Tuple[Project, Study, Optimization, DataSetCollection]:
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

    study = create_empty_study("project-1", "study-1")
    study.optimizations = [
        create_optimization("project-1", "study-1", "optimization-1", training_set_ids)
    ]

    project = create_empty_project(study.project_id)
    project.studies = [study]

    db_project = ProjectCRUD.create(db, project)
    db.add(db_project)
    db.commit()

    project = ProjectCRUD.db_to_model(db_project)
    return project, study, study.optimizations[0], training_set
