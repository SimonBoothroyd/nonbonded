import pytest
from pydantic import BaseModel, ValidationError

from nonbonded.library.models.validators.string import NonEmptyStr


class TestStrClass(BaseModel):

    string_field: NonEmptyStr


def test_none_empty_str():
    """Ensures that the non-empty string validator works as intended."""

    # Make sure a non-empty string is valid
    TestStrClass(string_field="x")
    # and an empty string is invalid
    with pytest.raises(ValidationError):
        TestStrClass(string_field="")
