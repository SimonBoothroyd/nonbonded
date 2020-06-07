import pandas
import pytest

from nonbonded.cli.dataset import dataset as dataset_cli
from nonbonded.library.curation.workflow import WorkflowSchema
from nonbonded.library.models.datasets import DataSet, DataSetCollection
from nonbonded.tests.backend.crud.utilities.create import create_data_set
from nonbonded.tests.cli.utilities import mock_get_data_set, mock_get_data_sets


@pytest.mark.usefixtures("change_api_url")
class TestDataSetCLI:
    @pytest.mark.parametrize("as_pandas", [True, False])
    def test_retrieve(self, requests_mock, runner, as_pandas):

        data_set = create_data_set("data-set-1")
        data_set.entries[0].id = 1
        mock_get_data_set(requests_mock, data_set)

        output_path = "dataset.json" if not as_pandas else "dataset.csv"

        arguments = ["retrieve", "--id", data_set.id, "--output", output_path]

        if as_pandas:
            arguments.append("--pandas")

        result = runner.invoke(dataset_cli, arguments)

        if result.exit_code != 0:
            raise result.exception

        if as_pandas:
            rest_data_set = pandas.read_csv(output_path)
            assert len(rest_data_set) == len(data_set.entries)

        else:

            rest_data_set = DataSet.parse_file(output_path)
            assert rest_data_set.json().replace("\n", "") == data_set.json()

    def test_list(self, requests_mock, runner):

        data_sets = DataSetCollection(data_sets=[create_data_set("data-set-1")])
        mock_get_data_sets(requests_mock, data_sets)

        result = runner.invoke(dataset_cli, ["list"])

        if result.exit_code != 0:
            raise result.exception

        assert data_sets.data_sets[0].id in result.output

    def test_curate(self, runner):

        schema = WorkflowSchema(component_schemas=[])

        with open("schema.json", "w") as file:
            file.write(schema.json())

        result = runner.invoke(
            dataset_cli, ["curate", "--schema", "schema.json", "--output", "output.csv"]
        )

        if result.exit_code != 0:
            raise result.exception
