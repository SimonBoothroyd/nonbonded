import abc
from typing import List, Optional

import requests
from pydantic import Field

from nonbonded.library.models import BaseORM, BaseREST
from nonbonded.library.models.datasets import Component
from nonbonded.library.models.forcefield import ForceField
from nonbonded.library.utilities.exceptions import UnsupportedEndpointError


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


class OptimizationResult(BaseResult):

    objective_function: List[float] = Field(
        ..., description="The value of the objective function at each iteration"
    )
    refit_force_field: ForceField = Field(
        ..., description="The refit force field produced by the optimization."
    )
