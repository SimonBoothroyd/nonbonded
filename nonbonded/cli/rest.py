import click

from nonbonded.library.utilities.logging import get_log_levels


@click.group(help="A collection of sub-commands for interacting with the RESTful API.")
def rest():
    """The stub group for any RESTful API commands."""


@click.command(help="Launch the main RESTful API server.")
@click.option(
    "--debug", is_flag=True, default=False, help="Run the server in debug mode."
)
@click.option(
    "--host",
    default="127.0.0.1",
    type=click.STRING,
    help="The ip address to use for the server.",
    show_default=True,
)
@click.option(
    "--port",
    default=5000,
    type=click.INT,
    help="The port to use for the server.",
    show_default=True,
)
@click.option(
    "--log-level",
    default="info",
    type=click.Choice(get_log_levels()),
    help="The verbosity of the server logger.",
    show_default=True,
)
def start_server(debug, host, port, log_level):

    import uvicorn

    uvicorn.run(
        "nonbonded.backend.app:app",
        host=host,
        port=port,
        log_level=log_level,
        reload=debug,
    )


rest.add_command(start_server)
