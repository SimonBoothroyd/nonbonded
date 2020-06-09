import pytest
from pydantic import BaseModel, ValidationError

from nonbonded.library.models.validators.string import IdentifierStr, NonEmptyStr


class TestStrClass(BaseModel):

    string_field: NonEmptyStr


class TestIdStrClass(BaseModel):

    string_field: IdentifierStr


def test_none_empty_str():
    """Ensures that the non-empty string validator works as intended."""

    # Make sure a non-empty string is valid
    TestStrClass(string_field="x")
    # and an empty string is invalid
    with pytest.raises(ValidationError):
        TestStrClass(string_field="")


@pytest.mark.parametrize(
    "valid_string", ["a", "-" "abc-123-cba", "".join(["a"] * 32)],
)
def test_valid_identifier_str(valid_string):
    """Ensures that the identifier string validator works as intended
    for valid strings."""

    TestIdStrClass(string_field=valid_string)


@pytest.mark.parametrize(
    "invalid_string",
    ["", "A", "Z", ".", ",", " ", "_", "/", "\\", "".join(["a"] * 33)],
)
def test_invalid_identifier_str(invalid_string):
    """Ensures that the identifier string validator catches invalid strings."""

    with pytest.raises(ValidationError):
        TestIdStrClass(string_field=invalid_string)
