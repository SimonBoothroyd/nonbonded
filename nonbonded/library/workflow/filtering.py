import abc
import logging
from typing import Dict, List, Optional, Tuple

import numpy
import pandas
from openforcefield.topology import Molecule
from openforcefield.utils import UndefinedStereochemistryError
from pydantic import BaseModel, Field, PositiveInt, root_validator, validator
from scipy.optimize import linear_sum_assignment

from nonbonded.library.utilities.checkmol import analyse_functional_groups
from nonbonded.library.utilities.environments import ChemicalEnvironment
from nonbonded.library.utilities.molecules import find_smirks_matches
from nonbonded.library.utilities.pandas import reorder_data_frame
from nonbonded.library.workflow.component import WorkflowComponent

logger = logging.getLogger(__name__)


ComponentEnvironments = List[List[ChemicalEnvironment]]


class FilterDuplicatesSchema(BaseModel, abc.ABC):

    temperature_precision: PositiveInt = Field(
        2,
        description="The number of decimal places to compare temperatures (K) to "
        "within.",
    )
    pressure_precision: PositiveInt = Field(
        3,
        description="The number of decimal places to compare pressures (kPa) to "
        "within.",
    )
    mole_fraction_precision: PositiveInt = Field(
        6,
        description="The number of decimal places to compare mole fractions to within.",
    )


class FilterDuplicates(WorkflowComponent[FilterDuplicatesSchema]):
    @classmethod
    def _apply(
        cls, data_frame: pandas.DataFrame, schema: FilterDuplicatesSchema
    ) -> pandas.DataFrame:

        if len(data_frame) == 0:
            return data_frame

        data_frame = data_frame.copy()
        data_frame = reorder_data_frame(data_frame)

        minimum_n_components = data_frame["N Components"].min()
        maximum_n_components = data_frame["N Components"].max()

        filtered_data = []

        for n_components in range(minimum_n_components, maximum_n_components + 1):

            component_data = data_frame[data_frame["N Components"] == n_components]

            component_data["Temperature (K)"] = component_data["Temperature (K)"].round(
                schema.temperature_precision
            )
            component_data["Pressure (kPa)"] = component_data["Pressure (kPa)"].round(
                schema.pressure_precision
            )

            subset_columns = ["Temperature (K)", "Pressure (kPa)", "Phase"]

            for index in range(n_components):

                component_data[f"Mole Fraction {index + 1}"] = component_data[
                    f"Mole Fraction {index + 1}"
                ].round(schema.mole_fraction_precision)

                subset_columns.extend(
                    [
                        f"Component {index + 1}",
                        f"Role {index + 1}",
                        f"Mole Fraction {index + 1}",
                        f"Exact Amount {index + 1}",
                    ]
                )

            subset_columns = [x for x in subset_columns if x in component_data]
            value_headers = [x for x in component_data if x.find(" Value ") >= 0]

            sorted_data = []

            for value_header in value_headers:

                uncertainty_header = value_header.replace("Value", "Uncertainty")

                if uncertainty_header not in component_data:
                    continue

                property_data = component_data[component_data[value_header].notna()]
                property_data = property_data.sort_values(uncertainty_header)

                sorted_data.append(property_data)

            sorted_data = pandas.concat(sorted_data, ignore_index=True, sort=False)

            filtered_data.append(
                sorted_data.drop_duplicates(subset=subset_columns, keep="last")
            )

        filtered_data = pandas.concat(filtered_data, ignore_index=True, sort=False)
        return filtered_data


class FilterByTemperatureSchema(BaseModel, abc.ABC):

    minimum_temperature: Optional[float] = Field(
        ...,
        description="Retain data points measured for temperatures above this value (K)",
    )
    maximum_temperature: Optional[float] = Field(
        ...,
        description="Retain data points measured for temperatures below this value (K)",
    )

    @root_validator
    def _min_max(cls, values):
        minimum_temperature = values.get("minimum_temperature")
        maximum_temperature = values.get("maximum_temperature")

        if minimum_temperature is not None:
            assert minimum_temperature > 0
        if maximum_temperature is not None:
            assert maximum_temperature > 0

        if minimum_temperature is not None and maximum_temperature is not None:
            assert maximum_temperature > minimum_temperature

        return values


class FilterByTemperature(WorkflowComponent[FilterByTemperatureSchema]):
    @classmethod
    def _apply(
        cls, data_frame: pandas.DataFrame, schema: FilterByTemperatureSchema
    ) -> pandas.DataFrame:

        return data_frame[
            (schema.minimum_temperature < data_frame["Temperature (K)"])
            & (data_frame["Temperature (K)"] < schema.maximum_temperature)
        ]


class FilterByPressureSchema(BaseModel, abc.ABC):

    minimum_pressure: Optional[float] = Field(
        ...,
        description="Retain data points measured for pressures above this value (kPa)",
    )
    maximum_pressure: Optional[float] = Field(
        ...,
        description="Retain data points measured for pressures below this value (kPa)",
    )

    @root_validator
    def _min_max(cls, values):
        minimum_pressure = values.get("minimum_pressure")
        maximum_pressure = values.get("maximum_pressure")

        if minimum_pressure is not None:
            assert minimum_pressure > 0
        if maximum_pressure is not None:
            assert maximum_pressure > 0

        if minimum_pressure is not None and maximum_pressure is not None:
            assert maximum_pressure > minimum_pressure

        return values


class FilterByPressure(WorkflowComponent[FilterByPressureSchema]):
    @classmethod
    def _apply(
        cls, data_frame: pandas.DataFrame, schema: FilterByPressureSchema
    ) -> pandas.DataFrame:

        return data_frame[
            (schema.minimum_pressure < data_frame["Pressure (kPa)"])
            & (data_frame["Pressure (kPa)"] < schema.maximum_pressure)
        ]


class FilterByElementsSchema(BaseModel, abc.ABC):

    allowed_elements: Optional[List[str]] = Field(
        None,
        description="The only elements which must be present in the measured system "
        "for the data point to be retained. This option is mutually exclusive with "
        "`forbidden_elements`",
    )
    forbidden_elements: Optional[List[str]] = Field(
        None,
        description="The elements which must not be present in the measured system for "
        "the data point to be retained. This option is mutually exclusive with "
        "`allowed_elements`",
    )

    @root_validator
    def _validate_mutually_exclusive(cls, values):

        allowed_elements = values.get("allowed_elements")
        forbidden_elements = values.get("forbidden_elements")

        assert allowed_elements is not None or forbidden_elements is not None
        assert allowed_elements is None or forbidden_elements is None

        return values


class FilterByElements(WorkflowComponent[FilterByElementsSchema]):
    @classmethod
    def _apply(
        cls, data_frame: pandas.DataFrame, schema: FilterByElementsSchema
    ) -> pandas.DataFrame:
        def filter_function(data_row):

            n_components = data_row["N Components"]

            for index in range(n_components):

                smiles = data_row[f"Component {index + 1}"]
                molecule = Molecule.from_smiles(smiles, allow_undefined_stereo=True)

                if schema.allowed_elements is not None and not all(
                    [
                        x.element.symbol in schema.allowed_elements
                        for x in molecule.atoms
                    ]
                ):
                    return False

                if schema.forbidden_elements is not None and any(
                    [
                        x.element.symbol in schema.forbidden_elements
                        for x in molecule.atoms
                    ]
                ):
                    return False

            return True

        return data_frame[data_frame.apply(cls, filter_function, axis=1)]


class FilterByStereochemistrySchema(BaseModel, abc.ABC):
    ...


class FilterByStereochemistry(WorkflowComponent[FilterByStereochemistrySchema]):
    @classmethod
    def _apply(
        cls, data_frame: pandas.DataFrame, schema: FilterByStereochemistrySchema
    ) -> pandas.DataFrame:
        def filter_function(data_row):

            n_components = data_row["N Components"]

            for index in range(n_components):

                smiles = data_row[f"Component {index + 1}"]

                try:
                    Molecule.from_smiles(smiles)
                except UndefinedStereochemistryError:
                    return False

            return True

        return data_frame[data_frame.apply(cls, filter_function, axis=1)]


class FilterByChargedSchema(BaseModel, abc.ABC):
    ...


class FilterByCharged(WorkflowComponent[FilterByChargedSchema]):
    """Filters out any substance where any of the constituent components
    have a net non-zero charge.
    """

    @classmethod
    def _apply(
        cls, data_frame: pandas.DataFrame, schema: FilterByChargedSchema
    ) -> pandas.DataFrame:
        def filter_function(data_row):

            n_components = data_row["N Components"]

            for index in range(n_components):

                smiles = data_row[f"Component {index + 1}"]
                molecule = Molecule.from_smiles(smiles, allow_undefined_stereo=True)

                if numpy.isclose(
                    sum([atom.formal_charge for atom in molecule.atoms]), 0.0
                ):

                    continue

                return False

            return True

        return data_frame[data_frame.apply(cls, filter_function, axis=1)]


class FilterByIonicLiquidSchema(BaseModel, abc.ABC):
    ...


class FilterByIonicLiquid(WorkflowComponent[FilterByIonicLiquidSchema]):
    """Filters out any substance which contain or are classed as an ionic liquid.
    """

    @classmethod
    def _apply(
        cls, data_frame: pandas.DataFrame, schema: FilterByIonicLiquidSchema
    ) -> pandas.DataFrame:
        def filter_function(data_row):

            n_components = data_row["N Components"]

            for index in range(n_components):

                smiles = data_row[f"Component {index + 1}"]

                if "." in smiles:
                    return False

            return True

        return data_frame[data_frame.apply(cls, filter_function, axis=1)]


class FilterBySmilesSchema(BaseModel, abc.ABC):

    smiles_to_include: Optional[List[str]] = Field(
        None,
        description="The smiles patterns to retain. This option is mutually "
        "exclusive with `smiles_to_exclude`",
    )
    smiles_to_exclude: Optional[List[str]] = Field(
        None,
        description="The smiles patterns to exclude. This option is mutually "
        "exclusive with `smiles_to_include`",
    )
    allow_partial_inclusion: bool = Field(
        False,
        description="If False, all the components in a substance must appear in "
        "the `smiles_to_include` list, otherwise, only some must appear. "
        "This option only applies when `smiles_to_include` is set.",
    )

    @root_validator
    def _validate_mutually_exclusive(cls, values):

        smiles_to_include = values.get("smiles_to_include")
        smiles_to_exclude = values.get("smiles_to_exclude")

        assert smiles_to_include is not None or smiles_to_exclude is not None
        assert smiles_to_include is None or smiles_to_exclude is None

        return values


class FilterBySmiles(WorkflowComponent[FilterBySmilesSchema]):
    """Filters the data set so that it only contains either a specific set
    of smiles, or does not contain any of a set of specifically excluded smiles.
    """

    @classmethod
    def _apply(
        cls, data_frame: pandas.DataFrame, schema: FilterBySmilesSchema
    ) -> pandas.DataFrame:

        smiles_to_include = schema.smiles_to_include
        smiles_to_exclude = schema.smiles_to_exclude

        if smiles_to_include is not None:
            smiles_to_exclude = []
        elif smiles_to_exclude is not None:
            smiles_to_include = []

        def filter_function(data_row):

            n_components = data_row["N Components"]

            component_smiles = [
                data_row[f"Component {index + 1}"] for index in range(n_components)
            ]

            if any(x in smiles_to_exclude for x in component_smiles):
                return False
            elif len(smiles_to_exclude) > 0:
                return True

            if not schema.allow_partial_inclusion and not all(
                x in smiles_to_include for x in component_smiles
            ):
                return False

            if schema.allow_partial_inclusion and not any(
                x in smiles_to_include for x in component_smiles
            ):
                return False

            return True

        return data_frame[data_frame.apply(filter_function, axis=1)]


class FilterBySmirksSchema(BaseModel, abc.ABC):

    smirks_to_include: Optional[List[str]] = Field(
        None,
        description="The smirks patterns which must be matched by a substance in "
        "order to retain a measurement. This option is mutually exclusive with "
        "`smirks_to_exclude`",
    )
    smirks_to_exclude: Optional[List[str]] = Field(
        None,
        description="The smirks patterns which must not be matched by a substance in "
        "order to retain a measurement. This option is mutually exclusive with "
        "`smirks_to_include`",
    )
    allow_partial_inclusion: bool = Field(
        False,
        description="If False, all the components in a substance must match at least "
        "one pattern in `smirks_to_include` in order to retain a measurement, "
        "otherwise, only a least one component must match. This option only applies "
        "when `smirks_to_include` is set.",
    )

    @root_validator
    def _validate_mutually_exclusive(cls, values):

        smirks_to_include = values.get("smirks_to_include")
        smirks_to_exclude = values.get("smirks_to_exclude")

        assert smirks_to_include is not None or smirks_to_exclude is not None
        assert smirks_to_include is None or smirks_to_exclude is None

        return values


class FilterBySmirks(WorkflowComponent[FilterBySmirksSchema]):
    """Filters a data set so that it only contains measurements made
    for molecules which contain (or don't) a set of chemical environments
    represented by SMIRKS patterns.
    """

    @classmethod
    def _apply(
        cls, data_frame: pandas.DataFrame, schema: FilterBySmirksSchema
    ) -> pandas.DataFrame:

        smirks_to_match = (
            schema.smirks_to_include
            if schema.smirks_to_include
            else schema.smirks_to_exclude
        )

        def filter_function(data_row):

            n_components = data_row["N Components"]

            component_smiles = [
                data_row[f"Component {index + 1}"] for index in range(n_components)
            ]

            smirks_matches = {
                smiles: find_smirks_matches(smiles, *smirks_to_match)
                for smiles in component_smiles
            }

            if schema.smirks_to_exclude is not None:
                return not any(len(x) > 0 for x in smirks_matches.values())

            if schema.allow_partial_inclusion:
                return any(len(x) > 0 for x in smirks_matches.values())

            return all(len(x) > 0 for x in smirks_matches.values())

        return data_frame[data_frame.apply(filter_function, axis=1)]


class FilterByNComponentsSchema(BaseModel, abc.ABC):

    n_components: List[int] = Field(
        ...,
        description="The number of components that measurements should have been "
        "measured for in order to be retained.",
    )

    @validator("n_components")
    def _validate_n_components(cls, value):

        assert len(value) > 0
        assert all(x > 0 for x in value)

        return value


class FilterByNComponents(WorkflowComponent[FilterByNComponentsSchema]):
    """
    """

    @classmethod
    def _apply(
        cls, data_frame: pandas.DataFrame, schema: FilterByNComponentsSchema
    ) -> pandas.DataFrame:

        return data_frame[data_frame["N Components"].isin(schema.n_components)]


class FilterBySubstancesSchema(BaseModel, abc.ABC):

    substances_to_include: Optional[List[Tuple[str, ...]]] = Field(
        None,
        description="The substances compositions to retain, where each tuple in the "
        "list contains the smiles patterns which make up the substance to include. "
        "This option is mutually exclusive with `substances_to_exclude`.",
    )
    substances_to_exclude: Optional[List[Tuple[str, ...]]] = Field(
        None,
        description="The substances compositions to retain, where each tuple in the "
        "list contains the smiles patterns which make up the substance to exclude. "
        "This option is mutually exclusive with `substances_to_include`.",
    )

    @root_validator
    def _validate_mutually_exclusive(cls, values):

        substances_to_include = values.get("substances_to_include")
        substances_to_exclude = values.get("substances_to_exclude")

        assert substances_to_include is not None or substances_to_exclude is not None
        assert substances_to_include is None or substances_to_exclude is None

        return values


class FilterBySubstances(WorkflowComponent[FilterBySubstancesSchema]):
    """Filters the data set so that it only contains properties measured for
    particular substances.

    This method is similar to `filter_by_smiles`, however here we explicitly define
    the full substances compositions, rather than individual smiles which should
    either be included or excluded.

    Examples
    --------
    To filter the data set to only include measurements for pure methanol, pure
    benzene or an aqueous ethanol mix:

    >>> schema = FilterBySubstancesSchema(
    >>>     substances_to_include=[
    >>>         ('CO',),
    >>>         ('C1=CC=CC=C1',),
    >>>         ('CCO', 'O')
    >>>     ]
    >>> )

    To filter out measurements made for an aqueous mix of benzene:

    >>> schema = FilterBySubstancesSchema(
    >>>     substances_to_exclude=[('O', 'C1=CC=CC=C1')]
    >>> )
    """

    @classmethod
    def _apply(
        cls, data_frame: pandas.DataFrame, schema: FilterBySubstancesSchema
    ) -> pandas.DataFrame:
        def filter_function(data_row):

            n_components = data_row["N Components"]

            substance = tuple(
                sorted(
                    [
                        data_row[f"Component {index + 1}"]
                        for index in range(n_components)
                    ]
                )
            )

            return (
                schema.substances_to_exclude is not None
                and substance not in schema.substances_to_exclude
            ) or (
                schema.substances_to_include is not None
                and substance in schema.substances_to_include
            )

        return data_frame[data_frame.apply(filter_function, axis=1)]


class FilterByEnvironmentsSchema(BaseModel, abc.ABC):

    per_component_environments: Optional[Dict[int, ComponentEnvironments]] = Field(
        None,
        description="The environments which should be present in the components of "
        "the substance for which the measurements were made. Each dictionary "
        "key corresponds to the expected number of components in the system, and each "
        "value the environments for each component. This option is mutually exclusive "
        "with `environments`.",
    )
    environments: Optional[List[ChemicalEnvironment]] = Field(
        None,
        description="The environments which should be present in the substances for "
        "which measurements were made. This option is mutually exclusive with "
        "`per_component_environments`.",
    )

    at_least_one: bool = Field(
        True,
        description="If true, data points will only be retained if all of the "
        "components in the measured system contain at least one of the specified "
        "environments. This option is mutually exclusive with `all_of`.",
    )
    all_of: bool = Field(
        False,
        description="If true, data points will only be retained if all of the "
        "components in the measured system contain only the specified environments "
        "and no others. This option is mutually exclusive with `at_least_one`.",
    )

    @validator("per_component_environments")
    def _validate_per_component_environments(cls, value):

        if value is None:
            return value

        assert all(len(y) == x for x, y in value.items())
        return value

    @root_validator
    def _validate_mutually_exclusive(cls, values):

        at_least_one = values.get("at_least_one")
        all_of = values.get("all_of")

        assert at_least_one is True or all_of is True
        assert at_least_one is False or all_of is False

        per_component_environments = values.get("per_component_environments")
        environments = values.get("environments")

        assert per_component_environments is not None or environments is not None
        assert per_component_environments is None or environments is None

        return values


class FilterByEnvironments(WorkflowComponent[FilterByEnvironmentsSchema]):
    """Filters a data set so that it only contains measurements made for substances
    which contain specific chemical environments..
    """

    @classmethod
    def _find_environments_per_component(cls, data_row: pandas.Series):

        n_components = data_row["N Components"]

        component_smiles = [
            data_row[f"Component {index + 1}"] for index in range(n_components)
        ]
        component_moieties = [analyse_functional_groups(x) for x in component_smiles]

        if any(x is None for x in component_moieties):

            logger.info(
                f"Checkmol was unable to parse the system with components="
                f"{component_smiles} and so this data point was discarded."
            )

            return None

        return component_moieties

    @classmethod
    def _is_match(
        cls,
        component_environments,
        environments_to_match,
        schema
    ):

        operator = all if schema.all_of else any

        return operator(
            environment in environments_to_match
            for environment in component_environments
        )

    @classmethod
    def _filter_by_environments(cls, data_row, schema: FilterByEnvironmentsSchema):

        environments_per_component = cls._find_environments_per_component(data_row)

        if environments_per_component is None:
            return False

        return all(
            cls._is_match(component_environments, schema.environments, schema)
            for component_environments in environments_per_component
        )

    @classmethod
    def _filter_by_per_component(cls, data_row, schema: FilterByEnvironmentsSchema):

        n_components = data_row["N Components"]

        if (
            schema.per_component_environments is not None
            and n_components not in schema.per_component_environments
        ):
            # No filter was specified for this number of components.
            return True

        environments_per_component = cls._find_environments_per_component(data_row)

        if environments_per_component is None:
            return False

        match_matrix = numpy.zeros((n_components, n_components))

        for component_index, component_environments in enumerate(
            environments_per_component
        ):

            # noinspection PyUnresolvedReferences
            for environments_index, environments_to_match in enumerate(
                schema.per_component_environments[n_components]
            ):

                match_matrix[component_index, environments_index] = cls._is_match(
                    component_environments, environments_to_match, schema
                )

        x_indices, y_indices = linear_sum_assignment(
            match_matrix, maximize=True
        )

        return numpy.all(match_matrix[x_indices, y_indices] > 0)

    @classmethod
    def _apply(
        cls, data_frame: pandas.DataFrame, schema: FilterByEnvironmentsSchema
    ) -> pandas.DataFrame:

        if schema.environments is not None:
            filter_function = cls._filter_by_environments
        else:
            filter_function = cls._filter_by_per_component

        return data_frame[data_frame.apply(filter_function, axis=1)]
