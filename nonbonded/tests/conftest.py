import os

import pytest
import yaml


@pytest.fixture()
def dummy_conda_env(tmpdir, file_name: str = "conda-env.yaml") -> str:
    """Creates a dummy conda-environment file in a temporary directory and returns
    the path to the file."""

    # Create a dummy environment
    dummy_environment = {
        "name": "test-env",
        "channels": ["conda-forge"],
        "dependencies": [
            "forcebalance=1.7.5=py37h48f8a5e_0",
            "nonbonded=0.0.1a4=pyh87d46a9_0",
            "openff-evaluator=0.3.1=pyhf40f5cb_0",
            "openff-recharge=0.0.1a6=pyhf40f5cb_0",
            "pint=0.14=py_0",
            "openmm=7.4.2=py37_cuda101_rc_1",
            "yank=0.25.2=py37_1",
            "pymbar=3.0.5=py37hc1659b7_0",
            "openforcefield=0.8.0=pyh39e3cac_0",
            "openeye-toolkits=2020.1.0=py37_0",
            "rdkit=2020.09.2=py37h713bca6_0",
            "xorg-xextproto=7.3.0=h14c3975_1002",
            "openmmtools=0.20.0=py37_0",
            {"pip": ["ambertools==20.9", "amberlite==16.0"]},
        ],
    }

    with open(os.path.join(tmpdir, file_name), "w") as file:
        yaml.safe_dump(dummy_environment, file)

    return os.path.join(tmpdir, file_name)
