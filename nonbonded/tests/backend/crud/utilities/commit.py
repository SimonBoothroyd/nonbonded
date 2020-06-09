from typing import Optional, Tuple

from sqlalchemy.orm import Session

from nonbonded.backend.database.crud.datasets import DataSetCRUD
from nonbonded.backend.database.crud.projects import BenchmarkCRUD, ProjectCRUD
from nonbonded.backend.database.crud.results import (
    BenchmarkResultCRUD,
    OptimizationResultCRUD,
)
from nonbonded.library.models.datasets import DataSet, DataSetCollection
from nonbonded.library.models.projects import Benchmark, Optimization, Project, Study
from nonbonded.library.models.results import BenchmarkResult, OptimizationResult
from nonbonded.tests.backend.crud.utilities.create import (
    create_benchmark,
    create_benchmark_result,
    create_data_set,
    create_empty_project,
    create_empty_study,
    create_force_field,
    create_optimization,
    create_optimization_result,
)


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


def commit_optimization_result(
    db: Session,
) -> Tuple[Project, Study, Optimization, DataSetCollection, OptimizationResult]:
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

    result = OptimizationResultCRUD.db_to_model(db_result)
    return project, study, optimization, training_set, result


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
            optimization_result,
        ) = commit_optimization_result(db)
        data_set_ids = [x.id for x in data_set.data_sets]

        optimization_id = optimization.id

    benchmark = create_benchmark(
        project.id, study.id, "benchmark-1", data_set_ids, optimization_id, force_field,
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

    db_benchmark = BenchmarkCRUD.query(db, project.id, study.id, benchmark.id)

    db_result = BenchmarkResultCRUD.create(db, result)
    db.add(db_result)
    db.commit()

    # noinspection PyTypeChecker
    result = BenchmarkResultCRUD.db_to_model(
        db_benchmark, db_result.results_entries, db_result.statistic_entries
    )

    return (
        project,
        study,
        benchmark,
        result,
        data_sets,
        optimization,
        optimization_result,
    )
