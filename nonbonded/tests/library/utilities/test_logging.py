import logging
from tempfile import NamedTemporaryFile

import pytest

from nonbonded.library.utilities.logging import (
    get_log_levels,
    setup_timestamp_logging,
    string_to_log_level,
)


@pytest.mark.parametrize("log_level_string", get_log_levels())
def test_string_to_logging_level(log_level_string):
    """Test that all of the string logging levels listed by
    `get_log_levels` can be converted into logging levels."""
    string_to_log_level(log_level_string)


def test_setup_logging():
    """Test that timestamp logging can be setup without exception."""
    setup_timestamp_logging(logging_level=logging.INFO)

    with NamedTemporaryFile() as file:
        setup_timestamp_logging(logging_level=logging.INFO, file_path=file.name)
