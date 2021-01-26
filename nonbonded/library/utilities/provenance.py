import importlib
from typing import Dict

import packaging.version
import yaml


def summarise_conda_environment(environment_path: str) -> Dict[str, str]:
    """Attempts to parse the versions of the key packages from a conda environment file
    produced by ``conda env export``.

    Currently the returned packages may (where present) include:

        * forcebalance
        * nonbonded
        * openff-evaluator
        * openff-recharge
        * pint
        * openmm
        * openmmtools
        * yank
        * pymbar
        * openforcefield
        * openff-toolkit
        * openeye-toolkits
        * rdkit
        * ambertools

    Parameters
    ----------
    environment_path
        The path to the conda environment file.

    Returns
    -------
        A dictionary of package names and corresponding version strings.
    """

    with open(environment_path) as file:
        environment = yaml.safe_load(file)

    # Find the relevant dependencies.
    dependencies = {
        version_string.split("=")[0]: version_string.split("=")[1]
        for version_string in environment["dependencies"]
        if version_string != "pip"
    }
    dependencies.update(
        {
            dependency.split("==")[0]: dependency.split("==")[1]
            for dependency in environment["dependencies"].get("pip", [])
            if dependency.find("ambertools") >= 0
        }
    )

    return {
        name: str(packaging.version.parse(version))
        for name, version in dependencies.items()
        if name
        in [
            # Package to launch the calculation.
            "forcebalance",
            "nonbonded",
            # Core target dependencies.
            "openff-evaluator",
            "openff-recharge",
            # - Sub-target dependencies.
            "pint",
            "openmm",
            "openmmtools",
            "yank",
            "pymbar",
            # The OpenFF toolkit
            "openforcefield",
            "openff-toolkit",
            # Cheminformatics toolkits.
            "openeye-toolkits",
            "rdkit",
            "ambertools",
        ]
    }


def summarise_current_versions() -> Dict[str, str]:
    """Attempts to summarise the versions of the key packages which can currently be
    imported.

    Currently the returned packages (where present) include:

        * forcebalance
        * nonbonded
        * openff-evaluator
        * openff-recharge
        * pint
        * openmm
        * openmmtools
        * yank
        * pymbar
        * openforcefield
        * openff-toolkit
        * openeye-toolkits
        * rdkit
        * ambertools

    Parameters
    ----------
    environment_path
        The path to the conda environment file.

    Returns
    -------
        A dictionary of package names and corresponding version strings.
    """

    packages = {
        "forcebalance": "forcebalance",
        "nonbonded": "nonbonded",
        "openff-evaluator": "openff.evaluator",
        "openff-recharge": "openff.recharge",
        "pint": "pint",
        "openmm": "simtk.openmm.version",
        "openmmtools": "openmmtools",
        "yank": "yank",
        "pymbar": "pymbar",
        "openforcefield": "openforcefield",
        "openff-toolkit": "openff.toolkit",
        "openeye-toolkits": "openeye",
        "rdkit": "rdkit",
    }

    versions = {}

    for name, import_path in packages.items():

        try:
            module = importlib.import_module(import_path)
        except (ImportError, ModuleNotFoundError):
            continue

        if name == "pymbar":
            versions[name] = module.version.short_version
        elif name == "openmm":
            versions[name] = module.short_version
        else:
            versions[name] = module.__version__

        versions[name] = str(packaging.version.parse(versions[name]))

    return versions
