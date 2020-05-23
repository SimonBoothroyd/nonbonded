import click

from nonbonded.library.models.datasets import DataSet


@click.command(help="Retrieves a data set from the restful API.")
@click.option(
    "--id",
    "data_set_id",
    required=True,
    type=click.STRING,
    help="The id of the data set to retrieve.",
)
@click.option(
    "--pandas",
    "return_pandas",
    is_flag=True,
    type=click.BOOL,
    help="If set, the data set will be returned as a pandas DataFrame.",
    show_default=True,
)
@click.option(
    "--output",
    "output_path",
    required=True,
    type=click.Path(dir_okay=False),
    help="The path to save the data set to.",
)
def retrieve(data_set_id, return_pandas, output_path):

    data_set = DataSet.from_rest(data_set_id)

    if return_pandas:
        data_set = data_set.to_pandas()
        data_set.to_csv(output_path, index=False)
    else:

        with open(output_path, "w") as file:
            file.write(data_set.json())
