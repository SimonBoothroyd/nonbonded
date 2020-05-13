from sqlalchemy.orm import Session

from nonbonded.backend.database import models
from nonbonded.backend.database.crud.authors import AuthorCRUD
from nonbonded.backend.database.crud.forcefield import SmirnoffParameterCRUD
from nonbonded.library.models import projects


class OptimizationCRUD:

    @staticmethod
    def read_all(db: Session, project_id: str, study_id: str):

        db_study = StudyCRUD.read_by_identifier(
            db, project_id=project_id, study_id=study_id
        )

        if not db_study:
            return

        return db_study.optimizations

    @staticmethod
    def read_by_identifier(
        db: Session, project_id: str, study_id: str, optimization_id: str
    ):

        db_study = StudyCRUD.read_by_identifier(
            db, project_id=project_id, study_id=study_id
        )

        if not db_study:
            return

        db_optimization = next(
            (x for x in db_study.optimizations if x.id == optimization_id), None
        )

        if not db_optimization:
            return

        return db_optimization

    @staticmethod
    def create(db: Session, optimization: projects.Optimization) -> models.Optimization:

        db_optimization = models.Optimization(
            identifier=optimization.id,
            name=optimization.name,
            description=optimization.description,
            training_set_id=optimization.training_set_id,
            parameters_to_train=[
                SmirnoffParameterCRUD.create(db, x)
                for x in optimization.parameters_to_train
            ],
            force_balance_input=models.ForceBalanceOptions(
                **optimization.force_balance_input.dict()
            ),
            initial_force_field=optimization.initial_force_field
        )

        db.add(db_optimization)
        db.commit()
        db.refresh(db_optimization)

        return db_optimization

    @staticmethod
    def db_to_model(db_optimization: models.Optimization) -> projects.Optimization:

        db_parent_study = db_optimization.parent
        db_parent_project = db_parent_study.parent

        optimization = projects.Optimization(
            id=db_optimization.identifier,
            study_id=db_parent_study.identifier,
            project_id=db_parent_project.identifier,
            name=db_optimization.name,
            description=db_optimization.description,
            training_set_id=db_optimization.training_set_id,
            parameters_to_train=db_optimization.parameters_to_train,
            force_balance_input=db_optimization.force_balance_input,
            initial_force_field=db_optimization.initial_force_field
        )

        return optimization


class BenchmarkCRUD:

    @staticmethod
    def read_all(db: Session, project_id: str, study_id: str):

        db_study = StudyCRUD.read_by_identifier(
            db, project_id=project_id, study_id=study_id
        )

        if not db_study:
            return

        return db_study.benchmarks

    @staticmethod
    def read_by_identifier(
        db: Session, project_id: str, study_id: str, benchmark_id: str
    ):

        db_study = StudyCRUD.read_by_identifier(
            db, project_id=project_id, study_id=study_id
        )

        if not db_study:
            return

        db_benchmark = next(
            (x for x in db_study.benchmarks if x.id == benchmark_id), None
        )

        if not db_benchmark:
            return

        return db_benchmark

    @staticmethod
    def create(db: Session, benchmark: projects.Benchmark) -> models.Benchmark:

        db_benchmark = models.Benchmark(
            identifier=benchmark.id,
            name=benchmark.name,
            description=benchmark.description,
            test_set_id=benchmark.test_set_id,
            optimization_id=benchmark.optimization_id,
            force_field_name=benchmark.force_field_name,
        )

        db.add(db_benchmark)
        db.commit()
        db.refresh(db_benchmark)

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
            force_field_name=db_benchmark.force_field_name
        )

        return benchmark


class StudyCRUD:

    @staticmethod
    def read_all(db: Session, project_id):

        db_studies = (
            db.query(models.Study)
            .filter(models.Study.parent.has(models.Project.identifier == project_id))
            .all()
        )

        return [StudyCRUD.db_to_model(x) for x in db_studies]

    @staticmethod
    def read_by_identifier(db: Session, project_id: str, study_id: str):

        db_study = (
            db.query(models.Study)
            .filter(models.Study.parent.has(models.Project.identifier == project_id))
            .filter(models.Study.identifier == study_id)
            .first()
        )

        if not db_study:
            return

        return StudyCRUD.db_to_model(db_study)

    @staticmethod
    def create(db: Session, study: projects.Study) -> models.Study:

        # noinspection PyTypeChecker
        db_study = models.Study(
            identifier=study.id,
            name=study.name,
            description=study.description,
            optimizations=[OptimizationCRUD.create(db, x) for x in study.optimizations],
            benchmarks=[BenchmarkCRUD.create(db, x) for x in study.benchmarks],
        )

        db.add(db_study)
        db.commit()
        db.refresh(db_study)

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
            benchmarks=[
                BenchmarkCRUD.db_to_model(x) for x in db_study.benchmarks
            ]
        )

        return study


class ProjectCRUD:
    @staticmethod
    def read_all(db: Session, skip: int = 0, limit: int = 100):

        db_projects = db.query(models.Project).offset(skip).limit(limit).all()
        return [ProjectCRUD.db_to_model(x) for x in db_projects]

    @staticmethod
    def read_by_identifier(db: Session, identifier: str):

        db_project = (
            db.query(models.Project)
            .filter(models.Project.identifier == identifier)
            .first()
        )

        if db_project is None:
            return

        return ProjectCRUD.db_to_model(db_project)

    @staticmethod
    def create(db: Session, project: projects.Project) -> models.Project:

        # noinspection PyTypeChecker
        db_project = models.Project(
            identifier=project.id,
            name=project.name,
            description=project.description,
            authors=[AuthorCRUD.create(db, x) for x in project.authors],
            studies=[StudyCRUD.create(db, x) for x in project.studies],
        )

        db.add(db_project)
        db.commit()
        db.refresh(db_project)

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
