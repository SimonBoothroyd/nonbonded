import pytest
from click.testing import CliRunner


@pytest.yield_fixture(scope="module")
def change_api_url():
    """Correct the API url to be useable directly by the `requests`
    module."""
    from nonbonded.library.config import settings

    previous_api_url = settings.API_URL
    settings.API_URL = "http://localhost"
    yield
    settings.API_URL = previous_api_url


@pytest.yield_fixture(scope="module")
def runner() -> CliRunner:
    """Creates a new click CLI runner object and sets the temporarily moves
    the working directory to a temporary directory"""
    click_runner = CliRunner()

    with click_runner.isolated_filesystem():
        yield click_runner
