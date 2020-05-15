from sqlalchemy.orm import Session

from nonbonded.backend.database import models
from nonbonded.backend.database.crud.authors import AuthorCRUD
from nonbonded.backend.database.crud.datasets import DataSetCRUD
from nonbonded.backend.database.crud.forcefield import ParameterCRUD
from nonbonded.backend.database.utilities.exceptions import (
    BenchmarkExistsError,
    BenchmarkNotFoundError,
    DataSetNotFoundError,
    OptimizationExistsError,
    OptimizationNotFoundError,
    ProjectExistsError,
    ProjectNotFoundError,
    StudyExistsError,
    StudyNotFoundError,
)
from nonbonded.library.models import projects


class OptimizationCRUD:
    @staticmethod
    def query_optimization(
        db: Session, project_id: str, study_id: str, optimization_id: str
    ):

        db_optimization = (
            db.query(models.Optimization)
            .filter(models.Optimization.identifier == optimization_id)
            .join(models.Study)
            .filter(models.Study.identifier == study_id)
            .join(models.Project)
            .filter(models.Project.identifier == project_id)
            .first()
        )

        return db_optimization

    @staticmethod
    def read_all(db: Session, project_id: str, study_id: str):

        db_study = StudyCRUD.query_study(db, project_id=project_id, study_id=study_id)

        if not db_study:
            raise StudyNotFoundError(project_id, study_id)

        return [OptimizationCRUD.db_to_model(x) for x in db_study.optimizations]

    @staticmethod
    def read_by_identifier(
        db: Session, project_id: str, study_id: str, optimization_id: str
    ):

        db_optimization = OptimizationCRUD.query_optimization(
            db, project_id, study_id, optimization_id
        )

        if not db_optimization:
            raise OptimizationNotFoundError(project_id, study_id, optimization_id)

        return OptimizationCRUD.db_to_model(db_optimization)

    @staticmethod
    def create(db: Session, optimization: projects.Optimization) -> models.Optimization:

        if (
            OptimizationCRUD.query_optimization(
                db, optimization.project_id, optimization.study_id, optimization.id
            )
            is not None
        ):

            raise OptimizationExistsError(
                optimization.project_id, optimization.study_id, optimization.id
            )

        if not DataSetCRUD.query_data_set(db, optimization.training_set_id):
            raise DataSetNotFoundError(optimization.training_set_id)

        # noinspection PyTypeChecker
        db_optimization = models.Optimization(
            identifier=optimization.id,
            name=optimization.name,
            description=optimization.description,
            training_set_id=optimization.training_set_id,
            parameters_to_train=[
                ParameterCRUD.create(db, x) for x in optimization.parameters_to_train
            ],
            force_balance_input=models.ForceBalanceOptions(
                **optimization.force_balance_input.dict()
            ),
            initial_force_field=optimization.initial_force_field,
            denominators=[
                models.Denominator(property_type=key, value=value) for key, value in
                optimization.denominators.items()
            ],
            priors=[
                models.Prior(parameter_type=key, value=value) for key, value in
                optimization.priors.items()
            ]
        )

        return db_optimization

    @staticmethod
    def db_to_model(db_optimization: models.Optimization) -> projects.Optimization:

        db_parent_study = db_optimization.parent
        db_parent_project = db_parent_study.parent

        # noinspection PyTypeChecker
        optimization = projects.Optimization(
            id=db_optimization.identifier,
            study_id=db_parent_study.identifier,
            project_id=db_parent_project.identifier,
            name=db_optimization.name,
            description=db_optimization.description,
            training_set_id=db_optimization.training_set_id,
            parameters_to_train=db_optimization.parameters_to_train,
            force_balance_input=db_optimization.force_balance_input,
            initial_force_field=db_optimization.initial_force_field,
            denominators={
                x.property_type: x.value for x in db_optimization.denominators
            },
            priors={
                x.parameter_type: x.value for x in db_optimization.priors
            }
        )

        return optimization


class BenchmarkCRUD:
    @staticmethod
    def query_benchmark(db: Session, project_id: str, study_id: str, benchmark_id: str):

        db_benchmark = (
            db.query(models.Benchmark)
            .filter(models.Benchmark.identifier == benchmark_id)
            .join(models.Study)
            .filter(models.Study.identifier == study_id)
            .join(models.Project)
            .filter(models.Project.identifier == project_id)
            .first()
        )

        return db_benchmark

    @staticmethod
    def read_all(db: Session, project_id: str, study_id: str):

        db_study = StudyCRUD.query_study(db, project_id=project_id, study_id=study_id)

        if not db_study:
            raise StudyNotFoundError(project_id, study_id)

        return [BenchmarkCRUD.db_to_model(x) for x in db_study.benchmarks]

    @staticmethod
    def read_by_identifier(
        db: Session, project_id: str, study_id: str, benchmark_id: str
    ):

        db_benchmark = BenchmarkCRUD.query_benchmark(
            db, project_id, study_id, benchmark_id
        )

        if not db_benchmark:
            raise BenchmarkNotFoundError(project_id, study_id, benchmark_id)

        return BenchmarkCRUD.db_to_model(db_benchmark)

    @staticmethod
    def create(db: Session, benchmark: projects.Benchmark) -> models.Benchmark:

        if (
            BenchmarkCRUD.query_benchmark(
                db, benchmark.project_id, benchmark.study_id, benchmark.id
            )
            is not None
        ):

            raise BenchmarkExistsError(
                benchmark.project_id, benchmark.study_id, benchmark.id
            )

        if not DataSetCRUD.query_data_set(db, benchmark.test_set_id):
            raise DataSetNotFoundError(benchmark.test_set_id)

        db_benchmark = models.Benchmark(
            identifier=benchmark.id,
            name=benchmark.name,
            description=benchmark.description,
            test_set_id=benchmark.test_set_id,
            optimization_id=benchmark.optimization_id,
            force_field_name=benchmark.force_field_name,
        )

        return db_benchmark

    @staticmethod
    def db_to_model(db_benchmark: models.Benchmark) -> projects.Benchmark:

        db_parent_study = db_benchmark.parent
        db_parent_project = db_parent_study.parent

        benchmark = projects.Benchmark(
            id=db_benchmark.identifier,
            study_id=db_parent_study.identifier,
            project_id=db_parent_project.identifier,
            name=db_benchmark.name,
            description=db_benchmark.description,
            test_set_id=db_benchmark.test_set_id,
            optimization_id=db_benchmark.optimization_id,
            force_field_name=db_benchmark.force_field_name,
        )

        return benchmark


class StudyCRUD:
    @staticmethod
    def query_study(db: Session, project_id: str, study_id: str):

        db_study = (
            db.query(models.Study)
            .filter(models.Study.identifier == study_id)
            .join(models.Project)
            .filter(models.Project.identifier == project_id)
            .first()
        )

        return db_study

    @staticmethod
    def read_all(db: Session, project_id):

        db_project = ProjectCRUD.query_project(db, project_id)

        if not db_project:
            raise ProjectNotFoundError(project_id)

        return [StudyCRUD.db_to_model(x) for x in db_project.studies]

    @staticmethod
    def read_by_identifier(db: Session, project_id: str, study_id: str):

        db_study = StudyCRUD.query_study(db, project_id, study_id)

        if not db_study:
            raise StudyNotFoundError(project_id, study_id)

        return StudyCRUD.db_to_model(db_study)

    @staticmethod
    def create(db: Session, study: projects.Study) -> models.Study:

        if StudyCRUD.query_study(db, study.project_id, study.id) is not None:
            raise StudyExistsError(study.project_id, study.id)

        # noinspection PyTypeChecker
        db_study = models.Study(
            identifier=study.id,
            name=study.name,
            description=study.description,
            optimizations=[OptimizationCRUD.create(db, x) for x in study.optimizations],
            benchmarks=[BenchmarkCRUD.create(db, x) for x in study.benchmarks],
        )

        return db_study

    @staticmethod
    def db_to_model(db_study: models.Study) -> projects.Study:

        db_parent_project = db_study.parent

        # noinspection PyTypeChecker
        study = projects.Study(
            id=db_study.identifier,
            project_id=db_parent_project.identifier,
            name=db_study.name,
            description=db_study.description,
            optimizations=[
                OptimizationCRUD.db_to_model(x) for x in db_study.optimizations
            ],
            benchmarks=[BenchmarkCRUD.db_to_model(x) for x in db_study.benchmarks],
        )

        return study


class ProjectCRUD:
    @staticmethod
    def query_project(db: Session, project_id: str):

        db_project = (
            db.query(models.Project)
            .filter(models.Project.identifier == project_id)
            .first()
        )

        return db_project

    @staticmethod
    def read_all(db: Session, skip: int = 0, limit: int = 100):

        db_projects = db.query(models.Project).offset(skip).limit(limit).all()
        return [ProjectCRUD.db_to_model(x) for x in db_projects]

    @staticmethod
    def read_by_identifier(db: Session, project_id: str):

        db_project = ProjectCRUD.query_project(db, project_id)

        if db_project is None:
            raise ProjectNotFoundError(project_id)

        return ProjectCRUD.db_to_model(db_project)

    @staticmethod
    def create(db: Session, project: projects.Project) -> models.Project:

        if ProjectCRUD.query_project(db, project.id) is not None:
            raise ProjectExistsError(project.id)

        # noinspection PyTypeChecker
        db_project = models.Project(
            identifier=project.id,
            name=project.name,
            description=project.description,
            authors=[AuthorCRUD.create(db, x) for x in project.authors],
            studies=[StudyCRUD.create(db, x) for x in project.studies],
        )

        return db_project

    @staticmethod
    def db_to_model(db_project: models.Project) -> projects.Project:

        # noinspection PyTypeChecker
        project = projects.Project(
            id=db_project.identifier,
            name=db_project.name,
            description=db_project.description,
            authors=db_project.authors,
            studies=[StudyCRUD.db_to_model(x) for x in db_project.studies],
        )

        return project
