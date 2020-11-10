import re
from typing import Dict, List

import pandas

from nonbonded.library.models.datasets import DataSet, DataSetEntry
from nonbonded.library.models.projects import Benchmark
from nonbonded.library.models.results import BenchmarkResult


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
            category = result_entry.category

            if category is None:
                category = "Uncategorized"

            category = re.sub("[<>~]", "+", category)
            category = re.sub("Carboxylic Acid Ester", "Ester", category)
            category = re.sub("Carboxylic Acid", "Acid", category)

            property_type = (
                f"{reference_data_point.property_type}-"
                f"{len(reference_data_point.components)}"
            )

            # Generate a meaningful title for the plot.
            property_title = property_type_to_title(
                reference_data_point.property_type, len(reference_data_point.components)
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
