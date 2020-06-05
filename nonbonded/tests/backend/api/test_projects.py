import pytest
from fastapi.testclient import TestClient
from requests import HTTPError
from sqlalchemy.orm import Session

from nonbonded.backend.database import models
from nonbonded.library.models.projects import Project, Study
from nonbonded.tests.backend.crud.utilities.commit import commit_project, commit_study
from nonbonded.tests.backend.crud.utilities.comparison import (
    compare_projects,
    compare_studies,
)
from nonbonded.tests.backend.crud.utilities.create import (
    create_empty_project,
    create_empty_study,
)


class TestProjectEndpoints:
    def test_get(self, rest_client: TestClient, rest_db: Session):

        project = commit_project(rest_db)
        rest_project = Project.from_rest(
            project_id=project.id, requests_class=rest_client
        )

        compare_projects(project, rest_project)

    def test_post(self, rest_client: TestClient):

        project = create_empty_project("project-1")
        rest_project = Project.upload(project, rest_client)

        compare_projects(project, rest_project)

    def test_put(self, rest_client: TestClient, rest_db: Session):

        original_project = commit_project(rest_db)

        updated_project = original_project.copy()
        updated_project.name = "Updated"

        rest_project = Project.update(updated_project, rest_client)

        compare_projects(updated_project, rest_project)

    def test_delete(self, rest_client: TestClient, rest_db: Session):

        project = commit_project(rest_db)
        assert rest_db.query(models.Project.id).count() == 1

        project.delete(rest_client)
        assert rest_db.query(models.Project.id).count() == 0

    def test_not_found(self, rest_client: TestClient):

        project = create_empty_project("project-1")

        with pytest.raises(HTTPError) as error_info:
            project.delete(rest_client)

        assert error_info.value.response.status_code == 404

        with pytest.raises(HTTPError) as error_info:
            project.update(rest_client)

        assert error_info.value.response.status_code == 404


class TestStudyEndpoints:
    def test_get(self, rest_client: TestClient, rest_db: Session):

        _, study = commit_study(rest_db)
        rest_study = Study.from_rest(
            project_id=study.project_id, study_id=study.id, requests_class=rest_client
        )

        compare_studies(study, rest_study)

    def test_post(self, rest_client: TestClient, rest_db: Session):

        project = commit_project(rest_db)
        study = create_empty_study(project.id, "study-1")

        rest_study = Study.upload(study, rest_client)

        compare_studies(study, rest_study)

    def test_put(self, rest_client: TestClient, rest_db: Session):

        _, original_study = commit_study(rest_db)

        updated_study = original_study.copy()
        updated_study.name = "Updated"

        rest_study = Study.update(updated_study, rest_client)

        compare_studies(updated_study, rest_study)

    def test_delete(self, rest_client: TestClient, rest_db: Session):

        _, study = commit_study(rest_db)
        assert rest_db.query(models.Study.id).count() == 1

        study.delete(rest_client)
        assert rest_db.query(models.Study.id).count() == 0

    def test_not_found(self, rest_client: TestClient):

        study = create_empty_study("project-1", "study-1")

        with pytest.raises(HTTPError) as error_info:
            study.delete(rest_client)

        assert error_info.value.response.status_code == 404

        with pytest.raises(HTTPError) as error_info:
            study.update(rest_client)

        assert error_info.value.response.status_code == 404
