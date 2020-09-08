from textwrap import TextWrapper

import click

from nonbonded.library.models.datasets import DataSetCollection


@click.command(name="list")
def list_data_sets():
    """Lists all of the data sets which are available from the RESTful API."""

    data_sets = DataSetCollection.from_rest()

    text_wrapper = TextWrapper(initial_indent="    ", subsequent_indent="    ")

    for index, data_set in enumerate(data_sets.data_sets):

        print(f"{index}) {data_set.id}\n")
        print("\n".join(text_wrapper.wrap(data_set.description.split("\n")[0])))
        print()
