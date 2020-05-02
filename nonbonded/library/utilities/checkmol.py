import functools
import shutil
import subprocess
import tempfile

from openforcefield.topology import Molecule

from nonbonded.library.models.environments import ChemicalEnvironment


@functools.lru_cache(500)
def analyse_functional_groups(smiles):
    """Employs checkmol to determine which chemical moieties
    are encoded by a given smiles pattern.

    Notes
    -----
    See https://homepage.univie.ac.at/norbert.haider/cheminf/fgtable.pdf
    for information about the group numbers (i.e moiety types).

    Parameters
    ----------
    smiles: str
        The smiles pattern to examine.

    Returns
    -------
    dict of ChemicalEnvironment and int, optional
        A dictionary where each key corresponds to the `checkmol` defined group
        number, and each value if the number of instances of that moiety. If
        `checkmol` did not execute correctly, returns None.
    """

    # Make sure the checkmol utility has been installed separately.
    if shutil.which("checkmol") is None:

        raise FileNotFoundError(
            "checkmol was not found on this machine. Visit http://merian.pch.univie.ac."
            "at/~nhaider/cheminf/cmmm.html to obtain it."
        )

    openff_molecule: Molecule = Molecule.from_smiles(
        smiles, allow_undefined_stereo=True
    )

    # Save the smile pattern out as an SDF file, ready to use as input to checkmol.
    with tempfile.NamedTemporaryFile(suffix=".sdf") as file:

        openff_molecule.to_file(file.name, "SDF")

        # Execute checkmol.
        try:

            result = subprocess.check_output(
                ["checkmol", "-p", file.name], stderr=subprocess.STDOUT,
            ).decode()

        except subprocess.CalledProcessError:
            result = None

    if result is None:
        return None
    elif len(result) == 0:
        return {ChemicalEnvironment.Alkane: 1}

    groups = {}

    for group in result.splitlines():

        group_code, group_count, _ = group.split(":")

        group_environment = ChemicalEnvironment(group_code[1:])
        groups[group_environment] = int(group_count)

    return groups
