from collections import defaultdict

from sqlalchemy.orm import Session

from nonbonded.backend.database import models
from nonbonded.backend.database.crud.authors import AuthorCRUD
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


class DataSetEntryCRUD:

    @staticmethod
    def create(
        value: datasets.DataSetEntry,
    ) -> models.DataSetEntry:

        # noinspection PyTypeChecker
        db_value = models.DataSetEntry(
            property_type=value.property_type,
            temperature=value.state_point.temperature,
            pressure=value.state_point.pressure,
            value=value.value,
            std_error=value.std_error,
            doi=value.doi,
            components=[
                models.ComponentAmount(smiles=smiles, mole_fraction=mole_fraction)
                for smiles, mole_fraction in zip(
                    value.substance.smiles, value.state_point.mole_fractions
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
    def read_by_identifier(db: Session, identifier: str):

        db_data_set = db.query(models.DataSet)
        db_data_set = db_data_set.filter(models.DataSet.id == identifier)

        data_set = db_data_set.first()

        if data_set is None:
            return

        return DataSetCRUD.db_to_model(data_set)

    @staticmethod
    def create(db: Session, data_set: datasets.DataSet) -> models.DataSet:

        # noinspection PyTypeChecker
        db_data_set = models.DataSet(
            id=data_set.identifier,
            description=data_set.description,
            authors=[AuthorCRUD.create(db, author) for author in data_set.authors],
            entries=[DataSetEntryCRUD.create(entry) for entry in data_set.entries]
        )

        db.add(db_data_set)
        db.commit()
        db.refresh(db_data_set)

        return db_data_set

    @staticmethod
    def db_to_model(db_data_set: models.DataSet) -> datasets.DataSet:

        data_entries = []

        # noinspection PyTypeChecker
        for db_entry in db_data_set.entries:

            substance = datasets.Substance(
                smiles=[component.smiles for component in db_entry.components]
            )

            state_point = datasets.StatePoint(
                temperature=db_entry.temperature,
                pressure=db_entry.pressure,
                mole_fractions=[
                    component.mole_fraction for component in db_entry.components
                ],
            )

            data_value = datasets.DataSetEntry(
                substance=substance,
                property_type=db_entry.property_type,
                state_point=state_point,
                value=db_entry.value,
                std_error=db_entry.std_error,
                doi=db_entry.doi
            )

            data_entries.append(data_value)

        data_set = datasets.DataSet(
            identifier=db_data_set.id,
            description=db_data_set.description,
            entries=data_entries,
            authors=db_data_set.authors
        )

        return data_set
