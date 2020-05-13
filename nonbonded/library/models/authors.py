from pydantic import Field

from nonbonded.library.models import BaseORM


class Author(BaseORM):

    name: str = Field(..., description="The full name of the author.")
    email: str = Field(..., description="The author's email address.")
    institute: str = Field(..., description="The author's host institute.")
