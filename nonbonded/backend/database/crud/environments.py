from sqlalchemy.orm import Session

from nonbonded.backend.database import models
from nonbonded.library.models import environments


class ChemicalEnvironmentCRUD:
    @staticmethod
    def create(
        db: Session, environment: environments.ChemicalEnvironment
    ) -> models.ChemicalEnvironment:

        existing_instance = (
            db.query(models.ChemicalEnvironment)
            .filter(models.ChemicalEnvironment.value == environment.value)
            .first()
        )

        if existing_instance:
            return existing_instance

        db_environment = models.ChemicalEnvironment(value=environment.value)

        db.add(db_environment)
        db.commit()
        db.refresh(db_environment)

        return db_environment
