from typing import TYPE_CHECKING

from pydantic import Field

from nonbonded.library.models import BaseORM
from nonbonded.library.models.validators.string import NonEmptyStr

if TYPE_CHECKING:
    EmailStr = str
else:
    from pydantic import EmailStr


class Author(BaseORM):
    """A representation an author. This may be the author of a project
    or a data set for example.
    """

    name: NonEmptyStr = Field(..., description="The full name of the author.")
    email: EmailStr = Field(..., description="The author's email address.")
    institute: NonEmptyStr = Field(..., description="The author's host institute.")
