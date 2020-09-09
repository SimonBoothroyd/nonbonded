import abc
import logging
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple, Union

import requests
from pydantic import Field, conint, validator
from typing_extensions import Literal

from nonbonded.library.config import settings
from nonbonded.library.models import BaseORM, BaseREST
from nonbonded.library.models.datasets import (
    Component,
    DataSet,
    DataSetCollection,
    DataSetEntry,
)
from nonbonded.library.models.forcefield import ForceField
from nonbonded.library.models.validators.string import IdentifierStr, NonEmptyStr
from nonbonded.library.statistics.statistics import StatisticType, compute_statistics
from nonbonded.library.utilities.checkmol import analyse_functional_groups
from nonbonded.library.utilities.environments import ChemicalEnvironment
from nonbonded.library.utilities.exceptions import UnsupportedEndpointError

if TYPE_CHECKING:

    import pandas
    from openff.evaluator.datasets import PhysicalPropertyDataSet

    PositiveInt = int
else:
    from pydantic import PositiveInt


logger = logging.getLogger(__name__)


class Statistic(BaseORM):
    """An object which contains information about a statistic (e.g. the RMSE) computed
    from a set of reference and estimated points."""

    statistic_type: StatisticType = Field(
        ..., description="The type of statistic recorded by this entry."
    )

    value: float = Field(..., description="The value of the statistic.")

    lower_95_ci: float = Field(
        ..., description="The lower 95% confidence interval of the statistic."
    )
    upper_95_ci: float = Field(
        ..., description="The upper 95% confidence interval of the statistic."
    )

    category: Optional[str] = Field(
        None, description="The category which this statistic has been placed into."
    )


class DataSetStatistic(Statistic):

    property_type: NonEmptyStr = Field(
        ..., description="The type of property which the statistic was calculated for."
    )
    n_components: Optional[PositiveInt] = Field(
        ...,
        description="The number of components in the systems which the statistic was "
        "calculated for (pure, binary, etc.).",
    )


class DataSetResultEntry(BaseORM):
    """An object which stores the value of an estimated data entry as well as the
    original id of the data entry which was estimated."""

    reference_id: int = Field(
        ...,
        description="The unique id of the original data point which has been "
        "estimated.",
    )

    estimated_value: float = Field(..., description="The estimated value.")
    estimated_std_error: float = Field(..., description="The estimated std error")

    category: Optional[str] = Field(
        ...,
        description="The category which this result has been assigned. This may "
        "indicate, for example, the measurement was made for a system of alcohols.",
    )


class DataSetResult(BaseORM):
    """Encodes the results of estimating a data set of physical properties using
    a particular force field as part of a sub-study."""

    result_entries: List[DataSetResultEntry] = Field(
        ...,
        description="The estimated values of each property within a reference data "
        "set.",
    )
    statistic_entries: List[DataSetStatistic] = Field(
        ...,
        description="Statistics about how the estimated properties compare to the "
        "reference set. These include, e.g. R^2 and RMSE values.",
    )

    @classmethod
    def _components_to_category(
        cls,
        components: List[Component],
        analysis_environments: List[ChemicalEnvironment],
    ) -> Optional[str]:

        import numpy

        if len(analysis_environments) == 0:
            return None

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
                return "Uncategorized"

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

            previous_component = sorted_components[
                assigned_environments.index(previous_environment)
            ]
            current_component = sorted_components[
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
        reference_data_set: Union[DataSet, DataSetCollection],
        estimated_data_set: "PhysicalPropertyDataSet",
        analysis_environments: List[ChemicalEnvironment],
    ) -> Tuple[List[DataSetResultEntry], "pandas.DataFrame"]:

        import pandas
        from openff.evaluator.datasets import PhysicalProperty

        if isinstance(reference_data_set, DataSet):
            reference_entries_by_id: Dict[str, DataSetEntry] = {
                int(x.id): x for x in reference_data_set.entries
            }
        elif isinstance(reference_data_set, DataSetCollection):
            reference_entries_by_id: Dict[str, DataSetEntry] = {
                int(y.id): y for x in reference_data_set.data_sets for y in x.entries
            }
        else:
            raise NotImplementedError()

        estimated_entries_by_id: Dict[str, PhysicalProperty] = {
            int(x.id): x for x in estimated_data_set
        }

        results_entries = []
        results_rows = []

        for identifier in reference_entries_by_id:

            if identifier not in estimated_entries_by_id:

                logger.warning(
                    f"The property with id={identifier} appears in the reference data "
                    f"set but not in the estimated set."
                )

                continue

            reference_entry = reference_entries_by_id[identifier]
            estimated_entry = estimated_entries_by_id[identifier]

            # Check that at the very least the two types of property are of the same
            # type and were measured for the same number of components
            assert reference_entry.property_type == estimated_entry.__class__.__name__
            assert len(reference_entry.components) == len(estimated_entry.substance)

            property_class = estimated_entry.__class__
            default_units = property_class.default_unit()

            results_entry = DataSetResultEntry(
                reference_id=reference_entry.id,
                estimated_value=estimated_entry.value.to(default_units).magnitude,
                estimated_std_error=estimated_entry.uncertainty.to(
                    default_units
                ).magnitude,
                category=cls._components_to_category(
                    reference_entry.components, analysis_environments
                ),
            )

            results_entries.append(results_entry)

            results_rows.append(
                {
                    "Property Type": reference_entry.property_type,
                    "N Components": len(reference_entry.components),
                    "Reference Value": reference_entry.value,
                    "Reference Std": reference_entry.std_error,
                    "Estimated Value": results_entry.estimated_value,
                    "Estimated Std": results_entry.estimated_std_error,
                    "Category": results_entry.category,
                }
            )

        results_frame = pandas.DataFrame(results_rows)

        return results_entries, results_frame

    @classmethod
    def _results_frame_to_statistics(
        cls,
        results_frame: "pandas.DataFrame",
        property_type: str,
        n_components: int,
        category: Optional[str],
        bootstrap_iterations: int,
        statistic_types: List[StatisticType],
    ) -> List[DataSetStatistic]:

        bulk_statistics, _, bulk_statistics_ci = compute_statistics(
            measured_values=results_frame["Reference Value"].values,
            measured_std=results_frame["Reference Std"].values,
            estimated_values=results_frame["Estimated Value"].values,
            estimated_std=results_frame["Estimated Std"].values,
            bootstrap_iterations=bootstrap_iterations,
            statistic_types=statistic_types,
        )

        statistics_entries = []

        for statistic_type in bulk_statistics:
            statistics_entry = DataSetStatistic(
                statistic_type=statistic_type,
                property_type=property_type,
                n_components=n_components,
                category=category,
                value=bulk_statistics[statistic_type],
                lower_95_ci=bulk_statistics_ci[statistic_type][0],
                upper_95_ci=bulk_statistics_ci[statistic_type][1],
            )
            statistics_entries.append(statistics_entry)

        return statistics_entries

    @classmethod
    def from_evaluator(
        cls,
        reference_data_set: Union[DataSet, DataSetCollection],
        estimated_data_set: "PhysicalPropertyDataSet",
        analysis_environments: List[ChemicalEnvironment],
        bootstrap_iterations: int = 1000,
        statistic_types: List[StatisticType] = None,
    ) -> "DataSetResult":

        if statistic_types is None:

            statistic_types = [StatisticType.RMSE, StatisticType.R2, StatisticType.MSE]

        results_entries, results_frame = cls._evaluator_to_results_entries(
            reference_data_set, estimated_data_set, analysis_environments
        )

        property_types = results_frame[
            ["Property Type", "N Components"]
        ].drop_duplicates()
        property_types = list(property_types.to_records(index=False))

        categories = results_frame["Category"].unique()

        if len(categories) == 1 and categories[0] is None:
            categories = []

        statistic_entries = []

        for (property_type, n_components) in property_types:

            property_results_frame = results_frame[
                (results_frame["Property Type"] == property_type)
                & (results_frame["N Components"] == n_components)
            ]

            # Calculate statistics over the entire set (i.e. not by category).
            statistic_entries.extend(
                cls._results_frame_to_statistics(
                    property_results_frame,
                    property_type,
                    n_components,
                    None,
                    bootstrap_iterations,
                    statistic_types,
                )
            )

            # Calculate statistics per category
            for category in categories:

                category_results_frame = property_results_frame[
                    property_results_frame["Category"] == category
                ]

                if len(category_results_frame) == 0:
                    continue

                statistic_entries.extend(
                    cls._results_frame_to_statistics(
                        category_results_frame,
                        property_type,
                        n_components,
                        category,
                        bootstrap_iterations,
                        statistic_types,
                    )
                )

        assert len(statistic_entries) <= len(property_types) * (
            len(categories) + 1
        ) * len(statistic_types)

        data_set_result = DataSetResult(
            statistic_entries=statistic_entries,
            result_entries=results_entries,
        )

        return data_set_result


class SubStudyResult(BaseREST, abc.ABC):

    id: IdentifierStr = Field(
        ...,
        description="The unique id of the sub-study which generated this result.",
    )

    study_id: IdentifierStr = Field(..., description="The id of the parent study.")
    project_id: IdentifierStr = Field(..., description="The id of the parent project.")

    @classmethod
    def _url_name(cls):
        return cls.__name__.replace("Result", "").lower() + "s"

    @classmethod
    def _get_endpoint(cls, *, project_id: str, study_id: str, model_id: str):
        return (
            f"{settings.API_URL}/projects/"
            f"{project_id}"
            f"/studies/"
            f"{study_id}"
            f"/{cls._url_name()}/"
            f"{model_id}"
            f"/results/"
        )

    def _post_endpoint(self):

        return (
            f"{settings.API_URL}/projects/"
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
            f"{settings.API_URL}/projects/"
            f"{self.project_id}"
            f"/studies/"
            f"{self.study_id}"
            f"/{self._url_name()}/"
            f"{self.id}"
            f"/results/"
        )

    @classmethod
    def from_rest(
        cls,
        *,
        project_id: str,
        study_id: str,
        model_id: str,
        requests_class=requests,
    ):
        # noinspection PyTypeChecker
        return super(SubStudyResult, cls).from_rest(
            project_id=project_id,
            study_id=study_id,
            model_id=model_id,
            requests_class=requests_class,
        )


class BenchmarkResult(SubStudyResult):

    data_set_result: DataSetResult = Field(
        ..., description="The analysed results of the benchmark"
    )

    @classmethod
    def from_evaluator(
        cls,
        project_id: str,
        study_id: str,
        benchmark_id: str,
        reference_data_set: Union[DataSet, DataSetCollection],
        estimated_data_set: "PhysicalPropertyDataSet",
        analysis_environments: List[ChemicalEnvironment],
        bootstrap_iterations: int = 1000,
    ) -> "BenchmarkResult":

        benchmark_result = BenchmarkResult(
            project_id=project_id,
            study_id=study_id,
            id=benchmark_id,
            data_set_result=DataSetResult.from_evaluator(
                reference_data_set=reference_data_set,
                estimated_data_set=estimated_data_set,
                analysis_environments=analysis_environments,
                bootstrap_iterations=bootstrap_iterations,
            ),
        )

        return benchmark_result


class TargetResult(BaseORM, abc.ABC):
    """A base class for the results of a particular optimization target at a
    single optimization iteration.
    """

    objective_function: float = Field(
        ...,
        description="The targets contribution to the total objective function.",
    )


class EvaluatorTargetResult(TargetResult):
    """Results output while training against an OpenFF Evaluator optimization
    target."""

    type: Literal["evaluator"] = "evaluator"

    statistic_entries: List[DataSetStatistic] = Field(
        ...,
        description="Statistics measuring the performance of the force field being "
        "refit against the training set.",
    )


class RechargeTargetResult(TargetResult):
    """Results output while training against an OpenFF Recharge optimization
    target at a particular optimization iteration."""

    type: Literal["recharge"] = "recharge"

    statistic_entries: List[Statistic] = Field(
        ...,
        description="Statistics measuring the performance of the force field being "
        "refit against the training set.",
    )


TargetResultType = Union[EvaluatorTargetResult, RechargeTargetResult]


class OptimizationResult(SubStudyResult):

    target_results: Dict[conint(ge=0), Dict[IdentifierStr, TargetResultType]] = Field(
        ...,
        description="The results output by each optimization target at each iteration.",
    )

    refit_force_field: ForceField = Field(
        ..., description="The refit force field produced by the optimization."
    )

    @validator("target_results")
    def validate_target_results(cls, value):

        # Make sure at least one target result is provided.
        assert len(value) > 0
        assert all(len(x) > 0 for x in value.values())

        # Make sure the targets are the same between iterations.
        expected_targets = value[next(iter(value))]

        for iteration in value:

            assert {*expected_targets} == {*value[iteration]}

            assert all(
                isinstance(
                    value[iteration][target_id], type(expected_targets[target_id])
                )
                for target_id in expected_targets
            )

        return value
