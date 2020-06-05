from fastapi.testclient import TestClient

from nonbonded.library.config import settings


def test_get_molecule_image(rest_client: TestClient):

    request = rest_client.get(f"{settings.API_URL}/molecules/CCO/image")
    request.raise_for_status()
