import pytest

from nonbonded.library.models.datasets import Component
from nonbonded.library.utilities.checkmol import (
    analyse_functional_groups,
    components_to_category,
)
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


@pytest.mark.parametrize(
    "components, expected_category",
    [
        ([Component(smiles="CC(O)CC", mole_fraction=1.0)], "Alcohol"),
        (["CC(O)CC"], "Alcohol"),
        ([Component(smiles="CC(=O)CC", mole_fraction=1.0)], "Ketone"),
        (["CC(=O)CC"], "Ketone"),
        (
            [
                Component(smiles="CC(O)CC", mole_fraction=0.5),
                Component(smiles="CC(=O)CC", mole_fraction=0.5),
            ],
            "Alcohol ~ Ketone",
        ),
        (
            [
                Component(smiles="CC(O)CC", mole_fraction=0.44),
                Component(smiles="CC(=O)CC", mole_fraction=0.56),
            ],
            "Alcohol < Ketone",
        ),
        (
            [
                Component(smiles="CC(=O)CC", mole_fraction=0.56),
                Component(smiles="CC(O)CC", mole_fraction=0.44),
            ],
            "Alcohol < Ketone",
        ),
        (
            [
                Component(smiles="CC(O)CC", mole_fraction=0.56),
                Component(smiles="CC(=O)CC", mole_fraction=0.44),
            ],
            "Alcohol > Ketone",
        ),
        (
            [
                Component(smiles="CC(=O)CC", mole_fraction=0.44),
                Component(smiles="CC(O)CC", mole_fraction=0.56),
            ],
            "Alcohol > Ketone",
        ),
        (
            [
                Component(smiles="CC(O)CC", mole_fraction=0.56),
                Component(smiles="O", mole_fraction=0.44),
            ],
            "Alcohol > Aqueous",
        ),
        (
            [
                Component(smiles="O", mole_fraction=0.44),
                Component(smiles="CC(O)CC", mole_fraction=0.56),
            ],
            "Alcohol > Aqueous",
        ),
    ],
)
def test_components_to_category(components, expected_category):
    """Tests the private `_components_to_category` function of `AnalysedResult`"""

    environments = [
        ChemicalEnvironment.Alcohol,
        ChemicalEnvironment.Ketone,
        ChemicalEnvironment.Aqueous,
    ]

    assert components_to_category(components, environments) == expected_category


def test_components_to_category_type():

    with pytest.raises(TypeError):
        components_to_category(
            ["C", Component(smiles="C", mole_fraction=1.0)],
            [ChemicalEnvironment.Alkane],
        )
