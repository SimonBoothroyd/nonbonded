from enum import Enum
from typing import Iterable, Tuple

import numpy


class StatisticType(Enum):

    R2 = "R^2"
    RMSE = "RMSE"
    MSE = "MSE"


def _compute_statistics(measured_values, estimated_values, statistics):
    """Calculates a collection of common statistics comparing the measured
    and estimated values.

    Parameters
    ----------
    measured_values: numpy.ndarray
        The experimentally measured values with shape=(number of data points)
    estimated_values: numpy.ndarray
        The computationally estimated values with shape=(number of data points)
    statistics: list of StatisticType
        The statistics to compute. If `None`, all statistics will be computed

    Returns
    -------
    numpy.ndarray
        An array of the summarised statistics, containing the
        R^2, RMSE, and MSE
    list of StatisticType
        Human readable labels for each of the statistics.
    """
    import scipy.stats

    if statistics is None:
        statistics = [StatisticType.R2, StatisticType.RMSE, StatisticType.MSE]

    summary_statistics = {}

    if StatisticType.R2 in statistics:

        with numpy.errstate(divide="ignore", invalid="ignore"):
            (_, _, r, _, _) = scipy.stats.linregress(measured_values, estimated_values)

        summary_statistics[StatisticType.R2] = r ** 2

    if StatisticType.RMSE in statistics:

        summary_statistics[StatisticType.RMSE] = numpy.sqrt(
            numpy.mean((estimated_values - measured_values) ** 2)
        )

    if StatisticType.MSE in statistics:

        summary_statistics[StatisticType.MSE] = numpy.mean(
            estimated_values - measured_values
        )

    return numpy.array([summary_statistics[x] for x in statistics]), statistics


def _compute_bootstrapped_statistics(
    measured_values,
    measured_stds,
    estimated_values,
    estimated_stds,
    statistics=None,
    percentile=0.95,
    bootstrap_iterations=1000,
):
    """Compute the bootstrapped mean and confidence interval for a set
    of common error statistics.

    Notes
    -----
    Bootstrapped samples are generated with replacement from the full
    original data set.

    Parameters
    ----------
    measured_values: numpy.ndarray
        The experimentally measured values with shape=(n_data_points)
    measured_stds: numpy.ndarray, optional
        The standard deviations in the experimentally measured values with
        shape=(number of data points)
    estimated_values: numpy.ndarray
        The computationally estimated values with shape=(n_data_points)
    estimated_stds: numpy.ndarray, optional
        The standard deviations in the computationally estimated values with
        shape=(number of data points)
    statistics: list of StatisticType
        The statistics to compute. If `None`, all statistics will be computed
    percentile: float
        The percentile of the confidence interval to calculate.
    bootstrap_iterations: int
        The number of bootstrap iterations to perform.
    """
    sample_count = len(measured_values)

    # Compute the mean of the statistics.
    mean_statistics, statistics_labels = _compute_statistics(
        measured_values, estimated_values, statistics
    )

    # Generate the bootstrapped statistics samples.
    sample_statistics = numpy.zeros((bootstrap_iterations, len(mean_statistics)))

    for sample_index in range(bootstrap_iterations):

        samples_indices = numpy.random.randint(
            low=0, high=sample_count, size=sample_count
        )

        sample_measured_values = measured_values[samples_indices]

        if measured_stds is not None:
            sample_measured_values += numpy.random.normal(0.0, measured_stds)

        sample_estimated_values = estimated_values[samples_indices]

        if estimated_stds is not None:
            sample_estimated_values += numpy.random.normal(0.0, estimated_stds)

        sample_statistics[sample_index], _ = _compute_statistics(
            sample_measured_values, sample_estimated_values, statistics
        )

    # Compute the SEM
    standard_errors_array = numpy.std(sample_statistics, axis=0)

    # Store the means and SEMs in dictionaries
    means = dict()
    standard_errors = dict()

    for statistic_index in range(len(mean_statistics)):
        statistic_label = statistics_labels[statistic_index]

        means[statistic_label] = mean_statistics[statistic_index]
        standard_errors[statistic_label] = standard_errors_array[statistic_index]

    # Compute the confidence intervals.
    lower_percentile_index = int(bootstrap_iterations * (1 - percentile) / 2)
    upper_percentile_index = int(bootstrap_iterations * (1 + percentile) / 2)

    confidence_intervals = dict()

    for statistic_index in range(len(mean_statistics)):
        statistic_label = statistics_labels[statistic_index]

        sorted_samples = numpy.sort(sample_statistics[:, statistic_index])

        confidence_intervals[statistic_label] = (
            sorted_samples[lower_percentile_index],
            sorted_samples[upper_percentile_index],
        )

    return means, standard_errors, confidence_intervals


def bootstrap_residuals(
    squared_residuals: Iterable[float],
    percentile: float = 0.95,
    bootstrap_iterations: int = 1000,
) -> Tuple[float, float, Tuple[float, float]]:
    """A general method for computing the RMSE and associated confidence intervals
    given a list of squared residuals.

    Parameters
    ----------
    squared_residuals
        The list of squared residuals - i.e. (ref - calc)^2
    percentile
        The confidence interval percentile.
    bootstrap_iterations
        The number of bootstrap intervals.

    Returns
    -------
        The average RMSE, the STD error on the RMSE and the confidence
        intervals (as defined by the provided ``percentile``).
    """

    square_residuals = numpy.array(squared_residuals)

    # Compute the mean RMSE
    mean = numpy.sqrt(square_residuals.sum() / len(square_residuals))

    # Generate the bootstrapped statistics samples.
    sample_count = len(square_residuals)
    sample_statistics = numpy.zeros((bootstrap_iterations, 1))

    for sample_index in range(bootstrap_iterations):

        samples_indices = numpy.random.randint(
            low=0, high=sample_count, size=sample_count
        )

        sample_square_residuals = square_residuals[samples_indices]

        sample_statistics[sample_index] = numpy.sqrt(
            sample_square_residuals.sum() / len(sample_square_residuals)
        )

    # Compute the SEM
    standard_error = numpy.std(sample_statistics, axis=0)[0]

    # Compute the confidence intervals.
    lower_percentile_index = int(bootstrap_iterations * (1 - percentile) / 2)
    upper_percentile_index = int(bootstrap_iterations * (1 + percentile) / 2)

    sorted_samples = numpy.sort(sample_statistics[:, 0])

    confidence_intervals = (
        sorted_samples[lower_percentile_index],
        sorted_samples[upper_percentile_index],
    )

    return mean, standard_error, confidence_intervals


def compute_statistics(
    measured_values,
    measured_std,
    estimated_values,
    estimated_std,
    bootstrap_iterations,
    statistic_types,
):
    """Computes a set of statistics comparing deviations of a set
    of estimated properties from the corresponding measured properties

    Parameters
    ----------
    measured_values: numpy.ndarray
        The measured values.
    measured_std: numpy.ndarray
        The std error in the measured values.
    estimated_values: numpy.ndarray
        The estimated values.
    estimated_std: numpy.ndarray
        The std error in the estimated values.
    bootstrap_iterations: int
        The number of bootstrap intervals to perform when computing the
        standard error and confidence intervals.
    statistic_types: list of StatisticType

    Returns
    -------
    dict of StatisticType and float
        The value of each statistic.
    dict of StatisticType and float
        The standard deviation of each statistic.
    dict of StatisticType and tuple of float and float
        The 95% confidence intervals of each statistic.
    """
    measured_std = measured_std.astype(numpy.float64)
    measured_std[numpy.isnan(measured_std)] = 0.0

    (
        bootstrapped_statistics,
        bootstrapped_std,
        bootstrapped_ci,
    ) = _compute_bootstrapped_statistics(
        measured_values,
        measured_std,
        estimated_values,
        estimated_std,
        statistics=statistic_types,
        bootstrap_iterations=bootstrap_iterations,
    )

    return bootstrapped_statistics, bootstrapped_std, bootstrapped_ci
