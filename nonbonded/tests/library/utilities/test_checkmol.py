import pytest

from nonbonded.library.utilities.checkmol import analyse_functional_groups
from nonbonded.library.utilities.environments import ChemicalEnvironment


@pytest.mark.parametrize(
    "smiles, expected_environment",
    [
        ("O", ChemicalEnvironment.Aqueous),
        ("N", ChemicalEnvironment.Amine),
        ("C", ChemicalEnvironment.Alkane),
        ("CO", ChemicalEnvironment.Alcohol),
        ("C=O", ChemicalEnvironment.Aldehyde),
    ],
)
def test_analyse_functional_groups(smiles, expected_environment):
    """Performs a simple test of the analyse_functional_groups function."""
    chemical_moieties = analyse_functional_groups(smiles)
    assert expected_environment in chemical_moieties


def test_analyse_functional_groups_error():
    """Tests the the function returns None when an unknown
    smiles pattern is passed."""
    assert analyse_functional_groups("[Ar]") is None
