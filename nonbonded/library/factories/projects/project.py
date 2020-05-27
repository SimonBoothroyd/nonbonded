import logging
import os

from nonbonded.library.factories.projects.study import StudyFactory
from nonbonded.library.models.projects import Project
from nonbonded.library.utilities import temporary_cd

logger = logging.getLogger(__name__)


class ProjectFactory:
    """An factory used to create the directory structure and
    inputs for a particular project.
    """

    @classmethod
    def generate(
        cls,
        project: Project,
        backend_name: str,
        environment_name: str,
        max_workers: int,
        max_wall_clock: str,
        max_memory: int,
    ):
        root_directory = project.id
        os.makedirs(root_directory, exist_ok=True)

        studies_directory = os.path.join(root_directory, "studies")
        os.makedirs(studies_directory, exist_ok=True)

        with temporary_cd(studies_directory):

            for study in project.studies:

                logger.info(f"Generating {study.__class__.__name__.lower()}={study.id}")

                StudyFactory.generate(
                    study,
                    backend_name,
                    environment_name,
                    max_workers,
                    max_wall_clock,
                    max_memory,
                )
