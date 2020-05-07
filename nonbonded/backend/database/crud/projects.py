from sqlalchemy.orm import Session

from nonbonded.backend.database.models import projects as models
from nonbonded.library.models import projects as schemas


def read_projects(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Project).offset(skip).limit(limit).all()


def read_project_by_identifier(db: Session, identifier: str):
    return (
        db.query(models.Project).filter(models.Project.identifier == identifier).first()
    )


def create_project(db: Session, project: schemas.Project):

    db_project = models.Project.from_schema(project)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project
