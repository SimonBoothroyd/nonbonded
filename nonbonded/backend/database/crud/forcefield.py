from sqlalchemy.orm import Session

from nonbonded.backend.database import models
from nonbonded.library.models import forcefield


class ParameterCRUD:
    @staticmethod
    def create(db: Session, parameter: forcefield.Parameter) -> models.Parameter:
        db_parameter = models.Parameter.unique(db, models.Parameter(**parameter.dict()))
        return db_parameter


class ForceFieldCRUD:
    @staticmethod
    def delete(db: Session, force_field: models.ForceField):

        # Check if the force field still has parents.
        # noinspection PyUnresolvedReferences
        if len(force_field.sub_studies) > 0 or len(force_field.results) > 0:
            return

        db.delete(force_field)
