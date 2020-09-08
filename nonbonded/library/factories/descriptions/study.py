from textwrap import TextWrapper

import click

from nonbonded.library.models.projects import StudyCollection


@click.command(name="list", help="Lists the studies of a particular project.")
@click.option(
    "--project-id",
    type=click.STRING,
    help="The id of the project.",
)
def list_studies(project_id: str):

    studies = StudyCollection.from_rest(project_id=project_id)

    print(f"Listing the studies of project={project_id}:\n")

    text_wrapper = TextWrapper(initial_indent="    ", subsequent_indent="    ")

    for index, study in enumerate(studies.studies):

        print(f"{index}) {study.id}\n")
        print("\n".join(text_wrapper.wrap(study.name)))
        print()
        print("\n".join(text_wrapper.wrap(study.description.split("\n")[0])))
        print()
