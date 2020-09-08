from openff.recharge.conformers import ConformerSettings
from openff.recharge.esp import ESPSettings, PCMSettings
from openff.recharge.grids import GridSettings
from sqlalchemy.orm import Session

from nonbonded.backend.database import models
from nonbonded.backend.database.crud.datasets import DataSetCRUD, MoleculeSetCRUD
from nonbonded.backend.database.utilities.exceptions import (
    DataSetNotFoundError,
    MoleculeSetNotFoundError,
)
from nonbonded.library.models.results import EvaluatorTargetResult, RechargeTargetResult
from nonbonded.library.models.targets import EvaluatorTarget, RechargeTarget


class EvaluatorTargetCRUD:
    @classmethod
    def model_to_db(
        cls, db: Session, target: EvaluatorTarget
    ) -> models.EvaluatorTarget:

        data_sets = [
            DataSetCRUD.query(db, data_set_id) for data_set_id in target.data_set_ids
        ]

        if any(x is None for x in data_sets):
            raise DataSetNotFoundError(
                next(
                    iter(x for x, y in zip(target.data_set_ids, data_sets) if y is None)
                )
            )

        # noinspection PyTypeChecker
        db_target = models.EvaluatorTarget(
            identifier=target.id,
            **target.dict(exclude={"id", "denominators", "data_set_ids"}),
            training_sets=data_sets,
            denominators=[
                models.EvaluatorDenominator(property_type=key, value=value)
                for key, value in target.denominators.items()
            ],
        )

        return db_target

    @staticmethod
    def db_to_model(db_target: models.EvaluatorTarget) -> EvaluatorTarget:

        # noinspection PyTypeChecker
        return EvaluatorTarget(
            id=db_target.identifier,
            weight=db_target.weight,
            data_set_ids=[x.id for x in db_target.training_sets],
            denominators={x.property_type: x.value for x in db_target.denominators},
            allow_direct_simulation=db_target.allow_direct_simulation,
            n_molecules=db_target.n_molecules,
            allow_reweighting=db_target.allow_reweighting,
            n_effective_samples=db_target.n_effective_samples,
        )


class EvaluatorTargetResultCRUD:
    @classmethod
    def model_to_db(
        cls,
        result: EvaluatorTargetResult,
        iteration: int,
        db_target: models.EvaluatorTarget,
    ) -> models.EvaluatorTargetResult:

        # noinspection PyTypeChecker
        db_target_result = models.EvaluatorTargetResult(
            target_id=db_target.id,
            iteration=iteration,
            objective_function=result.objective_function,
            data_set_result=models.DataSetResult(
                statistic_entries=[
                    models.DataSetStatistic(
                        **statistic.dict(exclude={"statistic_type"}),
                        statistic_type=statistic.statistic_type.value,
                    )
                    for statistic in result.statistic_entries
                ],
            ),
        )

        return db_target_result

    @staticmethod
    def db_to_model(db_target_result: models.EvaluatorTargetResult) -> EvaluatorTarget:

        # noinspection PyTypeChecker
        return EvaluatorTargetResult(
            objective_function=db_target_result.objective_function,
            statistic_entries=db_target_result.data_set_result.statistic_entries,
        )


class RechargeTargetCRUD:
    @classmethod
    def model_to_db(cls, db: Session, target: RechargeTarget) -> models.RechargeTarget:
        molecule_sets = [
            MoleculeSetCRUD.query(db, molecule_set_id)
            for molecule_set_id in target.molecule_set_ids
        ]

        if any(x is None for x in molecule_sets):
            raise MoleculeSetNotFoundError(
                next(
                    iter(
                        x
                        for x, y in zip(target.molecule_set_ids, molecule_sets)
                        if y is None
                    )
                )
            )

        # noinspection PyUnresolvedReferences
        db_target = models.RechargeTarget(
            identifier=target.id,
            weight=target.weight,
            training_sets=molecule_sets,
            grid_settings=models.RechargeGridSettings(
                **target.esp_settings.grid_settings.dict()
            ),
            pcm_settings=(
                None
                if target.esp_settings.pcm_settings is None
                else models.RechargePCMSettings(
                    **target.esp_settings.pcm_settings.dict()
                )
            ),
            esp_settings=models.RechargeESPSettings.as_unique(
                db,
                basis=target.esp_settings.basis,
                method=target.esp_settings.method,
            ),
            conformer_settings=models.RechargeConformerSettings.as_unique(
                db, **target.conformer_settings.dict()
            ),
            property=target.property,
        )

        return db_target

    @staticmethod
    def db_to_model(db_target: models.RechargeTarget) -> RechargeTarget:
        # noinspection PyTypeChecker,PyUnresolvedReferences
        return RechargeTarget(
            id=db_target.identifier,
            weight=db_target.weight,
            molecule_set_ids=[x.id for x in db_target.training_sets],
            esp_settings=ESPSettings(
                basis=db_target.esp_settings.basis,
                method=db_target.esp_settings.method,
                grid_settings=GridSettings(
                    type=db_target.grid_settings.type,
                    spacing=db_target.grid_settings.spacing,
                    inner_vdw_scale=db_target.grid_settings.inner_vdw_scale,
                    outer_vdw_scale=db_target.grid_settings.outer_vdw_scale,
                ),
                pcm_settings=(
                    None
                    if db_target.pcm_settings is None
                    else PCMSettings(
                        solver=db_target.pcm_settings.solver,
                        solvent=db_target.pcm_settings.solvent,
                        radii_model=db_target.pcm_settings.radii_model,
                        radii_scaling=db_target.pcm_settings.radii_scaling,
                        cavity_area=db_target.pcm_settings.cavity_area,
                    )
                ),
            ),
            conformer_settings=ConformerSettings(
                method=db_target.conformer_settings.method,
                sampling_mode=db_target.conformer_settings.sampling_mode,
                max_conformers=db_target.conformer_settings.max_conformers,
            ),
            property=db_target.property,
        )


class RechargeTargetResultCRUD:
    @classmethod
    def model_to_db(
        cls,
        result: RechargeTargetResult,
        iteration: int,
        db_target: models.RechargeTarget,
    ) -> models.RechargeTargetResult:
        # noinspection PyTypeChecker
        db_target_result = models.RechargeTargetResult(
            target_id=db_target.id,
            iteration=iteration,
            objective_function=result.objective_function,
            molecule_set_result=models.MoleculeSetResult(
                statistic_entries=[
                    models.MoleculeSetStatistic(
                        **statistic.dict(exclude={"statistic_type"}),
                        statistic_type=statistic.statistic_type.value,
                    )
                    for statistic in result.statistic_entries
                ],
            ),
        )

        return db_target_result

    @staticmethod
    def db_to_model(db_target_result: models.RechargeTargetResult) -> RechargeTarget:
        # noinspection PyTypeChecker
        return RechargeTargetResult(
            objective_function=db_target_result.objective_function,
            statistic_entries=db_target_result.molecule_set_result.statistic_entries,
        )
