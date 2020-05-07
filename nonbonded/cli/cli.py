import click

from nonbonded.cli.rest import rest
from nonbonded.cli.run import run

# from nonbonded.cli.generate import generate
# from nonbonded.cli.retrieve import retrieve
# from nonbonded.cli.upload import upload


@click.group()
def cli():
    pass


# cli.add_command(generate)
cli.add_command(rest)
# cli.add_command(retrieve)
cli.add_command(run)
# cli.add_command(upload)
