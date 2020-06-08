from textwrap import TextWrapper

import click

from nonbonded.library.models.projects import ProjectCollection


@click.command(name="list", help="Lists the projects available from the REST API.")
def list_projects():

    projects = ProjectCollection.from_rest()

    text_wrapper = TextWrapper(initial_indent="    ", subsequent_indent="    ")

    print("\n")

    for index, project in enumerate(projects.projects):
        authors = ", ".join(x.name for x in project.authors)

        print(f"{index}) {project.id}\n")
        print("\n".join(text_wrapper.wrap(project.name)))
        print("\n".join(text_wrapper.wrap(authors)))
        print()
        print("\n".join(text_wrapper.wrap(project.description.split("\n")[0])))
        print()
