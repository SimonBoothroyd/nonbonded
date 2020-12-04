import logging
import os
import subprocess
from glob import glob

import pytest

from nonbonded.cli.projects.optimization.run import (
    _launch_required_services,
    _prepare_restart,
    _remove_previous_files,
    run_command,
)
from nonbonded.library.factories.inputs.evaluator import (
    ComputeResources,
    DaskLocalClusterConfig,
    EvaluatorServerConfig,
)
from nonbonded.library.utilities import temporary_cd
from nonbonded.tests.utilities.comparison import does_not_raise
from nonbonded.tests.utilities.factory import (
    create_evaluator_target,
    create_optimization,
    create_recharge_target,
)


@pytest.mark.parametrize(
    "optimization, server_config, expected_raises",
    [
        (
            create_optimization(
                "project-1",
                "study-1",
                "optimization-1",
                [create_recharge_target("recharge-target", ["qc-data-set-1"])],
            ),
            None,
            does_not_raise(),
        ),
        (
            create_optimization(
                "project-1",
                "study-1",
                "optimization-1",
                [create_evaluator_target("evaluator-target", ["data-set-1"])],
            ),
            None,
            pytest.raises(RuntimeError),
        ),
        (
            create_optimization(
                "project-1",
                "study-1",
                "optimization-1",
                [create_evaluator_target("evaluator-target", ["data-set-1"])],
            ),
            EvaluatorServerConfig(
                backend_config=DaskLocalClusterConfig(
                    resources_per_worker=ComputeResources()
                )
            ),
            does_not_raise(),
        ),
    ],
)
def test_launch_required_services(
    optimization, server_config, expected_raises, monkeypatch
):

    monkeypatch.setattr(
        EvaluatorServerConfig, "to_backend", lambda *_: does_not_raise()
    )
    monkeypatch.setattr(EvaluatorServerConfig, "to_server", lambda *_: does_not_raise())

    with temporary_cd():

        if server_config is not None:

            with open("server-config.json", "w") as file:
                file.write(server_config.json())

            server_config = "server-config.json"

        with expected_raises:

            with _launch_required_services(optimization, server_config):
                pass


def test_remove_previous_files():

    with temporary_cd():

        with open("optimize.sav", "w") as file:
            file.write("")

        for directory_name in [
            "optimize.tmp",
            "optimize.bak",
            "result",
            "working-data",
        ]:

            os.makedirs(directory_name)

        assert len(glob("*")) == 5
        _remove_previous_files()
        assert len(glob("*")) == 0


def test_prepare_restart_finished(caplog):

    optimization = create_optimization(
        "project-1",
        "study-1",
        "optimization-1",
        [
            create_recharge_target("recharge-target-1", ["qc-data-set-1"]),
            create_recharge_target("recharge-target-2", ["qc-data-set-1"]),
        ],
    )

    with temporary_cd():

        directories = [
            os.path.join("optimize.tmp", "recharge-target-1", "iter_0000"),
            os.path.join("optimize.tmp", "recharge-target-1", "iter_0001"),
            os.path.join("optimize.tmp", "recharge-target-2", "iter_0000"),
            os.path.join("optimize.tmp", "recharge-target-2", "iter_0001"),
        ]

        for directory in directories:

            os.makedirs(directory)

            for file_name in ["mvals.txt", "force-field.offxml", "objective.p"]:

                with open(os.path.join(directory, file_name), "w") as file:
                    file.write("")

        assert len(glob(os.path.join("optimize.tmp", "recharge-target-1", "*"))) == 2
        assert len(glob(os.path.join("optimize.tmp", "recharge-target-2", "*"))) == 2

        with caplog.at_level(logging.INFO):
            _prepare_restart(optimization)

        assert len(glob(os.path.join("optimize.tmp", "recharge-target-1", "*"))) == 2
        assert len(glob(os.path.join("optimize.tmp", "recharge-target-2", "*"))) == 2

        assert (
            "2 iterations had previously been completed. The optimization will be "
            "restarted from iteration 0002"
        ) in caplog.text


@pytest.mark.parametrize("partial_restart", [False, True])
def test_prepare_restart_unfinished(partial_restart, caplog):

    optimization = create_optimization(
        "project-1",
        "study-1",
        "optimization-1",
        [
            create_recharge_target("recharge-target-1", ["qc-data-set-1"]),
            create_recharge_target("recharge-target-2", ["qc-data-set-1"]),
        ],
    )

    with temporary_cd():

        directories = [
            os.path.join("optimize.tmp", "recharge-target-1", "iter_0000"),
            os.path.join("optimize.tmp", "recharge-target-2", "iter_0000"),
            os.path.join("optimize.tmp", "recharge-target-1", "iter_0001"),
            os.path.join("optimize.tmp", "recharge-target-2", "iter_0001"),
        ]

        for index, directory in enumerate(directories):

            os.makedirs(directory)

            expected_files = ["mvals.txt"]

            if index < 3:
                expected_files.append("objective.p")
            if index < (3 if not partial_restart else 4):
                expected_files.append("force-field.offxml")

            for file_name in expected_files:

                with open(os.path.join(directory, file_name), "w") as file:
                    file.write("")

        assert len(glob(os.path.join("optimize.tmp", "recharge-target-1", "*"))) == 2
        assert len(glob(os.path.join("optimize.tmp", "recharge-target-2", "*"))) == 2

        with caplog.at_level(logging.INFO):
            _prepare_restart(optimization)

        expected_directories = 2 if partial_restart else 1

        assert (
            len(glob(os.path.join("optimize.tmp", "recharge-target-1", "*")))
            == expected_directories
        )
        assert (
            len(glob(os.path.join("optimize.tmp", "recharge-target-2", "*")))
            == expected_directories
        )

        if not partial_restart:
            assert (
                f"Removing the {directories[2]} directory which was not expected to be "
                f"present"
            ) in caplog.text
            assert (
                f"Removing the {directories[3]} directory which was not expected to be "
                f"present"
            ) in caplog.text
        else:
            assert "Removing the" not in caplog.text

        assert (
            "1 iterations had previously been completed. The optimization will be "
            f"restarted from iteration {'0000' if not partial_restart else '0001'}"
        ) in caplog.text


@pytest.mark.parametrize("restart", [False, True])
@pytest.mark.parametrize("create_save", [False, True])
def test_run_command(restart: bool, create_save: bool, runner, monkeypatch):

    from nonbonded.cli.projects.optimization import run

    monkeypatch.setattr(run, "_remove_previous_files", lambda: print("REMOVE"))
    monkeypatch.setattr(run, "_prepare_restart", lambda *args: print("PREPARE"))
    monkeypatch.setattr(subprocess, "check_call", lambda *args, **kwargs: None)

    optimization = create_optimization(
        "project-1",
        "study-1",
        "optimization-1",
        [create_recharge_target("recharge-target-1", ["qc-data-set-1"])],
    )

    # Save a copy of the result model.
    with temporary_cd():

        with open("optimization.json", "w") as file:
            file.write(optimization.json())

        if create_save:

            with open("optimize.sav", "w") as file:
                file.write("")

        arguments = [] if not restart else ["--restart", True]

        result = runner.invoke(run_command(), arguments)

        if restart and create_save:
            assert "REMOVE" not in result.output
            assert "PREPARE" in result.output

        elif restart and not create_save:
            assert "REMOVE" in result.output
            assert "PREPARE" not in result.output

        if not restart:
            assert "REMOVE" in result.output
            assert "PREPARE" not in result.output

    if result.exit_code != 0:
        raise result.exception
