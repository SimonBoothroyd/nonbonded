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
    def _yield_child_factory(cls, project: Project):
        """Temporarily navigates into the parent directory of each child of
        a project (creating it if it doesn't exist) and then yields the
        child and its corresponding factory.

        Parameters
        ----------
        project
            The parent project
        """

        root_directory = project.id
        os.makedirs(root_directory, exist_ok=True)

        if len(project.studies) > 0:

            studies_directory = os.path.join(root_directory, "studies")
            os.makedirs(studies_directory, exist_ok=True)

            with temporary_cd(studies_directory):

                for study in project.studies:
                    yield study, StudyFactory

    @classmethod
    def retrieve_results(
        cls, project: Project,
    ):
        """Retrieves the full results for a project and stores them
        in an organised directory structure.

        Parameters
        ----------
        project
            The project to retrieve the results for.
        """

        for study, factory in cls._yield_child_factory(project):
            factory.retrieve_results(study)

    @classmethod
    def generate_inputs(
        cls,
        project: Project,
        backend_name: str,
        environment_name: str,
        max_workers: int,
        max_wall_clock: str,
        max_memory: int,
    ):

        for study, factory in cls._yield_child_factory(project):

            logger.info(f"Generating {study.__class__.__name__.lower()}={study.id}")

            StudyFactory.generate_inputs(
                study,
                backend_name,
                environment_name,
                max_workers,
                max_wall_clock,
                max_memory,
            )
