import re
from typing import Dict, List, Optional, Tuple

import numpy
import pandas

from nonbonded.library.models.datasets import DataSet, DataSetEntry
from nonbonded.library.models.projects import Benchmark
from nonbonded.library.models.results import BenchmarkResult, TargetResultType
from nonbonded.library.models.targets import (
    EvaluatorTarget,
    OptimizationTarget,
    RechargeTarget,
)
from nonbonded.library.statistics.statistics import StatisticType


def property_type_to_title(property_type: str, n_components: int):

    try:
        from openff.evaluator import unit
    except ImportError:
        unit = None

    abbreviations = {
        "Density": r"\rho",
        "DielectricConstant": r"\epsilon",
        "EnthalpyOfMixing": r"H_{mix}",
        "EnthalpyOfVaporization": r"H_{vap}",
        "ExcessMolarVolume": r"V_{ex}",
        "SolvationFreeEnergy": r"G_{solv}",
    }

    unit_string = DataSetEntry.default_units()[property_type]

    if unit is not None:

        property_unit = unit.Unit(unit_string)

        unit_string = (
            "" if property_unit == unit.dimensionless else f" ({property_unit:~P})"
        )

    abbreviation = abbreviations.get(property_type, property_type)

    if "FreeEnergy" not in property_type and n_components > 1:
        abbreviation = f"{abbreviation} (x)"

    return f"${abbreviation}$ {unit_string}"


def format_category(category: Optional[str]) -> str:
    """Formats a category ready for plotting."""

    if category is None:
        category = "Other"

    category = re.sub("Carboxylic Acid Ester", "Ester", category)
    category = re.sub("Carboxylic Acid", "Acid", category)

    return category


def combine_data_set_results(
    data_sets: List[DataSet],
    benchmarks: List[Benchmark],
    benchmark_results: List[BenchmarkResult],
) -> pandas.DataFrame:
    """Combines a set of benchmarked results with their corresponding reference
    data set values into a pandas data frame which can be readily plotted.

    Parameters
    ----------
    data_sets
        The data sets which contain the reference data points.
    benchmarks
        The benchmarks associated with each result.
    benchmark_results
        The results to map.

    Returns
    -------
        A pandas data frames containing the estimated and reference
        values for each set of benchmark results.

        The data frame has columns:

            * "Benchmark Id": The benchmark name.
            * "Property Type": The type of physical property.
            * "Property Title": A friendly title for the property type.
            * "Estimated Value": The benchmarked value.
            * "Estimated Std": The uncertainty in the benchmarked value.
            * "Reference Value": The reference value.
            * "Reference Std": The uncertainty in the reference value.
            * "Category": The category assigned to the data point.
    """
    reference_data_points: Dict[int, DataSetEntry] = {
        entry.id: entry for data_set in data_sets for entry in data_set.entries
    }

    # Re-shape the data into a pandas data frame for easier plotting.
    data_rows = []

    for benchmark, benchmark_result in zip(benchmarks, benchmark_results):

        for result_entry in benchmark_result.data_set_result.result_entries:

            reference_data_point = reference_data_points[result_entry.reference_id]

            reference_value = reference_data_point.value
            reference_std = reference_data_point.std_error

            estimated_value = result_entry.estimated_value
            estimated_std = result_entry.estimated_std_error

            # For now trim down the number of different categories and
            # shorten certain category names.
            for category in (
                [None] if len(result_entry.categories) == 0 else result_entry.categories
            ):

                category = re.sub("[<>~]", "+", format_category(category))

                property_type = (
                    f"{reference_data_point.property_type}-"
                    f"{len(reference_data_point.components)}"
                )

                # Generate a meaningful title for the plot.
                property_title = property_type_to_title(
                    reference_data_point.property_type,
                    len(reference_data_point.components),
                )

                data_row = {
                    "Benchmark Id": benchmark.id,
                    "Benchmark Name": benchmark.name,
                    "Property Type": property_type,
                    "Property Title": property_title,
                    "Estimated Value": estimated_value,
                    "Estimated Std": estimated_std,
                    "Reference Value": reference_value,
                    "Reference Std": reference_std,
                    "Category": category,
                }
                data_rows.append(data_row)

    return pandas.DataFrame(data_rows)


def combine_target_rmse(
    targets: List[OptimizationTarget],
    target_results: List[TargetResultType],
    target_labels: List[str],
):
    """Combines the RMSE information from multiple target results into a single,
    easily plottable, pandas data frame.

    Parameters
    ----------
    targets
        The targets which the results were collected for.
    target_results
        The target results to combine.
    target_labels
        The labels associated with each target result.

    Returns
    -------
        A pandas data frames containing the combined RMSE values.

        The data frame has columns:

            * "Label": The label associated with the parent result target.
            * "Data Type": The data type associated with a given RMSE. For evaluator
              target results this will be a combination of the property type and the
              number of components. For recharge targets this will be the targeted
              electronic property.
            * "Value": The value of the RMSE.
            * "Lower CI": The lower 95% confidence interval.
            * "Upper CI": The upper 95% confidence interval.
            * "Category": The category associated with the RMSE.
    """

    def statistic_to_key(target, statistic):

        if isinstance(target, EvaluatorTarget):
            return f"{statistic.property_type}-{statistic.n_components}"
        elif isinstance(target, RechargeTarget):
            return target.property

    # Gather the statistics
    statistics_per_label = {
        label: {
            (statistic_to_key(target, statistic), statistic.category): statistic
            for statistic in target_result.statistic_entries
            if statistic.category is not None
            and statistic.statistic_type == StatisticType.RMSE
        }
        for label, target, target_result in zip(target_labels, targets, target_results)
    }

    # Reshape the statistics into a uniform data frame.
    data_rows = []

    for label, statistics in statistics_per_label.items():

        for statistic_key, statistic in statistics.items():

            data_type, category = statistic_key

            data_row = {
                "Label": label,
                "Data Type": data_type,
                "Value": statistic.value,
                "Lower CI": numpy.abs(statistic.lower_95_ci - statistic.value),
                "Upper CI": numpy.abs(statistic.upper_95_ci - statistic.value),
                "Category": format_category(category),
            }

            data_rows.append(data_row)

    return pandas.DataFrame(data_rows)


def sort_categories_key(category: str) -> Tuple[str, Optional[str], Optional[int]]:
    """A function which may be used as the key when sorting a list of categories.
    This function assumes categories are based on chemical environments and
    compositions (up to a maximum of two components).

    Parameters
    ----------
    category
        The category to map to a sortable key.

    Returns
    -------
        A tuple containing at least the primary category key. For categories
        encoding a binary mixture, the tuple also the category key of the second
        component and an integer describing the type of composition (i.e. less than,
        equal or greater than).
    """
    splitter = (
        "<"
        if "<" in category
        else "~"
        if "~" in category
        else ">"
        if ">" in category
        else None
    )

    if splitter is None:
        return category, None, None

    splitter_ordering = {"<": 0, "~": 1, ">": 2}
    split_string = category.split(splitter)

    return (
        split_string[0].strip(),
        split_string[1].strip(),
        splitter_ordering[splitter],
    )
