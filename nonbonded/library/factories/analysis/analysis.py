import abc
import logging
from typing import TypeVar

from nonbonded.library.factories.factories import BaseRecursiveFactory
from nonbonded.library.models.projects import Benchmark, Optimization, Project, Study

logger = logging.getLogger(__name__)

T = TypeVar("T")
S = TypeVar("S")


class AnalysisFactory(BaseRecursiveFactory, abc.ABC):
    """A factory used analyze the optimizations and benchmarks in a standard
    directory structure.
    """

    @classmethod
    def model_type_to_factory(cls, model_type):

        from nonbonded.library.factories.analysis.benchmark import BenchmarkFactory
        from nonbonded.library.factories.analysis.optimization import (
            OptimizationFactory,
        )

        if issubclass(model_type, (Project, Study)):
            return AnalysisFactory
        elif issubclass(model_type, Optimization):
            return OptimizationFactory
        elif issubclass(model_type, Benchmark):
            return BenchmarkFactory

        raise NotImplementedError()

    @classmethod
    def _generate(cls, **kwargs):
        pass

    @classmethod
    def generate(cls, model: T, reindex: bool):
        """Generates statistics from the output of a particular sub-study.

        Parameters
        ----------
        model
            The model to generate the inputs for.
        reindex
            Whether to re-index the evaluated data sets before analysis to match
            the database indices. This option is expected to only be used for
            analysing the results of past studies not generated using the framework.
        """

        super(AnalysisFactory, cls).generate(model=model, reindex=reindex)
