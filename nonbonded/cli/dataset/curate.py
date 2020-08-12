import click

from nonbonded.library.utilities.logging import (
    get_log_levels,
    setup_timestamp_logging,
    string_to_log_level,
)


@click.command(help="Curate a data set by applying a curation schema.")
@click.option(
    "--schema",
    "schema_path",
    required=True,
    type=click.Path(exists=True, dir_okay=False),
    help="The file path to the schema which defines how the data set should be curated.",
)
@click.option(
    "--output",
    "output_path",
    required=True,
    type=click.Path(dir_okay=False),
    help="The path to save the curated data set to.",
)
@click.option(
    "--initial-dataset",
    "initial_data_set_path",
    required=False,
    type=click.Path(exists=True, dir_okay=False),
    help="The optional file path to the pandas data frame (.csv) to use as the "
    "starting point of the curation. If one is not specified, the curation will "
    "proceed from an empty data frame.",
)
@click.option(
    "--n-procs",
    "n_processes",
    default=1,
    type=click.INT,
    help="The maximum number of processes to parallelize over.",
    show_default=True,
)
@click.option(
    "--log-level",
    default="info",
    type=click.Choice(get_log_levels()),
    help="The verbosity of the server logger.",
    show_default=True,
)
def curate(schema_path, output_path, initial_data_set_path, n_processes, log_level):

    import pandas

    from nonbonded.library.curation.workflow import Workflow, WorkflowSchema

    # Set up logging if requested.
    logging_level = string_to_log_level(log_level)

    if logging_level is not None:
        setup_timestamp_logging(logging_level)

    workflow_schema = WorkflowSchema.parse_file(schema_path)

    initial_data_set = pandas.DataFrame()

    if initial_data_set_path is not None:
        initial_data_set = pandas.read_csv(initial_data_set_path)

    final_data_set = Workflow.apply(initial_data_set, workflow_schema, n_processes)
    final_data_set.to_csv(output_path, index=False)
