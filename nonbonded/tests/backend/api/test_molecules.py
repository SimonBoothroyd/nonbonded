import sys

import mock
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from nonbonded.backend.api.dev.endpoints.molecules import _get_molecule_image
from nonbonded.library.config import settings


def test_get_molecule_image(rest_client: TestClient):

    request = rest_client.get(f"{settings.API_URL}/molecules/CCO/image")
    request.raise_for_status()


def test_rdkit_error():
    """Make sure that a friendly exception is raised when rdkit cannot
    be found."""

    with pytest.raises(HTTPException) as error_info:

        with mock.patch.dict(sys.modules, {"rdkit": None}):
            _get_molecule_image("CCCO")

    assert error_info.value.status_code == 501
