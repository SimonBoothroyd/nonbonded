import click

from nonbonded.cli.project.generate import generate


@click.group()
def project():
    pass


project.add_command(generate)
