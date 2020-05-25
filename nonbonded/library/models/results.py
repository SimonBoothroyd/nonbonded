import abc
import logging
from typing import TYPE_CHECKING, List, Optional

from pydantic import Field

from nonbonded.library.models import BaseORM, BaseREST
from nonbonded.library.models.datasets import Component
from nonbonded.library.models.forcefield import ForceField
from nonbonded.library.statistics.statistics import compute_statistics
from nonbonded.library.utilities.checkmol import analyse_functional_groups
from nonbonded.library.utilities.environments import ChemicalEnvironment
from nonbonded.library.utilities.exceptions import UnsupportedEndpointError

if TYPE_CHECKING:

    import pandas
    from openff.evaluator.datasets import PhysicalPropertyDataSet

logger = logging.getLogger(__name__)


class ResultsEntry(BaseORM):

    property_type: str = Field(
        ..., description="The type of property that this entry is recording."
    )

    temperature: float = Field(
        ..., description="The temperature (K) at which this entry was recorded."
    )
    pressure: float = Field(
        ..., description="The pressure (kPa) at which this entry was recorded."
    )
    phase: str = Field(
        "Liquid", description="The phase that the property was recorded in."
    )

    components: List[Component] = Field(
        ...,
        description="The components in the systems for which the measurement was made.",
    )

    unit: str = Field(
        ..., description="The unit that the values in standard errors are reported in."
    )

    reference_value: float = Field(
        ..., description="The reference value in units of `unit`."
    )
    reference_std_error: Optional[float] = Field(
        None, description="The reference std error in units of `unit`"
    )

    estimated_value: float = Field(
        ..., description="The estimated value in units of `unit`."
    )
    estimated_std_error: float = Field(
        ..., description="The estimated std error in units of `unit`"
    )

    category: Optional[str] = Field(
        ..., description="The category which this data point has been placed into."
    )


class StatisticsEntry(BaseORM):

    statistics_type: str = Field(
        ..., description="The type of statistic recorded by this entry."
    )

    property_type: str = Field(
        ..., description="The type of property which the statistic was calculated for."
    )
    n_components: Optional[int] = Field(
        ...,
        description="The number of components in the systems which the statistic was "
        "calculated for (pure, binary, etc.).",
    )

    category: Optional[str] = Field(
        None, description="The category which this statistic has been placed into."
    )

    unit: str = Field(
        ...,
        description="The unit that the value in confidence intervals are reported in.",
    )

    value: float = Field(..., description="The value of the statistic.")

    lower_95_ci: float = Field(
        ..., description="The lower 95% confidence interval of the statistic."
    )
    upper_95_ci: float = Field(
        ..., description="The upper 95% confidence interval of the statistic."
    )


class BaseResult(BaseREST, abc.ABC):

    project_id: str = Field(
        ..., description="The id of the project that these results were generated for."
    )
    study_id: str = Field(
        ..., description="The id of the study that these results were generated for."
    )
    id: str = Field(
        ...,
        description="The unique id assigned to these results. This should match the id "
        "of the benchmark / optimization which yielded this result.",
    )

    @classmethod
    def _url_name(cls):
        return cls.__name__.replace("Result", "").lower() + "s"

    def _post_endpoint(self):

        return (
            f"http://localhost:5000/api/v1/projects/"
            f"{self.project_id}"
            f"/studies/"
            f"{self.study_id}"
            f"/{self._url_name()}/"
            f"{self.id}"
            f"/results/"
        )

    def _put_endpoint(self):

        raise UnsupportedEndpointError("Results cannot be updated via the RESTful API.")

    def _delete_endpoint(self):

        return (
            f"http://localhost:5000/api/v1/projects/"
            f"{self.project_id}"
            f"/studies/"
            f"{self.study_id}"
            f"/{self._url_name()}/"
            f"{self.id}"
            f"/results/"
        )

    @classmethod
    def from_rest(cls, project_id: str, study_id: str, id: str):
        import requests

        request = requests.get(
            f"http://localhost:5000/api/v1/projects/"
            f"{project_id}"
            f"/studies/"
            f"{study_id}"
            f"/{cls._url_name()}/"
            f"{id}"
            f"/results/"
        )

        return cls._from_rest(request)


class BenchmarkResult(BaseResult):

    statistic_entries: List[StatisticsEntry] = Field(
        ...,
        description="Overall statistics about collected from the benchmark, including "
        "values such as the RMSE and R^2 of each type of property.",
    )

    results_entries: List[ResultsEntry] = Field(
        ...,
        description="A comparison of the estimated and reference values for each of "
        "the properties which were benchmarked against.",
    )

    @classmethod
    def _components_to_category(
        cls,
        components: List[Component],
        analysis_environments: List[ChemicalEnvironment],
    ) -> str:

        import numpy

        sorted_components = [*sorted(components, key=lambda x: x.smiles)]
        assigned_environments = []

        for component in sorted_components:

            # Determine which environments are present in this component.
            component_environments = analyse_functional_groups(component.smiles)
            # Filter out any environments which we are not interested in.
            component_environments = {
                x: y
                for x, y in component_environments.items()
                if x in analysis_environments
            }

            if len(component_environments) == 0:
                logger.info(
                    f"The substance with components={[x.smiles for x in components]} "
                    f"could not be assigned a category. More than likely one or more "
                    f"of the components contains only environments which were not "
                    f"marked for analysis. It will be assigned a category of 'None' "
                    f"instead."
                )
                return "None"

            # Try to find the environment which appears the most times in a molecule.
            # We sort the environments to try and make the case where multiple
            # environments appear with the same frequency deterministic.
            component_environment_keys = sorted(
                component_environments.keys(), key=lambda x: x.value
            )

            most_common_environment = "None"
            most_occurrences = -1

            for key in component_environment_keys:

                if component_environments[key] > most_occurrences:

                    most_common_environment = key.value
                    most_occurrences = component_environments[key]

            assigned_environments.append(most_common_environment)

        # Sort the assignments to try and make the categories deterministic.
        sorted_assigned_environments = [*sorted(assigned_environments)]
        category = ""

        for index, assigned_environment in enumerate(sorted_assigned_environments):

            if index == 0:

                category = assigned_environment
                continue

            previous_environment = sorted_assigned_environments[index - 1]

            previous_component = components[
                assigned_environments.index(previous_environment)
            ]
            current_component = components[
                assigned_environments.index(assigned_environment)
            ]

            if numpy.isclose(
                previous_component.mole_fraction, 1.0 / len(components), rtol=0.1
            ) and numpy.isclose(
                current_component.mole_fraction, 1.0 / len(components), rtol=0.1
            ):
                category = f"{category} ~ {assigned_environment}"

            elif previous_component.mole_fraction < current_component.mole_fraction:
                category = f"{category} < {assigned_environment}"
            else:
                category = f"{category} > {assigned_environment}"

        return category

    @classmethod
    def _evaluator_to_results_entries(
        cls,
        reference_data_set: "PhysicalPropertyDataSet",
        estimated_data_set: "PhysicalPropertyDataSet",
        analysis_environments: List[ChemicalEnvironment],
    ) -> List[ResultsEntry]:

        import numpy
        import pandas

        from openff.evaluator import properties

        reference_data_frame = reference_data_set.to_pandas()
        estimated_data_frame = estimated_data_set.to_pandas()

        value_headers = [
            "Id",
            *(x for x in estimated_data_frame if x.find(" Value ") >= 0),
            *(x for x in estimated_data_frame if x.find(" Uncertainty ") >= 0),
        ]

        estimated_data_frame = estimated_data_frame[value_headers]

        joined_data_frame = pandas.merge(
            estimated_data_frame,
            reference_data_frame,
            on=["Id"],
            suffixes=("", "_ref"),
        )

        results_entries = []

        for _, data_row in joined_data_frame.iterrows():

            property_type = next(
                iter(
                    x.split(" ")[0]
                    for x, _ in data_row.iteritems()
                    if x.find(" Value ") >= 0 and not numpy.isnan(data_row[x])
                )
            )

            property_class = getattr(properties, property_type)
            default_unit = property_class.default_unit()

            value_header = f"{property_type} Value ({default_unit:~})"
            std_header = f"{property_type} Uncertainty ({default_unit:~})"

            components = []

            for index in range(data_row["N Components"]):

                smiles = data_row[f"Component {index + 1}"]
                role = data_row[f"Role {index + 1}"]

                mole_fraction = data_row.get(f"Mole Fraction {index + 1}", 0.0)
                exact_amount = data_row.get(f"Exact Amount {index + 1}", 0)

                if pandas.isnull(mole_fraction):
                    mole_fraction = 0.0
                if pandas.isnull(exact_amount):
                    exact_amount = 0

                component = Component(
                    smiles=smiles,
                    mole_fraction=mole_fraction,
                    exact_amount=exact_amount,
                    role=role,
                )

                components.append(component)

            results_entry = ResultsEntry(
                property_type=property_type,
                temperature=data_row["Temperature (K)"],
                pressure=data_row["Pressure (kPa)"],
                phase=data_row["Phase"],
                components=components,
                unit=str(default_unit),
                reference_value=data_row[f"{value_header}_ref"],
                reference_std_error=data_row.get(f"{std_header}_ref", None),
                estimated_value=data_row[value_header],
                estimated_std_error=data_row[std_header],
                category=cls._components_to_category(components, analysis_environments),
            )

            results_entries.append(results_entry)

        return results_entries

    @classmethod
    def _results_frame_to_statistics(
        cls,
        results_frame: "pandas.DataFrame",
        property_type: str,
        n_components: int,
        unit: str,
        category: Optional[str],
        bootstrap_iterations: int,
    ) -> List[StatisticsEntry]:

        bulk_statistics, _, bulk_statistics_ci = compute_statistics(
            measured_values=results_frame["Reference Value"].values,
            measured_std=results_frame["Reference Std"].values,
            estimated_values=results_frame["Estimated Value"].values,
            estimated_std=results_frame["Estimated Std"].values,
            bootstrap_iterations=bootstrap_iterations,
        )

        statistics_entries = []

        for statistic_type in bulk_statistics:

            statistics_entry = StatisticsEntry(
                statistics_type=statistic_type.value,
                property_type=property_type,
                n_components=n_components,
                category=category,
                unit=unit,
                value=bulk_statistics[statistic_type],
                lower_95_ci=bulk_statistics_ci[statistic_type][0],
                upper_95_ci=bulk_statistics_ci[statistic_type][1],
            )
            statistics_entries.append(statistics_entry)

        return statistics_entries

    @classmethod
    def _results_entries_to_statistics(
        cls, results_entries: List[ResultsEntry], bootstrap_iterations: int
    ) -> List[StatisticsEntry]:

        import pandas

        results_rows = []

        property_types = set()
        categories = set()

        units = {}

        for results_entry in results_entries:

            results_row = {
                "Property Type": results_entry.property_type,
                "N Components": len(results_entry.components),
                "Reference Value": results_entry.reference_value,
                "Reference Std": results_entry.reference_std_error,
                "Estimated Value": results_entry.estimated_value,
                "Estimated Std": results_entry.estimated_std_error,
                "Category": results_entry.category,
            }
            results_rows.append(results_row)

            property_type = (results_entry.property_type, len(results_entry.components))

            property_types.add(property_type)
            categories.add(results_entry.category)

            units[results_entry.property_type] = results_entry.unit

        results_frame = pandas.DataFrame(results_rows)

        statistics_entries = []

        for property_type, n_components in property_types:

            property_results_frame = results_frame[
                (results_frame["Property Type"] == property_type)
                & (results_frame["N Components"] == n_components)
            ]

            # Calculate statistics over the entire set (i.e. not by category).
            statistics_entries.extend(
                cls._results_frame_to_statistics(
                    property_results_frame,
                    property_type,
                    n_components,
                    units[property_type],
                    None,
                    bootstrap_iterations,
                )
            )

            # Calculate statistics per category
            for category in categories:

                category_results_frame = property_results_frame[
                    property_results_frame["Category"] == category
                ]

                if len(category_results_frame) == 0:
                    continue

                statistics_entries.extend(
                    cls._results_frame_to_statistics(
                        category_results_frame,
                        property_type,
                        n_components,
                        units[property_type],
                        category,
                        bootstrap_iterations,
                    )
                )

        return statistics_entries

    @classmethod
    def from_evaluator(
        cls,
        project_id: str,
        study_id: str,
        benchmark_id: str,
        reference_data_set: "PhysicalPropertyDataSet",
        estimated_data_set: "PhysicalPropertyDataSet",
        analysis_environments: List[ChemicalEnvironment],
        bootstrap_iterations: int = 1000,
    ) -> "BenchmarkResult":

        results_entries = cls._evaluator_to_results_entries(
            reference_data_set, estimated_data_set, analysis_environments
        )
        statistic_entries = cls._results_entries_to_statistics(
            results_entries, bootstrap_iterations
        )

        benchmark_result = BenchmarkResult(
            project_id=project_id,
            study_id=study_id,
            id=benchmark_id,
            statistic_entries=statistic_entries,
            results_entries=results_entries,
        )

        return benchmark_result


class OptimizationResult(BaseResult):

    objective_function: List[float] = Field(
        ..., description="The value of the objective function at each iteration"
    )
    refit_force_field: ForceField = Field(
        ..., description="The refit force field produced by the optimization."
    )
