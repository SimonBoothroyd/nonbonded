import abc
import logging
from typing import TypeVar

from nonbonded.library.factories.factories import BaseRecursiveFactory
from nonbonded.library.models.projects import Benchmark, Optimization, Project, Study

logger = logging.getLogger(__name__)

T = TypeVar("T")
S = TypeVar("S")


class PlotFactory(BaseRecursiveFactory, abc.ABC):
    """A factory used to generate plots of the outputs of the optimizations and
    benchmarks in a standard directory structure.
    """

    @classmethod
    def model_type_to_factory(cls, model_type):

        from nonbonded.library.factories.plots.benchmark import BenchmarkFactory
        from nonbonded.library.factories.plots.optimization import OptimizationFactory

        if issubclass(model_type, (Project, Study)):
            return PlotFactory
        elif issubclass(model_type, Optimization):
            return OptimizationFactory
        elif issubclass(model_type, Benchmark):
            return BenchmarkFactory

        raise NotImplementedError()

    @classmethod
    def _generate(cls, **kwargs):
        pass

    @classmethod
    def generate(cls, model: T):
        """Generates plots from the output of a particular sub-study.

        Parameters
        ----------
        model
            The model to generate the plots for.
        """

        super(PlotFactory, cls).generate(model=model)
