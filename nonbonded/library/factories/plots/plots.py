import abc
import logging
from typing import TypeVar

from nonbonded.library.models.projects import Benchmark, Optimization

logger = logging.getLogger(__name__)

T = TypeVar("T")
S = TypeVar("S")


class PlotFactory(abc.ABC):
    """A factory used to analyze the results of a particular sub-study."""

    @classmethod
    def model_type_to_factory(cls, model_type):

        from nonbonded.library.factories.plots.benchmark import BenchmarkPlotFactory
        from nonbonded.library.factories.plots.optimization import (
            OptimizationPlotFactory,
        )

        if issubclass(model_type, Optimization):
            return OptimizationPlotFactory
        elif issubclass(model_type, Benchmark):
            return BenchmarkPlotFactory

        raise NotImplementedError()

    @classmethod
    @abc.abstractmethod
    def plot(cls):
        """Plots the analyzed output of a sub-study."""
        raise NotImplementedError()
