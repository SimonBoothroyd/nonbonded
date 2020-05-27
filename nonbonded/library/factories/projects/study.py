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
    def generate(
        cls,
        study: Study,
        backend_name: str,
        environment_name: str,
        max_workers: int,
        max_wall_clock: str,
        max_memory: int,
    ):

        root_directory = study.id
        os.makedirs(root_directory, exist_ok=True)

        port_counter = 8000

        with temporary_cd(root_directory):

            for child in [*study.optimizations, *study.benchmarks]:

                logger.info(f"Generating {child.__class__.__name__.lower()}={child.id}")

                factory = (
                    OptimizationFactory
                    if isinstance(child, Optimization)
                    else BenchmarkFactory
                )

                factory.generate(
                    child,
                    backend_name,
                    environment_name,
                    port_counter,
                    max_workers,
                    max_wall_clock,
                    max_memory,
                )

                port_counter += 1
