from typing import Dict, List, Tuple

from pydantic import Field

from nonbonded.library.models import BaseORM


class ScatterSeries(BaseORM):

    name: str = Field(..., description="The name of this series.")

    x: List[float] = Field(..., description="The x values of the series.")
    y: List[float] = Field(..., description="The y values of the series.")

    metadata: List[str] = Field(
        ...,
        description="String metadata (e.g. smiles) associated with each " "data point.",
    )


class ScatterData(BaseORM):

    series: List[ScatterSeries] = Field(
        ..., description="The different series of this set."
    )


class StatisticData(BaseORM):

    values: Dict[str, float] = Field(
        ..., description="The value of this series statistic."
    )
    confidence_intervals: Dict[str, Tuple[float, float]] = Field(
        ..., description="The 95% confidence intervals."
    )


class ForceFieldResults(BaseORM):

    force_field_name: str = Field(
        ..., description="The name of the force field used to generate the results."
    )

    scatter_data: ScatterData = Field(
        ...,
        description="The reference values vs the estimated of the property obtained "
        "using this force field.",
    )
    statistic_data: StatisticData = Field(
        ..., description="Bootstrapped-statistics about the scatter data."
    )


class PropertyResults(BaseORM):

    property_type: str = Field(
        ..., description="The type of property that these results were collected for."
    )
    n_components: int = Field(
        ...,
        description="The number of components in the system for which the property "
        "was measured / estimated.",
    )

    force_field_results: List[ForceFieldResults] = Field(
        ...,
        description="The results obtained for each force field that was benchmarked "
        "against.",
    )


class BenchmarkResults(BaseORM):

    project_identifier: str = Field(
        ..., description="The project that this data set belongs to."
    )
    study_identifier: str = Field(
        ..., description="The study that this data set belongs to."
    )

    property_results: List[PropertyResults] = Field(
        ...,
        description="The results of each class of property which was benchmarked "
        "against.",
    )


class BenchmarkResultsCollection(BaseORM):

    results: List[BenchmarkResults] = Field(
        default_factory=list, description="A collection of benchmark results.",
    )


class OptimizationResult(BaseORM):

    project_identifier: str = Field(
        ..., description="The project that this data set belongs to."
    )
    study_identifier: str = Field(
        ..., description="The study that this data set belongs to."
    )
    optimization_identifier: str = Field(
        ..., description="The optimization that this data set belongs to."
    )

    objective_function: Dict[int, float] = Field(
        ..., description="The value of the objective function at each iteration"
    )


class OptimizationResultCollection(BaseORM):

    results: List[OptimizationResult] = Field(
        default_factory=list, description="A collection of optimization results.",
    )
