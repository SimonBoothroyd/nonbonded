import pytest

from nonbonded.library.models.datasets import Component
from nonbonded.library.utilities.checkmol import (
    analyse_functional_groups,
    components_to_categories,
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
    "components, expected_categories",
    [
        ([Component(smiles="CC(O)CC", mole_fraction=1.0)], ["Alcohol"]),
        ([Component(smiles="CC(=O)CC", mole_fraction=1.0)], ["Ketone"]),
        ([Component(smiles="C(=O)CC", mole_fraction=1.0)], ["Other"]),
        ([Component(smiles="CC(=O)CO", mole_fraction=1.0)], ["Alcohol", "Ketone"]),
        (
            [
                Component(smiles="CC(O)CC", mole_fraction=0.5),
                Component(smiles="CC(O)C", mole_fraction=0.5),
            ],
            ["Alcohol + Alcohol"],
        ),
        (
            [
                Component(smiles="CC(O)CC", mole_fraction=0.5),
                Component(smiles="CC(=O)CO", mole_fraction=0.5),
            ],
            ["Alcohol + Alcohol", "Alcohol ~ Ketone"],
        ),
        (
            [
                Component(smiles="CC(O)CC", mole_fraction=0.44),
                Component(smiles="CC(=O)CO", mole_fraction=0.56),
            ],
            ["Alcohol + Alcohol", "Alcohol < Ketone"],
        ),
        (
            [
                Component(smiles="CC(=O)CO", mole_fraction=0.56),
                Component(smiles="CC(O)CC", mole_fraction=0.44),
            ],
            ["Alcohol + Alcohol", "Alcohol < Ketone"],
        ),
        (
            [
                Component(smiles="CC(O)CC", mole_fraction=0.56),
                Component(smiles="CC(=O)CC", mole_fraction=0.44),
            ],
            ["Alcohol > Ketone"],
        ),
        (
            [
                Component(smiles="CC(=O)CC", mole_fraction=0.44),
                Component(smiles="CC(O)CC", mole_fraction=0.56),
            ],
            ["Alcohol > Ketone"],
        ),
        (
            [
                Component(smiles="O", mole_fraction=1.0),
                Component(smiles="CC(O)CC", mole_fraction=0.0, exact_amount=2),
            ],
            ["Aqueous (x=1.0) + Alcohol (n=2)"],
        ),
        (
            [
                Component(smiles="CC(O)CC", mole_fraction=0.0, exact_amount=2),
                Component(smiles="O", mole_fraction=1.0),
            ],
            ["Aqueous (x=1.0) + Alcohol (n=2)"],
        ),
    ],
)
def test_components_to_category(components, expected_categories):
    """Tests the `components_to_categories` function"""

    environments = [
        ChemicalEnvironment.Alcohol,
        ChemicalEnvironment.Ketone,
        ChemicalEnvironment.Aqueous,
    ]

    assert components_to_categories(components, environments) == expected_categories


def test_three_components_to_categories():

    with pytest.raises(NotImplementedError):
        components_to_categories(
            [Component(smiles="C", mole_fraction=1.0)] * 3,
            [ChemicalEnvironment.Alkane],
        )


def test_components_to_categories_empty():

    assert (
        components_to_categories([Component(smiles="C", mole_fraction=1.0)], []) == []
    )
