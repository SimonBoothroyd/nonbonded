import functools
from typing import Tuple

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from nonbonded.backend.database import models
from nonbonded.backend.database.crud.projects import ProjectCRUD, StudyCRUD
from nonbonded.backend.database.utilities.exceptions import (
    ProjectExistsError,
    ProjectNotFoundError, StudyExistsError, StudyNotFoundError,
)
from nonbonded.library.models.authors import Author
from nonbonded.library.models.projects import Project, Study
from nonbonded.tests.backend.crud.utilities import (
    compare_projects,
    create_author,
    create_empty_project,
    create_empty_study, compare_studies, create_and_compare_models, paginate_models,
    update_and_compare_model,
)


class TestProjectCRUD:

    @staticmethod
    def create(db: Session) -> Project:
        """Creates a new project and commits it the current session.

        Parameters
        ----------
        db
            The current data base session.
        """
        db_project = ProjectCRUD.create(db, create_empty_project("project-1"))

        db.add(db_project)
        db.commit()

        return ProjectCRUD.db_to_model(db_project)

    def test_create_read_empty(self, db: Session):
        """Test that an empty project (i.e. one without studies) can be created, and then
        read back out again while maintaining the integrity of the data.
        """

        project_id = "project-1"
        project = create_empty_project(project_id)

        create_and_compare_models(
            db,
            project,
            ProjectCRUD.create,
            ProjectCRUD.read_all,
            functools.partial(ProjectCRUD.read, project_id=project_id),
            compare_projects,
        )

        # Make sure projects with duplicate ids cannot be added.
        with pytest.raises(ProjectExistsError):
            ProjectCRUD.create(db, project)

    def test_create_read(self, db: Session):
        """Test that a project containing studies can be created, and then
        read back out again while maintaining the integrity of the data.
        """

        project = create_empty_project("project-1")
        project.studies = [create_empty_study(project.id, "study-1")]

        create_and_compare_models(
            db,
            project,
            ProjectCRUD.create,
            ProjectCRUD.read_all,
            functools.partial(ProjectCRUD.read, project_id=project.id),
            compare_projects,
        )

    def test_update_empty(self, db: Session):
        """Test that an empty project (i.e. one without studies) can be correctly
        updated.
        """
        from nonbonded.backend.database.models.projects import author_projects_table

        project = self.create(db)

        # Test simple text updates
        updated_project = project.copy()
        updated_project.name += " Updated"
        updated_project.description += " Updated"

        update_and_compare_model(
            db,
            updated_project,
            ProjectCRUD.update,
            functools.partial(ProjectCRUD.read, project_id=project.id),
            compare_projects,
        )

        # Test adding a new author.
        updated_project.authors = [
            *updated_project.authors,
            Author(name="Fake Name 2", email="fake@email2.com", institute="Fake"),
        ]
        update_and_compare_model(
            db,
            updated_project,
            ProjectCRUD.update,
            functools.partial(ProjectCRUD.read, project_id=project.id),
            compare_projects,
        )

        # Make sure the authors list looks as expected
        assert db.query(models.Author.email).count() == 2

        # Test removing an author.
        updated_project.authors = [create_author()]
        update_and_compare_model(
            db,
            updated_project,
            ProjectCRUD.update,
            functools.partial(ProjectCRUD.read, project_id=project.id),
            compare_projects,
        )

        # Make sure the author was removed from the association table
        assert db.query(author_projects_table).count() == 1

        # Test that adding an invalid author raises the correct exception.
        bad_updated_project = updated_project.copy()
        bad_updated_project.authors = [
            Author(**{**create_author().dict(), "name": "Fake 2"})
        ]

        with pytest.raises(IntegrityError):
            update_and_compare_model(
                db,
                bad_updated_project,
                ProjectCRUD.update,
                functools.partial(ProjectCRUD.read, project_id=project.id),
                compare_projects,
            )

    def test_update_studies(self, db: Session):
        """Test that an project studies can be correctly updated.
        """

        # Create the parent project.
        project = self.create(db)

        # Attempt to add a new study by updating the existing project.
        project.studies = [create_empty_study(project.id, "study-1")]

        update_and_compare_model(
            db,
            project,
            ProjectCRUD.update,
            functools.partial(ProjectCRUD.read, project_id=project.id),
            compare_projects,
        )

        assert db.query(models.Study.id).count() == 1

        # Attempt to update the study through a project update.
        project.studies[0].name = "Updated"

        update_and_compare_model(
            db,
            project,
            ProjectCRUD.update,
            functools.partial(ProjectCRUD.read, project_id=project.id),
            compare_projects,
        )

        assert StudyCRUD.query(db, project.id, "study-1").name == "Updated"

        # Attempt to remove the study via project updates.
        project.studies = []

        update_and_compare_model(
            db,
            project,
            ProjectCRUD.update,
            functools.partial(ProjectCRUD.read, project_id=project.id),
            compare_projects,
        )

        assert db.query(models.Study.id).count() == 0

    def test_delete_empty(self, db: Session):
        """Test that an empty project (i.e. one without studies) can be correctly
        deleted.
        """
        from nonbonded.backend.database.models.projects import author_projects_table

        project = self.create(db)

        assert db.query(models.Author.id).count() == 1

        ProjectCRUD.delete(db, project.id)
        db.commit()

        assert db.query(models.Project.id).count() == 0
        assert db.query(models.Author.id).count() == 1
        assert db.query(author_projects_table).count() == 0

    def test_delete(self, db: Session):
        """Test that a projects studies also get deleted when it gets deleted.
        """

        project, _ = TestStudyCRUD.create(db)

        assert db.query(models.Study.id).count() == 1

        ProjectCRUD.delete(db, project.id)
        db.commit()

        assert db.query(models.Study.id).count() == 0

    def test_pagination(self, db: Session):

        paginate_models(
            db=db,
            models_to_create=[
                create_empty_project("project-1"),
                create_empty_project("project-2"),
                create_empty_project("project-3"),
            ],
            create_function=ProjectCRUD.create,
            read_all_function=ProjectCRUD.read_all,
            compare_function=compare_projects,
        )

    def test_delete_not_found(self, db: Session):

        with pytest.raises(ProjectNotFoundError):
            ProjectCRUD.delete(db, "project-id")

    def test_duplicate_id(self, db: Session):
        """Make sure the database integrity tests catch
        adding two projects with the same id in the same commit.
        """

        # Test adding duplicates in the same commit.
        project_id = "project-1"
        project = create_empty_project(project_id)

        db_project_1 = ProjectCRUD.create(db, project)
        db_project_2 = ProjectCRUD.create(db, project)

        db.add(db_project_1)
        db.add(db_project_2)

        with pytest.raises(IntegrityError):
            db.commit()


class TestStudyCRUD:

    @staticmethod
    def create(db: Session) -> Tuple[Project, Study]:
        """Commits a new project to the current session and appends an empty
        study onto it.

        Parameters
        ----------
        db
            The current data base session.
        """
        project = create_empty_project("project-1")
        project.studies = [create_empty_study(project.id, "study-1")]

        db_project = ProjectCRUD.create(db, project)
        db.add(db_project)
        db.commit()

        project = ProjectCRUD.db_to_model(db_project)
        return project, project.studies[0]

    def test_create_read_empty(self, db: Session):
        """Test that a study can be successfully created and then
        retrieved out again while maintaining the integrity of the data.
        """

        parent = TestProjectCRUD.create(db)
        study = create_empty_study(parent.id, "study-1")

        create_and_compare_models(
            db,
            study,
            StudyCRUD.create,
            functools.partial(StudyCRUD.read_all, project_id=parent.id),
            functools.partial(StudyCRUD.read, project_id=parent.id, study_id=study.id),
            compare_studies,
        )

        # Test that adding a new study with the same id raises an exception
        with pytest.raises(StudyExistsError):

            create_and_compare_models(
                db,
                study,
                StudyCRUD.create,
                None,
                StudyCRUD.read,
                compare_studies,
            )

    def test_update_empty(self, db: Session):
        """Test that an empty study (i.e. one without optimization and benchmarks)
        can be correctly updated.
        """
        _, study = self.create(db)

        # Test simple text updates
        updated_study = study.copy()
        updated_study.name += " Updated"
        updated_study.description += " Updated"

        update_and_compare_model(
            db,
            updated_study,
            StudyCRUD.update,
            functools.partial(
                StudyCRUD.read, project_id=study.project_id, study_id=study.id
            ),
            compare_studies,
        )

    def test_missing_parent(self, db: Session):
        """Test that an exception is raised when a study is added but
        the parent project cannot be found.
        """

        study = create_empty_study("project-1", "study-1")

        with pytest.raises(ProjectNotFoundError):

            create_and_compare_models(
                db,
                study,
                StudyCRUD.create,
                None,
                StudyCRUD.read,
                compare_studies,
            )

    def test_delete_empty(self, db: Session):
        """Test that an empty study (i.e. one without any children) can be correctly
        deleted.
        """

        project, study = self.create(db)

        db_project = ProjectCRUD.query(db, project.id)
        assert len(db_project.studies) == 1

        StudyCRUD.delete(db, project.id, study.id)
        db.commit()

        assert db.query(models.Study.id).count() == 0

        db_project = ProjectCRUD.query(db, project.id)
        assert len(db_project.studies) == 0

    def test_delete_not_found(self, db: Session):

        # Try to delete a study when there is no project or study
        with pytest.raises(StudyNotFoundError):
            StudyCRUD.delete(db, "project-1", "study-id")

        # Try to delete a study when there is only a project but no study
        project = TestProjectCRUD.create(db)

        with pytest.raises(StudyNotFoundError):
            StudyCRUD.delete(db, project.id, "study-id")
