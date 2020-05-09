from sqlalchemy.orm import Session

from nonbonded.backend.database import models
from nonbonded.library.models import forcefield


class SmirnoffParameterCRUD:
    @staticmethod
    def create(
        db: Session, parameter: forcefield.SmirnoffParameter
    ) -> models.SmirnoffParameter:

        existing_instance = (
            db.query(models.SmirnoffParameter)
            .filter(models.SmirnoffParameter.handler_type == parameter.handler_type)
            .filter(models.SmirnoffParameter.smirks == parameter.smirks)
            .filter(models.SmirnoffParameter.attribute_name == parameter.attribute_name)
            .first()
        )

        if existing_instance:
            return existing_instance

        db_parameter = models.SmirnoffParameter(**parameter.dict())
        db.add(db_parameter)
        db.commit()
        db.refresh(db_parameter)

        return db_parameter
