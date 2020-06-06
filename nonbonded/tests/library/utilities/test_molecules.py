from nonbonded.library.utilities.molecules import (
    find_smirks_matches,
    smiles_to_url_string,
    url_string_to_smiles,
)


def test_smiles_to_url_string():
    """A simple test that a smiles pattern with a forbidden url
    character is correctly encoded."""
    assert smiles_to_url_string("N#N") == "N%23N"


def test_url_string_to_smiles():
    """A simple test that a url encoded smiles pattern can be decoded."""
    assert url_string_to_smiles("N%23N") == "N#N"


def test_find_smirks_matches():
    """A simple test that the smirks matching utility functions as expected."""

    # Test that nothing is returned when no smirks are provided.
    assert find_smirks_matches("CCC") == []

    # Test that an alkane is correctly matched
    assert find_smirks_matches("CCC", "[#6:1]") == ["[#6:1]"]

    # Test that no matches are found for water
    assert find_smirks_matches("O", "[#6:1]") == []
