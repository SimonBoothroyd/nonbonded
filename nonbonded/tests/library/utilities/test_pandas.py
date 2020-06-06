import pandas

from nonbonded.library.utilities.pandas import reorder_data_frame


def test_reorder_data_frame():
    """Tests that the ``reorder_data_frame`` function behaves as expected
    for 1 and 2 component entries."""

    data_rows = [
        {
            "N Components": 1,
            "Component 1": "C",
            "Role": "Solvent",
            "Mole Fraction 1": 1.0,
            "Exact Amount": 1,
        },
        {
            "N Components": 2,
            "Component 1": "CC",
            "Role 1": "Solvent",
            "Mole Fraction 1": 0.25,
            "Exact Amount 1": 1,
            "Component 2": "CO",
            "Role 2": "Solute",
            "Mole Fraction 2": 0.75,
            "Exact Amount 2": 2,
        },
        {
            "N Components": 2,
            "Component 1": "CO",
            "Role 1": "Solute",
            "Mole Fraction 1": 0.75,
            "Exact Amount 1": 2,
            "Component 2": "CC",
            "Role 2": "Solvent",
            "Mole Fraction 2": 0.25,
            "Exact Amount 2": 1,
        },
    ]

    data_frame = pandas.DataFrame(data_rows)

    reordered_data_frame = reorder_data_frame(data_frame)
    assert len(reordered_data_frame) == 3

    assert reordered_data_frame.loc[0, "N Components"] == 1

    for index in [1, 2]:

        assert reordered_data_frame.loc[index, "N Components"] == 2
        assert reordered_data_frame.loc[index, "Component 1"] == "CC"
        assert reordered_data_frame.loc[index, "Role 1"] == "Solvent"
        assert reordered_data_frame.loc[index, "Mole Fraction 1"] == 0.25
        assert reordered_data_frame.loc[index, "Exact Amount 1"] == 1
        assert reordered_data_frame.loc[index, "Component 2"] == "CO"
        assert reordered_data_frame.loc[index, "Role 2"] == "Solute"
        assert reordered_data_frame.loc[index, "Mole Fraction 2"] == 0.75
        assert reordered_data_frame.loc[index, "Exact Amount 2"] == 2
