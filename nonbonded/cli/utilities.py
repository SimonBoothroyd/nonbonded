from typing import List

import click

from nonbonded.library.utilities.logging import (
    get_log_levels,
    setup_timestamp_logging,
    string_to_log_level,
)


def common_options() -> List[click.option]:

    return [
        click.option(
            "--log-level",
            default="info",
            type=click.Choice(get_log_levels()),
            help="The verbosity of the logger.",
            show_default=True,
        ),
    ]


def generate_click_command(
    command_decorator: click.command,
    option_decorators: List[click.option],
    inner_function,
):
    """Generates a full ``click`` command from its constituent pieces.

    Parameters
    ----------
    command_decorator
        The main command decorator
    option_decorators
        The option decorators
    inner_function
        The inner function of the command
    """

    click_options = [*common_options(), *option_decorators]

    def wrapped_function(**kwargs):

        log_level = kwargs.pop("log_level")

        # Set up logging if requested.
        logging_level = string_to_log_level(log_level)

        if logging_level is not None:
            setup_timestamp_logging(logging_level)

        inner_function(**kwargs)

    click_function = wrapped_function

    click_decorators = [command_decorator, *click_options]

    for click_decorator in reversed(click_decorators):
        click_function = click_decorator(click_function)

    return click_function
