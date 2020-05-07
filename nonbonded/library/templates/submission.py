import abc
import os

from jinja2 import Template
from pydantic import Field
from pydantic.main import BaseModel

from nonbonded.library.templates import BaseTemplate
from nonbonded.library.utilities import get_data_filename


class Submission(BaseModel):

    environment_name: str = Field(
        ..., description="The name of the conda environment to run using."
    )
    max_memory: int = Field(8, description="The amount of memory to request.")


class _BaseSubmissionTemplate(BaseTemplate, abc.ABC):
    @classmethod
    @abc.abstractmethod
    def template_file_name(cls):
        raise NotImplementedError()

    @classmethod
    def generate(cls, environment_name: str, max_memory: int, **options):

        cls._check_unrecognised_options(**options)

        template_file_name = get_data_filename(
            os.path.join("jinja", cls.template_file_name())
        )

        with open(template_file_name) as file:
            template = Template(file.read())

        rendered_template = template.render(
            environment_name=environment_name, max_memory=max_memory
        )
        return rendered_template


class SubmitTestTemplate(_BaseSubmissionTemplate):
    @classmethod
    def template_file_name(cls):
        return "submit_test.txt"


class SubmitTrainTemplate(_BaseSubmissionTemplate):
    @classmethod
    def template_file_name(cls):
        return "submit_train.txt"
