from nonbonded.library.utilities.molecules import (
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
