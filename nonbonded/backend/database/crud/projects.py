from sqlalchemy.orm import Session

from nonbonded.backend.database import models
from nonbonded.backend.database.crud.datasets import TargetDataSetCRUD
from nonbonded.backend.database.crud.forcefield import SmirnoffParameterCRUD
from nonbonded.library.models import projects


class AuthorCRUD:
    @staticmethod
    def read_all(db: Session, skip: int = 0, limit: int = 100):
        return db.query(models.Author).offset(skip).limit(limit).all()

    @staticmethod
    def create(db: Session, author: projects.Author) -> models.Author:

        existing_instance = (
            db.query(models.Author)
            .filter(models.Author.name == author.name)
            .filter(models.Author.email == author.email)
            .filter(models.Author.institute == author.institute)
            .first()
        )

        if existing_instance:
            return existing_instance

        db_author = models.Author(**author.dict())
        db.add(db_author)
        db.commit()
        db.refresh(db_author)

        return db_author


class OptimizationCRUD:
    @staticmethod
    def create(db: Session, optimization: projects.Optimization) -> models.Optimization:

        db_optimization = models.Optimization(
            title=optimization.title,
            identifier=optimization.identifier,
            description=optimization.description,
            parameters_to_train=[
                SmirnoffParameterCRUD.create(db, x)
                for x in optimization.parameters_to_train
            ],
            target_training_set=TargetDataSetCRUD.create(
                db, optimization.target_training_set
            ),
        )

        db.add(db_optimization)
        db.commit()
        db.refresh(db_optimization)

        return db_optimization

    @staticmethod
    def db_to_model(db_optimization: models.Optimization) -> projects.Optimization:

        optimization = projects.Optimization(
            title=db_optimization.title,
            identifier=db_optimization.identifier,
            description=db_optimization.description,
            parameters_to_train=db_optimization.parameters_to_train,
            target_training_set=TargetDataSetCRUD.db_to_model(
                db_optimization.target_training_set
            ),
        )

        return optimization


class StudyCRUD:
    @staticmethod
    def create(db: Session, study: projects.Study) -> models.Study:

        optimizations = [OptimizationCRUD.create(db, x) for x in study.optimizations]

        # noinspection PyTypeChecker
        db_study = models.Study(
            title=study.title,
            identifier=study.identifier,
            description=study.description,
            optimizations=optimizations,
            optimization_inputs=models.ForceBalanceOptions(
                **study.optimization_inputs.dict()
            ),
            target_test_set=TargetDataSetCRUD.create(db, study.target_test_set),
            initial_force_field=study.initial_force_field,
        )

        db.add(db_study)
        db.commit()
        db.refresh(db_study)

        return db_study

    @staticmethod
    def db_to_model(db_study: models.Study) -> projects.Study:

        study = projects.Study(
            title=db_study.title,
            identifier=db_study.identifier,
            description=db_study.description,
            optimizations=[
                OptimizationCRUD.db_to_model(x) for x in db_study.optimizations
            ],
            optimization_inputs=db_study.optimization_inputs,
            target_test_set=TargetDataSetCRUD.db_to_model(db_study.target_test_set),
            initial_force_field=db_study.initial_force_field,
        )

        return study


class ProjectCRUD:
    @staticmethod
    def read_all(db: Session, skip: int = 0, limit: int = 100):

        projects = db.query(models.Project).offset(skip).limit(limit).all()
        return [ProjectCRUD.db_to_model(x) for x in projects]

    @staticmethod
    def read_by_identifier(db: Session, identifier: str):
        return (
            db.query(models.Project)
            .filter(models.Project.identifier == identifier)
            .first()
        )

    @staticmethod
    def create(db: Session, project: projects.Project) -> models.Project:

        # noinspection PyTypeChecker
        db_project = models.Project(
            title=project.title,
            identifier=project.identifier,
            abstract=project.abstract,
            authors=[AuthorCRUD.create(db, x) for x in project.authors],
            studies=[StudyCRUD.create(db, x) for x in project.studies],
        )

        db.add(db_project)
        db.commit()
        db.refresh(db_project)

        return db_project

    @staticmethod
    def db_to_model(db_project: models.Project) -> projects.Project:

        project = projects.Project(
            title=db_project.title,
            identifier=db_project.identifier,
            abstract=db_project.abstract,
            authors=db_project.authors,
            studies=[StudyCRUD.db_to_model(x) for x in db_project.studies],
        )

        return project
