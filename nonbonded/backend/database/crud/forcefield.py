from sqlalchemy.orm import Session

from nonbonded.backend.database import models
from nonbonded.backend.database.utilities.exceptions import (
    OptimizationNotFoundError,
    RefitForceFieldExistsError,
    RefitForceFieldNotFoundError,
)
from nonbonded.library.models import forcefield


class ParameterCRUD:
    @staticmethod
    def create(db: Session, parameter: forcefield.Parameter) -> models.Parameter:

        db_parameter = models.Parameter.as_unique(db, **parameter.dict())
        return db_parameter


class RefitForceFieldCRUD:
    @staticmethod
    def read_all(db: Session, skip: int = 0, limit: int = 100):

        force_fields = db.query(models.RefitForceField).offset(skip).limit(limit).all()
        return [RefitForceFieldCRUD.db_to_model(x) for x in force_fields]

    @staticmethod
    def read_by_optimization(
        db: Session, project_id: str, study_id: str, optimization_id: str
    ):

        from nonbonded.backend.database.crud.projects import OptimizationCRUD

        db_optimization = OptimizationCRUD.query_optimization(
            db, project_id, study_id, optimization_id
        )

        if not db_optimization:
            raise OptimizationNotFoundError(project_id, study_id, optimization_id)

        db_force_field = db_optimization.refit_force_field

        if not db_force_field:
            raise RefitForceFieldNotFoundError(project_id, study_id, optimization_id)

        return RefitForceFieldCRUD.db_to_model(db_force_field)

    @staticmethod
    def create(
        db: Session, refit_force_field: forcefield.RefitForceField
    ) -> models.RefitForceField:

        from nonbonded.backend.database.crud.projects import OptimizationCRUD

        db_optimization = OptimizationCRUD.query_optimization(
            db,
            refit_force_field.project_id,
            refit_force_field.study_id,
            refit_force_field.optimization_id,
        )

        if not db_optimization:

            raise OptimizationNotFoundError(
                refit_force_field.project_id,
                refit_force_field.study_id,
                refit_force_field.optimization_id,
            )

        if db_optimization.refit_force_field is not None:

            raise RefitForceFieldExistsError(
                refit_force_field.project_id,
                refit_force_field.study_id,
                refit_force_field.optimization_id,
            )

        db_force_field = models.RefitForceField(
            inner_xml=refit_force_field.inner_xml, optimization_id=db_optimization.id,
        )
        return db_force_field

    @staticmethod
    def db_to_model(
        db_force_field: models.RefitForceField,
    ) -> forcefield.RefitForceField:

        optimization_id = db_force_field.optimization.identifier
        study_id = db_force_field.optimization.parent.identifier
        project_id = db_force_field.optimization.parent.parent.identifier

        force_field = forcefield.RefitForceField(
            inner_xml=db_force_field.inner_xml,
            project_id=project_id,
            study_id=study_id,
            optimization_id=optimization_id,
        )

        return force_field
