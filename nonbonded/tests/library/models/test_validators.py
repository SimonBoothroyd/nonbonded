import pytest
from pydantic import BaseModel, ValidationError

from nonbonded.library.models.validators.string import IdentifierStr, NonEmptyStr


class MockStrClass(BaseModel):

    string_field: NonEmptyStr


class MockIdStrClass(BaseModel):

    string_field: IdentifierStr


def test_none_empty_str():
    """Ensures that the non-empty string validator works as intended."""

    # Make sure a non-empty string is valid
    MockStrClass(string_field="x")
    # and an empty string is invalid
    with pytest.raises(ValidationError):
        MockStrClass(string_field="")


@pytest.mark.parametrize(
    "valid_string",
    ["a", "-" "abc-123-cba", "".join(["a"] * 32)],
)
def test_valid_identifier_str(valid_string):
    """Ensures that the identifier string validator works as intended
    for valid strings."""

    MockIdStrClass(string_field=valid_string)


@pytest.mark.parametrize(
    "invalid_string",
    ["", "A", "Z", ".", ",", " ", "_", "/", "\\", "".join(["a"] * 33)],
)
def test_invalid_identifier_str(invalid_string):
    """Ensures that the identifier string validator catches invalid strings."""

    with pytest.raises(ValidationError):
        MockIdStrClass(string_field=invalid_string)
