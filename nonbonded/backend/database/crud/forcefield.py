from sqlalchemy.orm import Session

from nonbonded.backend.database import models
from nonbonded.library.models import forcefield


class ParameterCRUD:
    @staticmethod
    def create(db: Session, parameter: forcefield.Parameter) -> models.Parameter:
        db_parameter = models.Parameter.as_unique(db, **parameter.dict())
        return db_parameter
