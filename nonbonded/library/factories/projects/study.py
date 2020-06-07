import logging
import os

from nonbonded.library.factories.projects.benchmark import BenchmarkFactory
from nonbonded.library.factories.projects.optimization import OptimizationFactory
from nonbonded.library.models.projects import Optimization, Study
from nonbonded.library.utilities import temporary_cd

logger = logging.getLogger(__name__)


class StudyFactory:
    """An factory used to create the directory structure and
    inputs for a particular study.
    """

    @classmethod
    def _yield_child_factory(cls, study: Study):
        """Temporarily navigates into the parent directory of each child of
        a study (creating it if it doesn't exist) and then yields the
        child and its corresponding factory.

        Parameters
        ----------
        study
            The parent study
        """

        os.makedirs(study.id, exist_ok=True)

        optimizations_directory = os.path.join(study.id, "optimizations")
        benchmarks_directory = os.path.join(study.id, "benchmarks")

        for child in [*study.optimizations, *study.benchmarks]:

            child_directory = (
                optimizations_directory
                if isinstance(child, Optimization)
                else benchmarks_directory
            )
            os.makedirs(child_directory, exist_ok=True)

            with temporary_cd(child_directory):

                factory = (
                    OptimizationFactory
                    if isinstance(child, Optimization)
                    else BenchmarkFactory
                )

                yield child, factory

    @classmethod
    def retrieve_results(
        cls, study: Study,
    ):
        """Retrieves the full results for a study and stores them
        in an organised directory structure.

        Parameters
        ----------
        study
            The study to retrieve the results for.
        """

        for child, factory in cls._yield_child_factory(study):
            factory.retrieve_results(child)

    @classmethod
    def generate_inputs(
        cls,
        study: Study,
        backend_name: str,
        environment_name: str,
        max_workers: int,
        max_wall_clock: str,
        max_memory: int,
    ):

        port_counter = 8000

        for child, factory in cls._yield_child_factory(study):

            logger.info(f"Generating {child.__class__.__name__.lower()}={child.id}")

            factory.generate_inputs(
                child,
                backend_name,
                environment_name,
                port_counter,
                max_workers,
                max_wall_clock,
                max_memory,
            )

            port_counter += 1
