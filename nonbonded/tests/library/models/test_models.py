import pytest
import requests

from nonbonded.library.models.models import BaseRESTCollection


def test_collection_from_rest_error(requests_mock):

    requests_mock.get("http://missing.mocked.com", reason="Missing", status_code=404)

    class MockRestCollection(BaseRESTCollection):
        @classmethod
        def _get_endpoint(cls, **kwargs):
            return "http://missing.mocked.com"

    with pytest.raises(requests.HTTPError):
        MockRestCollection.from_rest()
