from nonbonded.library.plotting.plotly.optimization import plot_objective_per_iteration


def test_plot_objective_per_iteration(optimizations_and_results, tmpdir):

    optimizations, results = optimizations_and_results

    figure = plot_objective_per_iteration(optimizations, results)

    assert figure is not None
    assert figure.to_plotly() is not None
