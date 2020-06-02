import pytest
from pydantic import ValidationError

from nonbonded.library.models.authors import Author


def test_author_validation():
    """Test that pydantic correctly validates authors"""

    # Create a valid author
    Author(name="SB", email="fake@email.com", institute="Inst")

    # Create an author with an invalid email
    with pytest.raises(ValidationError):
        Author(name="SB", email="fakeemail.com", institute="Inst")
