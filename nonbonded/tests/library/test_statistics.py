import numpy

from nonbonded.library.statistics.statistics import StatisticType, compute_statistics

N_DATA_POINTS = 1000
N_ITERATIONS = 1000


def test_rmse():
    """Test that the statistics module returns the 'correct' RMSE
    to within some noise given a set of noisy estimated values."""

    expected_std = numpy.random.rand() + 1.0

    estimated_values = numpy.random.normal(0.0, expected_std, N_DATA_POINTS)
    estimated_std = numpy.zeros(N_DATA_POINTS)

    (statistic_values, _, _) = compute_statistics(
        numpy.zeros(N_DATA_POINTS),
        numpy.array([None] * N_DATA_POINTS),
        estimated_values,
        estimated_std,
        N_ITERATIONS,
        statistic_types=[StatisticType.RMSE],
    )

    assert numpy.isclose(statistic_values[StatisticType.RMSE], expected_std, rtol=0.1)


def test_r2():
    """Test that the statistics module returns the 'correct' R2
    to within some noise given a set of noisy estimated values."""

    measured_values = numpy.linspace(0.0, 1.0, N_DATA_POINTS)
    estimated_values = measured_values + numpy.random.rand() / 100.0

    (statistic_values, _, _) = compute_statistics(
        measured_values,
        numpy.zeros(N_DATA_POINTS),
        estimated_values,
        numpy.zeros(N_DATA_POINTS),
        N_ITERATIONS,
        statistic_types=[StatisticType.R2],
    )

    assert numpy.isclose(statistic_values[StatisticType.R2], 1.0, rtol=0.05)

    estimated_values = numpy.zeros(N_DATA_POINTS) + numpy.random.rand() / 100.0

    (statistic_values, _, _) = compute_statistics(
        measured_values,
        numpy.zeros(N_DATA_POINTS),
        estimated_values,
        numpy.zeros(N_DATA_POINTS),
        N_ITERATIONS,
        statistic_types=[StatisticType.R2],
    )

    assert numpy.isclose(statistic_values[StatisticType.R2], 0.0, rtol=0.05)


def test_mse():
    """Test that the statistics module returns the 'correct' R2
    to within some noise given a set of noisy estimated values."""

    n_half = int(N_DATA_POINTS / 2)
    n_data_points = n_half * 2

    measured_values = numpy.zeros(n_data_points)
    estimated_values = numpy.array([-1.0, 1.0] * n_half).flatten()

    (statistic_values, _, _) = compute_statistics(
        measured_values,
        numpy.zeros(n_data_points),
        estimated_values,
        numpy.zeros(n_data_points),
        N_ITERATIONS,
        statistic_types=[StatisticType.MSE],
    )

    assert numpy.isclose(statistic_values[StatisticType.MSE], 0.0, rtol=0.05)
