import abc
import logging
from typing import TypeVar

from nonbonded.library.models.projects import Benchmark, Optimization

logger = logging.getLogger(__name__)

T = TypeVar("T")
S = TypeVar("S")


class AnalysisFactory(abc.ABC):
    """A factory used to analyze the results of a particular sub-study."""

    @classmethod
    def model_type_to_factory(cls, model_type):

        from nonbonded.library.factories.analysis.benchmark import (
            BenchmarkAnalysisFactory,
        )
        from nonbonded.library.factories.analysis.optimization import (
            OptimizationAnalysisFactory,
        )

        if issubclass(model_type, Optimization):
            return OptimizationAnalysisFactory
        elif issubclass(model_type, Benchmark):
            return BenchmarkAnalysisFactory

        raise NotImplementedError()

    @classmethod
    @abc.abstractmethod
    def analyze(cls, reindex: bool):
        """Generates statistics from the output of a particular sub-study.

        Parameters
        ----------
        reindex
            Whether to re-index the evaluated data sets before analysis to match
            the database indices. This option is expected to only be used for
            analysing the results of past studies not generated using the framework.
        """
        raise NotImplementedError()
