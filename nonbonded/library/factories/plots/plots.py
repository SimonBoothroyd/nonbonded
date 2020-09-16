import abc
import logging
import os
from typing import List, Tuple, TypeVar

from typing_extensions import Literal

from nonbonded.library.models.projects import Benchmark, Optimization, SubStudy
from nonbonded.library.models.results import SubStudyResult
from nonbonded.library.utilities import temporary_cd

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
    def _load_sub_study(cls, directory) -> Tuple[SubStudy, SubStudyResult]:
        """Attempts to load a plottable sub-study from a specified directory.

        Parameters
        ----------
        directory
            The directory to attempt to lead the sub-study from.

        Returns
        -------
            The sub-study and its associated results.
        """
        raise NotImplementedError()

    @classmethod
    @abc.abstractmethod
    def _plot(
        cls,
        directories: List[str],
        sub_studies: List[SubStudy],
        results: List[SubStudyResult],
        file_type: Literal["png", "pdf"],
    ):
        """Plots the output of a set of sub-studies.

        Parameters
        ----------
        directories
            The directories which each sub-study was loaded from.
        sub_studies
            The sub-studies to plot.
        results
            The results associated with each of the sub-studies.
        file_type
            The file type to use for the plots.
        """
        raise NotImplementedError()

    @classmethod
    def plot(cls, directories: List[str], file_type: Literal["png", "pdf"]):
        """Plots the analyzed output of a sub-study.

        Parameters
        ----------
        directories
            The directories containing the sub-studies to plot.
        file_type
            The file type to use for the plots.
        """

        if len(directories) == 0:
            return

        # Load in the sub-studies and their results.
        sub_studies = []
        results = []

        for directory in directories:

            sub_study, result = cls._load_sub_study(directory)

            sub_studies.append(sub_study)
            results.append(result)

        # Attempt the plot the sub-studies and save them in the plots folder.
        os.makedirs("plots", exist_ok=True)

        with temporary_cd("plots"):
            cls._plot(
                [os.path.join(os.path.pardir, directory) for directory in directories],
                sub_studies,
                results,
                file_type,
            )
