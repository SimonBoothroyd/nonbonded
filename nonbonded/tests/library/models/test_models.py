import os

import pytest
import requests
from pydantic import Field

from nonbonded.library.models.models import BaseORM, BaseRESTCollection


def test_collection_from_rest_error(requests_mock):

    requests_mock.get("http://missing.mocked.com", reason="Missing", status_code=404)

    class MockRestCollection(BaseRESTCollection):
        @classmethod
        def _get_endpoint(cls, **kwargs):
            return "http://missing.mocked.com"

    with pytest.raises(requests.HTTPError):
        MockRestCollection.from_rest()


def test_to_file(tmpdir):
    class MockORMObject(BaseORM):
        attribute: str = Field("mock_attribute")

    mock_object = MockORMObject()
    mock_object.to_file(os.path.join(tmpdir, "mock.json"))

    with open(os.path.join(tmpdir, "mock.json")) as file:
        contents = file.read()

    assert contents == mock_object.json()
