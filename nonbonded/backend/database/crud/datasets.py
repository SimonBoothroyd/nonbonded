from collections import defaultdict
from typing import Optional

from sqlalchemy.orm import Session

from nonbonded.backend.database import models
from nonbonded.backend.database.crud.environments import ChemicalEnvironmentCRUD
from nonbonded.library.models import datasets, environments


class TargetPropertyCRUD:
    @staticmethod
    def create(
        target_property: datasets.TargetProperty, target_state: datasets.StatePoint,
    ) -> models.TargetProperty:

        # noinspection PyTypeChecker
        db_target_property = models.TargetProperty(
            property_type=target_property.property_type,
            n_components=target_property.n_components,
            temperature=target_state.temperature,
            pressure=target_state.pressure,
            mole_fractions=[
                models.TargetAmount(mole_fraction=x)
                for x in target_state.mole_fractions
            ],
        )

        return db_target_property


class TargetDataSetCRUD:
    @staticmethod
    def create(db: Session, data_set: datasets.TargetDataSet) -> models.TargetDataSet:

        target_properties = [
            TargetPropertyCRUD.create(target_property, target_state)
            for target_property in data_set.target_properties
            for target_state in target_property.target_states
        ]

        # noinspection PyTypeChecker
        db_data_set = models.TargetDataSet(
            target_properties=target_properties,
            chemical_environments=[
                ChemicalEnvironmentCRUD.create(db, x)
                for x in data_set.chemical_environments
            ],
        )

        db.add(db_data_set)
        db.commit()
        db.refresh(db_data_set)

        return db_data_set

    @staticmethod
    def db_to_model(db_data_set: models.TargetDataSet) -> datasets.TargetDataSet:

        target_property_dict = defaultdict(list)

        # noinspection PyTypeChecker
        for db_target_property in db_data_set.target_properties:

            state_point = datasets.StatePoint(
                temperature=db_target_property.temperature,
                pressure=db_target_property.pressure,
                mole_fractions=[
                    x.mole_fraction for x in db_target_property.mole_fractions
                ],
            )

            property_key = (
                db_target_property.property_type,
                db_target_property.n_components,
            )

            target_property_dict[property_key].append(state_point)

        target_properties = []

        for (property_name, n_components), state_points in target_property_dict.items():

            target_properties.append(
                datasets.TargetProperty(
                    property_type=property_name,
                    n_components=n_components,
                    target_states=state_points,
                )
            )

        # noinspection PyArgumentList
        data_set = datasets.TargetDataSet(
            target_properties=target_properties,
            chemical_environments=[
                environments.ChemicalEnvironment(x.value)
                for x in db_data_set.chemical_environments
            ],
        )

        return data_set


class DataSetValueCRUD:
    @staticmethod
    def create(
        value: datasets.DataSetValue, substance: datasets.Substance,
    ) -> models.DataSetValue:

        # noinspection PyTypeChecker
        db_value = models.DataSetValue(
            property_type=value.property_type,
            temperature=value.state_point.temperature,
            pressure=value.state_point.pressure,
            value=value.value,
            std_error=value.std_error,
            components=[
                models.ComponentAmount(smiles=smiles, mole_fraction=mole_fraction)
                for smiles, mole_fraction in zip(
                    substance.smiles, value.state_point.mole_fractions
                )
            ],
        )

        return db_value


class DataSetCRUD:
    @staticmethod
    def read_all(db: Session, skip: int = 0, limit: int = 100):

        data_sets = db.query(models.DataSet).offset(skip).limit(limit).all()
        return data_sets

    @staticmethod
    def read_by_identifiers(
        db: Session,
        project_identifier: Optional[str],
        study_identifier: Optional[str],
        optimization_identifier: Optional[str],
    ):

        data_set = db.query(models.DataSet)

        print(project_identifier, study_identifier, optimization_identifier)

        if project_identifier is not None:

            data_set = data_set.filter(
                models.DataSet.project_identifier == project_identifier
            )

        if study_identifier is not None:

            data_set = data_set.filter(
                models.DataSet.study_identifier == study_identifier
            )

        if optimization_identifier is not None:

            data_set = data_set.filter(
                models.DataSet.optimization_identifier == optimization_identifier
            )

        return [DataSetCRUD.db_to_model(x) for x in data_set.all()]

    @staticmethod
    def create(db: Session, data_set: datasets.DataSet,) -> models.DataSet:

        db_data_values = []

        for data_entry in data_set.data_entries:

            for data_set_value in data_entry.values:

                db_data_values.append(
                    DataSetValueCRUD.create(data_set_value, data_entry.substance,)
                )

        # noinspection PyTypeChecker
        db_data_set = models.DataSet(
            project_identifier=data_set.project_identifier,
            study_identifier=data_set.study_identifier,
            optimization_identifier=data_set.optimization_identifier,
            data_values=db_data_values,
        )

        db.add(db_data_set)
        db.commit()
        db.refresh(db_data_set)

        return db_data_set

    @staticmethod
    def db_to_model(db_data_set: models.DataSet) -> datasets.DataSet:

        data_entries_dict = defaultdict(list)

        # noinspection PyTypeChecker
        for db_data_value in db_data_set.data_values:

            substance = datasets.Substance(
                smiles=[component.smiles for component in db_data_value.components]
            )

            state_point = datasets.StatePoint(
                temperature=db_data_value.temperature,
                pressure=db_data_value.pressure,
                mole_fractions=[
                    component.mole_fraction for component in db_data_value.components
                ],
            )

            data_value = datasets.DataSetValue(
                property_type=db_data_value.property_type,
                state_point=state_point,
                value=db_data_value.value,
                std_error=db_data_value.std_error,
            )

            data_entries_dict[substance].append(data_value)

        data_entries = []

        for substance, values in data_entries_dict.items():

            data_entry = datasets.DataSetEntry(substance=substance, values=values)
            data_entries.append(data_entry)

        data_set = datasets.DataSet(
            project_identifier=db_data_set.project_identifier,
            study_identifier=db_data_set.study_identifier,
            optimization_identifier=db_data_set.optimization_identifier,
            data_entries=data_entries,
        )

        return data_set
