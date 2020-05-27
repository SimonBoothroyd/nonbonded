import click

from nonbonded.cli.study.generate import generate


@click.group()
def study():
    pass


study.add_command(generate)
