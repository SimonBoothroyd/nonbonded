import abc
import os
from typing import List

from jinja2 import Template
from pydantic import Field
from pydantic.main import BaseModel

from nonbonded.library.templates import BaseTemplate
from nonbonded.library.utilities import get_data_filename


class Submission(BaseModel):

    job_name: str = Field(..., description="The name of the job.")
    wall_clock_limit: str = Field(
        ...,
        description="The maximum wall clock time for the job. This should be a "
        "string of the form HH:MM.",
    )
    max_memory: int = Field(
        ..., description="The maximum amount of memory to request for the job."
    )

    gpu: bool = Field(..., description="Whether to request a GPU node or not.")

    environment_name: str = Field(
        ..., description="The name of the conda environment to run using."
    )

    commands: List[str] = Field(
        ..., description="The commands to run as part of the job."
    )


class SubmissionTemplate(BaseTemplate, abc.ABC):
    @classmethod
    def generate(cls, template_name: str, submission_options: Submission, **options):

        cls._check_unrecognised_options(**options)

        template_file_name = get_data_filename(os.path.join("jinja", template_name))

        with open(template_file_name) as file:
            template = Template(file.read())

        rendered_template = template.render(**submission_options.dict())
        return rendered_template
