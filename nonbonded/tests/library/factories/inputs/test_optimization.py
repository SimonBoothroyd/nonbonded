import json
import logging
import os

import pytest
from openff.evaluator.attributes import UNDEFINED
from openff.evaluator.datasets import PhysicalPropertyDataSet
from openff.evaluator.properties import Density
from openforcefield.typing.engines.smirnoff import ForceField as OFFForceField

from nonbonded.library.factories.inputs.optimization import OptimizationInputFactory
from nonbonded.library.models.datasets import DataSetCollection
from nonbonded.library.models.forcefield import Parameter
from nonbonded.library.models.projects import Optimization
from nonbonded.library.models.results import OptimizationResult
from nonbonded.library.utilities import temporary_cd
from nonbonded.tests.utilities.factory import (
    create_data_set,
    create_evaluator_target,
    create_optimization,
    create_optimization_result,
    create_qc_data_set,
    create_recharge_target,
)
from nonbonded.tests.utilities.mock import (
    mock_get_data_set,
    mock_get_optimization_result,
    mock_get_qc_data_set,
)

logger = logging.getLogger(__name__)


@pytest.fixture()
def optimization(force_field) -> Optimization:
    optimization = create_optimization(
        "project-1",
        "study-1",
        "optimization-1",
        [
            create_evaluator_target("evaluator-target-1", ["data-set-1"]),
            create_recharge_target("recharge-target-1", ["qc-data-set-1"]),
        ],
    )
    optimization.force_field = force_field

    return optimization


@pytest.mark.usefixtures("change_api_url")
class TestOptimizationInputFactory:
    def test_prepare_force_field(self, optimization):
        """Test that the correct cosmetic attributes are attached to the FF, especially
        in the special case of BCC handlers."""

        optimization.parameters_to_train.append(
            Parameter(
                handler_type="ChargeIncrementModel",
                smirks="[#6:1]-[#6:2]",
                attribute_name="charge_increment1",
            )
        )

        with temporary_cd():

            OptimizationInputFactory._prepare_force_field(optimization)

            assert os.path.isfile(os.path.join("forcefield", "force-field.offxml"))

            off_force_field = OFFForceField(
                os.path.join("forcefield", "force-field.offxml"),
                allow_cosmetic_attributes=True,
            )

        vdw_handler = off_force_field.get_parameter_handler("vdW")
        assert len(vdw_handler.parameters) == 1
        parameter = vdw_handler.parameters["[#6:1]"]
        assert parameter._parameterize == "epsilon, sigma"

        bcc_handler = off_force_field.get_parameter_handler("ChargeIncrementModel")
        assert len(bcc_handler.parameters) == 1
        parameter = bcc_handler.parameters["[#6:1]-[#6:2]"]
        assert parameter._parameterize == "charge_increment1"
        assert parameter._parameter_eval == (
            "charge_increment2=-PRM['ChargeIncrementModel/ChargeIncrement/"
            "charge_increment1/[#6:1]-[#6:2]']"
        )

    def test_generate_force_balance_input(self, optimization):

        with temporary_cd():
            OptimizationInputFactory._generate_force_balance_input(optimization)
            assert os.path.isfile("optimize.in")

    @pytest.mark.parametrize("allow_reweighting", [False, True])
    def test_generate_request_options_default(self, allow_reweighting):

        training_set = create_data_set("data-set-1", 1)

        target = create_evaluator_target("evaluator-target-1", ["data-set-1"])
        target.allow_direct_simulation = True
        target.allow_reweighting = allow_reweighting

        request_options = OptimizationInputFactory._generate_request_options(
            target, training_set.to_evaluator()
        )

        if allow_reweighting:
            assert request_options.calculation_layers == [
                "ReweightingLayer",
                "SimulationLayer",
            ]
        else:
            assert request_options.calculation_layers == ["SimulationLayer"]

        assert request_options.calculation_schemas == UNDEFINED

    def test_generate_request_options(self):

        training_set = create_data_set("data-set-1", 1)
        target = create_evaluator_target("evaluator-target-1", [training_set.id])

        target.allow_direct_simulation = True
        target.allow_reweighting = True
        target.n_molecules = 512
        target.n_effective_samples = 10

        request_options = OptimizationInputFactory._generate_request_options(
            target, training_set.to_evaluator()
        )

        assert request_options.calculation_layers == [
            "ReweightingLayer",
            "SimulationLayer",
        ]

        assert request_options.calculation_schemas != UNDEFINED

        expected_simulation_schema = Density.default_simulation_schema(n_molecules=512)
        expected_reweighting_schema = Density.default_reweighting_schema(
            n_effective_samples=10
        )

        assert (
            request_options.calculation_schemas["Density"]["SimulationLayer"].json()
            == expected_simulation_schema.json()
        )
        assert (
            request_options.calculation_schemas["Density"]["ReweightingLayer"].json()
            == expected_reweighting_schema.json()
        )

    def test_generate_evaluator_target(self, requests_mock):

        data_set = create_data_set("data-set-1")
        mock_get_data_set(requests_mock, data_set)

        target = create_evaluator_target("evaluator-target-1", [data_set.id])

        with temporary_cd():

            OptimizationInputFactory._generate_evaluator_target(target, 8000)

            assert os.path.isfile("training-set-collection.json")
            data_set_collection = DataSetCollection.parse_file(
                "training-set-collection.json"
            )
            assert data_set_collection.data_sets[0].json() == data_set.json()

            assert os.path.isfile("training-set.json")
            off_data_set = PhysicalPropertyDataSet.from_json("training-set.json")
            assert off_data_set.json() == data_set.to_evaluator().json()

            assert os.path.isfile("options.json")

    def test_generate_recharge_target(self, requests_mock):

        qc_data_set = create_qc_data_set("qc-data-set-1")
        mock_get_qc_data_set(requests_mock, qc_data_set)

        target = create_recharge_target("recharge-target-1", [qc_data_set.id])

        with temporary_cd():

            OptimizationInputFactory._generate_recharge_target(target)

            with open("training-set.json") as file:
                training_entries = json.load(file)

            assert training_entries == qc_data_set.entries

            with open("esp-settings.json") as file:
                assert file.read() == target.esp_settings.json()

    @pytest.mark.parametrize(
        "target",
        [
            create_evaluator_target("evaluator-target-1", ["data-set-1"]),
            create_recharge_target("recharge-target-1", ["qc-data-set-1"]),
        ],
    )
    def test_generate_target(self, target, caplog, monkeypatch):

        monkeypatch.setattr(
            OptimizationInputFactory,
            "_generate_evaluator_target",
            lambda *args: logging.info("EvaluatorTarget"),
        )
        monkeypatch.setattr(
            OptimizationInputFactory,
            "_generate_recharge_target",
            lambda *args: logging.info("RechargeTarget"),
        )

        with caplog.at_level(logging.INFO):

            with temporary_cd():
                OptimizationInputFactory._generate_target(target, 8000)
                assert os.path.isdir(os.path.join("targets", target.id))

        assert target.__class__.__name__ in caplog.text

    def test_retrieve_results(self, optimization, requests_mock):

        result = create_optimization_result(
            optimization.project_id,
            optimization.study_id,
            optimization.id,
            ["evaluator-target-1"],
            [],
        )
        mock_get_optimization_result(requests_mock, result)

        with temporary_cd():

            OptimizationInputFactory._retrieve_results(optimization)

            stored_result = OptimizationResult.parse_file(
                os.path.join("analysis", "optimization-results.json")
            )
            assert stored_result.json() == result.json()

    def test_generate(self, optimization, monkeypatch):

        logging.basicConfig(level=logging.INFO)

        # Mock the already tested functions
        monkeypatch.setattr(
            OptimizationInputFactory, "_prepare_force_field", lambda *args: None
        )
        monkeypatch.setattr(
            OptimizationInputFactory,
            "_generate_force_balance_input",
            lambda *args: None,
        )
        monkeypatch.setattr(
            OptimizationInputFactory, "_generate_target", lambda *args: None
        )
        monkeypatch.setattr(
            OptimizationInputFactory, "_generate_submission_script", lambda *args: None
        )
        monkeypatch.setattr(
            OptimizationInputFactory, "_retrieve_results", lambda *args: None
        )

        with temporary_cd():

            OptimizationInputFactory.generate(
                optimization, "env", "01:00", "lilac-local", 8000, 1, True
            )
