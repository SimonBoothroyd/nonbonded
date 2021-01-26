from nonbonded.library.utilities.provenance import (
    summarise_conda_environment,
    summarise_current_versions,
)


def test_summarise_conda_environment(dummy_conda_env):

    detected_environments = summarise_conda_environment(dummy_conda_env)
    expected_environment = {
        "forcebalance": "1.7.5",
        "nonbonded": "0.0.1a4",
        "openff-evaluator": "0.3.1",
        "openff-recharge": "0.0.1a6",
        "pint": "0.14",
        "openmm": "7.4.2",
        "openmmtools": "0.20.0",
        "yank": "0.25.2",
        "pymbar": "3.0.5",
        "openforcefield": "0.8.0",
        "openeye-toolkits": "2020.1.0",
        "rdkit": "2020.9.2",
        "ambertools": "20.9",
    }

    assert detected_environments == expected_environment


def test_summarise_current_versions(tmpdir):

    detected_environments = summarise_current_versions()

    assert all(
        package in detected_environments
        for package in [
            "forcebalance",
            "nonbonded",
            "openff-evaluator",
            "openff-recharge",
            "pint",
            "openmm",
            "openmmtools",
            "yank",
            "pymbar",
            "openforcefield",
            "rdkit",
        ]
    )
